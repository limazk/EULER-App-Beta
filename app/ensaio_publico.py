"""Ensaio reproduzível de fontes públicas, separado dos dados ativos do usuário.

As médias sem data são avaliadas como pontos, nunca integradas como um histórico.
Pressões do caso subcrítico são interpretadas como absolutas de forma CONDICIONAL.
Nenhum preço, PCI ou intervalo operacional é inventado para fechar balanços.
"""

import json
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from euler.capacidades import avaliar
from euler.deteccao import comparar
from euler.fluxos import fluxo_entalpia_vapor
from euler.io import importar_pacote
from euler.saude import avaliar_saude
from euler.tipos import Grandeza
from euler.vapor import h_agua_mj_kg, h_liquido_saturado_mj_kg, h_vapor_mj_kg

DADOS = Path(__file__).resolve().parents[1] / "validation/public/ensaio_2026"


def executar() -> dict:
    """Executa módulos atuais sobre fontes fixas e referências HEOS pré-calculadas."""
    fonte = json.loads((DADOS / "subcritica.json").read_text(encoding="utf-8"))
    estados = []
    for e in fonte["estados"]:
        p, t = e["p_mpa"] * 10, e["t_c"]
        if e["tipo"] == "agua":
            h = h_agua_mj_kg(p, t)
        elif e["tipo"] == "liquido_saturado":
            h = h_liquido_saturado_mj_kg(p)
        else:
            h = h_vapor_mj_kg(p, e["tipo"], t_vapor_c=t)
        estados.append(
            {
                **e,
                "h_euler_kj_kg": h * 1000,
                "delta_heos_pct": 100 * (h * 1000 / e["h_heos_kj_kg"] - 1),
                "delta_fonte_pct": 100 * (h * 1000 / e["h_fonte_kj_kg"] - 1),
            }
        )
    cargas = []
    for c in fonte["cargas"]:
        h = h_vapor_mj_kg(c["p_vapor_mpa"] * 10, "superaquecido", t_vapor_c=c["t_vapor_c"])
        hw = h_agua_mj_kg(c["p_agua_mpa"] * 10, c["t_agua_c"])
        fluxo = fluxo_entalpia_vapor(
            pd.DataFrame(
                [
                    {
                        "caldeira_id": "PUBLICA-SUBCRITICA",
                        "vazao_vapor_t_h": c["vapor_kg_s"] * 3.6,
                        "p_vapor_bar_abs": c["p_vapor_mpa"] * 10,
                        "t_vapor_c": c["t_vapor_c"],
                        "estado_vapor": "superaquecido",
                    }
                ]
            )
        )
        cargas.append(
            {
                **c,
                "vapor_t_h": c["vapor_kg_s"] * 3.6,
                "consumo_kg_t": 1000 * c["combustivel_kg_s"] / c["vapor_kg_s"],
                "fluxo_entalpia_mw": fluxo.media_mw,
                "potencia_vapor_mw": c["vapor_kg_s"] * (h - hw),
            }
        )
    cmp = comparar(
        "Consumo entre cargas diferentes",
        "kg/t",
        *[
            Grandeza(
                c["consumo_kg_t"],
                "kg/t",
                "estimado",
                nota="Razão de médias publicadas; sem incerteza.",
            )
            for c in (cargas[0], cargas[-1])
        ],
    )
    raw = (DADOS / "diario.csv").read_bytes()
    pacote = importar_pacote({"diario": raw})
    diario = pacote.dados("diario")
    original = pd.read_csv(DADOS / "diario.csv")
    caps = {c.id: c.situacao for c in avaliar(pacote)}
    saude = avaliar_saude(pacote)
    return {
        "fonte_subcritica": fonte,
        "estados": estados,
        "cargas": cargas,
        "comparacao": asdict(cmp),
        "zhejiang": json.loads((DADOS / "zhejiang.json").read_text(encoding="utf-8")),
        "importacao": {
            "linhas": len(diario),
            "origens": sorted(pacote.origens_de_dado()),
            "sintetico": bool(pacote.sintetico),
            "valores_preservados": diario["t_vapor_c"].astype(float).tolist()
            == original.t_vapor_c.tolist(),
            "eficiencia": caps["eficiencia_direta"],
            "energia_vapor": caps["energia_vapor"],
            "saude": saude.selo,
            "motivo_saude": saude.frase,
        },
        "perda_financeira_brl": None,
        "economia_comprovada_brl": None,
    }
