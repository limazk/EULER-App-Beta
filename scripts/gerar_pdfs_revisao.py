"""Gera os PDFs para os revisores científicos (Etapa 8) em docs/revisao/.

- fisica_para_revisao.pdf: docs/fisica/fisica_para_revisao.md na íntegra, com uma capa que diz a
  versão do código e a situação da revisão (nenhum item aprovado).
- perguntas_revisores.pdf: docs/fisica/perguntas_revisores.md (três decisões prioritárias + Q1–Q17).

Uso:
    pip install -e ".[prints]"     # playwright + markdown
    python scripts/gerar_pdfs_revisao.py

O conteúdo vem dos arquivos .md (fonte única); o PDF só formata para imprimir e anotar.
"""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime
from html import escape
from pathlib import Path
from zoneinfo import ZoneInfo

import markdown
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prints import RAIZ, _abrir_navegador

DESTINO = RAIZ / "docs" / "revisao"

CSS = """
@page { size: A4; margin: 18mm 16mm 20mm; }
body { font-family: "DejaVu Sans", Arial, sans-serif; font-size: 10.5pt; line-height: 1.45;
       color: #1d1d1f; }
h1 { font-size: 19pt; margin: 0 0 8px; }
h2 { font-size: 14pt; margin: 22px 0 8px; padding-bottom: 3px; border-bottom: 1px solid #ccc;
     break-after: avoid-page; }
h3 { font-size: 11.5pt; margin: 16px 0 6px; break-after: avoid-page; }
p, li { orphans: 3; widows: 3; }
p { margin: 0 0 12px; }
code { font-family: "DejaVu Sans Mono", monospace; font-size: 9.5pt; background: #f3f3f3;
       padding: 0 3px; border-radius: 3px; }
table { border-collapse: collapse; width: 100%; margin: 8px 0 12px; font-size: 9.5pt; }
th, td { border: 1px solid #c8c8c8; padding: 4px 6px; text-align: left; vertical-align: top; }
th { background: #f1f1f1; }
tr { break-inside: avoid; }
blockquote { margin: 8px 0; padding: 6px 12px; border-left: 3px solid #c2410c;
             background: #fff7ed; }
hr { border: 0; border-top: 1px solid #ddd; margin: 18px 0; }
.capa { border: 2px solid #c2410c; border-radius: 8px; padding: 18px 22px; margin-bottom: 26px;
        break-inside: avoid; }
.capa .marca { color: #c2410c; font-weight: 700; letter-spacing: .08em; font-size: 9pt; }
.capa table { font-size: 10pt; }
.capa td:first-child { width: 34%; font-weight: 700; background: #fafafa; }
"""

# (título, cada linha do .md é uma frase separada?). fisica_para_revisao.md escreve uma
# afirmação por linha (equação, pergunta, campo do revisor); perguntas_revisores.md quebra
# parágrafos longos em várias linhas, que devem voltar a ser um parágrafo só.
DOCUMENTOS = {
    "fisica_para_revisao": ("Física e cálculos para revisão científica (E1–E15)", True),
    "perguntas_revisores": ("Três decisões prioritárias e perguntas Q1–Q17", False),
}


def _versao() -> str:
    try:
        saida = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=RAIZ,
            capture_output=True,
            text=True,
            check=False,
        )
        return saida.stdout.strip() or "desconhecida"
    except OSError:
        return "desconhecida"


def _capa(titulo: str, versao: str) -> str:
    linhas = [
        ("Documento", titulo),
        ("Versão do código", f"commit {versao} (branch claude/new-session-xytynj)"),
        ("Gerado em", f"{datetime.now(ZoneInfo('America/Sao_Paulo')):%d/%m/%Y}"),
        (
            "Situação",
            (
                "Nenhum item aprovado. Os cálculos estão implementados e verificados por "
                "testes automáticos; as hipóteses aguardam revisão humana. Ainda sem "
                "validação com dados reais de caldeira."
            ),
        ),
        (
            "Como devolver",
            (
                "Marcar o status de cada item e escrever correções com referência "
                "bibliográfica. Cada resposta vira uma decisão aprovada em docs/gestao/decisoes.md, "
                "com o nome do revisor."
            ),
        ),
        (
            "Por onde começar",
            (
                "Pelas três decisões prioritárias (perguntas_revisores.pdf): combustível "
                "efetivamente queimado; amostragem de umidade e estado do vapor; "
                "interpretação das incertezas e do critério D29."
            ),
        ),
    ]
    corpo = "".join(f"<tr><td>{escape(a)}</td><td>{escape(b)}</td></tr>" for a, b in linhas)
    return (
        '<div class="capa"><div class="marca">EULER · MATERIAL PARA REVISORES</div>'
        f"<table>{corpo}</table></div>"
    )


def _html(nome: str, titulo: str, versao: str, linha_por_frase: bool) -> str:
    texto = (RAIZ / "docs" / "fisica" / f"{nome}.md").read_text(encoding="utf-8")
    extensoes = ["tables", "sane_lists"] + (["nl2br"] if linha_por_frase else [])
    corpo = markdown.markdown(texto, extensions=extensoes)
    return (
        '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
        f"<title>EULER · {escape(titulo)}</title><style>{CSS}</style></head>"
        f"<body>{_capa(titulo, versao)}{corpo}</body></html>"
    )


RODAPE = (
    '<div style="font-size:8px;width:100%;text-align:center;color:#777;">'
    "EULER · material para revisão científica · página "
    '<span class="pageNumber"></span> de <span class="totalPages"></span></div>'
)


def gerar() -> list[Path]:
    DESTINO.mkdir(parents=True, exist_ok=True)
    versao = _versao()
    saidas = []
    with sync_playwright() as pw:
        navegador = _abrir_navegador(pw)
        for nome, (titulo, linha_por_frase) in DOCUMENTOS.items():
            pagina = navegador.new_page()
            pagina.set_content(_html(nome, titulo, versao, linha_por_frase), wait_until="load")
            destino = DESTINO / f"{nome}.pdf"
            pagina.pdf(
                path=str(destino),
                format="A4",
                print_background=True,
                display_header_footer=True,
                header_template="<div></div>",
                footer_template=RODAPE,
                margin={"top": "18mm", "bottom": "20mm", "left": "16mm", "right": "16mm"},
            )
            pagina.close()
            saidas.append(destino)
            print(destino.relative_to(RAIZ))
        navegador.close()
    return saidas


if __name__ == "__main__":
    gerar()
