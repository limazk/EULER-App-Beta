"""Atualizações locais não podem reutilizar outro servidor nem ignorar edições."""

import importlib.util
import os
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "abrir_local", Path(__file__).resolve().parents[1] / "scripts/abrir_local.py"
)
launcher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(launcher)


def test_assinatura_muda_com_edicao_sem_commit_e_ignora_cache(tmp_path):
    app = tmp_path / "app"
    app.mkdir()
    code = app / "main.py"
    code.write_text("versao = 1", encoding="utf-8")
    before = launcher.fingerprint(tmp_path)
    cache = app / "__pycache__"
    cache.mkdir()
    (cache / "main.py").write_text("cache", encoding="utf-8")
    assert launcher.fingerprint(tmp_path) == before
    code.write_text("versao = 2", encoding="utf-8")
    assert launcher.fingerprint(tmp_path) != before


def test_pid_reaproveitado_nao_e_servidor_proprio(monkeypatch):
    identity = {
        "pid": 123,
        "created": 456,
        "executable": os.path.normcase(str(launcher.SERVER_PYTHON)),
    }
    record = {"identity": identity, "repository": str(launcher.ROOT)}
    monkeypatch.setattr(launcher, "process_identity", lambda pid: dict(identity))
    assert launcher.owned(record)
    monkeypatch.setattr(launcher, "process_identity", lambda pid: {**identity, "created": 789})
    assert not launcher.owned(record)


def test_outro_checkout_nao_e_servidor_proprio(monkeypatch):
    identity = {
        "pid": 123,
        "created": 456,
        "executable": os.path.normcase(str(launcher.SERVER_PYTHON)),
    }
    monkeypatch.setattr(launcher, "process_identity", lambda pid: identity)
    assert not launcher.owned({"identity": identity, "repository": "outra-instalacao"})
