"""Gera os 3 relatórios de exemplo em docs/exemplos_relatorio/ a partir do caso de demonstração.

Uso: python scripts/gerar_exemplos_relatorio.py
"""

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from euler.investigacao import investigar
from euler.io import importar_pasta
from euler.periodos import periodos_entre_estoques
from euler.relatorio import gerar_html, gerar_pdf
from euler.vapor import p_atm_por_altitude_bar

RAIZ = Path(__file__).resolve().parents[1]
DESTINO = RAIZ / "docs" / "exemplos_relatorio"
GERADO_EM = datetime(2026, 10, 1, 9, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))


def exemplos() -> dict[str, tuple[str, tuple, tuple]]:
    pacote = importar_pasta(RAIZ / "demo" / "caso_demo", p_atm_bar=p_atm_por_altitude_bar(1000))
    s = periodos_entre_estoques(pacote)
    base = (s[0][0], s[3][1])  # semanas 1 a 4
    return pacote, {
        "01_semanas_5_6_umidade_a_confirmar": ("Semanas 1–4 × 5–6: gases mais quentes; umidade a confirmar", base, (s[4][0], s[5][1])),
        "02_abstencao_sem_vapor": ("Semanas 1–4 × 7: medidor de vapor fora", base, s[6]),
        "03_semana_8_umidade_a_confirmar": ("Semanas 1–4 × 8: depois da limpeza; umidade a confirmar", base, s[7]),
    }  # fmt: skip


if __name__ == "__main__":
    DESTINO.mkdir(parents=True, exist_ok=True)
    pacote, casos = exemplos()
    for nome, (_, ref, comp) in casos.items():
        html = gerar_html(investigar(pacote, ref, comp), gerado_em=GERADO_EM)
        (DESTINO / f"{nome}.html").write_text(html, encoding="utf-8")
        pdf = gerar_pdf(html)
        if pdf:
            (DESTINO / f"{nome}.pdf").write_bytes(pdf)
        print(f"docs/exemplos_relatorio/{nome}.html" + (" (+ PDF)" if pdf else ""))
