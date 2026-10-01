"""Grava um RASCUNHO do vídeo do edital (sem narração, com legendas) seguindo demo/ROTEIRO_VIDEO.md.

Uso:
    pip install -e ".[prints]"
    python scripts/gravar_video_demo.py        # salva em demo/video/rascunho_video_demo.webm

O app sobe numa porta livre; o navegador (1280 × 720) segue as cenas do roteiro.
"""

from __future__ import annotations

import shutil
import sys
import time
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prints import RAIZ, _abrir_navegador, _esperar_app, _porta_livre

DESTINO = RAIZ / "demo" / "video"
LARGURA, ALTURA = 1280, 720

LEGENDA_JS = """(t) => {
  let el = document.getElementById('legenda-euler');
  if (!el) {
    el = document.createElement('div');
    el.id = 'legenda-euler';
    Object.assign(el.style, {position: 'fixed', left: '50%', bottom: '24px',
      transform: 'translateX(-50%)', width: '86%', maxWidth: '1000px',
      background: 'rgba(17,17,17,.88)', color: '#fff', padding: '12px 20px',
      borderRadius: '8px', font: '500 20px/1.35 "Source Sans 3", Arial, sans-serif',
      zIndex: 999999, textAlign: 'center', boxShadow: '0 4px 18px rgba(0,0,0,.25)'});
    document.body.appendChild(el);
  }
  el.textContent = t;
  el.style.display = t ? 'block' : 'none';
}"""

ROLAR_JS = """(px) => document.querySelector('[data-testid="stMain"]').scrollBy({top: px, behavior: 'smooth'})"""
TOPO_JS = """() => document.querySelector('[data-testid="stMain"]').scrollTo({top: 0})"""


def legenda(p: Page, texto: str) -> None:
    p.evaluate(LEGENDA_JS, texto)


def rolar(p: Page, px: int, pausa_ms: int = 1800) -> None:
    p.evaluate(ROLAR_JS, px)
    p.wait_for_timeout(pausa_ms)


def ir_para(p: Page, menu: str, esperar: str) -> None:
    p.get_by_role("link", name=menu).first.click()
    p.get_by_text(esperar).first.wait_for(timeout=60_000)
    p.evaluate(TOPO_JS)
    p.wait_for_timeout(600)


def roteiro(p: Page, url: str) -> None:
    p.goto(url)
    p.get_by_text("Não é um Registro de Segurança").wait_for(timeout=60_000)

    # 0:00 Início
    legenda(
        p,
        "Uma fábrica compra cavaco por tonelada. Mas a caldeira consome energia — e o consumo mudou.",
    )
    p.wait_for_timeout(5000)
    rolar(p, 300, 4500)

    # 0:10 Importar
    ir_para(p, "1. Importar dados", "Arraste os arquivos aqui")
    legenda(
        p,
        "A EULER usa os registros que a fábrica já tem: diário do operador, recebimentos e amostras.",
    )
    p.get_by_role("button", name="Caso de demonstração (8 semanas)").click()
    p.get_by_text("Resultado da importação").first.wait_for(timeout=60_000)
    p.wait_for_timeout(3500)
    rolar(p, 700, 2500)
    legenda(p, "Ela aponta os problemas — lacunas, medidor zerado — sem corrigir nada em silêncio.")
    rolar(p, 450, 5000)

    # 0:24 Dados e limites
    ir_para(p, "2. Dados e limites", "Análises liberadas")
    legenda(p, "Antes de concluir, ela mostra o que dá e o que não dá para saber.")
    p.wait_for_timeout(3500)
    p.get_by_text("Período a período").scroll_into_view_if_needed()
    p.wait_for_timeout(800)
    legenda(p, "Nesta semana, o medidor de vapor estava fora: ali, não dá para fechar a conta.")
    p.wait_for_timeout(6500)

    # 0:36 Investigação
    ir_para(p, "3. Investigação", "Próxima verificação")
    legenda(p, "Agosto × as duas semanas seguintes: o consumo por tonelada de vapor subiu 10%.")
    p.wait_for_timeout(4500)
    rolar(p, 330, 4500)
    legenda(
        p,
        "Os dados sustentam duas causas: cavaco mais úmido (sobretudo do F3) e gases 32 °C mais quentes.",
    )
    rolar(p, 650, 5500)
    legenda(p, "Excesso de ar e perdas ocultas foram descartados — com o motivo.")
    rolar(p, 650, 5500)
    legenda(p, "A saída não é uma ordem para a caldeira: é a próxima verificação.")
    p.get_by_text("5. Próxima verificação").scroll_into_view_if_needed()
    p.wait_for_timeout(7000)

    # 1:06 Extrato
    ir_para(p, "4. Extrato por fornecedor", "Custo por energia")
    legenda(p, "O fornecedor mais barato por tonelada nem sempre é o mais barato por energia.")
    p.wait_for_timeout(3000)
    rolar(p, 480, 6000)
    legenda(p, "O F3 cobra menos por tonelada, mas o cavaco dele ficou mais úmido semana a semana.")
    p.get_by_text("Umidade do cavaco por semana").scroll_into_view_if_needed()
    p.wait_for_timeout(7500)

    # 1:24 Relatório
    ir_para(p, "5. Relatório", "Gerar relatório")
    legenda(
        p,
        "Tudo vira um relatório em linguagem simples, com cinco blocos fixos e o aviso de segurança.",
    )
    p.get_by_role("button", name="Gerar relatório").click()
    p.get_by_text("Prévia").wait_for(timeout=60_000)
    p.wait_for_timeout(3000)
    rolar(p, 600, 6500)
    p.wait_for_timeout(4000)

    # 1:40 Abstenção: comparar com a semana sem medidor de vapor
    ir_para(p, "3. Investigação", "Próxima verificação")
    legenda(p, "E quando falta dado? Vamos olhar a semana em que o medidor de vapor estava fora.")
    alca = p.get_by_role("slider")
    alca.nth(3).focus()
    p.keyboard.press("ArrowRight")
    p.wait_for_timeout(1500)
    alca.nth(2).focus()
    p.keyboard.press("ArrowRight")
    p.wait_for_timeout(1200)
    p.keyboard.press("ArrowRight")
    p.get_by_text("Não dá para concluir").first.wait_for(timeout=60_000)
    legenda(p, "A resposta honesta: não dá para concluir — e a EULER diz exatamente o que medir.")
    p.wait_for_timeout(7000)

    # 1:54 Encerramento
    p.evaluate(TOPO_JS)
    legenda(
        p,
        "EULER: quanto de energia a fábrica comprou, quanto virou vapor e onde o resto foi parar.",
    )
    p.wait_for_timeout(6000)


def gravar() -> Path:
    import subprocess

    DESTINO.mkdir(parents=True, exist_ok=True)
    temporaria = DESTINO / "_gravando"
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
    )
    try:
        _esperar_app(url)
        with sync_playwright() as pw:
            navegador = _abrir_navegador(pw)
            contexto = navegador.new_context(
                viewport={"width": LARGURA, "height": ALTURA},
                record_video_dir=str(temporaria),
                record_video_size={"width": LARGURA, "height": ALTURA},
            )
            pagina = contexto.new_page()
            inicio = time.time()
            roteiro(pagina, url)
            duracao = time.time() - inicio
            video = Path(pagina.video.path())
            contexto.close()
            navegador.close()
    finally:
        app.terminate()
        app.wait(timeout=10)
    destino = DESTINO / "rascunho_video_demo.webm"
    shutil.move(video, destino)
    shutil.rmtree(temporaria, ignore_errors=True)
    print(f"{destino.relative_to(RAIZ)} · {duracao:.0f} s")
    return destino


if __name__ == "__main__":
    gravar()
