"""Política do bypass de autenticação, sem acessar serviços externos."""

import importlib
import sys
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[1] / "app"
sys.path.insert(0, str(APP))

VARIAVEIS_PROTEGIDAS = (
    "RENDER",
    "RENDER_SERVICE_ID",
    "RENDER_EXTERNAL_HOSTNAME",
    "RENDER_GIT_COMMIT",
    "EULER_ENV",
    "ENVIRONMENT",
    "APP_ENV",
    "SUPABASE_URL",
    "SUPABASE_PUBLISHABLE_KEY",
    "SUPABASE_ANON_KEY",
    "SUPABASE_SECRET_KEY",
    "SUPABASE_SERVICE_ROLE_KEY",
)


@pytest.fixture
def auth_isolado(monkeypatch):
    auth = importlib.import_module("auth")
    for nome in VARIAVEIS_PROTEGIDAS:
        monkeypatch.delenv(nome, raising=False)
    monkeypatch.setattr(auth.st, "secrets", {})
    return auth


def test_bypass_exige_pytest_local_sem_configuracao_real(auth_isolado, monkeypatch):
    monkeypatch.setenv("EULER_TEST_BYPASS_AUTH", "1")
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "teste isolado")

    assert auth_isolado._modo_teste() is True


@pytest.mark.parametrize("valor", ["", "0", "false", "TRUE"])
def test_bypass_desabilitado_nao_e_aceito(auth_isolado, monkeypatch, valor):
    monkeypatch.setenv("EULER_TEST_BYPASS_AUTH", valor)
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "teste isolado")

    assert auth_isolado._modo_teste() is False


def test_bypass_fora_do_pytest_falha_fechado(auth_isolado, monkeypatch):
    monkeypatch.setenv("EULER_TEST_BYPASS_AUTH", "1")
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)

    assert auth_isolado._modo_teste() is False


@pytest.mark.parametrize(
    ("nome", "valor"),
    [
        ("RENDER", "true"),
        ("RENDER_SERVICE_ID", "srv-producao"),
        ("EULER_ENV", "production"),
        ("ENVIRONMENT", "staging"),
        ("APP_ENV", "qa"),
        ("SUPABASE_URL", "https://projeto.supabase.co"),
        ("SUPABASE_PUBLISHABLE_KEY", "chave-publica-configurada"),
        ("SUPABASE_SERVICE_ROLE_KEY", "chave-servidor-configurada"),
    ],
)
def test_bypass_recusado_em_ambiente_protegido_ou_parcial(auth_isolado, monkeypatch, nome, valor):
    monkeypatch.setenv("EULER_TEST_BYPASS_AUTH", "1")
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "teste isolado")
    monkeypatch.setenv(nome, valor)

    assert auth_isolado._modo_teste() is False


def test_bypass_recusado_com_supabase_nos_secrets(auth_isolado, monkeypatch):
    monkeypatch.setenv("EULER_TEST_BYPASS_AUTH", "1")
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "teste isolado")
    monkeypatch.setattr(auth_isolado.st, "secrets", {"SUPABASE_URL": "https://real.supabase.co"})

    assert auth_isolado._modo_teste() is False
