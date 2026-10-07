"""Testes offline das ferramentas operacionais do Beta (scripts/)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def _carregar(nome: str):
    spec = importlib.util.spec_from_file_location(nome, SCRIPTS / f"{nome}.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


beta_check = _carregar("beta_check")
bootstrap = _carregar("bootstrap_superadmin")
smoke_beta = _carregar("smoke_beta")


# ---------- beta_check ----------


def test_beta_check_nunca_imprime_segredos(tmp_path, capsys):
    env = {
        "SUPABASE_URL": "https://abc.supabase.co",
        "SUPABASE_PUBLISHABLE_KEY": "pub-VALOR-SECRETO-1",
        "SUPABASE_SECRET_KEY": "sec-VALOR-SECRETO-2",
        "EULER_DADOS_DIR": str(tmp_path),
    }
    assert beta_check.checar_ambiente(env) == []
    saida = capsys.readouterr().out
    assert "VALOR-SECRETO" not in saida
    assert "SUPABASE_SECRET_KEY: OK" in saida


def test_beta_check_aponta_ausentes_e_url_invalida(capsys):
    problemas = beta_check.checar_ambiente({"SUPABASE_URL": "http://x"})
    saida = capsys.readouterr().out
    assert "SUPABASE_PUBLISHABLE_KEY: AUSENTE" in saida
    assert "SUPABASE_SECRET_KEY: AUSENTE" in saida
    assert "SUPABASE_URL inválida" in problemas
    assert "SUPABASE_SECRET_KEY ausente" not in problemas  # opcional


PUBLICA = "sb_publishable_NAO_IMPRIMIR"
SECRETA = "sb_secret_NAO_IMPRIMIR"


@pytest.fixture
def supabase_falso(monkeypatch):
    """Módulos falsos: registra as tabelas consultadas por cada chave, sem rede."""
    consultas: dict[str, list[str]] = {}

    class Cliente:
        def __init__(self, chave):
            self.chave = chave

        def table(self, nome):
            consultas.setdefault(self.chave, []).append(nome)
            return self

        def select(self, *a, **k):
            return self

        def limit(self, _):
            return self

        def execute(self):
            return SimpleNamespace(data=[])

    falso = SimpleNamespace(create_client=lambda url, chave, **k: Cliente(chave))
    opcoes = SimpleNamespace(ClientOptions=lambda **k: None)
    monkeypatch.setitem(sys.modules, "supabase", falso)
    monkeypatch.setitem(sys.modules, "supabase.lib", SimpleNamespace())
    monkeypatch.setitem(sys.modules, "supabase.lib.client_options", opcoes)
    return consultas


def test_beta_check_sem_secret_nao_consulta_tabelas(supabase_falso, capsys):
    env = {"SUPABASE_URL": "https://abc.supabase.co", "SUPABASE_PUBLISHABLE_KEY": PUBLICA}
    assert beta_check.checar_supabase(env) == []
    saida = capsys.readouterr().out
    assert supabase_falso == {}  # cliente público nunca consulta tabelas
    assert "verificação administrativa das tabelas ignorada" in saida
    assert PUBLICA not in saida


def test_beta_check_com_secret_admin_verifica_tabelas(supabase_falso, capsys):
    env = {
        "SUPABASE_URL": "https://abc.supabase.co",
        "SUPABASE_PUBLISHABLE_KEY": PUBLICA,
        "SUPABASE_SECRET_KEY": SECRETA,
    }
    assert beta_check.checar_supabase(env) == []
    saida = capsys.readouterr().out
    assert supabase_falso == {SECRETA: list(beta_check.TABELAS)}
    assert PUBLICA not in saida and SECRETA not in saida


# ---------- bootstrap_superadmin ----------


class FakeSupabase:
    def __init__(self, perfis):
        self.perfis = perfis
        self.updates = []
        self._filtro = None
        self._dados = None

    def table(self, nome):
        assert nome == "profiles"
        self._filtro, self._dados = None, None
        return self

    def select(self, *_):
        return self

    def limit(self, _):
        return self

    def update(self, dados):
        self._dados = dados
        return self

    def eq(self, coluna, valor):
        self._filtro = (coluna, valor)
        return self

    def execute(self):
        coluna, valor = self._filtro
        alvo = [p for p in self.perfis if p.get(coluna) == valor]
        if self._dados is not None:
            self.updates.append((self._filtro, self._dados))
            for p in alvo:
                p.update(self._dados)
        return SimpleNamespace(data=alvo)


ENV = {"SUPABASE_URL": "https://abc.supabase.co", "SUPABASE_SECRET_KEY": "s"}


def _perfis():
    return [
        {"id": "1", "email": "dono@exemplo.com", "status": "pending", "is_superadmin": False},
        {"id": "2", "email": "outro@exemplo.com", "status": "pending", "is_superadmin": False},
    ]


def test_bootstrap_promove_somente_o_email_confirmado():
    fake = FakeSupabase(_perfis())
    rc = bootstrap.executar(
        ["Dono@Exemplo.com"], ENV, entrada=lambda _: "dono@exemplo.com", cliente=fake
    )
    assert rc == 0
    assert fake.updates == [
        (("id", "1"), {**fake.updates[0][1], "status": "active", "is_superadmin": True})
    ]
    assert fake.updates[0][1]["approved_at"]
    assert fake.perfis[1]["is_superadmin"] is False


def test_bootstrap_sem_confirmacao_nao_altera():
    fake = FakeSupabase(_perfis())
    rc = bootstrap.executar(["dono@exemplo.com"], ENV, entrada=lambda _: "n", cliente=fake)
    assert rc == 1
    assert fake.updates == []


def test_bootstrap_aborta_sem_perfil_ou_duplicado():
    with pytest.raises(bootstrap.Abortar, match="Nenhum perfil"):
        bootstrap.executar(["x@exemplo.com"], ENV, entrada=lambda _: "", cliente=FakeSupabase([]))
    duplicado = _perfis() + [{"id": "3", "email": "dono@exemplo.com"}]
    with pytest.raises(bootstrap.Abortar, match="inesperado"):
        bootstrap.executar(
            ["dono@exemplo.com"], ENV, entrada=lambda _: "", cliente=FakeSupabase(duplicado)
        )


@pytest.mark.parametrize("email", ["%@exemplo.com", "*", "a@b", "a@b.com,c@d.com"])
def test_bootstrap_rejeita_curingas_e_emails_invalidos(email):
    with pytest.raises(bootstrap.Abortar, match="inválido"):
        bootstrap.executar([email], ENV, cliente=FakeSupabase(_perfis()))


def test_bootstrap_exige_secret():
    with pytest.raises(bootstrap.Abortar, match="SUPABASE_SECRET_KEY"):
        bootstrap.executar(["dono@exemplo.com"], {"SUPABASE_URL": "https://a.supabase.co"})


# ---------- smoke_beta ----------


def _buscar_fake(respostas):
    def buscar(url, timeout):
        for sufixo, resp in respostas.items():
            if url.endswith(sufixo):
                return resp
        return 404, "", 1.0, None

    return buscar


def test_smoke_online(capsys):
    fake = _buscar_fake(
        {
            "/_stcore/health": (200, "ok", 5.0, None),
            "/": (200, "<title>Streamlit</title>", 10, None),
        }
    )
    assert smoke_beta.smoke("https://x", 1, buscar=fake) == 0
    saida = capsys.readouterr().out
    assert "ONLINE" in saida and "Health: OK" in saida


def test_smoke_5xx_e_offline(capsys):
    assert smoke_beta.smoke("https://x", 1, buscar=_buscar_fake({"/": (502, "", 1, None)})) == 1
    assert smoke_beta.smoke("https://x", 1, buscar=lambda u, t: (None, "", 1, "timeout")) == 1
    assert "OFFLINE" in capsys.readouterr().out
