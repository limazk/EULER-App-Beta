"""Smoke tests do runtime Supabase sem acessar a rede."""

from importlib import import_module
from importlib.metadata import version
from pathlib import Path
import sys

from supabase import Client, create_client
from supabase.client import ClientOptions

APP = Path(__file__).resolve().parents[1] / "app"
sys.path.insert(0, str(APP))

SUPABASE_STACK = {
    "supabase": "2.32.0",
    "postgrest": "2.32.0",
    "realtime": "2.32.0",
    "storage3": "2.32.0",
    "supabase-auth": "2.32.0",
    "supabase-functions": "2.32.0",
}


def test_supabase_stack_usa_uma_unica_release():
    """Evita combinações de pacotes que já causaram regressão no ClientOptions."""
    assert {pacote: version(pacote) for pacote in SUPABASE_STACK} == SUPABASE_STACK


def test_create_client_public_api_constroi_sem_rede():
    """Exercita a API pública recomendada pelo SDK, inclusive ClientOptions."""
    cliente = create_client(
        "https://example.supabase.co",
        "sb_publishable_smoke_test",
        options=ClientOptions(
            postgrest_client_timeout=5,
            storage_client_timeout=5,
            schema="public",
        ),
    )

    assert isinstance(cliente, Client)
    assert cliente.auth is not None
    assert cliente.postgrest is not None
    assert cliente.storage is not None


def test_clientes_euler_constroem_sem_rede(monkeypatch):
    """Cobre os dois caminhos usados pelo app sem enviar nenhuma requisição."""
    auth = import_module("auth")
    monkeypatch.setattr(
        auth,
        "configuracao",
        lambda: {
            "url": "https://example.supabase.co",
            "public_key": "sb_publishable_smoke_test",
            "secret_key": "sb_secret_smoke_test",
        },
    )
    monkeypatch.setattr(auth.st, "session_state", {})

    usuario = auth._cliente_usuario()
    admin = auth._cliente_admin()

    assert isinstance(usuario, Client)
    assert isinstance(admin, Client)
