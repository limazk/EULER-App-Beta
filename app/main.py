"""Ponto de entrada do app EULER.

Rodar com: streamlit run app/main.py
"""

import streamlit as st
from componentes import rodape

import euler

st.set_page_config(page_title="EULER", page_icon=":material/local_fire_department:", layout="wide")

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
st.sidebar.caption(f"EULER · protótipo v{euler.__version__} · dados sintéticos")
# As telas não usam st.stop(): o rodapé de segurança precisa aparecer sempre.
navegacao.run()
rodape()
