"""Tira prints das telas do app com o Playwright e salva em prints/.

Uso:
    pip install -e ".[prints]"
    python scripts/prints.py            # todas as telas
    python scripts/prints.py inicio     # só as telas cujo nome contém "inicio"

O script sobe o app numa porta livre, abre cada tela num navegador sem janela,
espera o rodapé de segurança aparecer e salva a imagem da página inteira.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

RAIZ = Path(__file__).resolve().parents[1]
PASTA_PRINTS = RAIZ / "prints"
CHROMIUM_ALTERNATIVO = "/opt/pw-browsers/chromium"


@dataclass
class Tela:
    nome: str
    caminho: str = ""
    acoes: Callable[[Page], None] | None = None
    largura: int = 1280


def _abrir_expansor(texto: str) -> Callable[[Page], None]:
    def acao(pagina: Page) -> None:
        pagina.get_by_text(texto).click()

    return acao


def _clicar(botao: str, esperar: str) -> Callable[[Page], None]:
    def acao(pagina: Page) -> None:
        pagina.get_by_role("button", name=botao).click()
        pagina.get_by_text(esperar).first.wait_for(timeout=30_000)

    return acao


def _com_demo(menu: str, esperar: str) -> Callable[[Page], None]:
    """Carrega o caso de demonstração e abre a tela pelo menu lateral (mesma sessão)."""

    def acao(pagina: Page) -> None:
        pagina.get_by_role("button", name="Ato 2 · dados insuficientes").click()
        pagina.get_by_text("Resultado da importação").first.wait_for(timeout=30_000)
        pagina.get_by_role("link", name=menu).click()
        pagina.get_by_text(esperar).first.wait_for(timeout=30_000)
        pagina.wait_for_timeout(1500)

    return acao


def _relatorio_demo(pagina: Page) -> None:
    """Demo → Investigação → Relatório → Gerar relatório (mesma sessão)."""
    _com_demo("Investigação", "Próxima verificação")(pagina)
    pagina.get_by_role("link", name="Relatório").first.click()
    pagina.get_by_role("button", name="Gerar relatório").click()
    pagina.get_by_text("Prévia").wait_for(timeout=60_000)
    pagina.wait_for_timeout(2500)


def _investigacao_sem_vapor(pagina: Page) -> None:
    """Demo → Investigação → comparação estendida até 21/09 (semana sem medidor de vapor)."""
    _com_demo("Investigação", "Próxima verificação")(pagina)
    pagina.get_by_role("slider").nth(3).focus()
    pagina.keyboard.press("ArrowRight")
    pagina.get_by_text("Não dá para saber se o consumo").first.wait_for(timeout=60_000)
    pagina.wait_for_timeout(1500)


TELAS: list[Tela] = [
    Tela("01_inicio"),
    Tela("02_calculadora", "calculadora", _abrir_expansor("Detalhes do cálculo")),
    Tela(
        "03_importar_exemplo_com_problemas",
        "importar",
        _clicar("Exemplo com problemas (sintético)", "Resultado da importação"),
    ),
    Tela(
        "04_extrato_fornecedor",
        "importar",
        _com_demo("Extrato por fornecedor", "Custo por energia"),
    ),
    Tela(
        "05_dados_e_limites",
        "importar",
        _com_demo("Dados e limites", "21/09 a 28/09"),
    ),
    Tela("06_investigacao", "importar", _com_demo("Investigação", "Próxima verificação")),
    Tela("07_relatorio", "importar", _relatorio_demo),
    Tela("08_investigacao_sem_vapor", "importar", _investigacao_sem_vapor),
]


def _porta_livre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _esperar_app(url: str, limite_s: float = 60) -> None:
    fim = time.time() + limite_s
    while time.time() < fim:
        try:
            with urllib.request.urlopen(f"{url}/_stcore/health", timeout=2) as r:
                if r.status == 200:
                    return
        except OSError:
            time.sleep(0.5)
    raise RuntimeError("o app não respondeu a tempo")


def _abrir_navegador(p):
    try:
        return p.chromium.launch()
    except Exception:
        if Path(CHROMIUM_ALTERNATIVO).exists():
            return p.chromium.launch(executable_path=CHROMIUM_ALTERNATIVO)
        raise


def tirar_prints(filtro: str = "") -> list[Path]:
    PASTA_PRINTS.mkdir(exist_ok=True)
    porta = _porta_livre()
    url = f"http://127.0.0.1:{porta}"
    app = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "app/main.py",
            "--server.headless=true",
            f"--server.port={porta}",
        ],
        cwd=RAIZ,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env={**os.environ, "PYTHONUNBUFFERED": "1"},
    )
    salvos: list[Path] = []
    try:
        _esperar_app(url)
        with sync_playwright() as p:
            navegador = _abrir_navegador(p)
            for tela in TELAS:
                if filtro and filtro not in tela.nome:
                    continue
                pagina = navegador.new_page(viewport={"width": tela.largura, "height": 900})
                pagina.goto(f"{url}/{tela.caminho}")
                pagina.get_by_text("Não é um Registro de Segurança").wait_for(timeout=30_000)
                if tela.acoes:
                    tela.acoes(pagina)
                pagina.wait_for_timeout(800)
                # O Streamlit rola o conteúdo dentro de um contêiner, não na página:
                # aumenta a janela até caber tudo para o print sair inteiro.
                altura = pagina.evaluate(
                    "() => document.querySelector('[data-testid=\"stMain\"]').scrollHeight"
                )
                pagina.set_viewport_size({"width": tela.largura, "height": max(900, altura + 40)})
                pagina.wait_for_timeout(500)
                destino = PASTA_PRINTS / f"{tela.nome}.png"
                pagina.screenshot(path=str(destino), full_page=True)
                salvos.append(destino)
                pagina.close()
            navegador.close()
    finally:
        app.terminate()
        app.wait(timeout=10)
    return salvos


if __name__ == "__main__":
    for caminho in tirar_prints(sys.argv[1] if len(sys.argv) > 1 else ""):
        print(caminho.relative_to(RAIZ))
