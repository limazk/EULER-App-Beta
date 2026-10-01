"""Ponto de entrada do app EULER.

Rodar com: streamlit run app/main.py
"""

import streamlit as st
from componentes import rodape

import euler

st.set_page_config(page_title="EULER", page_icon=":material/local_fire_department:", layout="wide")

paginas = [
    st.Page("paginas/inicio.py", title="Início", icon=":material/home:", default=True),
    st.Page("paginas/importar.py", title="Importar dados", icon=":material/upload_file:"),
    st.Page(
        "paginas/calculadora.py", title="Calculadora de referência", icon=":material/calculate:"
    ),
]

navegacao = st.navigation(paginas)
st.sidebar.caption(f"EULER · protótipo v{euler.__version__} · dados sintéticos")
# As telas não usam st.stop(): o rodapé de segurança precisa aparecer sempre.
navegacao.run()
rodape()
