"""Ponte entre a sessão Streamlit e o arquivo SQLite de cada planta.

Arquiva conjuntos completos; não concatena períodos nem altera dados científicos.
Uma análise só é atual se arquivos, local, planta e versão do motor coincidirem.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3

import streamlit as st

from euler.persistencia import Repositorio, raiz_padrao

ERROS = (ValueError, OSError, sqlite3.Error)


def repositorio() -> Repositorio:
    """Isola a biblioteca local por organização durante o beta multiusuário."""
    try:
        from auth import contexto_atual

        ctx = contexto_atual()
    except ImportError:
        ctx = None

    if not ctx:
        return Repositorio()

    memberships = ctx.get("memberships") or []
    if memberships:
        tenant_id = memberships[0]["organization_id"]
    elif ctx.get("is_superadmin"):
        tenant_id = f"admin-{ctx['user_id']}"
    else:
        raise ValueError("Usuário autenticado ainda não possui organização.")

    return Repositorio(raiz_padrao() / "tenants" / tenant_id)


def contexto() -> dict | None:
    return st.session_state.get("persistencia")


def _assinatura_entrada() -> str:
    dados = {
        "arquivos": [
            [n, hashlib.sha256(b).hexdigest()] for n, b in st.session_state.get("arquivos", ())
        ],
        "altitude": st.session_state.get("altitude_m"),
        "sinteticos": st.session_state.get("dados_sinteticos", False),
    }
    return hashlib.sha256(json.dumps(dados, sort_keys=True).encode()).hexdigest()


def abrir_importacao(planta: dict, importacao_id: str, autor: str = "") -> None:
    """Lê e valida antes de trocar a sessão; não reutiliza análise de outro motor."""
    import estado

    repo = repositorio()
    salvo = repo.carregar_importacao(planta["id"], importacao_id)
    analises = repo.listar_analises(planta["id"], importacao_id)
    estado.limpar_dados()
    estado.definir_arquivos(salvo["arquivos"], salvo["rotulo"], salvo["sinteticos"])
    st.session_state["altitude_m"] = salvo["altitude"]
    st.session_state["persistencia"] = {
        "planta_id": planta["id"],
        "planta_nome": planta["nome"],
        "importacao_id": importacao_id,
        "entrada": _assinatura_entrada(),
        "autor": autor,
    }
    atual = estado.assinatura()
    compativeis = [
        a
        for a in analises
        if a["assinatura"] == atual
        and isinstance(a["resultado"], dict)
        and isinstance(a["resultado"].get("investigacao"), dict)
    ]
    if compativeis:
        resultado = compativeis[0]["resultado"]
        st.session_state["investigacao"] = {"assinatura": atual, "json": resultado["investigacao"]}
        periodos = resultado.get("periodos_escolhidos")
        if (
            isinstance(periodos, dict)
            and periodos.get("assinatura") == atual
            and all(
                isinstance(periodos.get(chave), (list, tuple))
                and len(periodos[chave]) == 2
                and all(type(i) is int and i >= 0 for i in periodos[chave])
                for chave in ("ref", "comp")
            )
        ):
            st.session_state["periodos_escolhidos"] = {
                **periodos,
                "ref": tuple(periodos["ref"]),
                "comp": tuple(periodos["comp"]),
            }
    elif analises:
        st.session_state["persistencia_aviso"] = (
            "Há análises históricas de outro contexto, versão do motor ou formato. "
            "Após uma restauração, a planta também recebe uma nova identificação. "
            "Recalcule a investigação para usar o contexto atual; o histórico continua disponível."
        )


def salvar_sessao(planta: dict, *, autor: str, motivo: str) -> dict:
    """Grava a versão inteira; só associa a sessão depois do commit bem-sucedido."""
    import estado

    arquivos = dict(st.session_state.get("arquivos", ()))
    if not arquivos:
        raise ValueError("Importe arquivos antes de salvar uma versão.")
    ctx = contexto()
    anterior = ctx["importacao_id"] if ctx and ctx["planta_id"] == planta["id"] else None
    salvo = repositorio().salvar_importacao(
        planta["id"],
        arquivos,
        altitude=estado.altitude_m(),
        rotulo=estado.rotulo_dados(),
        sinteticos=estado.dados_sinteticos(),
        autor=autor,
        motivo=motivo,
        anterior_id=anterior,
    )
    abrir_importacao(planta, salvo["id"], autor)
    return salvo


def importar_na_planta(
    arquivos: dict[str, bytes], altitude: float | None, *, autor: str, motivo: str
) -> dict:
    """Importação explícita da tela: substitui o conjunto ativo, preservando anteriores."""
    ctx = contexto()
    if not ctx:
        raise ValueError("Abra uma planta salva antes de importar uma nova versão nela.")
    repo = repositorio()
    planta = next(p for p in repo.listar_plantas() if p["id"] == ctx["planta_id"])
    salvo = repo.salvar_importacao(
        ctx["planta_id"],
        arquivos,
        altitude=altitude,
        rotulo=f"{len(arquivos)} arquivo(s) enviado(s)",
        sinteticos=planta["classe"] == "sintetico",
        autor=autor,
        motivo=motivo,
        anterior_id=ctx["importacao_id"],
    )
    abrir_importacao({"id": ctx["planta_id"], "nome": ctx["planta_nome"]}, salvo["id"], autor)
    return salvo


def abrir_serie(planta, armazem, equip_id, *, autor):
    """Materializa uma revisão canônica para o motor; mantém os arquivos originais intactos."""
    arquivos = armazem.arquivos(equip_id)
    if not arquivos:
        raise ValueError("Confirme os registros do equipamento antes de analisar a série.")
    revisao = armazem.revisao
    salvo = repositorio().salvar_importacao(
        planta["id"],
        arquivos,
        altitude=armazem.equipamento(equip_id)["config"]["altitude_m"],
        rotulo=f"Série consolidada · {equip_id} · revisão {revisao}",
        sinteticos=armazem.info["classe"] == "sintetico",
        autor=autor,
        motivo=f"Materialização dos registros normalizados de {equip_id}, revisão {revisao}; originais preservados nos lotes.",
    )
    abrir_importacao(planta, salvo["id"], autor)


def guardar_analise(j: dict) -> None:
    """Persiste somente análise produzida pela entrada salva; falha fica visível na tela."""
    import estado

    ctx = contexto()
    if not ctx:
        return
    try:
        if ctx["entrada"] != _assinatura_entrada():
            raise ValueError(
                "A entrada atual não corresponde à versão salva. Salve uma nova versão "
                "em Plantas e histórico antes de arquivar esta análise."
            )
        repositorio().salvar_analise(
            ctx["planta_id"],
            ctx["importacao_id"],
            assinatura=estado.assinatura(),
            resultado={
                "investigacao": j,
                "periodos_escolhidos": st.session_state.get("periodos_escolhidos"),
            },
        )
        st.session_state.pop("persistencia_erro", None)
    except ERROS as exc:
        st.session_state["persistencia_erro"] = f"Análise não salva no banco: {exc}"


def situacao() -> str:
    ctx = contexto()
    if not ctx:
        return "Dados somente nesta sessão. Salve em Plantas e histórico para reabrir depois."
    if ctx["entrada"] != _assinatura_entrada():
        return "Dados alterados nesta sessão; salve uma nova versão para preservá-los."
    return f"Salvo em {ctx['planta_nome']} · versão {ctx['importacao_id'][:8]}"
