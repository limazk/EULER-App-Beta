"""Peças de tela reaproveitadas por todas as páginas do app (identidade visual EULER).

Tema escuro e marca minimalista (D61, pedido do Adryan): fundo grafite, barra lateral mais
escura, interface monocromática e cor só onde informa. Só apresentação: nenhuma conta física
aqui. O estilo usa as classes que o Streamlit dá aos contêineres com `key`
(`st-key-<chave>`) e alguns `data-testid`; a versão do Streamlit está travada em
`pyproject.toml` (<2).
"""

from html import escape
from pathlib import Path

import streamlit as st

from euler.textos import RODAPE_SEGURANCA

IMAGENS = Path(__file__).resolve().parent / "imagens"
LOGO = IMAGENS / "euler_logo.svg"
MARCA = IMAGENS / "euler_marca.svg"
ICONE = IMAGENS / "euler_icone.svg"

TEMAS = {
    "dark": {
        "fundo": "#080C0E",
        "lateral": "#090D0F",
        "cartao": "#141A1C",
        "cartao_secundario": "#1D2528",
        "linha": "#293136",
        "hover": "#1D2528",
        "texto": "#F2F5F3",
        "suave": "#9AA6A1",
        "sombra": "rgba(0, 0, 0, .32)",
    },
    "light": {
        "fundo": "#F5F7FA",
        "lateral": "#FFFFFF",
        "cartao": "#FFFFFF",
        "cartao_secundario": "#F8FAFC",
        "linha": "#DDE2E9",
        "hover": "#EEF2F6",
        "texto": "#101318",
        "suave": "#626D7C",
        "sombra": "rgba(16, 19, 24, .08)",
    },
}

# Cores dos dois períodos comparados (as mesmas nas faixas do gráfico e na linha do tempo).
# A referência usa verde escuro e a comparação, âmbar escuro: ambos pertencem à paleta v3.
COR_REFERENCIA = "#173A28"
COR_COMPARACAO = "#463719"

ESTILO = f"""<style>
:root {{
  --euler-fundo: #080C0E;
  --euler-cartao: #141A1C;
  --euler-hover: #1D2528;
  --euler-lateral: #090D0F;
  --euler-texto: #F2F5F3;
  --euler-suave: #9AA6A1;
  --euler-fraco: #9AA6A1;
  --euler-linha: #293136;
  --euler-verde: #31D877;
  --euler-vermelho: #EB4B56;
  --euler-ambar: #E8B33D;
  --euler-ref: {COR_REFERENCIA};
  --euler-ref-texto: #87E7AD;
  --euler-ref-borda: #2C7048;
  --euler-comp: {COR_COMPARACAO};
  --euler-comp-texto: #F0CA70;
  --euler-comp-borda: #765E27;
}}
html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{
  background: var(--euler-fundo);
}}
header[data-testid="stHeader"] {{ background: rgba(8, 12, 14, .92); pointer-events: none; }}
header[data-testid="stHeader"] button {{ pointer-events: auto; }}
[data-testid="stSidebar"] {{ background: var(--euler-lateral); border-right: 1px solid var(--euler-linha); }}
.stMainBlockContainer {{ max-width: 1440px; padding-top: 1.8rem; padding-bottom: 3rem; }}
/* Hierarquia compacta; informações complementares ficam em expansores. */
.stMainBlockContainer h2 {{ font-size: 1.35rem; letter-spacing: -.015em; }}
[data-testid="stMetricValue"] {{ font-variant-numeric: tabular-nums; }}
.st-key-cartao-saude-selo {{ padding: 1.5rem; border-left: 3px solid var(--euler-ref-texto); }}
.st-key-cartao-saude-selo [data-testid="stMetric"] {{ background: transparent; }}
.st-key-cartao-saude-selo [data-testid="stMetricValue"] {{ font-size: 1.55rem; }}
[data-testid="stExpander"] details {{ background: transparent; }}
a:focus-visible, button:focus-visible, input:focus-visible, [tabindex]:focus-visible {{
  outline: 2px solid var(--euler-verde); outline-offset: 3px; }}
@media(max-width:640px) {{
  .stMainBlockContainer {{ padding: 1.25rem 1rem 2rem; }}
  .st-key-cartao-saude-selo {{ padding: 1rem; }}
  .st-key-euler-abertura {{ padding: 1.25rem !important; }}
  [data-testid="stMetricValue"] {{ font-size: 1.35rem; overflow-wrap: anywhere; }}
  [data-testid="stForm"] button {{ width: 100%; }}
  [data-testid="stDataFrame"] {{ max-width: calc(100vw - 2rem); overflow-x: auto; }}
}}
[data-testid="stSidebarContent"] [data-testid="stCaptionContainer"] {{ color: var(--euler-fraco); }}

/* Botões: ação primária verde, sem brilho ou gradiente. */
[data-testid="stBaseButton-primary"] {{ background: var(--euler-verde); border-color: var(--euler-verde);
  color: #07110B; font-weight: 700; }}
[data-testid="stBaseButton-primary"]:hover {{ background: #54E58D; border-color: #54E58D;
  color: #07110B; }}
[data-testid="stBaseButton-primary"] p {{ color: inherit; }}
[data-testid="stBaseButton-secondary"]:hover {{ border-color: var(--euler-verde);
  color: var(--euler-texto); }}
[data-testid="stPageLink"] a {{ border-radius: 7px; transition: background 150ms ease,
  border-color 150ms ease; }}
[data-testid="stPageLink"] a:hover {{ background: var(--euler-hover); }}

/* Cabeçalho de cada tela */
.st-key-euler-cabecalho {{ gap: .2rem; padding-bottom: 1rem; margin-bottom: .35rem;
  border-bottom: 1px solid var(--euler-linha); }}
.st-key-euler-cabecalho h1 {{ padding: .1rem 0 .35rem; letter-spacing: -.01em; }}
.st-key-euler-cabecalho [data-testid="stMarkdownContainer"] p {{ color: var(--euler-suave);
  font-size: 1.04rem; max-width: 62rem; }}
.euler-sobrelinha {{ text-transform: uppercase; letter-spacing: .12em; font-size: .72rem;
  font-weight: 600; color: var(--euler-fraco); }}

/* Cartões (contêineres com key "cartao-…") e indicadores */
[class*="st-key-cartao"] {{ background: var(--euler-cartao); }}
[class*="st-key-cartao"] {{ border-color: var(--euler-linha); border-radius: 10px;
  box-shadow: 0 10px 28px rgba(0, 0, 0, .12); }}
/* cartões lado a lado com a mesma altura (indicadores, passos, estágios) */
[data-testid="stColumn"] > [data-testid="stVerticalBlock"] {{ height: 100%; }}
[data-testid="stLayoutWrapper"]:has(> [class*="st-key-cartao-kpi"]),
[data-testid="stLayoutWrapper"]:has(> [class*="st-key-cartao-passo"]),
[data-testid="stLayoutWrapper"]:has(> [class*="st-key-cartao-estagio"]),
[data-testid="stLayoutWrapper"]:has(> [class*="st-key-cartao-exemplo"]) {{ flex: 1 1 auto; }}
[class*="st-key-cartao-kpi"], [class*="st-key-cartao-passo"],
[class*="st-key-cartao-estagio"], [class*="st-key-cartao-exemplo"] {{ flex: 1 1 auto; }}
[class*="st-key-cartao-passo"] {{ justify-content: space-between; }}
[data-testid="stMetric"] {{ background: var(--euler-cartao); }}
[data-testid="stMetricLabel"] p {{ color: var(--euler-suave); font-weight: 500; }}
.euler-secao {{ text-transform: uppercase; letter-spacing: .12em; font-size: .74rem;
  font-weight: 600; color: var(--euler-fraco); margin: .4rem 0 -.2rem; }}

/* Abertura da tela inicial */
.st-key-euler-abertura {{ background:
  var(--euler-lateral); border: 1px solid var(--euler-linha); border-radius: 10px;
  padding: 1.4rem 1.6rem 1.35rem; gap: .35rem; }}
.st-key-euler-abertura h1 {{ color: #FFFFFF; font-size: 1rem; font-weight: 750;
  letter-spacing: .18em; padding: 0; }}
.st-key-euler-abertura h3 {{ color: var(--euler-texto); font-weight: 500; max-width: 46rem; }}
.st-key-euler-abertura p, .st-key-euler-abertura li {{ color: var(--euler-suave);
  font-size: 1.05rem; max-width: 50rem; }}
.st-key-euler-abertura [data-testid="stBaseButton-primary"] p {{ color: #171717;
  font-size: 1rem; }}
.st-key-euler-abertura [data-testid="stPageLink"] a {{ border: 1px solid #3A3A3A;
  border-radius: .45rem; padding: .32rem .9rem; }}
.st-key-euler-abertura [data-testid="stPageLink"] a p,
.st-key-euler-abertura [data-testid="stPageLink"] a span {{ color: var(--euler-texto);
  font-size: 1rem; }}

/* Dashboard v3 */
.euler-dashboard-title {{ color: var(--euler-texto); font-size: clamp(1.8rem, 4vw, 2.55rem);
  line-height: 1.08; letter-spacing: -.035em; font-weight: 680; margin: .15rem 0 .3rem; }}
.euler-contexto {{ display: flex; flex-wrap: wrap; gap: .45rem; margin-top: .4rem; }}
.euler-contexto span {{ display: inline-flex; align-items: center; min-height: 1.8rem;
  padding: .25rem .58rem; border-radius: 999px; border: 1px solid var(--euler-linha);
  background: var(--euler-cartao); color: var(--euler-suave); font-size: .78rem; }}
.euler-contexto strong {{ color: var(--euler-texto); font-weight: 600; margin-left: .3rem; }}
.euler-chip {{ display: inline-flex; align-items: center; gap: .38rem; width: fit-content;
  border: 1px solid var(--euler-linha); border-radius: 999px; padding: .22rem .52rem;
  color: var(--euler-suave); background: #101618; font-size: .76rem; font-weight: 600; }}
.euler-chip::before {{ content: ""; width: .42rem; height: .42rem; border-radius: 50%;
  background: var(--euler-suave); }}
.euler-chip--positivo {{ color: #87E7AD; border-color: #28583B; }}
.euler-chip--positivo::before {{ background: var(--euler-verde); }}
.euler-chip--atencao {{ color: #F0CA70; border-color: #6C5728; }}
.euler-chip--atencao::before {{ background: var(--euler-ambar); }}
.euler-chip--alerta {{ color: #F39AA1; border-color: #6D3036; }}
.euler-chip--alerta::before {{ background: var(--euler-vermelho); }}
.euler-chip--indisponivel::before {{ background: #69736F; }}
.st-key-cartao-intelligence {{ border-style: dashed; }}
.st-key-cartao-intelligence h3 {{ margin-bottom: .15rem; }}
.st-key-cartao-intelligence [data-testid="stButton"] button {{ width: 100%; }}
.st-key-dashboard-kpis [data-testid="stMetricValue"] {{ font-size: clamp(1.35rem, 2.3vw, 2rem); }}
.st-key-dashboard-kpis [data-testid="stMetric"] {{ min-height: 8.8rem; }}

/* Botão "Próximo passo" no fim das telas do fluxo */
.st-key-euler-proximo [data-testid="stPageLink"] a {{ border: 1px solid #4A4A4A;
  border-radius: .45rem; padding: .35rem 1rem; background: var(--euler-cartao); }}
.st-key-euler-proximo [data-testid="stPageLink"] a:hover {{ border-color: #8A8A8A; }}
.st-key-euler-proximo [data-testid="stPageLink"] a p {{ color: var(--euler-texto);
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
  border-radius: 5px; background: #2A2A2A; color: var(--euler-fraco);
  border: 1px solid #333333; font-variant-numeric: tabular-nums; }}
.euler-tempo .p.ref {{ background: var(--euler-ref); color: var(--euler-ref-texto);
  border-color: var(--euler-ref-borda); font-weight: 600; }}
.euler-tempo .p.comp {{ background: var(--euler-comp); color: var(--euler-comp-texto);
  border-color: var(--euler-comp-borda); font-weight: 600; }}
.euler-tempo-legenda {{ display: flex; flex-wrap: wrap; gap: 1.4rem; font-size: .9rem;
  color: var(--euler-suave); }}
.euler-tempo-legenda b {{ color: var(--euler-texto); font-weight: 600; }}
.euler-tempo-legenda span.q {{ display: inline-block; width: .8rem; height: .8rem;
  border-radius: 3px; margin-right: .4rem; vertical-align: -1px; }}
.euler-tempo-legenda span.q.ref {{ background: var(--euler-ref);
  border: 1px solid var(--euler-ref-borda); }}
.euler-tempo-legenda span.q.comp {{ background: var(--euler-comp);
  border: 1px solid var(--euler-comp-borda); }}

/* Carregamento da investigação: feedback visual sem porcentagem inventada. */
.euler-loading-card {{
  background:
    radial-gradient(110% 140% at 0% 0%, rgba(236, 236, 236, .055) 0%, rgba(236, 236, 236, 0) 48%),
    var(--euler-lateral);
  border: 1px solid #343434;
  border-radius: 14px;
  padding: 1rem 1.1rem .95rem;
  box-shadow: 0 14px 34px rgba(0, 0, 0, .18);
}}
.euler-loading-head {{
  display: flex; align-items: center; justify-content: space-between; gap: 1rem;
}}
.euler-loading-brand {{ display: flex; align-items: center; gap: .8rem; min-width: 0; }}
.euler-loading-icon {{
  width: 38px; height: 38px; flex: 0 0 38px; display: grid; place-items: center;
  border-radius: 9px; border: 1px solid #3A3A3A; background: #1B1B1B;
  animation: euler-pulse 1.45s ease-in-out infinite;
}}
.euler-loading-icon svg {{ width: 28px; height: 28px; display: block; }}
.euler-loading-copy {{ min-width: 0; }}
.euler-loading-title {{
  color: var(--euler-texto); font-size: 1rem; font-weight: 650; line-height: 1.25;
}}
.euler-loading-stage {{
  color: var(--euler-suave); font-size: .88rem; margin-top: .18rem; line-height: 1.35;
}}
.euler-loading-live {{
  display: inline-flex; align-items: center; gap: .45rem; flex: 0 0 auto;
  color: #CFCFCF; font-size: .78rem; border: 1px solid #3A3A3A;
  border-radius: 999px; padding: .35rem .6rem; background: #202020;
}}
.euler-loading-live::before {{
  content: ""; width: .46rem; height: .46rem; border-radius: 50%; background: #ECECEC;
  box-shadow: 0 0 0 0 rgba(236, 236, 236, .3);
  animation: euler-dot 1.45s ease-out infinite;
}}
.euler-loading-track {{
  position: relative; height: 4px; overflow: hidden; margin: .9rem 0 .75rem;
  border-radius: 999px; background: #303030;
}}
.euler-loading-sweep {{
  position: absolute; inset: 0 auto 0 -34%; width: 34%; border-radius: inherit;
  background: linear-gradient(90deg, transparent, #C9C9C9, transparent);
  animation: euler-sweep 1.35s ease-in-out infinite;
}}
.euler-loading-details {{
  display: flex; flex-wrap: wrap; gap: .45rem .55rem; color: var(--euler-fraco);
  font-size: .78rem;
}}
.euler-loading-details span {{
  display: inline-flex; align-items: center; gap: .34rem;
  border: 1px solid #333333; border-radius: 999px; padding: .28rem .5rem;
  background: #232323;
}}
.euler-loading-details span::before {{ content: "·"; color: var(--euler-texto); font-weight: 700; }}
@keyframes euler-pulse {{
  0%, 100% {{ transform: scale(1); opacity: .9; }}
  50% {{ transform: scale(1.045); opacity: 1; }}
}}
@keyframes euler-dot {{
  0% {{ box-shadow: 0 0 0 0 rgba(236, 236, 236, .28); }}
  70% {{ box-shadow: 0 0 0 7px rgba(236, 236, 236, 0); }}
  100% {{ box-shadow: 0 0 0 0 rgba(236, 236, 236, 0); }}
}}
@keyframes euler-sweep {{
  0% {{ left: -34%; }}
  100% {{ left: 100%; }}
}}
@media(max-width:640px) {{
  .euler-loading-head {{ align-items: flex-start; }}
  .euler-loading-live {{ font-size: .72rem; }}
  .euler-loading-details {{ gap: .35rem; }}
  .euler-contexto {{ display: grid; grid-template-columns: 1fr; }}
  .euler-contexto span {{ width: 100%; }}
  .st-key-dashboard-kpis [data-testid="stMetric"] {{ min-height: auto; }}
}}
</style>"""


def carregamento_analise(
    titulo: str = "Analisando a caldeira…",
    etapa: str = "Investigando os períodos selecionados",
    detalhes: tuple[str, ...] | None = None,
) -> None:
    """Feedback visual durante cálculos longos, sem simular porcentagem ou tempo restante."""
    detalhes = detalhes or (
        "Consistência dos dados",
        "Balanços e indicadores",
        "Hipóteses físicas",
        "Diagnóstico e evidências",
    )
    icone = ICONE.read_text(encoding="utf-8")
    chips = "".join(f"<span>{escape(item)}</span>" for item in detalhes)
    st.html(
        f"""
        <div class="euler-loading-card" role="status" aria-live="polite">
          <div class="euler-loading-head">
            <div class="euler-loading-brand">
              <div class="euler-loading-icon" aria-hidden="true">{icone}</div>
              <div class="euler-loading-copy">
                <div class="euler-loading-title">{escape(titulo)}</div>
                <div class="euler-loading-stage">{escape(etapa)}</div>
              </div>
            </div>
            <div class="euler-loading-live">Em processamento</div>
          </div>
          <div class="euler-loading-track" aria-hidden="true">
            <div class="euler-loading-sweep"></div>
          </div>
          <div class="euler-loading-details">{chips}</div>
        </div>
        """
    )


def aplicar_estilo() -> None:
    """Injeta o estilo EULER (uma vez por execução, antes da tela)."""
    tema = st.session_state.setdefault("euler_tema", "dark")
    if tema not in TEMAS:
        tema = "dark"
        st.session_state["euler_tema"] = tema
    t = TEMAS[tema]
    st.html(ESTILO + _estilo_do_tema(t))


def _estilo_do_tema(t: dict[str, str]) -> str:
    """Sobrescreve a base visual sem interferir na lógica das páginas."""
    return f"""<style>
:root {{
  --euler-fundo: {t["fundo"]}; --euler-lateral: {t["lateral"]};
  --euler-cartao: {t["cartao"]}; --euler-cartao-2: {t["cartao_secundario"]};
  --euler-linha: {t["linha"]}; --euler-hover: {t["hover"]};
  --euler-texto: {t["texto"]}; --euler-suave: {t["suave"]};
}}
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{
  background: var(--euler-fundo); color: var(--euler-texto);
}}
[data-testid="stSidebar"] {{
  background: var(--euler-lateral); border-right: 1px solid var(--euler-linha);
  min-width: 248px; max-width: 248px;
}}
[data-testid="stSidebarContent"] {{ padding: .75rem .8rem 1rem; }}
[data-testid="stSidebarNav"] {{ padding-top: .35rem; }}
[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] {{
  min-height: 42px; border-radius: 8px; padding: .55rem .7rem; margin: 2px 0;
  color: var(--euler-suave); border: 1px solid transparent;
}}
[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"]:hover {{
  background: var(--euler-hover); color: var(--euler-texto);
}}
[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"][aria-current="page"] {{
  background: var(--euler-hover); color: var(--euler-texto); border-color: var(--euler-linha);
}}
.stMainBlockContainer {{ max-width: 1260px; padding: 3.6rem 2rem 3rem; }}
p, label, [data-testid="stMarkdownContainer"], [data-testid="stMetricValue"] {{
  color: var(--euler-texto);
}}
[data-testid="stCaptionContainer"], [data-testid="stMetricLabel"] p {{
  color: var(--euler-suave) !important;
}}
[data-testid="stVerticalBlockBorderWrapper"] {{
  border-color: var(--euler-linha) !important; border-radius: 12px !important;
  background: var(--euler-cartao); box-shadow: 0 10px 26px {t["sombra"]};
}}
[data-testid="stMetric"] {{
  background: var(--euler-cartao); border: 1px solid var(--euler-linha);
  border-radius: 12px; padding: 1rem 1.05rem;
}}
[data-testid="stMetricValue"] {{ font-size: 1.55rem; font-weight: 650; }}
[data-testid="stForm"], [data-testid="stExpander"] details,
[data-baseweb="input"] > div, [data-baseweb="select"] > div, textarea {{
  background: var(--euler-cartao-2) !important; border-color: var(--euler-linha) !important;
  color: var(--euler-texto) !important;
}}
[data-testid="stBaseButton-primary"] {{
  background: var(--euler-texto); color: var(--euler-fundo); border-color: var(--euler-texto);
  border-radius: 8px; min-height: 40px;
}}
[data-testid="stBaseButton-secondary"], [data-testid="stPageLink"] a {{
  background: var(--euler-cartao); border-color: var(--euler-linha); color: var(--euler-texto);
  border-radius: 8px;
}}
[data-testid="stBaseButton-secondary"]:hover, [data-testid="stPageLink"] a:hover {{
  background: var(--euler-hover); border-color: var(--euler-suave); color: var(--euler-texto);
}}
.st-key-euler-topbar {{
  min-height: 52px; padding: .35rem .15rem .75rem; margin-bottom: .4rem;
  border-bottom: 1px solid var(--euler-linha); align-items: center;
}}
.st-key-euler-topbar [data-testid="stButton"] button {{ min-height: 36px; }}
.euler-connected {{ display:inline-flex; align-items:center; gap:.45rem; padding:.38rem .65rem;
  border:1px solid var(--euler-linha); border-radius:999px; color:#34D399; font-size:.8rem;
  background:var(--euler-cartao); }}
.euler-connected::before {{ content:""; width:7px; height:7px; border-radius:50%; background:#34D399; }}
.euler-page-kicker {{ color: var(--euler-suave); font-size: .82rem; }}
.euler-user-card {{ display:flex; align-items:center; gap:.7rem; padding:.75rem; margin:.25rem 0 .55rem;
  background:var(--euler-cartao); border:1px solid var(--euler-linha); border-radius:10px; }}
.euler-user-avatar {{ display:grid; place-items:center; width:34px; height:34px; border-radius:50%;
  background:var(--euler-hover); color:var(--euler-texto); font-weight:700; }}
.euler-user-copy {{ display:flex; flex-direction:column; min-width:0; }}
.euler-user-copy strong {{ color:var(--euler-texto); font-size:.88rem; white-space:nowrap;
  overflow:hidden; text-overflow:ellipsis; }}
.euler-user-copy small {{ color:var(--euler-suave); font-size:.72rem; white-space:nowrap;
  overflow:hidden; text-overflow:ellipsis; }}
.st-key-euler-abertura {{ background: var(--euler-cartao); border-color: var(--euler-linha);
  box-shadow: 0 14px 34px {t["sombra"]}; padding: 1.55rem 1.7rem; }}
.st-key-euler-abertura h1 {{ font-size: 2rem; letter-spacing: -.03em; }}
.st-key-euler-cabecalho {{ border-bottom-color: var(--euler-linha); }}
.st-key-euler-login {{ max-width: 440px; margin: 3vh auto 0; padding: 1.6rem 1.7rem 1.8rem;
  background: var(--euler-cartao); border: 1px solid var(--euler-linha); border-radius: 14px;
  box-shadow: 0 24px 70px {t["sombra"]}; }}
.st-key-euler-login h1 {{ text-align:center; letter-spacing:.13em; font-size:1.7rem; }}
.st-key-euler-login > div {{ gap: .65rem; }}
.st-key-euler-login [data-testid="stForm"] {{ border: 0; padding: .35rem 0; }}
@media(max-width: 900px) {{
  [data-testid="stSidebar"] {{ min-width: 220px; max-width: 220px; }}
  .stMainBlockContainer {{ padding: 3.5rem 1.15rem 2rem; }}
}}
@media(max-width: 640px) {{
  .stMainBlockContainer {{ padding: 3.4rem .85rem 2rem; }}
  .st-key-euler-topbar {{ min-height: 44px; }}
  [data-testid="stHorizontalBlock"] {{ flex-wrap: wrap; }}
}}
</style>"""


def alternar_tema() -> None:
    """Alterna o tema na sessão corrente."""
    st.session_state["euler_tema"] = (
        "light" if st.session_state.get("euler_tema", "dark") == "dark" else "dark"
    )


def seletor_tema(*, login: bool = False) -> None:
    """Controle de tema reutilizado no shell e na autenticação."""
    claro = st.session_state.get("euler_tema", "dark") == "light"
    rotulo = "☾  Escuro" if claro else "☀  Claro"
    if login:
        _, coluna = st.columns([4, 1])
        coluna.button(rotulo, key="tema-login", on_click=alternar_tema, help="Alternar tema")
    else:
        st.button(rotulo, key="tema-shell", on_click=alternar_tema, help="Alternar tema")


def barra_superior(ctx: dict) -> None:
    """Header enxuto com estado da sessão e troca instantânea de tema."""
    with st.container(key="euler-topbar"):
        contexto, status, tema = st.columns([6, 1.25, 1.1], vertical_alignment="center")
        perfil = ctx.get("profile") or {}
        contexto.html(
            f'<div class="euler-page-kicker">EULER · {escape(perfil.get("full_name") or "Sessão ativa")}</div>'
        )
        status.html('<div class="euler-connected">Conectado</div>')
        with tema:
            seletor_tema()


def cabecalho(titulo: str, resumo: str = "", sobrelinha: str = "") -> None:
    """Cabeçalho padrão: sobrelinha (ex.: "Analisar um período"), título e uma frase de resumo."""
    with st.container(key="euler-cabecalho"):
        if sobrelinha:
            st.html(f'<div class="euler-sobrelinha">{escape(sobrelinha)}</div>')
        st.title(titulo, anchor=False)
        if resumo:
            st.markdown(resumo)


def cartao(chave: str):
    """Contêiner grafite com borda discreta (chave única na tela)."""
    return st.container(border=True, key=f"cartao-{chave}")


def chip_status(texto: str, estado: str = "neutro") -> None:
    """Selo textual acessível; a situação nunca depende somente da cor."""
    estados = {"neutro", "positivo", "atencao", "alerta", "indisponivel"}
    if estado not in estados:
        raise ValueError(f"Estado visual desconhecido: {estado}")
    st.html(f'<span class="euler-chip euler-chip--{estado}" role="status">{escape(texto)}</span>')


def cartao_indicador(
    chave: str,
    titulo: str,
    valor: str | None,
    *,
    detalhe: str,
    estado: str = "neutro",
    ajuda: str | None = None,
) -> None:
    """KPI v3 com origem/limite explícito e estado vazio padronizado."""
    with cartao(f"kpi-{chave}"):
        st.metric(titulo, valor if valor not in (None, "") else "—", help=ajuda)
        chip_status("Dados insuficientes" if valor in (None, "") else "Dado apurado", estado)
        st.caption(detalhe)


def painel_intelligence_desativado() -> None:
    """Entrada visual da IA, bloqueada e sem qualquer chamada externa."""
    with cartao("intelligence"):
        chip_status("Não configurado", "indisponivel")
        st.markdown("### EULER Intelligence")
        st.caption(
            "IA aguardando escolha de provedor. As análises científicas continuam "
            "disponíveis e independentes deste recurso."
        )
        st.button(
            "Assistente indisponível",
            disabled=True,
            icon=":material/lock:",
            key="intelligence-desativada",
        )


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


def incerteza_explicada(inc: dict | None, *, recolhido: bool = False) -> None:
    """De onde vem a faixa do desvio e o que a estreitaria (D97): texto do motor, sem conta nova."""
    if not inc:
        return
    titulo = "Por que a faixa é larga e o que a estreita"

    def corpo():
        if inc.get("frase_origem"):
            st.markdown(md(inc["frase_origem"]))
        for chave in ("condicional", "melhor"):
            if inc.get(chave):
                st.markdown(md(f"- {inc[chave]['frase']}"))
        st.caption(inc["nota"])

    if recolhido:
        with st.expander(titulo):
            corpo()
    else:
        with st.container(border=True):
            st.markdown(f"**{titulo}**")
            corpo()
