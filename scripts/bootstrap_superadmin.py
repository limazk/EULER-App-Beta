"""Promove UM perfil existente a superadmin do EULER Beta, com confirmação.

Uso:
    python scripts/bootstrap_superadmin.py email@exemplo.com

Exige SUPABASE_URL e SUPABASE_SECRET_KEY no ambiente. Nunca cria usuário,
nunca usa curinga e só altera a linha cujo e-mail é exatamente o informado.
A pessoa precisa ter se cadastrado no app antes (o perfil nasce no cadastro).
"""

from __future__ import annotations

import os
import re
import sys
from datetime import UTC, datetime

EMAIL_RE = re.compile(r"^[^@\s%*,;]+@[^@\s%*,;]+\.[^@\s%*,;]+$")


class Abortar(Exception):
    """Erro de fluxo: imprime a mensagem e sai com código 1."""


def validar_email(bruto: str) -> str:
    email = bruto.strip().lower()
    if not EMAIL_RE.match(email):
        raise Abortar(f"E-mail inválido: {bruto!r}")
    return email


def buscar_perfil(cliente, email: str) -> dict:
    resp = (
        cliente.table("profiles")
        .select("id,email,status,is_superadmin")
        .eq("email", email)
        .limit(2)
        .execute()
    )
    linhas = resp.data or []
    if not linhas:
        raise Abortar(f"Nenhum perfil encontrado para {email}. Cadastre-se no app primeiro.")
    if len(linhas) != 1 or (linhas[0].get("email") or "").lower() != email:
        raise Abortar("Resultado inesperado na busca do perfil. Nada foi alterado.")
    return linhas[0]


def promover(cliente, perfil: dict) -> dict:
    dados = {
        "status": "active",
        "is_superadmin": True,
        "approved_at": datetime.now(UTC).isoformat(),
    }
    resp = cliente.table("profiles").update(dados).eq("id", perfil["id"]).execute()
    linhas = resp.data or []
    if len(linhas) != 1:
        raise Abortar(
            f"Atualização afetou {len(linhas)} linha(s); esperado 1. Verifique no painel."
        )
    return linhas[0]


def executar(argv: list[str], env: dict[str, str], entrada=input, cliente=None) -> int:
    if len(argv) != 1:
        raise Abortar("Uso: python scripts/bootstrap_superadmin.py email@exemplo.com")
    email = validar_email(argv[0])

    url = env.get("SUPABASE_URL", "").strip()
    secreta = env.get("SUPABASE_SECRET_KEY", "").strip()
    if not url:
        raise Abortar("SUPABASE_URL ausente.")
    if not secreta:
        raise Abortar("SUPABASE_SECRET_KEY ausente.")

    if cliente is None:
        from supabase.lib.client_options import ClientOptions

        from supabase import create_client

        cliente = create_client(
            url, secreta, options=ClientOptions(auto_refresh_token=False, persist_session=False)
        )

    perfil = buscar_perfil(cliente, email)
    print(f"E-mail:        {perfil['email']}")
    print(f"Status atual:  {perfil.get('status')}")
    print(f"Superadmin:    {bool(perfil.get('is_superadmin'))}")

    resposta = entrada("\nDigite o e-mail novamente para promover a superadmin ativo: ")
    if resposta.strip().lower() != email:
        print("Confirmação não confere. Nada foi alterado.")
        return 1

    novo = promover(cliente, perfil)
    print(
        f"OK: {novo.get('email')} agora status={novo.get('status')}, "
        f"is_superadmin={novo.get('is_superadmin')}"
    )
    return 0


def main() -> int:
    try:
        return executar(sys.argv[1:], dict(os.environ))
    except Abortar as exc:
        print(f"ABORTADO: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(
            f"ABORTADO: erro inesperado ({type(exc).__name__}). Nada confirmado.", file=sys.stderr
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
