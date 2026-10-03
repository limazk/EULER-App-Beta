"""python scripts/validar_ensaio_publico.py --saida resultado.json [--conferir-heos]."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "app")]
from ensaio_publico import executar

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--saida", type=Path, required=True)
parser.add_argument("--conferir-heos", action="store_true")
args = parser.parse_args()
r = executar()
if args.conferir_heos:
    import CoolProp
    from CoolProp.CoolProp import PropsSI

    for e in r["estados"]:
        tipo = e["tipo"]
        par = (
            ("Q", 0 if tipo == "liquido_saturado" else 1)
            if tipo in ("liquido_saturado", "saturado_seco")
            else ("T", e["t_c"] + 273.15)
        )
        h = PropsSI("H", "P", e["p_mpa"] * 1e6, *par, "HEOS::Water") / 1000
        if abs(h - e["h_heos_kj_kg"]) > 1e-6:
            raise ValueError("Referência HEOS divergiu: confira a versão e a origem do fixture.")
    r["conferencia_independente_executada"] = {
        "biblioteca": "CoolProp HEOS",
        "versao": CoolProp.__version__,
        "pontos": 15,
    }
args.saida.parent.mkdir(parents=True, exist_ok=True)
args.saida.write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
print("Importação:", r["importacao"])
print(
    "Maior diferença entre implementações (%):", max(abs(e["delta_heos_pct"]) for e in r["estados"])
)
print("Diferença de consumo entre cargas (kg/t):", r["comparacao"]["delta"])
print("Mudança detectável:", r["comparacao"]["detectavel"])
