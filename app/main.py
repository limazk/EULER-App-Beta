"""Ponto de entrada do app EULER.

Rodar com: streamlit run app/main.py
"""

import os

import estado
import streamlit as st
from auth import exigir_acesso, painel_conta_sidebar
from componentes import ICONE, LOGO, MARCA, aplicar_estilo, rodape
from navegacao import menu_lateral, todas_as_paginas

import euler

st.set_page_config(
    page_title="EULER",
    page_icon=str(ICONE),
    layout="wide",
    initial_sidebar_state="expanded",
)
st.logo(str(LOGO), icon_image=str(MARCA), size="large")
aplicar_estilo()

# O beta exige identidade antes de expor qualquer tela ou dado da EULER.
contexto_usuario = exigir_acesso()
incluir_admin = bool(contexto_usuario.get("is_superadmin"))

paginas = [
    st.Page(caminho, title=titulo, icon=f":material/{icone}:", default=i == 0)
    for i, (caminho, titulo, icone) in enumerate(todas_as_paginas(incluir_admin))
]
navegacao = st.navigation(paginas, position="hidden")
menu_lateral(st, incluir_admin)
painel_conta_sidebar(contexto_usuario)

# As telas não usam st.stop(): o rodapé de segurança precisa aparecer sempre.
navegacao.run()
rodape()

# depois da tela: um clique que troca os dados já aparece nesta mesma execução
if not st.session_state.get("arquivos"):
    situacao_dados = "sem dados carregados"
elif estado.dados_sinteticos():
    situacao_dados = "**dados sintéticos** em uso"
else:
    situacao_dados = "dados enviados em uso · origem conforme arquivos"
st.sidebar.caption(f"EULER · beta v{euler.__version__} · {situacao_dados}")

if st.session_state.get("arquivos"):
    import armazenamento

    st.sidebar.caption(armazenamento.situacao())
    st.sidebar.page_link(
        "paginas/plantas.py", label="Salvar ou reabrir dados", icon=":material/database:"
    )
if st.session_state.get("persistencia_erro"):
    st.warning(st.session_state["persistencia_erro"])
if st.session_state.get("persistencia_aviso"):
    st.info(st.session_state["persistencia_aviso"])
if st.session_state.get("arquivos"):
    st.sidebar.page_link(
        "paginas/importar.py", label="Trocar ou limpar dados", icon=":material/folder_open:"
    )
if os.environ.get("EULER_BUILD_LABEL"):
    st.sidebar.caption(os.environ["EULER_BUILD_LABEL"])
    with st.sidebar.expander("Detalhes técnicos da instalação"):
        st.caption("Revisão em execução: " + os.environ["EULER_BUILD_ID"])
