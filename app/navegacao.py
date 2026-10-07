"""Rotas do EULER e menu principal inspirado na referência final."""

PRINCIPAIS = (
    ("paginas/inicio.py", "Início", "home"),
    ("paginas/saude.py", "Análise da Caldeira", "monitor_heart"),
    ("paginas/painel.py", "Dia a Dia", "today"),
    ("paginas/diagnostico.py", "Condições", "health_and_safety"),
    ("paginas/fechamentos.py", "Mensal", "calendar_month"),
    ("paginas/conta_beta.py", "Atendimento", "support_agent"),
    ("paginas/acompanhamento.py", "Importação", "upload"),
    ("paginas/plantas.py", "Armazém", "inventory_2"),
    ("paginas/financeiro.py", "Financeiro", "payments"),
    ("paginas/relatorio.py", "Relatórios", "description"),
)

COMPLEMENTARES = {
    "Análise e acompanhamento": (
        ("paginas/investigacao.py", "Investigar uma mudança", "troubleshoot"),
        ("paginas/oportunidades.py", "Oportunidades", "flag"),
        ("paginas/acoes.py", "Ações e verificações", "task_alt"),
        ("paginas/limites.py", "Qualidade e limites", "rule"),
    ),
    "Dados e referências": (
        ("paginas/extrato.py", "Fornecedores", "receipt_long"),
        ("paginas/importar.py", "Arquivo avulso", "upload_file"),
        ("paginas/dados_publicos.py", "Testes com dados reais", "science"),
        ("paginas/calculadora.py", "Calculadora de referência", "calculate"),
    ),
}

ADMIN = ("paginas/admin.py", "Administração", "admin_panel_settings")


def todas_as_paginas(incluir_admin: bool = False) -> tuple:
    """Registra todas as rotas; autorização da tela administrativa continua fail-closed."""
    paginas = PRINCIPAIS + tuple(p for grupo in COMPLEMENTARES.values() for p in grupo)
    return paginas + ((ADMIN,) if incluir_admin else ())


def menu_lateral(st, incluir_admin: bool = False) -> None:
    """Menu diário com os nomes da UX final e ferramentas secundárias preservadas."""
    with st.sidebar:
        st.caption("NAVEGAÇÃO")
        for caminho, titulo, icone in PRINCIPAIS:
            st.page_link(caminho, label=titulo, icon=f":material/{icone}:")
        with st.expander("Mais ferramentas"):
            for grupo, paginas in COMPLEMENTARES.items():
                st.caption(grupo)
                for caminho, titulo, icone in paginas:
                    st.page_link(caminho, label=titulo, icon=f":material/{icone}:")
        if incluir_admin:
            st.divider()
            st.caption("ADMINISTRAÇÃO")
            st.page_link(ADMIN[0], label=ADMIN[1], icon=f":material/{ADMIN[2]}:")
