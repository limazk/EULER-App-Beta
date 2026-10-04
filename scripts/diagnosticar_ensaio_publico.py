"""Reproduz e exporta diagnóstico das quatro caldeiras; não baixa nem modifica fontes.

Uso: python scripts/diagnosticar_ensaio_publico.py --saida output/diagnostico-publico
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "app")]

from diagnostico_publico import diagnosticos
from ensaio_horario import executar
from parecer_ensaio import relatorio_texto

from euler.evidencias import assinatura, verificar_integridade


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, required=True)
    args = parser.parse_args()
    args.saida.mkdir(parents=True, exist_ok=True)
    r = executar()
    saida = {}
    comparacoes = []
    for unidade, u in r["unidades"].items():
        ds = diagnosticos(r, unidade)
        for d, m in zip(ds, u["comparacoes"], strict=True):
            if not verificar_integridade(d):
                raise ValueError("Diagnóstico com assinatura inconsistente.")
            for atual, anterior in (
                (d["observacao"]["variacao"], m["delta_gj"]),
                (d["economia"]["desvio_estimado"], m["valor_referencia_usd"]),
            ):
                if atual != anterior:
                    raise ValueError("Camada interpretativa alterou os cálculos existentes.")
            comparacoes.append(
                {
                    "unidade": unidade,
                    "mes": m["mes"],
                    "delta_gj_antes": m["delta_gj"],
                    "delta_gj_depois": d["observacao"]["variacao"],
                    "delta_pct": m["delta_pct"],
                    "valor_usd_antes": m["valor_referencia_usd"],
                    "valor_usd_depois": d["economia"]["desvio_estimado"],
                    "referencia": d["dimensoes"]["referencia"]["nivel"],
                    "robustez": d["dimensoes"]["robustez_estatistica"]["nivel"],
                    "conclusao": d["conclusao"],
                    "analise_id": d["analise_id"],
                }
            )
        saida[unidade] = ds
        (args.saida / f"EULER_diagnostico_{unidade}.md").write_text(
            relatorio_texto(r, unidade), encoding="utf-8"
        )
    artefato = {
        "fonte_sha256": r["fonte"]["recorte_sha256"],
        "diagnosticos": saida,
        "comparacoes_antes_depois": comparacoes,
    }
    (args.saida / "diagnosticos.json").write_text(
        json.dumps(artefato, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8"
    )
    (args.saida / "manifesto.json").write_text(
        json.dumps(
            {
                "conteudo_sha256": assinatura(artefato),
                "regra": "hash do JSON canônico UTF-8, não hash do arquivo com indentação",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    for c in comparacoes:
        print(
            f"{c['unidade']} {c['mes']}: {c['delta_pct']:.6f}% | referência {c['referencia']} | robustez {c['robustez']}"
        )


if __name__ == "__main__":
    main()
