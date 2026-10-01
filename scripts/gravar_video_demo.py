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


def mover(p: Page, alca: int, tecla: str, vezes: int = 1) -> None:
    """Move uma alça dos controles de período (0–1: referência; 2–3: comparação)."""
    p.get_by_role("slider").nth(alca).focus()
    for _ in range(vezes):
        p.keyboard.press(tecla)
        p.wait_for_timeout(900)


def roteiro(p: Page, url: str) -> None:
    """Cenas de demo/ROTEIRO_VIDEO.md (as legendas resumem a narração)."""
    p.goto(url)
    p.get_by_text("Não é um Registro de Segurança").wait_for(timeout=60_000)

    # 0:00 Início · o problema do gestor (dados sintéticos desde o começo)
    legenda(p, "Caso SINTÉTICO, criado para demonstração: uma caldeira a cavaco de 20 t/h.")
    p.wait_for_timeout(4000)
    legenda(p, "O consumo de cavaco subiu e o gestor não sabe dizer por quê.")
    p.get_by_text("Em que pé está a EULER").scroll_into_view_if_needed()
    p.wait_for_timeout(5500)
    p.evaluate(TOPO_JS)
    p.get_by_role("button", name="Começar com o caso de demonstração").click()

    # 0:16 Dados e limites · qualidade dos registros
    p.get_by_text("Qualidade dos registros").first.wait_for(timeout=60_000)
    legenda(p, "A EULER lê os registros que a fábrica já tem e aponta os problemas.")
    p.wait_for_timeout(5000)
    legenda(p, "Lacuna no diário, medidor de vapor zerado: nada é corrigido em silêncio.")
    p.wait_for_timeout(6000)

    # 0:28 Extrato por fornecedor · valor do extrato por energia
    ir_para(p, "4. Extrato por fornecedor", "Custo por energia")
    legenda(p, "O mais barato por tonelada (F3) é o mais caro por energia: R$ 20/GJ × R$ 17/GJ.")
    p.wait_for_timeout(6000)
    rolar(p, 380, 5000)
    legenda(p, "O cavaco do F3 ficou mais úmido semana a semana. A caldeira compra energia.")
    p.get_by_text("Umidade do cavaco por semana").scroll_into_view_if_needed()
    p.wait_for_timeout(9000)

    # 0:52 Investigação · a mudança de consumo
    ir_para(p, "3. Investigação", "Próxima verificação")
    rolar(p, 450, 1500)
    legenda(p, "Agosto × as duas semanas seguintes: o consumo por tonelada de vapor subiu 10%.")
    p.wait_for_timeout(6000)
    rolar(p, 650, 3000)
    legenda(p, "Gases 32 °C mais quentes: explicação compatível com os dados, não comprovada.")
    p.get_by_text("2. O que os dados sustentam").scroll_into_view_if_needed()
    p.wait_for_timeout(7000)
    legenda(p, "A umidade também subiu, mas falta a incerteza do método de umidade…")
    p.get_by_text("3. Explicações que continuam possíveis").scroll_into_view_if_needed()
    p.wait_for_timeout(6000)

    # 1:18 Dados insuficientes
    p.evaluate(TOPO_JS)
    legenda(p, "…por isso a EULER não conclui: diz o que fecharia a conta se fosse confirmado.")
    p.wait_for_timeout(6500)
    mover(p, 3, "ArrowRight")  # comparação: 31/08–21/09
    mover(p, 2, "ArrowRight", 2)  # comparação: só 14/09–21/09 (medidor de vapor fora)
    p.get_by_text("Não dá para saber se o consumo").first.wait_for(timeout=60_000)
    legenda(p, "Sem o medidor de vapor, ela nem tenta: não dá para saber se o consumo mudou.")
    p.wait_for_timeout(6000)
    mover(p, 2, "ArrowLeft", 2)  # volta para 31/08–14/09
    mover(p, 3, "ArrowLeft")
    p.get_by_text("subiu 10,1%").first.wait_for(timeout=60_000)

    # 1:38 Relatório e próxima verificação
    ir_para(p, "5. Relatório", "Gerar relatório")
    legenda(p, "Tudo vira um relatório em linguagem simples, com cinco blocos fixos.")
    p.get_by_role("button", name="Gerar relatório").click()
    p.get_by_text("Prévia").wait_for(timeout=90_000)
    p.wait_for_timeout(3500)
    quadro = p.frame_locator("iframe").first
    quadro.get_by_text("5. Próxima verificação").scroll_into_view_if_needed()
    legenda(p, "A saída nunca é uma ordem para a caldeira: é a próxima verificação.")
    p.wait_for_timeout(8000)

    # 1:56 Encerramento
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
