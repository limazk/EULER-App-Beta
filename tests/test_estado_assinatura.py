"""Cache da assinatura deve acelerar reruns sem mudar a identidade histórica dos dados."""

import hashlib
import importlib
import sys
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "app"
sys.path.insert(0, str(APP))


def _preparar(tmp_path, monkeypatch):
    import streamlit as st

    estado = importlib.import_module("estado")
    raiz = tmp_path / "repo"
    motor = raiz / "euler"
    motor.mkdir(parents=True)
    (motor / "a.py").write_bytes(b"x = 1\r\n")
    sessao = {}
    monkeypatch.setattr(st, "session_state", sessao)
    monkeypatch.setattr(estado, "RAIZ", raiz)
    return estado, sessao, raiz


def test_assinatura_preserva_algoritmo_legado(tmp_path, monkeypatch):
    estado, sessao, raiz = _preparar(tmp_path, monkeypatch)
    estado.definir_arquivos({"b.csv": b"bbb", "a.csv": b"aaa"}, "teste")
    sessao["altitude_m"] = 321.0
    sessao["persistencia"] = {"planta_id": "p1", "importacao_id": "i1"}

    h = hashlib.sha256(repr(321.0).encode())
    h.update(repr(("p1", "i1")).encode())
    for caminho in sorted((raiz / "euler").rglob("*.py")):
        h.update(caminho.relative_to(raiz).as_posix().encode())
        h.update(caminho.read_bytes().replace(b"\r\n", b"\n"))
    for nome, dados in sessao["arquivos"]:
        h.update(nome.encode())
        h.update(dados)

    assert estado.assinatura() == h.hexdigest()[:16]


def test_segunda_assinatura_nao_rele_motor(tmp_path, monkeypatch):
    estado, _, _ = _preparar(tmp_path, monkeypatch)
    estado.definir_arquivos({"a.csv": b"abc"}, "teste")
    primeira = estado.assinatura()
    monkeypatch.setattr(
        estado,
        "_atualizar_hash_com_motor",
        lambda *_: (_ for _ in ()).throw(AssertionError("motor foi relido")),
    )

    assert estado.assinatura() == primeira


def test_altitude_invalida_cache_da_assinatura(tmp_path, monkeypatch):
    estado, sessao, _ = _preparar(tmp_path, monkeypatch)
    estado.definir_arquivos({"a.csv": b"abc"}, "teste")
    sessao["altitude_m"] = 100.0
    primeira = estado.assinatura()
    original = estado._atualizar_hash_com_motor
    chamadas = []
    monkeypatch.setattr(
        estado,
        "_atualizar_hash_com_motor",
        lambda h, meta: chamadas.append(True) or original(h, meta),
    )
    sessao["altitude_m"] = 200.0
    segunda = estado.assinatura()

    assert segunda != primeira
    assert chamadas == [True]


def test_trocar_arquivos_invalida_cache(tmp_path, monkeypatch):
    estado, sessao, _ = _preparar(tmp_path, monkeypatch)
    estado.definir_arquivos({"a.csv": b"abc"}, "teste")
    primeira = estado.assinatura()
    hash_primeiro = sessao[estado.ARQUIVOS_HASH]
    estado.definir_arquivos({"a.csv": b"xyz"}, "teste 2")

    assert estado.ASSINATURA_CACHE not in sessao
    assert sessao[estado.ARQUIVOS_HASH] != hash_primeiro
    assert estado.assinatura() != primeira


def test_limpar_dados_remove_caches_de_assinatura(tmp_path, monkeypatch):
    estado, sessao, _ = _preparar(tmp_path, monkeypatch)
    estado.definir_arquivos({"a.csv": b"abc"}, "teste")
    estado.assinatura()
    assert estado.ARQUIVOS_HASH in sessao
    assert estado.ASSINATURA_CACHE in sessao

    estado.limpar_dados()

    assert estado.ARQUIVOS_HASH not in sessao
    assert estado.ASSINATURA_CACHE not in sessao
