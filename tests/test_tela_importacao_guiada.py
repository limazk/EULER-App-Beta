"""Envio real de bytes pelo formulário, com confirmação antes da troca da sessão."""

import io
from pathlib import Path

import streamlit as st
from streamlit.testing.v1 import AppTest


class Arquivo(io.BytesIO):
    name = "diario.csv"


def clicar(at, rotulo):
    next(b for b in at.button if b.label == rotulo).click().run()
    assert not at.exception, at.exception


def test_guia_confirma_previa_e_invalida_quando_conteudo_muda(tmp_path, monkeypatch):
    monkeypatch.setenv("EULER_DADOS_DIR", str(tmp_path / "dados"))
    arquivo = Arquivo(
        b"caldeira_id,instante_observado,vazao_vapor_t_h,origem_dado\nB1,2026-10-01 08:00,2,publico\n"
    )
    enviados = [arquivo]
    monkeypatch.setattr(st, "file_uploader", lambda *a, **k: enviados)
    app = Path(__file__).resolve().parents[1] / "app/main.py"
    at = AppTest.from_file(str(app), default_timeout=90).run()
    at.switch_page("paginas/importar.py").run()
    assert not at.exception, at.exception
    assert next(b for b in at.button if b.label == "Importar os arquivos enviados").disabled
    next(c for c in at.checkbox if c.label.startswith("Conferi as colunas")).check().run()
    clicar(at, "Preparar prévia")
    assert any(e.label == "O que estes dados permitem analisar" for e in at.expander)
    assert not next(b for b in at.button if b.label == "Importar os arquivos enviados").disabled
    clicar(at, "Importar os arquivos enviados")
    salvos = dict(at.session_state["arquivos"])
    assert "euler_importacao.json" in salvos
    assert salvos["original_01.bin"] == arquivo.getvalue()
    # Mesmo nome e outro conteúdo: não reaproveitar a confirmação nem a prévia.
    enviados[:] = [Arquivo(arquivo.getvalue().replace(b",2,publico", b",3,publico"))]
    at.run()
    assert not at.exception, at.exception
    assert next(b for b in at.button if b.label == "Importar os arquivos enviados").disabled
    assert dict(at.session_state["arquivos"]) == salvos
