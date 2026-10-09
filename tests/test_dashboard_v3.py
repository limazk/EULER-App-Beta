"""Regressões da primeira interface funcional EULER 3.0."""

from pathlib import Path

from componentes import ESTILO
from navegacao import COMPLEMENTARES, PRINCIPAIS, todas_as_paginas
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app"


def test_identidade_v3_usa_paleta_aprovada_sem_roxo():
    for cor in ("#080C0E", "#090D0F", "#141A1C", "#31D877", "#EB4B56", "#E8B33D"):
        assert cor in ESTILO
    assert "purple" not in ESTILO.lower()
    assert "violet" not in ESTILO.lower()


def test_sidebar_recolhida_nao_reserva_largura_vazia():
    from componentes import _estilo_do_tema

    css = _estilo_do_tema(
        {
            "fundo": "#000000",
            "lateral": "#000000",
            "cartao": "#000000",
            "cartao_secundario": "#000000",
            "linha": "#000000",
            "hover": "#000000",
            "texto": "#FFFFFF",
            "suave": "#FFFFFF",
            "sombra": "transparent",
        }
    )
    assert ':has([data-testid="stExpandSidebarButton"])' in css
    assert "flex-basis: 0 !important" in css


def test_navegacao_v3_agrupa_modulos_sem_perder_rotas():
    assert [pagina[1] for pagina in PRINCIPAIS] == [
        "Dashboard",
        "Minha planta",
        "Importação de dados",
        "Análises e resultados",
        "Fechamento mensal",
        "Ações e planejamento",
    ]
    assert "Investigações" in COMPLEMENTARES
    assert "Relatórios e fornecedores" in COMPLEMENTARES
    caminhos = [pagina[0] for pagina in todas_as_paginas()]
    assert len(caminhos) == len(set(caminhos))


def test_dashboard_sem_dados_nao_inventa_indicadores(tmp_path, monkeypatch):
    monkeypatch.setenv("EULER_TEST_BYPASS_AUTH", "1")
    monkeypatch.setenv("EULER_DADOS_DIR", str(tmp_path / "dados"))
    at = AppTest.from_file(str(APP / "main.py"), default_timeout=90).run()
    assert not at.exception, at.exception
    valores = {metrica.label: metrica.value for metrica in at.metric}
    for rotulo in ("Custo energético", "Custo esperado", "Diferença", "Consumo"):
        assert valores[rotulo] == "—"
    assert valores["Próxima verificação"] == "—"
    assert valores["Última leitura registrada"] == "—"
    assert at.button(key="intelligence-desativada").disabled
    assert any("IA aguardando escolha de provedor" in texto.value for texto in at.caption)


def test_dashboard_com_demo_mostra_historico_sem_simular_conexao(tmp_path, monkeypatch):
    monkeypatch.setenv("EULER_TEST_BYPASS_AUTH", "1")
    monkeypatch.setenv("EULER_DADOS_DIR", str(tmp_path / "dados"))
    at = AppTest.from_file(str(APP / "main.py"), default_timeout=90).run()
    at.switch_page("paginas/importar.py").run()
    at.button(key="importar_ato1").click().run()
    at.switch_page("paginas/inicio.py").run()
    assert not at.exception, at.exception
    assert at.get("vega_lite_chart")
    assert any("não significa conexão com sensores" in texto.value for texto in at.caption)
    assert any("Demonstração sintética" in texto.value for texto in at.get("html"))
    assert any("exibe somente" in texto.value for texto in at.info)
    assert not any("permanece sem dados" in texto.value for texto in at.info)
