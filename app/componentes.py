"""Peças de tela reaproveitadas por todas as páginas do app (identidade visual EULER, D58).

Só apresentação: nenhuma conta física aqui. O estilo usa as classes que o Streamlit dá aos
contêineres com `key` (`st-key-<chave>`), que são estáveis; a versão do Streamlit está
travada em `pyproject.toml` (<2).
"""

from html import escape
from pathlib import Path

import streamlit as st

from euler.textos import RODAPE_SEGURANCA

IMAGENS = Path(__file__).resolve().parent / "imagens"
LOGO = IMAGENS / "euler_logo.svg"
MARCA = IMAGENS / "euler_marca.svg"

# Cores dos dois períodos comparados (mesmas nas faixas do gráfico e na linha do tempo).
COR_REFERENCIA = "#E3E9F1"
COR_COMPARACAO = "#FBE1D2"

ESTILO = f"""<style>
:root {{
  --euler-ferrugem: #C2410C;
  --euler-ferrugem-escura: #9A3412;
  --euler-ferrugem-clara: #FDF1EA;
  --euler-marinho: #0F1B2D;
  --euler-marinho-2: #1B2C45;
  --euler-suave: #5B6573;
  --euler-linha: #DFE4EA;
  --euler-ref: {COR_REFERENCIA};
  --euler-comp: {COR_COMPARACAO};
  --euler-sombra: 0 1px 2px rgba(15, 27, 45, .05), 0 2px 8px rgba(15, 27, 45, .04);
}}
header[data-testid="stHeader"] {{ background: transparent; }}
.stMainBlockContainer {{ max-width: 1200px; padding-top: 2.4rem; padding-bottom: 3rem; }}
[data-testid="stSidebarContent"] [data-testid="stCaptionContainer"] {{ color: #9FB0C6; }}

/* Cabeçalho de cada tela */
.st-key-euler-cabecalho {{ gap: .2rem; padding-bottom: 1rem; margin-bottom: .35rem;
  border-bottom: 1px solid var(--euler-linha); }}
.st-key-euler-cabecalho h1 {{ padding: .1rem 0 .35rem; letter-spacing: -.01em; }}
.st-key-euler-cabecalho [data-testid="stMarkdownContainer"] p {{ color: var(--euler-suave);
  font-size: 1.04rem; max-width: 62rem; }}
.euler-sobrelinha {{ text-transform: uppercase; letter-spacing: .09em; font-size: .74rem;
  font-weight: 700; color: var(--euler-ferrugem); }}

/* Cartões (contêineres com key "cartao-…") e indicadores */
[class*="st-key-cartao"] {{ background: #FFFFFF; box-shadow: var(--euler-sombra); }}
/* cartões lado a lado com a mesma altura (indicadores, passos, estágios) */
[data-testid="stColumn"] > [data-testid="stVerticalBlock"] {{ height: 100%; }}
[data-testid="stLayoutWrapper"]:has(> [class*="st-key-cartao-kpi"]),
[data-testid="stLayoutWrapper"]:has(> [class*="st-key-cartao-passo"]),
[data-testid="stLayoutWrapper"]:has(> [class*="st-key-cartao-estagio"]),
[data-testid="stLayoutWrapper"]:has(> [class*="st-key-cartao-exemplo"]) {{ flex: 1 1 auto; }}
[class*="st-key-cartao-kpi"], [class*="st-key-cartao-passo"],
[class*="st-key-cartao-estagio"], [class*="st-key-cartao-exemplo"] {{ flex: 1 1 auto; }}
[class*="st-key-cartao-passo"] {{ justify-content: space-between; }}
[data-testid="stMetric"] {{ background: #FFFFFF; }}
[data-testid="stMetricLabel"] p {{ color: var(--euler-suave); font-weight: 600; }}
.euler-secao {{ text-transform: uppercase; letter-spacing: .08em; font-size: .78rem;
  font-weight: 700; color: var(--euler-suave); margin: .2rem 0 -.2rem; }}

/* Abertura da tela inicial */
.st-key-euler-abertura {{ background: linear-gradient(135deg, var(--euler-marinho) 0%,
  var(--euler-marinho-2) 100%); border-radius: 18px; padding: 2.4rem 2.6rem 2.2rem;
  gap: .6rem; }}
.st-key-euler-abertura h1 {{ color: #FFFFFF; font-size: 3rem; letter-spacing: .14em;
  padding: 0; }}
.st-key-euler-abertura h3 {{ color: #FFFFFF; font-weight: 600; max-width: 46rem; }}
.st-key-euler-abertura p, .st-key-euler-abertura li {{ color: #C9D3E0; font-size: 1.05rem;
  max-width: 50rem; }}
.st-key-euler-abertura .euler-sobrelinha {{ color: #F0A07A; }}
.st-key-euler-abertura [data-testid="stPageLink"] a {{ border: 1px solid #3A4E6B;
  border-radius: .5rem; padding: .32rem .9rem; background: rgba(255, 255, 255, .04); }}
.st-key-euler-abertura [data-testid="stPageLink"] a p,
.st-key-euler-abertura [data-testid="stPageLink"] a span {{ color: #FFFFFF; font-size: 1rem; }}

/* Botão "Próximo passo" no fim das telas do fluxo */
.st-key-euler-proximo [data-testid="stPageLink"] a {{ border: 1px solid var(--euler-ferrugem);
  border-radius: .5rem; padding: .35rem 1rem; background: var(--euler-ferrugem-clara); }}
.st-key-euler-proximo [data-testid="stPageLink"] a p {{ color: var(--euler-ferrugem-escura);
  font-weight: 600; }}

/* Envio de arquivos: o componente do Streamlit vem em inglês ("Upload", "200MB per file").
   O texto original fica com tamanho zero e o português entra no lugar. */
[data-testid="stFileUploaderDropzone"] button [data-testid="stMarkdownContainer"] p {{
  font-size: 0; }}
[data-testid="stFileUploaderDropzone"] button [data-testid="stMarkdownContainer"] p::after {{
  content: "Escolher arquivos"; font-size: .875rem; }}
[data-testid="stFileUploaderDropzoneInstructions"],
[data-testid="stFileUploaderDropzoneInstructions"] * {{ white-space: normal;
  overflow: visible; text-overflow: clip; }}
[data-testid="stFileUploaderDropzoneInstructions"] span {{ font-size: 0; }}
[data-testid="stFileUploaderDropzoneInstructions"] span::after {{
  content: "ou arraste para cá · CSV ou planilha .xlsx"; font-size: .82rem; }}

/* Linha do tempo dos períodos comparados (tela Investigação) */
.euler-tempo {{ display: flex; gap: 4px; margin: .2rem 0 .3rem; }}
.euler-tempo .p {{ flex: 1; text-align: center; font-size: .78rem; padding: .45rem 0;
  border-radius: 6px; background: #F3F5F8; color: #7A8594; border: 1px solid #E7EBF0; }}
.euler-tempo .p.ref {{ background: var(--euler-ref); color: #22324A; border-color: #C9D3E0;
  font-weight: 600; }}
.euler-tempo .p.comp {{ background: var(--euler-comp); color: var(--euler-ferrugem-escura);
  border-color: #F3C3A6; font-weight: 600; }}
.euler-tempo-legenda {{ display: flex; flex-wrap: wrap; gap: 1.4rem; font-size: .9rem;
  color: #2B3645; }}
.euler-tempo-legenda span.q {{ display: inline-block; width: .8rem; height: .8rem;
  border-radius: 3px; margin-right: .4rem; vertical-align: -1px; }}
</style>"""


def aplicar_estilo() -> None:
    """Injeta o estilo EULER (uma vez por execução, antes da tela)."""
    st.html(ESTILO)


def cabecalho(titulo: str, resumo: str = "", sobrelinha: str = "") -> None:
    """Cabeçalho padrão: sobrelinha (ex.: "Passo 3 de 5"), título e uma frase de resumo."""
    with st.container(key="euler-cabecalho"):
        if sobrelinha:
            st.html(f'<div class="euler-sobrelinha">{escape(sobrelinha)}</div>')
        st.title(titulo, anchor=False)
        if resumo:
            st.markdown(resumo)


def cartao(chave: str):
    """Contêiner com borda e fundo branco (chave única na tela)."""
    return st.container(border=True, key=f"cartao-{chave}")


def secao(texto: str) -> None:
    """Rótulo pequeno de seção, em maiúsculas (ex.: "Resultado")."""
    st.html(f'<div class="euler-secao">{escape(texto)}</div>')


def proximo_passo(pagina: str, rotulo: str) -> None:
    """Botão para a próxima tela do fluxo, alinhado à direita."""
    with st.container(key="euler-proximo", horizontal=True, horizontal_alignment="right"):
        st.page_link(
            pagina,
            label=f"Próximo: {rotulo}",
            icon=":material/arrow_forward:",
            icon_position="right",
        )


def rodape() -> None:
    """Mostra o rodapé de segurança (obrigatório em todas as telas)."""
    st.divider()
    st.caption(RODAPE_SEGURANCA)


def md(texto: str) -> str:
    """Protege o "$" para o Markdown do Streamlit não confundir "R$ … R$" com fórmula."""
    return texto.replace("$", r"\$")
