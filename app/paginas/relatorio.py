"""Tela Relatório: gera o relatório em linguagem simples da investigação (T14)."""

import streamlit as st
import streamlit.components.v1 as components

from euler.relatorio import comandos_operacionais, gerar_html, gerar_pdf

st.title("Relatório")
st.markdown(
    "Relatório em linguagem simples, com os 5 blocos fixos: **O que mudou · O que os dados "
    "sustentam · Explicações possíveis · O que falta saber · Próxima verificação**."
)


@st.cache_data(show_spinner="Gerando o PDF…")
def _pdf(html: str) -> bytes | None:
    return gerar_pdf(html)


def mostrar() -> None:
    j = st.session_state.get("investigacao")
    if j is None:
        st.info(
            "Primeiro escolha os períodos na tela Investigação; o relatório usa essa comparação.",
            icon=":material/troubleshoot:",
        )
        st.page_link(
            "paginas/investigacao.py", label="Ir para Investigação", icon=":material/arrow_forward:"
        )
        return
    ref, comp = j["periodos"]["referencia"]["rotulo"], j["periodos"]["comparacao"]["rotulo"]
    st.caption(f"Comparação em uso: **{ref}** (referência) × **{comp}**")
    if not st.button("Gerar relatório", type="primary", icon=":material/description:"):
        return
    html = gerar_html(j)
    if comandos_operacionais(html):  # trava de segurança: nunca deve acontecer
        st.error("O relatório não foi liberado: o texto contém um comando operacional.")
        return
    nome = f"relatorio_euler_{j.get('caldeira_id') or 'caldeira'}"
    c1, c2 = st.columns(2)
    c1.download_button(
        "Baixar HTML", html, file_name=f"{nome}.html", mime="text/html", icon=":material/download:"
    )
    pdf = _pdf(html)
    if pdf:
        c2.download_button(
            "Baixar PDF",
            pdf,
            file_name=f"{nome}.pdf",
            mime="application/pdf",
            icon=":material/picture_as_pdf:",
        )
    else:
        c2.caption("Para PDF: abra o HTML no navegador e use Imprimir → Salvar como PDF.")
    st.markdown("#### Prévia")
    components.html(html, height=1400, scrolling=True)


mostrar()
