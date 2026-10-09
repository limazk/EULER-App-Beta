"""Fluxos pequenos de autenticação que não acessam o Supabase remoto."""

import importlib
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

APP = Path(__file__).resolve().parents[1] / "app"
sys.path.insert(0, str(APP))


def test_recuperacao_normaliza_email_e_nao_enumera_usuario(monkeypatch):
    auth = importlib.import_module("auth")
    chamadas = []
    cliente = SimpleNamespace(
        auth=SimpleNamespace(
            reset_password_for_email=lambda email, options: chamadas.append((email, options))
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


def test_contexto_reutiliza_cache_dentro_do_ttl(monkeypatch):
    auth = importlib.import_module("auth")
    ctx = {"user_id": "u1"}
    sessao = {auth.CTX: ctx, auth.CTX_VALIDATED_AT: 100.0}
    monkeypatch.setattr(auth.st, "session_state", sessao)
    monkeypatch.setattr(auth, "_modo_teste", lambda: False)
    monkeypatch.setattr(auth.time, "monotonic", lambda: 120.0)
    monkeypatch.setattr(auth, "_carregar_contexto", lambda: (_ for _ in ()).throw(AssertionError()))
    assert auth.contexto_atual() is ctx


def test_contexto_recarrega_apos_ttl(monkeypatch):
    auth = importlib.import_module("auth")
    antigo = {"user_id": "u1"}
    novo = {"user_id": "u1", "profile": {"status": "active"}}
    sessao = {auth.CTX: antigo, auth.CTX_VALIDATED_AT: 100.0}
    chamadas = []
    monkeypatch.setattr(auth.st, "session_state", sessao)
    monkeypatch.setattr(auth, "_modo_teste", lambda: False)
    monkeypatch.setattr(auth.time, "monotonic", lambda: 200.0)
    monkeypatch.setattr(auth, "_carregar_contexto", lambda: chamadas.append(True) or novo)
    assert auth.contexto_atual() is novo
    assert chamadas == [True]


def test_contexto_recarregar_forca_validacao_mesmo_no_ttl(monkeypatch):
    auth = importlib.import_module("auth")
    antigo = {"user_id": "u1"}
    novo = {"user_id": "u1", "is_superadmin": True}
    sessao = {auth.CTX: antigo, auth.CTX_VALIDATED_AT: 100.0}
    chamadas = []
    monkeypatch.setattr(auth.st, "session_state", sessao)
    monkeypatch.setattr(auth, "_modo_teste", lambda: False)
    monkeypatch.setattr(auth.time, "monotonic", lambda: 110.0)
    monkeypatch.setattr(auth, "_carregar_contexto", lambda: chamadas.append(True) or novo)
    assert auth.contexto_atual(recarregar=True) is novo
    assert chamadas == [True]


def test_limpar_sessao_remove_timestamp_do_contexto(monkeypatch):
    auth = importlib.import_module("auth")
    sessao = {
        auth.TOKEN_ACCESS: "access",
        auth.TOKEN_REFRESH: "refresh",
        auth.CTX: {"user_id": "u1"},
        auth.CTX_VALIDATED_AT: 123.0,
        "outra_chave": "preservar",
    }
    monkeypatch.setattr(auth.st, "session_state", sessao)
    auth.limpar_sessao()
    assert sessao == {"outra_chave": "preservar"}


def test_logout_remove_dados_operacionais_do_usuario_anterior(monkeypatch):
    auth = importlib.import_module("auth")
    sessao = {
        auth.TOKEN_ACCESS: "access-a",
        auth.TOKEN_REFRESH: "refresh-a",
        auth.CTX: {"user_id": "usuario-a"},
        auth.SESSION_USER_ID: "usuario-a",
        "arquivos": (("dados-a.csv", b"segredo-a"),),
        "persistencia": {"planta_id": "planta-a"},
        "investigacao": {"json": {"usuario": "a"}},
        "dashboard_planta": "planta-a",
        "acomp_planta_atual": "planta-a",
        "biblioteca_planta": "planta-a",
        "euler_tema": "dark",
    }
    cliente = SimpleNamespace(auth=SimpleNamespace(sign_out=lambda: None))
    monkeypatch.setattr(auth.st, "session_state", sessao)
    monkeypatch.setattr(auth, "_cliente_usuario", lambda: cliente)

    auth.sair()

    assert sessao == {"euler_tema": "dark"}

    auth._guardar_sessao(
        SimpleNamespace(
            access_token="access-b",
            refresh_token="refresh-b",
            user=SimpleNamespace(id="usuario-b"),
        )
    )
    assert "arquivos" not in sessao
    assert "investigacao" not in sessao
    assert sessao[auth.SESSION_USER_ID] == "usuario-b"


def test_expiracao_remove_dados_antes_de_nova_autenticacao(monkeypatch):
    auth = importlib.import_module("auth")
    sessao = {
        auth.TOKEN_ACCESS: "access-expirado",
        auth.TOKEN_REFRESH: "refresh-expirado",
        auth.SESSION_USER_ID: "usuario-a",
        "arquivos": (("dados-a.csv", b"segredo-a"),),
        "dashboard_planta": "planta-a",
    }
    cliente = SimpleNamespace(
        auth=SimpleNamespace(get_user=lambda _token: (_ for _ in ()).throw(RuntimeError()))
    )
    monkeypatch.setattr(auth.st, "session_state", sessao)
    monkeypatch.setattr(auth, "_cliente_usuario", lambda: cliente)

    assert auth._usuario_validado() is None
    assert "arquivos" not in sessao
    assert "dashboard_planta" not in sessao
    assert auth.TOKEN_ACCESS not in sessao


def test_falha_ao_carregar_autorizacao_descarta_sessao_e_dados(monkeypatch):
    auth = importlib.import_module("auth")
    sessao = {
        auth.TOKEN_ACCESS: "access-valido",
        auth.TOKEN_REFRESH: "refresh-valido",
        auth.SESSION_USER_ID: "usuario-a",
        "arquivos": (("dados-a.csv", b"segredo-a"),),
        "investigacao": {"json": {"privado": True}},
        "dashboard_planta": "planta-a",
    }

    class ClienteIndisponivel:
        def table(self, _nome):
            raise RuntimeError("falha de comunicação simulada")

    monkeypatch.setattr(auth.st, "session_state", sessao)
    monkeypatch.setattr(
        auth,
        "_usuario_validado",
        lambda: SimpleNamespace(id="usuario-a", email="a@example.invalid"),
    )
    monkeypatch.setattr(auth, "_cliente_usuario", ClienteIndisponivel)

    assert auth._carregar_contexto() is None
    assert sessao == {}


def test_renovacao_de_token_do_mesmo_usuario_preserva_trabalho(monkeypatch):
    auth = importlib.import_module("auth")
    sessao = {
        auth.TOKEN_ACCESS: "access-antigo",
        auth.TOKEN_REFRESH: "refresh-antigo",
        auth.SESSION_USER_ID: "usuario-a",
        "arquivos": (("dados-a.csv", b"trabalho"),),
        "investigacao": {"json": {"preservar": True}},
        "dashboard_planta": "planta-a",
    }
    monkeypatch.setattr(auth.st, "session_state", sessao)
    renovada = SimpleNamespace(
        access_token="access-novo",
        refresh_token="refresh-novo",
        user=SimpleNamespace(id="usuario-a"),
    )

    auth._guardar_sessao(renovada)

    assert sessao["arquivos"][0][1] == b"trabalho"
    assert sessao["investigacao"]["json"] == {"preservar": True}
    assert sessao["dashboard_planta"] == "planta-a"
    assert sessao[auth.TOKEN_ACCESS] == "access-novo"


def test_troca_direta_de_identidade_descarta_trabalho_anterior(monkeypatch):
    auth = importlib.import_module("auth")
    sessao = {
        auth.TOKEN_ACCESS: "access-a",
        auth.TOKEN_REFRESH: "refresh-a",
        auth.SESSION_USER_ID: "usuario-a",
        auth.CTX: {"user_id": "usuario-a"},
        "arquivos": (("dados-a.csv", b"segredo-a"),),
        "persistencia": {"planta_id": "planta-a"},
        "dashboard_planta": "planta-a",
    }
    monkeypatch.setattr(auth.st, "session_state", sessao)
    nova = SimpleNamespace(
        access_token="access-b",
        refresh_token="refresh-b",
        user=SimpleNamespace(id="usuario-b"),
    )

    auth._guardar_sessao(nova)

    assert sessao[auth.SESSION_USER_ID] == "usuario-b"
    assert sessao[auth.TOKEN_ACCESS] == "access-b"
    assert "arquivos" not in sessao
    assert "persistencia" not in sessao
    assert "dashboard_planta" not in sessao


def test_membership_atual_acompanha_organizacao_ativa_selecionada(monkeypatch):
    auth = importlib.import_module("auth")
    ctx = {
        "memberships": [
            {
                "organization_id": "org-a",
                "role": "viewer",
                "organizations": {"name": "A", "status": "active"},
            },
            {
                "organization_id": "org-b",
                "role": "operator",
                "organizations": {"name": "B", "status": "active"},
            },
        ]
    }
    monkeypatch.setattr(auth.st, "session_state", {auth.ORGANIZACAO_SELECIONADA: "org-b"})

    assert auth._membership_atual(ctx)["organization_id"] == "org-b"


def test_membership_atual_nao_aceita_organizacao_suspensa_ou_ausente(monkeypatch):
    auth = importlib.import_module("auth")
    ctx = {
        "memberships": [
            {
                "organization_id": "org-suspensa",
                "organizations": {"name": "Suspensa", "status": "suspended"},
            }
        ]
    }
    monkeypatch.setattr(auth.st, "session_state", {auth.ORGANIZACAO_SELECIONADA: "org-suspensa"})

    assert auth._membership_atual(ctx) is None


def test_exigir_acesso_nao_revalida_em_todo_rerun(monkeypatch):
    auth = importlib.import_module("auth")
    ctx = {
        "user_id": "u1",
        "email": "u@example.com",
        "profile": {"status": "active", "is_superadmin": True},
        "memberships": [],
        "is_superadmin": True,
    }
    chamadas = []
    monkeypatch.setattr(auth.st, "session_state", {auth.TOKEN_ACCESS: "access"})
    monkeypatch.setattr(auth, "_modo_teste", lambda: False)
    monkeypatch.setattr(auth, "configurado", lambda: True)
    monkeypatch.setattr(auth, "contexto_atual", lambda **kwargs: chamadas.append(kwargs) or ctx)
    monkeypatch.setattr(auth, "registrar_atividade", lambda _ctx: None)
    assert auth.exigir_acesso() is ctx
    assert chamadas == [{}]


def test_exigir_superadmin_forca_revalidacao(monkeypatch):
    auth = importlib.import_module("auth")
    ctx = {"profile": {"status": "active"}, "is_superadmin": True}
    chamadas = []
    monkeypatch.setattr(auth, "contexto_atual", lambda **kwargs: chamadas.append(kwargs) or ctx)
    assert auth.exigir_superadmin() is ctx
    assert chamadas == [{"recarregar": True}]


@pytest.mark.parametrize(
    "ctx",
    [
        {
            "user_id": "u1",
            "email": "u@example.com",
            "profile": {"status": "suspended"},
            "memberships": [],
            "is_superadmin": False,
        },
        {
            "user_id": "u1",
            "email": "u@example.com",
            "profile": {"status": "active"},
            "memberships": [],
            "is_superadmin": False,
        },
        {
            "user_id": "u1",
            "email": "u@example.com",
            "profile": {"status": "active"},
            "memberships": [
                {
                    "organization_id": "org-suspensa",
                    "status": "active",
                    "organizations": {"id": "org-suspensa", "status": "suspended"},
                }
            ],
            "is_superadmin": False,
        },
    ],
    ids=["usuario-suspenso", "sem-organizacao", "organizacao-suspensa"],
)
def test_acesso_sem_autorizacao_descarta_contexto_operacional(ctx, monkeypatch):
    auth = importlib.import_module("auth")

    class InterrompeuAcesso(Exception):
        pass

    sessao = {
        auth.TOKEN_ACCESS: "access",
        auth.SESSION_USER_ID: "u1",
        "arquivos": (("dados.csv", b"privado"),),
        "dashboard_planta": "planta-anterior",
    }
    monkeypatch.setattr(auth.st, "session_state", sessao)
    monkeypatch.setattr(auth, "_modo_teste", lambda: False)
    monkeypatch.setattr(auth, "configurado", lambda: True)
    monkeypatch.setattr(auth, "contexto_atual", lambda **_kwargs: ctx)
    for nome in ("markdown", "info", "warning", "error", "caption"):
        monkeypatch.setattr(auth.st, nome, lambda *_args, **_kwargs: None)
    monkeypatch.setattr(auth.st, "button", lambda *_args, **_kwargs: False)
    monkeypatch.setattr(
        auth.st,
        "stop",
        lambda: (_ for _ in ()).throw(InterrompeuAcesso()),
    )

    with pytest.raises(InterrompeuAcesso):
        auth.exigir_acesso()

    assert "arquivos" not in sessao
    assert "dashboard_planta" not in sessao
