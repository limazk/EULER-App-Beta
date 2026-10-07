"""Fluxos pequenos de autenticação que não acessam o Supabase remoto."""

import importlib
import sys
from pathlib import Path
from types import SimpleNamespace

APP = Path(__file__).resolve().parents[1] / "app"
sys.path.insert(0, str(APP))


def test_recuperacao_normaliza_email_e_nao_enumera_usuario(monkeypatch):
    auth = importlib.import_module("auth")
    chamadas = []
    cliente = SimpleNamespace(
        auth=SimpleNamespace(
            reset_password_email=lambda email, options: chamadas.append((email, options))
        )
    )
    monkeypatch.setattr(auth, "_cliente_usuario", lambda: cliente)
    monkeypatch.delenv("EULER_PASSWORD_RESET_REDIRECT_URL", raising=False)

    ok, mensagem = auth.recuperar_senha("  Pessoa@Example.com ")

    assert ok is True
    assert chamadas == [("pessoa@example.com", None)]
    assert "Se o e-mail estiver cadastrado" in mensagem


def test_recuperacao_rejeita_email_invalido_sem_chamar_cliente(monkeypatch):
    auth = importlib.import_module("auth")
    monkeypatch.setattr(auth, "_cliente_usuario", lambda: (_ for _ in ()).throw(AssertionError()))
    assert auth.recuperar_senha("invalido") == (False, "Informe um e-mail válido.")


def test_redefinicao_valida_senhas_antes_do_supabase(monkeypatch):
    auth = importlib.import_module("auth")
    monkeypatch.setattr(auth, "_cliente_usuario", lambda: (_ for _ in ()).throw(AssertionError()))
    assert auth.redefinir_senha("curta", "curta")[0] is False
    assert auth.redefinir_senha("senha-segura", "outra-senha")[0] is False


def test_redefinicao_atualiza_senha_e_encerra_sessao(monkeypatch):
    auth = importlib.import_module("auth")
    chamadas = []
    cliente = SimpleNamespace(
        auth=SimpleNamespace(
            update_user=lambda dados: chamadas.append(dados),
            sign_out=lambda: chamadas.append("sair"),
        )
    )
    sessao = {
        auth.TOKEN_ACCESS: "access",
        auth.TOKEN_REFRESH: "refresh",
        "_euler_password_recovery": True,
    }
    monkeypatch.setattr(auth, "_cliente_usuario", lambda: cliente)
    monkeypatch.setattr(auth.st, "session_state", sessao)

    assert auth.redefinir_senha("senha-segura", "senha-segura")[0] is True
    assert chamadas == [{"password": "senha-segura"}, "sair"]
    assert sessao == {}


def test_feedback_vazio_e_recusado_antes_do_supabase(monkeypatch):
    auth = importlib.import_module("auth")
    monkeypatch.setattr(
        auth, "contexto_atual", lambda **kwargs: (_ for _ in ()).throw(AssertionError())
    )
    try:
        auth.enviar_feedback("bug", "   ")
    except ValueError as exc:
        assert "entre 5 e 4000" in str(exc)
    else:
        raise AssertionError("feedback vazio deveria ser recusado")
