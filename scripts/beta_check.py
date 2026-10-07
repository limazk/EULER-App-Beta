"""Valida o ambiente do EULER Beta sem nunca exibir valores de segredos.

Uso:
    python scripts/beta_check.py            # variáveis + cliente público + tabelas (admin, se houver secret)
    python scripts/beta_check.py --offline  # somente variáveis de ambiente

Lê apenas variáveis de ambiente. Não modifica dados.
Código de saída: 0 se tudo OK, 1 se algo obrigatório falhar.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

VARIAVEIS = (
    "SUPABASE_URL",
    "SUPABASE_PUBLISHABLE_KEY",
    "SUPABASE_SECRET_KEY",
    "EULER_DADOS_DIR",
)
TABELAS = ("profiles", "organizations", "memberships", "feedback")


def status_variaveis(env: dict[str, str]) -> dict[str, bool]:
    return {nome: bool(env.get(nome, "").strip()) for nome in VARIAVEIS}


def url_supabase_valida(url: str) -> bool:
    partes = urlparse(url.strip())
    return partes.scheme == "https" and bool(partes.hostname) and not partes.path.strip("/")


def checar_ambiente(env: dict[str, str]) -> list[str]:
    """Imprime o estado das variáveis e retorna a lista de problemas obrigatórios."""
    problemas: list[str] = []
    for nome, ok in status_variaveis(env).items():
        print(f"{nome}: {'OK' if ok else 'AUSENTE'}")
        if not ok and nome != "SUPABASE_SECRET_KEY":
            problemas.append(f"{nome} ausente")

    url = env.get("SUPABASE_URL", "")
    if url and not url_supabase_valida(url):
        print("SUPABASE_URL: formato inválido (esperado https://<ref>.supabase.co)")
        problemas.append("SUPABASE_URL inválida")

    dados = env.get("EULER_DADOS_DIR", "")
    if dados:
        pasta = Path(dados)
        if not pasta.is_dir():
            print("EULER_DADOS_DIR: diretório não existe")
            problemas.append("EULER_DADOS_DIR inexistente")
        elif not os.access(pasta, os.W_OK):
            print("EULER_DADOS_DIR: sem permissão de escrita")
            problemas.append("EULER_DADOS_DIR sem escrita")
    return problemas


def _consultar(cliente, tabela: str) -> str | None:
    """Consulta mínima (somente leitura). Retorna mensagem de erro ou None."""
    try:
        cliente.table(tabela).select("*", count="exact", head=True).limit(1).execute()
    except Exception as exc:  # noqa: BLE001
        return type(exc).__name__
    return None


def checar_supabase(env: dict[str, str]) -> list[str]:
    url = env.get("SUPABASE_URL", "").strip()
    publica = env.get("SUPABASE_PUBLISHABLE_KEY", "").strip()
    secreta = env.get("SUPABASE_SECRET_KEY", "").strip()
    if not url or not publica:
        print("Supabase: ignorado (SUPABASE_URL/SUPABASE_PUBLISHABLE_KEY ausentes)")
        return []

    from supabase.lib.client_options import ClientOptions

    from supabase import create_client

    opcoes = ClientOptions(auto_refresh_token=False, persist_session=False)
    try:
        create_client(url, publica, options=opcoes)
    except Exception as exc:  # noqa: BLE001
        print(f"Supabase: FALHA ao criar cliente público ({type(exc).__name__})")
        return ["Supabase indisponível"]
    # Sem sessão, o papel anon não tem grant nas tabelas: não consultar com este cliente.
    print("Cliente público: OK")

    if not secreta:
        print("SUPABASE_SECRET_KEY ausente — verificação administrativa das tabelas ignorada.")
        return []

    try:
        admin = create_client(url, secreta, options=opcoes)
    except Exception as exc:  # noqa: BLE001
        print(f"Cliente administrativo: FALHA ({type(exc).__name__})")
        return ["cliente administrativo"]

    problemas: list[str] = []
    for tabela in TABELAS:
        erro = _consultar(admin, tabela)
        print(f"Tabela {tabela} (admin): {'OK' if erro is None else f'FALHA ({erro})'}")
        if erro:
            problemas.append(f"tabela {tabela}")
    return problemas


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--offline", action="store_true", help="não testa conexão Supabase")
    args = parser.parse_args(argv)

    env = dict(os.environ)
    problemas = checar_ambiente(env)
    if not args.offline:
        problemas += checar_supabase(env)

    if problemas:
        print(f"\nResultado: FALHA ({len(problemas)} problema(s))")
        return 1
    print("\nResultado: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
