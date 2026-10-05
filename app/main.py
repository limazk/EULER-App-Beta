"""Ponto de entrada do app EULER.

Rodar com: streamlit run app/main.py
"""

import os

import estado
import streamlit as st
from componentes import ICONE, LOGO, MARCA, aplicar_estilo, rodape

import euler

st.set_page_config(
    page_title="EULER",
    page_icon=str(ICONE),
    layout="wide",
    initial_sidebar_state="expanded",
)
st.logo(str(LOGO), icon_image=str(MARCA), size="large")
aplicar_estilo()

paginas = {
    "": [st.Page("paginas/inicio.py", title="Início", icon=":material/home:", default=True)],
    # um período: os arquivos desta sessão (demonstração ou enviados)
    "Analisar um período": [
        st.Page("paginas/importar.py", title="Importar dados", icon=":material/upload_file:"),
        st.Page("paginas/saude.py", title="Saúde da caldeira", icon=":material/monitor_heart:"),
        st.Page("paginas/limites.py", title="Dados e limites", icon=":material/rule:"),
        st.Page("paginas/investigacao.py", title="Investigação", icon=":material/troubleshoot:"),
        st.Page("paginas/financeiro.py", title="Financeiro", icon=":material/payments:"),
        st.Page("paginas/oportunidades.py", title="Oportunidades", icon=":material/flag:"),
        st.Page(
            "paginas/extrato.py", title="Extrato por fornecedor", icon=":material/receipt_long:"
        ),
        st.Page("paginas/relatorio.py", title="Relatório", icon=":material/description:"),
    ],
    # ao longo do tempo: dados, fechamentos e ações guardados no banco de cada planta
    "Acompanhar a planta": [
        st.Page("paginas/painel.py", title="Painel", icon=":material/space_dashboard:"),
        st.Page("paginas/acompanhamento.py", title="Atualizar dados", icon=":material/upload:"),
        st.Page("paginas/fechamentos.py", title="Fechamentos", icon=":material/event_available:"),
        st.Page("paginas/acoes.py", title="Investigações e ações", icon=":material/task_alt:"),
        st.Page("paginas/plantas.py", title="Plantas e histórico", icon=":material/database:"),
    ],
    "Referência": [
        st.Page(
            "paginas/diagnostico.py",
            title="Diagnóstico de evidências",
            icon=":material/fact_check:",
        ),
        st.Page(
            "paginas/dados_publicos.py",
            title="Testes com dados públicos",
            icon=":material/science:",
        ),
        st.Page(
            "paginas/calculadora.py", title="Calculadora de referência", icon=":material/calculate:"
        ),
    ],
}

# expanded: com muitas telas o Streamlit esconde parte do menu em 'ver mais'
navegacao = st.navigation(paginas, expanded=True)
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
st.sidebar.caption(f"EULER · protótipo v{euler.__version__} · {situacao_dados}")
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
