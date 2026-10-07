"""Smoke test do EULER Beta publicado no Render (somente leitura, sem navegador).

Uso:
    python scripts/smoke_beta.py [URL] [--timeout SEGUNDOS]

URL padrão: https://euler-app-beta.onrender.com
Código de saída: 0 se online e sem 5xx, 1 caso contrário.
Obs.: no plano gratuito o Render "dorme"; a primeira chamada pode levar ~1 min.
"""

from __future__ import annotations

import argparse
import sys
import time
import urllib.error
import urllib.request

URL_PADRAO = "https://euler-app-beta.onrender.com"
HEALTH_PATHS = ("/_stcore/health", "/healthz")


def buscar(url: str, timeout: float) -> tuple[int | None, str, float, str | None]:
    """Retorna (status, corpo, ms, erro). Status None = sem resposta HTTP."""
    req = urllib.request.Request(url, headers={"User-Agent": "euler-smoke/1"})
    inicio = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            corpo = resp.read(65536).decode("utf-8", "replace")
            return resp.status, corpo, (time.monotonic() - inicio) * 1000, None
    except urllib.error.HTTPError as exc:
        return exc.code, "", (time.monotonic() - inicio) * 1000, None
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        motivo = getattr(exc, "reason", exc)
        return None, "", (time.monotonic() - inicio) * 1000, str(motivo)


def smoke(base: str, timeout: float, buscar=buscar) -> int:
    base = base.rstrip("/")
    status, corpo, ms, erro = buscar(base + "/", timeout)
    if status is None:
        print(f"EULER Beta: OFFLINE\nErro: {erro}")
        return 1

    online = 200 <= status < 400
    print(f"EULER Beta: {'ONLINE' if online else 'ERRO'}")
    print(f"HTTP: {status}")
    print(f"Tempo: {ms:.0f} ms")
    streamlit = "streamlit" in corpo.lower()
    print(f"Streamlit: {'OK' if streamlit else 'não detectado'}")

    health = "indisponível"
    for caminho in HEALTH_PATHS:
        h_status, h_corpo, _, _ = buscar(base + caminho, timeout)
        if h_status == 200 and h_corpo.strip().lower() == "ok":
            health = "OK"
            break
        if h_status is not None and h_status >= 500:
            health = f"FALHA (HTTP {h_status})"
            break
    print(f"Health: {health}")

    falhou = not online or status >= 500 or health.startswith("FALHA")
    return 1 if falhou else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Smoke test do EULER Beta")
    parser.add_argument("url", nargs="?", default=URL_PADRAO)
    parser.add_argument("--timeout", type=float, default=90.0)
    args = parser.parse_args(argv)
    return smoke(args.url, args.timeout)


if __name__ == "__main__":
    sys.exit(main())
