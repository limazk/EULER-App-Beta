"""Atualizações locais não podem reutilizar outro servidor, ignorar edições nem descartar
trabalho local ao buscar a versão principal (D91)."""

import importlib.util
import os
import subprocess
from pathlib import Path

import pytest

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


# ------------------------------------------------ atualização automática segura (D91)

GIT = [
    "git",
    "-c",
    "user.name=Teste",
    "-c",
    "user.email=teste@exemplo",
    "-c",
    "commit.gpgsign=false",
]


def _git(pasta, *args):
    return subprocess.run(
        [*GIT, *args], cwd=pasta, check=True, capture_output=True, text=True
    ).stdout.strip()


@pytest.fixture
def repos(tmp_path):
    """Remoto (principal = 'principal'), a instalação do usuário e outra cópia que publica."""
    remoto = tmp_path / "remoto.git"
    subprocess.run(["git", "init", "--bare", "-q", "-b", "principal", str(remoto)], check=True)
    autor = tmp_path / "autor"
    subprocess.run(["git", "clone", "-q", str(remoto), str(autor)], check=True)
    _git(autor, "checkout", "-q", "-b", "principal")
    (autor / "app.py").write_text("versao = 1\n", encoding="utf-8")
    _git(autor, "add", "app.py")
    _git(autor, "commit", "-q", "-m", "v1")
    _git(autor, "push", "-q", "origin", "principal")
    usuario = tmp_path / "usuario"
    subprocess.run(["git", "clone", "-q", str(remoto), str(usuario)], check=True)

    def publicar(texto):
        (autor / "app.py").write_text(texto, encoding="utf-8")
        _git(autor, "commit", "-q", "-am", texto)
        _git(autor, "push", "-q", "origin", "principal")
        return _git(autor, "rev-parse", "--short", "HEAD")

    return usuario, publicar


def test_instalacao_limpa_recebe_a_versao_principal(repos):
    usuario, publicar = repos
    nova = publicar("versao = 2\n")
    msg = launcher.update_from_remote(usuario)
    assert (usuario / "app.py").read_text(encoding="utf-8") == "versao = 2\n"
    assert nova in msg and "atualizada" in msg
    assert "em dia" in launcher.update_from_remote(usuario)


def test_alteracao_local_nao_salva_nunca_e_sobrescrita(repos):
    usuario, publicar = repos
    publicar("versao = 2\n")
    (usuario / "app.py").write_text("edição local do Adryan\n", encoding="utf-8")
    msg = launcher.update_from_remote(usuario)
    assert (usuario / "app.py").read_text(encoding="utf-8") == "edição local do Adryan\n"
    assert "alterações locais não salvas" in msg


def test_commit_local_divergente_e_preservado(repos):
    usuario, publicar = repos
    publicar("versao = 2\n")
    (usuario / "outro.py").write_text("x = 1\n", encoding="utf-8")
    _git(usuario, "add", "outro.py")
    _git(usuario, "commit", "-q", "-m", "trabalho local")
    local = _git(usuario, "rev-parse", "HEAD")
    msg = launcher.update_from_remote(usuario)
    assert _git(usuario, "rev-parse", "HEAD") == local
    assert "nada foi alterado" in msg


def test_branch_antiga_ja_integrada_passa_para_a_principal(repos):
    usuario, publicar = repos
    _git(usuario, "checkout", "-q", "-b", "codex/antiga")
    publicar("versao = 2\n")
    launcher.update_from_remote(usuario)
    assert _git(usuario, "rev-parse", "--abbrev-ref", "HEAD") == "principal"
    assert (usuario / "app.py").read_text(encoding="utf-8") == "versao = 2\n"


def test_sem_git_ou_sem_conexao_abre_a_versao_instalada(repos, tmp_path):
    sem_git = tmp_path / "sem_git"
    sem_git.mkdir()
    assert "sem git" in launcher.update_from_remote(sem_git)
    usuario, _ = repos
    _git(usuario, "remote", "set-url", "origin", str(tmp_path / "nao-existe.git"))
    antes = (usuario / "app.py").read_text(encoding="utf-8")
    assert "sem conexão" in launcher.update_from_remote(usuario)
    assert (usuario / "app.py").read_text(encoding="utf-8") == antes


def test_subpasta_nao_atualiza_o_repositorio_pai(repos):
    usuario, publicar = repos
    publicar("versao = 2\n")
    subpasta = usuario / "pasta-sem-repositorio-proprio"
    subpasta.mkdir()
    antes = _git(usuario, "rev-parse", "HEAD")
    assert "sem git" in launcher.update_from_remote(subpasta)
    assert _git(usuario, "rev-parse", "HEAD") == antes
    assert (usuario / "app.py").read_text(encoding="utf-8") == "versao = 1\n"
