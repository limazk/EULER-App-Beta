"""Dashboard inicial: panorama real, estados vazios e atalhos para os fluxos existentes."""

from __future__ import annotations

import armazenamento
import estado
import streamlit as st
from auth import contexto_atual
from componentes import cartao, md

from euler.textos import AVISO_PROTOTIPO


def _identidade() -> tuple[str, str]:
    ctx = contexto_atual() or {}
    perfil = ctx.get("profile") or {}
    nome = (perfil.get("full_name") or ctx.get("email") or "usuário").split()[0]
    membros = ctx.get("memberships") or []
    organizacao = ""
    if membros:
        organizacao = (membros[0].get("organizations") or {}).get("name") or ""
    elif ctx.get("is_superadmin"):
        organizacao = "Administração EULER"
    return nome, organizacao


def _panorama() -> tuple[list[dict], int]:
    """Lê somente cadastros do tenant atual; nenhum indicador é estimado."""
    equipamentos: list[dict] = []
    analises = 0
    try:
        repo = armazenamento.repositorio()
        for planta in repo.listar_plantas():
            armazem = repo.armazem(planta["id"])
            for equipamento in armazem.equipamentos():
                equipamentos.append({**equipamento, "planta": planta["nome"]})
            for importacao in repo.listar_importacoes(planta["id"]):
                analises += len(repo.listar_analises(planta["id"], importacao["id"]))
    except Exception:  # noqa: BLE001 — dashboard continua útil durante indisponibilidade local
        return [], 0
    return equipamentos, analises


nome, organizacao = _identidade()
equipamentos, total_analises = _panorama()

with st.container(key="euler-abertura"):
    st.html('<div class="euler-sobrelinha">Visão geral</div>')
    st.title("EULER", anchor=False)
    st.markdown(f"## Bem-vindo, {nome}")
    st.caption(
        "Investigue mudanças no consumo, confira as evidências e escolha a próxima verificação."
        + (f" · {organizacao}" if organizacao else "")
    )

st.html('<div class="euler-secao">Panorama</div>')
k1, k2, k3, k4 = st.columns(4)
k1.metric("Caldeiras monitoradas", len(equipamentos), border=True)
k2.metric("Análises realizadas", total_analises, border=True)
k3.metric("Alertas / condições", "—", border=True, help="Sem total consolidado disponível.")
k4.metric("Eficiência média", "—", border=True, help="Não calculada sem período selecionado.")

esquerda, direita = st.columns([1.7, 1])
with esquerda, cartao("status-caldeiras"):
    st.markdown("### Status das Caldeiras")
    st.caption("Somente registros cadastrados. Medidas ausentes permanecem como —.")
    if not equipamentos:
        st.info("Nenhuma caldeira cadastrada nesta organização.")
        st.page_link(
            "paginas/acompanhamento.py",
            label="Cadastrar ou importar dados",
            icon=":material/upload:",
        )
    else:
        for equipamento in equipamentos[:6]:
            nome_eq = equipamento.get("nome") or equipamento.get("id") or "Caldeira"
            st.markdown(md(f"**{nome_eq}** · {equipamento['planta']}"))
            c1, c2, c3, c4 = st.columns([1.25, 1, 1, 1])
            c1.caption("Status  **—**")
            c2.caption("Pressão  **—**")
            c3.caption("Temperatura  **—**")
            c4.caption("Eficiência  **—**")
            st.divider()
        st.page_link(
            "paginas/painel.py", label="Abrir acompanhamento", icon=":material/arrow_forward:"
        )

with direita, cartao("resumo-dashboard"):
    st.markdown("### Resumo")
    st.caption("Indicadores são exibidos apenas quando sustentados pelos dados.")
    st.markdown("**Conexão**")
    st.success("Sessão conectada")
    st.markdown("**Dados da sessão**")
    if st.session_state.get("arquivos"):
        st.caption("Há registros carregados nesta sessão.")
    else:
        st.caption("Nenhum conjunto de dados carregado.")
    st.page_link("paginas/plantas.py", label="Ver armazém", icon=":material/inventory_2:")

st.markdown("### Ações Rápidas")
a1, a2, a3, a4 = st.columns(4)
with a1, cartao("acao-analise"):
    st.markdown("**Nova análise**")
    st.caption("Analisar dados da caldeira")
    st.page_link("paginas/saude.py", label="Abrir", icon=":material/arrow_forward:")
with a2, cartao("acao-importar"):
    st.markdown("**Importar dados**")
    st.caption("Planilhas e registros")
    st.page_link("paginas/acompanhamento.py", label="Abrir", icon=":material/arrow_forward:")
with a3, cartao("acao-dia"):
    st.markdown("**Dia a Dia**")
    st.caption("Acompanhar a planta")
    st.page_link("paginas/painel.py", label="Abrir", icon=":material/arrow_forward:")
with a4, cartao("acao-mensal"):
    st.markdown("**Relatório mensal**")
    st.caption("Conferir fechamentos")
    st.page_link("paginas/fechamentos.py", label="Abrir", icon=":material/arrow_forward:")

with st.expander("Sobre a demonstração e os limites"):
    st.info(AVISO_PROTOTIPO)
    st.markdown(
        "A demonstração usa dados sintéticos. A validação pública separada reúne 660 dias "
        "de registros de uma planta brasileira."
    )
    c1, c2 = st.columns(2)
    if c1.button("Explorar demonstração", type="primary", key="ato1"):
        estado.usar_caso_demo(completo=True)
        st.switch_page("paginas/saude.py")
    if c2.button("Ver demonstração com dados incompletos", key="ato2"):
        estado.usar_caso_demo(completo=False)
        st.switch_page("paginas/saude.py")

st.caption(
    "A EULER investiga e recomenda verificações. Não comanda nem avalia a segurança da caldeira."
)
