"""Ponto de entrada do app EULER.

Rodar com: streamlit run app/main.py
"""

import estado
import streamlit as st
from componentes import LOGO, MARCA, aplicar_estilo, rodape

import euler

st.set_page_config(
    page_title="EULER",
    page_icon=str(MARCA),
    layout="wide",
    initial_sidebar_state="expanded",
)
st.logo(str(LOGO), icon_image=str(MARCA), size="large")
aplicar_estilo()

paginas = {
    "": [st.Page("paginas/inicio.py", title="Início", icon=":material/home:", default=True)],
    "Investigar": [
        st.Page("paginas/importar.py", title="1. Importar dados", icon=":material/upload_file:"),
        st.Page("paginas/limites.py", title="2. Dados e limites", icon=":material/rule:"),
        st.Page("paginas/investigacao.py", title="3. Investigação", icon=":material/troubleshoot:"),
        st.Page(
            "paginas/extrato.py", title="4. Extrato por fornecedor", icon=":material/receipt_long:"
        ),
        st.Page("paginas/relatorio.py", title="5. Relatório", icon=":material/description:"),
    ],
    "Referência": [
        st.Page(
            "paginas/calculadora.py", title="Calculadora de referência", icon=":material/calculate:"
        ),
    ],
}

navegacao = st.navigation(paginas)
# As telas não usam st.stop(): o rodapé de segurança precisa aparecer sempre.
navegacao.run()
rodape()
# depois da tela: um clique que troca os dados já aparece nesta mesma execução
if not st.session_state.get("arquivos"):
    situacao_dados = "sem dados carregados"
elif estado.dados_sinteticos():
    situacao_dados = "**dados sintéticos** em uso"
else:
    situacao_dados = "dados enviados em uso (não sintéticos)"
st.sidebar.caption(f"EULER · protótipo v{euler.__version__} · {situacao_dados}")
