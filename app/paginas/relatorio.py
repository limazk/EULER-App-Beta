"""Tela Relatório: gera o relatório em linguagem simples da investigação (T14).

Só usa a investigação feita com os dados em uso (assinatura em `estado`). O relatório gerado
fica guardado na sessão, junto com a comparação que o produziu: baixar o HTML ou o PDF não
apaga a prévia, e mudar dados ou períodos nunca mostra um relatório antigo.
"""

import estado
import streamlit as st
import streamlit.components.v1 as components

from euler.capacidades import avaliar
from euler.relatorio import comandos_operacionais, gerar_html, gerar_pdf

st.title("Relatório")
st.markdown(
    "Relatório em linguagem simples, com os 5 blocos fixos: **O que mudou · O que os dados "
    "sustentam · Explicações possíveis · O que falta saber · Próxima verificação**."
)

COMO_FAZER_PDF = (
    "PDF direto indisponível neste computador (precisa do pacote Playwright com o navegador "
    'Chromium: `pip install -e ".[prints]"` e `playwright install chromium`). Alternativa: '
    "baixe o HTML, abra no navegador e use **Imprimir → Salvar como PDF** (A4)."
)


@st.cache_data(show_spinner="Gerando o PDF…")
def _pdf(html: str) -> bytes | None:
    return gerar_pdf(html)


def _sem_investigacao(motivo: str) -> None:
    if estado.pacote() is None:
        st.info("Nenhum dado importado ainda.", icon=":material/upload_file:")
        st.page_link(
            "paginas/importar.py", label="Ir para Importar dados", icon=":material/arrow_forward:"
        )
        return
    if not {c.id: c for c in avaliar(estado.pacote())}["comparacao"].habilitada:
        st.info(
            "Com estes dados a investigação está bloqueada, então não há relatório a gerar. "
            "Veja o motivo e o que medir em Dados e limites.",
            icon=":material/block:",
        )
        st.page_link(
            "paginas/limites.py", label="Ir para Dados e limites", icon=":material/arrow_forward:"
        )
        return
    if motivo == "dados_mudaram":
        st.warning(
            "Os dados mudaram depois da última investigação. Abra a Investigação de novo: o "
            "relatório só usa uma comparação feita com os dados em uso.",
            icon=":material/sync_problem:",
        )
    else:
        st.info(
            "Primeiro escolha os períodos na tela Investigação; o relatório usa essa comparação.",
            icon=":material/troubleshoot:",
        )
    st.page_link(
        "paginas/investigacao.py", label="Ir para Investigação", icon=":material/arrow_forward:"
    )


def mostrar() -> None:
    j, motivo = estado.investigacao_atual()
    if j is None:
        _sem_investigacao(motivo)
        return
    ref, comp = j["periodos"]["referencia"]["rotulo"], j["periodos"]["comparacao"]["rotulo"]
    st.caption(f"Comparação em uso: **{ref}** (referência) × **{comp}** (comparação)")
    chave = (estado.assinatura(), ref, comp)

    if st.button("Gerar relatório", type="primary", icon=":material/description:"):
        html = gerar_html(j)
        if comandos_operacionais(html):  # trava de segurança: nunca deve acontecer
            st.error("O relatório não foi liberado: o texto contém um comando operacional.")
            return
        st.session_state["relatorio_gerado"] = {"chave": chave, "html": html, "pdf": _pdf(html)}

    gerado = st.session_state.get("relatorio_gerado")
    if gerado is None or gerado["chave"] != chave:
        st.caption("Clique em **Gerar relatório** para montar o relatório desta comparação.")
        return

    nome = f"relatorio_euler_{j.get('caldeira_id') or 'caldeira'}"
    c1, c2 = st.columns(2)
    c1.download_button(
        "Baixar HTML",
        gerado["html"],
        file_name=f"{nome}.html",
        mime="text/html",
        icon=":material/download:",
        on_click="ignore",
    )
    if gerado["pdf"]:
        c2.download_button(
            "Baixar PDF",
            gerado["pdf"],
            file_name=f"{nome}.pdf",
            mime="application/pdf",
            icon=":material/picture_as_pdf:",
            on_click="ignore",
        )
    else:
        c2.caption(COMO_FAZER_PDF)
    st.markdown("#### Prévia")
    components.html(gerado["html"], height=1400, scrolling=True)


mostrar()
