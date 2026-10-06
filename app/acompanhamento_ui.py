"""Peças comuns das telas de acompanhamento (painel, atualizar dados, fechamentos, ações).

Só apresentação e escolha da planta/equipamento; regras e cálculos ficam em `euler/`. O banco
é o mesmo da biblioteca de plantas (`armazenamento.repositorio()`), um arquivo por planta,
fora da pasta do código.
"""

from __future__ import annotations

from contextlib import contextmanager

import armazenamento as arm
import pandas as pd
import streamlit as st
from componentes import md

from euler.armazem import CLASSES, ErroArmazem
from euler.formato import num

ESTADOS_COR = {
    "acima": "orange",
    "abaixo": "green",
    "nao_estabelecido": "gray",
    "sem_faixa": "gray",
}


def brl(v) -> str:
    return "—" if v is None else ("−" if v < 0 else "") + f"R$ {num(abs(v), 0)}"


def data(x) -> str:
    return "—" if not x else f"{pd.Timestamp(x):%d/%m/%Y}"


def periodo(p: dict) -> str:
    return f"{data(p['inicio'])} a {data(p['fim'])}"


def _guardar_autor() -> None:
    st.session_state["acomp_autor_salvo"] = st.session_state["acomp_autor"]


def autor() -> str:
    """Nome de quem registra; fica no histórico de cada alteração.

    Digitado uma vez por sessão: cada tela cria o próprio campo (e o Streamlit o recria vazio
    ao trocar de tela), então o nome fica guardado fora do campo e é devolvido a ele.
    """
    st.session_state["acomp_autor"] = st.session_state.get("acomp_autor_salvo", "")
    return st.sidebar.text_input(
        "Seu nome (vai para o histórico)",
        key="acomp_autor",
        placeholder="obrigatório para registrar",
        on_change=_guardar_autor,
    ).strip()


def exigir_autor(nome: str) -> bool:
    if not nome:
        st.warning("Informe seu nome na barra lateral para registrar alterações.")
        return False
    return True


def chave_form(nome: str) -> str:
    """Chave de formulário que muda depois de cada gravação: os campos voltam limpos e o
    mesmo texto não é enviado duas vezes por engano."""
    return f"{nome}_{st.session_state.get('acomp_geracao', 0)}"


def recarregar(aviso: str | None = None) -> None:
    """Redesenha a tela com os dados recém-gravados; o aviso aparece no topo da próxima."""
    if aviso:
        st.session_state["acomp_aviso"] = aviso
    st.session_state["acomp_geracao"] = st.session_state.get("acomp_geracao", 0) + 1
    st.rerun()


def mostrar_aviso() -> None:
    """Aviso da última gravação, num espaço que sempre existe (com ou sem aviso).

    O espaço fixo mantém a posição dos blocos seguintes entre um desenho e outro; sem ele,
    abas com chave podiam deixar uma cópia velha na tela depois de redesenhar.
    """
    espaco = st.container()
    aviso = st.session_state.pop("acomp_aviso", None)
    if aviso:
        espaco.success(md(aviso), icon=":material/check_circle:")


def executar(acao, sucesso: str | None = None, *, recarregar_tela: bool = False):
    """Executa uma escrita; quando a regra recusa, mostra o motivo em vez de quebrar a tela.

    Com `recarregar_tela`, a tela é redesenhada depois do sucesso (contagens, histórico e
    situação já atualizados) e `sucesso` aparece no topo.
    """
    try:
        r = acao()
    except (ErroArmazem, *arm.ERROS) as e:
        st.error(str(e))
        return None
    except Exception as e:  # noqa: BLE001 — bloqueios do motor (AnaliseBloqueada etc.)
        st.error(f"Não foi possível concluir: {e}")
        return None
    if recarregar_tela:
        recarregar(sucesso)
    if sucesso:
        st.toast(sucesso)
    return True if r is None else r  # sucesso sempre verdadeiro; falha devolve None


def aviso_dados_salvos(passo: tuple[str, ...] = ()) -> None:
    """Deixa claro que a tela usa os dados gravados da planta, não os da sessão (D102)."""
    st.caption(
        ":material/database: **Dados salvos da planta.** O que você confirmar aqui fica "
        "gravado no histórico, com autor e data."
    )
    if passo:
        from blocos.percurso import marcador

        marcador(*passo)


@contextmanager
def planta_e_equipamento(exigir_equipamento: bool = True, passo: tuple[str, ...] = ()):
    """Escolha da planta e do equipamento; entrega (repo, planta, armazém, equipamento).

    Fecha o arquivo da planta ao final da tela. Sem planta ou equipamento, mostra o caminho
    para cadastrar e entrega None. `passo`: em qual passo do percurso da planta a tela está
    (D102); aparece numa linha abaixo da escolha, junto do aviso de que os dados são salvos.
    """
    mostrar_aviso()
    repo = arm.repositorio()
    plantas = {p["id"]: p for p in repo.listar_plantas()}
    if not plantas:
        st.info(
            "Nenhuma planta cadastrada nesta instalação. Comece em **Atualizar dados** "
            "(cadastro e primeira importação) ou crie a planta de demonstração lá."
        )
        st.page_link(
            "paginas/acompanhamento.py", label="Ir para Atualizar dados", icon=":material/upload:"
        )
        yield None
        return
    ids = list(plantas)
    atual = st.session_state.get("acomp_planta_atual")
    c1, c2 = st.columns(2)
    pid = c1.selectbox(
        "Planta",
        ids,
        index=ids.index(atual) if atual in ids else 0,
        format_func=lambda i: plantas[i]["nome"],
        key="acomp_planta_sel",
    )
    st.session_state["acomp_planta_atual"] = pid
    planta = plantas[pid]
    if planta["classe"] not in CLASSES:
        st.info(
            "Esta planta veio da biblioteca anterior: classifique a origem dos dados em Plantas e histórico."
        )
        st.page_link("paginas/plantas.py", label="Classificar planta", icon=":material/database:")
        yield None
        return
    a = repo.armazem(pid)
    try:
        equips = a.equipamentos()
        if not equips:
            if exigir_equipamento:
                st.info("Esta planta ainda não tem equipamento: cadastre em **Atualizar dados**.")
                st.page_link(
                    "paginas/acompanhamento.py",
                    label="Ir para Atualizar dados",
                    icon=":material/upload:",
                )
                yield None
            else:
                yield repo, planta, a, None
            return
        por_id = {e["id"]: e for e in equips}
        eq_atual = st.session_state.get("acomp_equip_atual")
        eid = c2.selectbox(
            "Equipamento",
            list(por_id),
            index=list(por_id).index(eq_atual) if eq_atual in por_id else 0,
            format_func=lambda i: f"{por_id[i]['nome']} · {por_id[i]['caldeira_id']}",
            key="acomp_equip_sel",
        )
        st.session_state["acomp_equip_atual"] = eid
        aviso_dados_salvos(passo)
        if planta["classe"] == "sintetico":
            st.caption(":orange[DADOS SINTÉTICOS] · não representam uma planta real.")
        yield repo, planta, a, por_id[eid]
    finally:
        a.fechar()


def faixa_situacao(situacao: str | None, frase: str) -> None:
    if situacao == "acima":
        st.warning(md(frase), icon=":material/trending_up:")
    elif situacao == "abaixo":
        st.success(md(frase), icon=":material/trending_down:")
    else:
        st.info(md(frase), icon=":material/info:")
