"""Regressões de navegação e isolamento entre demonstração e dados enviados."""

from streamlit.testing.v1 import AppTest
from test_app import abrir, abrir_com_demo, clicar


def test_limpar_sessao_remove_resultados_periodos_e_altitude():
    at = abrir_com_demo("investigacao.py")
    at.session_state["fin_recuperacao_teste"] = 75
    at.switch_page("paginas/importar.py").run()
    at.button(key="limpar_dados").click().run()
    assert not at.exception, at.exception
    for key in (
        "arquivos",
        "investigacao",
        "altitude_m",
        "periodos_escolhidos",
        "fin_recuperacao_teste",
    ):
        assert key not in at.session_state
    assert at.number_input[0].value is None
    at.switch_page("paginas/financeiro.py").run()
    assert any("Nenhum dado importado" in i.value for i in at.info)


def test_altitude_de_novos_arquivos_nao_herda_demo_nem_altera_analise():
    at = abrir_com_demo("investigacao.py")
    assinatura = at.session_state["investigacao"]["assinatura"]
    at.switch_page("paginas/importar.py").run()
    assert at.number_input[0].value is None
    at.number_input[0].set_value(500).run()
    assert at.session_state["altitude_m"] == 1000
    assert at.session_state["investigacao"]["assinatura"] == assinatura


def test_saude_resumo_e_detalhes_recolhidos():
    at = abrir_com_demo("saude.py")
    assert not at.exception, at.exception
    assert any("kg/t de vapor" in m.value for m in at.metric)
    assert any(e.label.startswith("Ver dados de cada período") for e in at.expander)
    assert any(e.label.startswith("Eventos registrados") for e in at.expander)
    assert at.toggle[0].value is False
    at.toggle[0].set_value(True).run()
    assert not at.exception, at.exception


def test_substituir_demo_nao_acumula_arquivos():
    at = clicar(abrir("importar.py"), "Ato 1 · caso completo")
    anterior = at.session_state["arquivos"]
    clicar(at, "Modelos (1 linha de exemplo)")
    assert at.session_state["arquivos"] != anterior
    assert len(at.session_state["arquivos"]) == len(anterior)


def test_novos_arquivos_substituem_anteriores_e_nao_herdam_altitude():
    abrir()  # registra o diretório do app no ambiente de teste
    at = AppTest.from_string("""
import estado
import streamlit as st
estado.definir_arquivos({"antigo.csv": b"exemplo"}, "demo", sinteticos=True)
st.session_state["altitude_m"] = 1000
st.session_state["investigacao"] = {"antigo": True}
estado.importar_novos({"novo.csv": b"cabecalho"}, None)
""").run()
    assert not at.exception, at.exception
    assert at.session_state["arquivos"] == (("novo.csv", b"cabecalho"),)
    assert at.session_state["altitude_m"] is None
    assert at.session_state["dados_sinteticos"] is False
    assert "investigacao" not in at.session_state
