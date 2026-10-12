"""Mapa único das rotas EULER, agrupadas pelos módulos de trabalho da interface v3."""

PRINCIPAIS = (
    ("paginas/inicio.py", "Dashboard", "dashboard"),
    ("paginas/painel.py", "Minha planta", "factory"),
    ("paginas/acompanhamento.py", "Importação de dados", "upload"),
    ("paginas/saude.py", "Análises e resultados", "monitor_heart"),
    ("paginas/fechamentos.py", "Fechamento mensal", "event_available"),
    ("paginas/acoes.py", "Ações e planejamento", "task_alt"),
)

COMPLEMENTARES = {
    "Investigações": (
        ("paginas/investigacao.py", "Investigar uma mudança", "troubleshoot"),
        ("paginas/diagnostico.py", "Diagnóstico de evidências", "fact_check"),
        ("paginas/oportunidades.py", "Oportunidades", "flag"),
        ("paginas/limites.py", "Qualidade e limites", "rule"),
    ),
    "Relatórios e fornecedores": (
        ("paginas/relatorio.py", "Relatório da análise", "description"),
        ("paginas/extrato.py", "Fornecedores", "receipt_long"),
        ("paginas/financeiro.py", "Financeiro", "payments"),
    ),
    "Plantas e arquivos": (
        ("paginas/plantas.py", "Plantas e histórico", "database"),
        ("paginas/importar.py", "Analisar arquivo avulso", "upload_file"),
    ),
    "Conta e referências": (
        ("paginas/conta_beta.py", "Conta e feedback", "account_circle"),
        ("paginas/dados_publicos.py", "Testes com dados reais", "science"),
        ("paginas/calculadora.py", "Calculadora de referência", "calculate"),
    ),
}

ADMIN = ("paginas/admin.py", "Administração", "admin_panel_settings")


def todas_as_paginas(incluir_admin: bool = False) -> tuple:
    """Registra todas as rotas; a autorização da página administrativa permanece intacta."""
    _ = incluir_admin  # compatibilidade com chamadas existentes
    return PRINCIPAIS + tuple(p for grupo in COMPLEMENTARES.values() for p in grupo) + (ADMIN,)


def menu_lateral(st, incluir_admin: bool = False) -> None:
    """Navegação por módulos, sem remover rotas nem expor o link administrativo."""
    with st.sidebar:
        st.caption("OPERAÇÃO")
        for caminho, titulo, icone in PRINCIPAIS:
            st.page_link(caminho, label=titulo, icon=f":material/{icone}:")
        with st.expander("Mais ferramentas"):
            for grupo, paginas in COMPLEMENTARES.items():
                st.caption(grupo)
                for caminho, titulo, icone in paginas:
                    st.page_link(caminho, label=titulo, icon=f":material/{icone}:")
        if incluir_admin:
            st.divider()
            st.caption("ACESSO RESTRITO")
            st.page_link(
                ADMIN[0],
                label=ADMIN[1],
                icon=f":material/{ADMIN[2]}:",
            )
