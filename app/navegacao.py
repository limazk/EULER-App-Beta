"""Seis entradas diárias, com todas as demais rotas preservadas em menu recolhido."""

PRINCIPAIS = (
    ("paginas/inicio.py", "Início", "home"),
    ("paginas/painel.py", "Minha planta", "space_dashboard"),
    ("paginas/saude.py", "Análise", "monitor_heart"),
    ("paginas/financeiro.py", "Financeiro", "payments"),
    ("paginas/acoes.py", "Ações", "task_alt"),
    ("paginas/acompanhamento.py", "Dados", "upload"),
)

COMPLEMENTARES = {
    "Aprofundar a análise": (
        ("paginas/investigacao.py", "Investigar uma mudança", "troubleshoot"),
        ("paginas/oportunidades.py", "Oportunidades", "flag"),
        ("paginas/extrato.py", "Fornecedores", "receipt_long"),
        ("paginas/limites.py", "Qualidade e limites dos dados", "rule"),
        ("paginas/relatorio.py", "Relatório da análise", "description"),
    ),
    "Histórico e cadastro": (
        ("paginas/fechamentos.py", "Fechamentos", "event_available"),
        ("paginas/plantas.py", "Plantas e histórico", "database"),
        ("paginas/importar.py", "Analisar um arquivo avulso", "upload_file"),
    ),
    "Validação e referências": (
        ("paginas/dados_publicos.py", "Testes com dados reais", "science"),
        ("paginas/diagnostico.py", "Diagnóstico de evidências", "fact_check"),
        ("paginas/calculadora.py", "Calculadora de referência", "calculate"),
    ),
}


def todas_as_paginas() -> tuple:
    """Inclui rotas recolhidas para preservar links diretos e navegação interna."""
    return PRINCIPAIS + tuple(p for grupo in COMPLEMENTARES.values() for p in grupo)


def menu_lateral(st) -> None:
    """Prioriza o uso diário sem remover ferramentas ou alterar os cálculos."""
    with st.sidebar:
        for caminho, titulo, icone in PRINCIPAIS:
            st.page_link(caminho, label=titulo, icon=f":material/{icone}:")
        with st.expander("Mais ferramentas"):
            for grupo, paginas in COMPLEMENTARES.items():
                st.caption(grupo)
                for caminho, titulo, icone in paginas:
                    st.page_link(caminho, label=titulo, icon=f":material/{icone}:")
