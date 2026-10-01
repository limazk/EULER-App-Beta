"""Ponto de entrada do app EULER.

Rodar com: streamlit run app/main.py
"""

import streamlit as st
from componentes import rodape

import euler

st.set_page_config(page_title="EULER", page_icon=":material/local_fire_department:", layout="wide")

paginas = [
    st.Page("paginas/inicio.py", title="Início", icon=":material/home:", default=True),
]

navegacao = st.navigation(paginas)
st.sidebar.caption(f"EULER · protótipo v{euler.__version__} · dados sintéticos")
navegacao.run()
rodape()
