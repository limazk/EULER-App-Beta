"""Testes de fumaça do app: cada tela abre sem erro e mostra o rodapé de segurança."""

import ast
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from euler.textos import RODAPE_SEGURANCA

APP = Path(__file__).resolve().parents[1] / "app"
PAGINAS = sorted(p.name for p in (APP / "paginas").glob("*.py"))


def abrir(pagina: str | None = None) -> AppTest:
    at = AppTest.from_file(str(APP / "main.py"), default_timeout=30).run()
    if pagina:
        at.switch_page(f"paginas/{pagina}").run()
    return at


def test_tela_inicial_abre_com_rodape():
    at = abrir()
    assert not at.exception
    assert any(t.value == "EULER" for t in at.title)
    assert any(c.value == RODAPE_SEGURANCA for c in at.caption)


@pytest.mark.parametrize("pagina", PAGINAS)
def test_toda_pagina_abre_sem_erro_e_com_rodape(pagina):
    at = abrir(pagina)
    assert not at.exception, at.exception
    assert any(c.value == RODAPE_SEGURANCA for c in at.caption)


def test_calculadora_mostra_caso_de_referencia_g01():
    at = abrir("calculadora.py")
    valores = {m.label: m.value for m in at.metric}
    assert valores["Perda nos gases"] == "11,77 % do PCI"
    assert valores["Razão de ar λ"] == "1,611"
    assert valores["PCI úmido"] == "10,12 MJ/kg"
    assert any("Simulação" in w.value for w in at.warning)


def test_calculadora_bloqueia_com_motivo():
    at = abrir("calculadora.py")
    # gases a 60 °C com combustível a 70% de umidade: abaixo do orvalho (≈71 °C)
    at.slider[0].set_value(60)
    at.slider[2].set_value(70).run()
    assert not at.metric
    assert any("bloqueado" in e.value for e in at.error)


def test_nenhuma_tela_usa_st_stop_que_esconderia_o_rodape():
    for arquivo in [*(APP / "paginas").glob("*.py"), APP / "estado.py", APP / "main.py"]:
        arvore = ast.parse(arquivo.read_text(encoding="utf-8"))
        chamadas = [
            n
            for n in ast.walk(arvore)
            if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute)
            and n.func.attr == "stop"
        ]
        assert not chamadas, arquivo.name


def clicar(at: AppTest, inicio_do_rotulo: str) -> AppTest:
    next(b for b in at.button if b.label.startswith(inicio_do_rotulo)).click().run()
    return at


def test_importar_exemplo_com_problemas_mostra_avisos():
    at = clicar(abrir("importar.py"), "Exemplo com problemas")
    assert not at.exception
    valores = {m.label: m.value for m in at.metric}
    assert valores["Tabelas importadas"] == "5"
    assert int(valores["Avisos de atenção"]) >= 15
    assert any(c.value == RODAPE_SEGURANCA for c in at.caption)


def abrir_com_demo(pagina: str) -> AppTest:
    at = clicar(abrir("importar.py"), "Caso de demonstração")
    at.switch_page(f"paginas/{pagina}").run()
    return at


def test_extrato_com_caso_de_demonstracao():
    at = abrir_com_demo("extrato.py")
    assert not at.exception, at.exception
    assert any("mais barato por tonelada nem sempre" in m.value for m in at.markdown)
    assert any(i.value.startswith("F3 tem o menor preço por tonelada") for i in at.info)
    assert any(c.value == RODAPE_SEGURANCA for c in at.caption)


def test_extrato_sem_dados_orienta_a_importar():
    at = abrir("extrato.py")
    assert not at.exception
    assert any("Nenhum dado importado" in i.value for i in at.info)


def test_dados_e_limites_com_demo_libera_tudo():
    at = abrir_com_demo("limites.py")
    assert not at.exception, at.exception
    valores = {m.label: m.value for m in at.metric}
    assert valores["Bloqueadas"] == "0"


def test_dados_e_limites_com_modelos_mostra_bloqueios():
    at = clicar(abrir("importar.py"), "Modelos")
    at.switch_page("paginas/limites.py").run()
    assert not at.exception
    assert int({m.label: m.value for m in at.metric}["Bloqueadas"]) > 0
    assert any("Por quê" in m.value for m in at.markdown)


def test_investigacao_com_demo_sustenta_temperatura_dos_gases():
    at = abrir_com_demo("investigacao.py")
    assert not at.exception, at.exception
    assert any("Os dados sustentam" in s.value for s in at.success)
    assert any("Mais calor saindo pela chaminé" in m.value for m in at.markdown)
    assert any(c.value == RODAPE_SEGURANCA for c in at.caption)


def test_investigacao_semana_sem_vapor_abstem():
    at = abrir_com_demo("investigacao.py")
    at.select_slider[1].set_value((6, 6)).run()  # semana 7: medidor de vapor fora
    assert not at.exception, at.exception
    assert any(w.value.startswith("Não dá para concluir") for w in at.warning)
