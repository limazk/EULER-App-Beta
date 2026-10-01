"""Estado compartilhado entre as telas: arquivos enviados, configuração do local e dados importados.

Resultados derivados (investigação, relatório gerado) são guardados junto com a
**assinatura** dos dados que os produziram (arquivos + altitude). Uma tela só mostra um
resultado guardado se a assinatura bater com os dados em uso: trocar os arquivos ou a
altitude nunca deixa um resultado antigo aparecer como se fosse dos dados novos.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import streamlit as st

from euler.io import Pacote, fontes_de_arquivos, importar_pacote
from euler.vapor import p_atm_por_altitude_bar

RAIZ = Path(__file__).resolve().parents[1]


@st.cache_data(show_spinner="Importando…")
def _importar(arquivos: tuple[tuple[str, bytes], ...], p_atm_bar: float | None) -> Pacote:
    fontes, avisos = fontes_de_arquivos(dict(arquivos))
    pacote = importar_pacote(fontes, p_atm_bar=p_atm_bar)
    pacote.avisos_gerais += avisos
    return pacote


def ler_pasta(pasta: Path) -> dict[str, bytes]:
    """Lê os CSVs de uma pasta do repositório como se tivessem sido enviados."""
    return {p.name: p.read_bytes() for p in sorted(pasta.glob("*.csv"))}


def definir_arquivos(arquivos: dict[str, bytes], rotulo: str, sinteticos: bool = False) -> None:
    """Troca os dados da sessão. `sinteticos`: exemplos do próprio projeto (marcados como tal)."""
    st.session_state["arquivos"] = tuple(sorted(arquivos.items()))
    st.session_state["rotulo_dados"] = rotulo
    st.session_state["dados_sinteticos"] = sinteticos
    esquecer_resultados()


def dados_sinteticos() -> bool:
    """True quando os dados em uso são sintéticos: um exemplo do projeto, ou arquivos em que
    toda linha com origem declarada diz `sintetico`."""
    if not st.session_state.get("arquivos"):
        return False
    if st.session_state.get("dados_sinteticos"):
        return True
    p = pacote()
    return p is not None and p.sintetico


def assinatura() -> str | None:
    """Identifica os dados em uso (conteúdo dos arquivos + altitude); None sem dados."""
    arquivos = st.session_state.get("arquivos")
    if not arquivos:
        return None
    h = hashlib.sha256(repr(st.session_state.get("altitude_m")).encode())
    for nome, dados in arquivos:
        h.update(nome.encode())
        h.update(dados)
    return h.hexdigest()[:16]


def esquecer_resultados() -> None:
    """Descarta investigação e relatório guardados (dados trocados ou comparação inválida)."""
    st.session_state.pop("investigacao", None)
    st.session_state.pop("relatorio_gerado", None)


def guardar_investigacao(j: dict) -> None:
    st.session_state["investigacao"] = {"assinatura": assinatura(), "json": j}


def investigacao_atual() -> tuple[dict | None, str]:
    """(JSON da investigação, motivo). JSON None se não houver investigação destes dados.

    motivo: "" (há investigação), "nenhuma" ou "dados_mudaram".
    """
    guardada = st.session_state.get("investigacao")
    if guardada is None:
        return None, "nenhuma"
    if guardada["assinatura"] != assinatura():
        return None, "dados_mudaram"
    return guardada["json"], ""


ALTITUDE_DEMO_M = 1000.0


def usar_caso_demo() -> None:
    """Carrega o caso de demonstração sintético (demo/caso_demo) e a altitude dele."""
    definir_arquivos(
        ler_pasta(RAIZ / "demo" / "caso_demo"),
        "caso de demonstração (caldeira sintética de 20 t/h, 8 semanas)",
        sinteticos=True,
    )
    st.session_state["altitude_m"] = ALTITUDE_DEMO_M


def altitude_m() -> float | None:
    return st.session_state.get("altitude_m")


def p_atm_bar() -> float | None:
    alt = altitude_m()
    return None if alt is None else p_atm_por_altitude_bar(alt)


def pacote() -> Pacote | None:
    """Dados importados na sessão (ou None se nada foi enviado)."""
    arquivos = st.session_state.get("arquivos")
    if not arquivos:
        return None
    return _importar(arquivos, p_atm_bar())


def rotulo_dados() -> str:
    return st.session_state.get("rotulo_dados", "")


def exigir_pacote() -> Pacote | None:
    """Para telas que dependem de dados: devolve o pacote ou mostra como importar.

    Não usa st.stop(), para o rodapé de segurança sempre aparecer.
    """
    p = pacote()
    if p is None:
        st.info("Nenhum dado importado ainda.", icon=":material/upload_file:")
        st.page_link(
            "paginas/importar.py", label="Ir para Importar dados", icon=":material/arrow_forward:"
        )
        return None
    selo = " · :orange-badge[:material/science: DADOS SINTÉTICOS]" if dados_sinteticos() else ""
    st.caption(f":material/database: Dados em uso: **{rotulo_dados()}**{selo}")
    return p
