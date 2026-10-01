"""Testes de fumaça do app: cada tela abre sem erro e mostra o rodapé de segurança."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

from euler.textos import RODAPE_SEGURANCA

APP = Path(__file__).resolve().parents[1] / "app" / "main.py"


def test_tela_inicial_abre_com_rodape():
    at = AppTest.from_file(str(APP)).run(timeout=30)
    assert not at.exception
    assert any(t.value == "EULER" for t in at.title)
    assert any(c.value == RODAPE_SEGURANCA for c in at.caption)
