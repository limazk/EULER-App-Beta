"""Reexecuta o ensaio horário público sem rede e exporta o resultado auditável."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "app")]
from ensaio_horario import executar

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--saida", type=Path, required=True)
args = parser.parse_args()
r = executar()
args.saida.parent.mkdir(parents=True, exist_ok=True)
args.saida.write_text(
    json.dumps(r, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8"
)
for unidade, u in r["unidades"].items():
    for m in u["comparacoes"]:
        print(
            unidade,
            m["mes"],
            "horas",
            m["horas_comparaveis"],
            "delta %",
            round(m["delta_pct"], 4),
            "USD referencia",
            round(m["valor_referencia_usd"], 2),
        )
