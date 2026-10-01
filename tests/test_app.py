"""Testes de fumaça do app: cada tela abre sem erro e mostra o rodapé de segurança."""

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
