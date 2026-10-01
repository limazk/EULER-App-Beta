"""Tela Relatório: gera o relatório em linguagem simples da investigação (T14).

Só usa a investigação feita com os dados em uso (assinatura em `estado`). O relatório gerado
fica guardado na sessão, junto com a comparação que o produziu: baixar o HTML ou o PDF não
apaga a prévia, e mudar dados ou períodos nunca mostra um relatório antigo.
"""

import estado
import streamlit as st
import streamlit.components.v1 as components
from componentes import cabecalho, cartao

from euler.capacidades import avaliar
from euler.relatorio import comandos_operacionais, gerar_html, gerar_pdf

cabecalho(
    "Relatório",
    "Relatório em linguagem simples, com os 5 blocos fixos: **O que mudou · O que os dados "
    "sustentam · Explicações possíveis · O que falta saber · Próxima verificação**.",
    "Passo 5 de 5",
)

COMO_FAZER_PDF = (
    "O botão **Baixar PDF** precisa do pacote Playwright com o navegador Chromium "
    '(`pip install -e ".[prints]"` e depois `playwright install chromium`). Sem ele, use o '
    "botão **Imprimir ou salvar como PDF** em cima da prévia (escolha “Salvar como PDF” e o "
    "papel A4), ou baixe o HTML e imprima pelo navegador."
)

# Só na prévia do app (o arquivo baixado não muda): imprime o próprio relatório pelo
# navegador, o que dá um PDF mesmo sem o Chromium do Playwright instalado. Nada de texto
# solto no nível do módulo: o Streamlit mostraria na tela ("magic").
BARRA_IMPRESSAO = """
<div class="euler-barra" style="position:sticky;top:0;z-index:5;display:flex;gap:10px;
 align-items:center;justify-content:flex-end;padding:8px 4px 10px;background:#fff;
 border-bottom:1px solid #e5e5e5;margin-bottom:14px;font-family:Arial,sans-serif;">
 <span style="color:#666;font-size:13px;margin-right:auto;">Prévia do relatório (A4)</span>
 <button onclick="window.print()" style="cursor:pointer;border:1px solid #c2410c;
  background:#fdf1ea;color:#9a3412;font-weight:600;border-radius:6px;padding:7px 14px;
  font-size:13px;">Imprimir ou salvar como PDF</button>
</div>
<style>@media print { .euler-barra { display: none !important; } }</style>
"""


def _com_barra_de_impressao(html: str) -> str:
    if "<body>" in html:
        return html.replace("<body>", "<body>" + BARRA_IMPRESSAO, 1)
    return BARRA_IMPRESSAO + html


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

    barra = st.container(horizontal=True, vertical_alignment="center", gap="small")
    if barra.button("Gerar relatório", type="primary", icon=":material/description:"):
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
    barra.download_button(
        "Baixar HTML",
        gerado["html"],
        file_name=f"{nome}.html",
        mime="text/html",
        icon=":material/download:",
        on_click="ignore",
    )
    if gerado["pdf"]:
        barra.download_button(
            "Baixar PDF",
            gerado["pdf"],
            file_name=f"{nome}.pdf",
            mime="application/pdf",
            icon=":material/picture_as_pdf:",
            on_click="ignore",
        )
    else:
        with st.expander("Sem o botão “Baixar PDF”? Como salvar em PDF"):
            st.markdown(COMO_FAZER_PDF)
    st.markdown("#### Prévia")
    with cartao("previa"):
        components.html(_com_barra_de_impressao(gerado["html"]), height=1400, scrolling=True)


mostrar()
