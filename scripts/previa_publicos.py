"""Dados das telas "Dados reais testados" para a prévia interativa (scripts/gerar_previa.py).

Executa os mesmos casos públicos da tela do app (EPA/PUDL horário, UTFPR, Unisanta, caldeira
a carvão em três cargas e Zhejiang) e guarda o que as telas mostram, já em texto. A página
não recalcula nada.
"""

from __future__ import annotations

import pandas as pd
from diagnostico_publico import diagnosticos
from ensaio_horario import executar as executar_horario
from ensaio_publico import executar
from parecer_ensaio import INVESTIGACOES, parecer
from resumo_publico import AVISO, linhas_resumo

from euler.economia import comparar_consumos
from euler.evidencias import ROTULOS
from euler.formato import num
from euler.relatorio_evidencias import casas
from euler.tipos import Grandeza

UNIDADES = ("B10", "B08", "B07", "B06")
MESES = {"2023-02": "Fevereiro", "2023-03": "Março"}


def _diagnostico(d: dict) -> dict:
    """O que a tela Diagnóstico de evidências mostra de um diagnóstico (blocos/diagnostico.py)."""
    o = d["observacao"]
    e = d["economia"]
    valor = e.get("desvio_estimado")
    return {
        "periodo": d["periodo"],
        "conclusao": d["conclusao"],
        "metricas": [
            [ROTULOS[k], d["dimensoes"][k]["nivel"].capitalize()]
            for k in ("robustez_estatistica", "referencia", "evidencia_fisica")
        ],
        "dimensoes": [
            [ROTULOS[k], v["nivel"].capitalize(), list(v["motivos"])]
            for k, v in d["dimensoes"].items()
        ],
        "escopo": d["escopo_classificacao"],
        "proximas": [[v["acao"], v["porque"]] for v in d.get("proximas_medicoes", [])],
        "observacao": [
            [rot, f"{num(o.get(ch), casas(o.get(ch)))} {o['unidade']}"]
            for rot, ch in (
                ("Referência calculada", "referencia"),
                ("Observado", "comparacao"),
                ("Diferença observada", "variacao"),
            )
        ],
        "hipoteses": [
            [
                h.get("titulo", h["id"]),
                h.get("estado_interpretacao", h.get("status")) or "—",
                list(h.get("evidencias", [])),
            ]
            for h in d.get("hipoteses", [])
        ],
        "valor": f"{e.get('moeda', '')} {num(valor)}" if valor is not None else "não estimado",
        "premissas": list(e.get("premissas", [])),
        "limitacoes": list(d.get("limitacoes", [])),
        "analise": f"Análise {d['analise_id']} · {d['versao_rubrica']}",
    }


def _unidade(h: dict, un: str) -> dict:
    u = h["unidades"][un]
    ds = diagnosticos(h, un)
    p = parecer(u, ds)
    meses = u["comparacoes"]
    diario = pd.DataFrame([x for m in meses for x in m["diario"]])
    diario["pct"] = 100 * (diario.energia_gj / diario.previsto_gj - 1)
    return {
        "titulo": p["titulo"],
        "conclusao": p["conclusao"],
        "investigar": p["status"] == "investigar",
        "valor": f"US$ {num(p['valor_usd'])}",
        "meses": [[MESES.get(m["mes"], m["mes"]), f"{num(m['delta_pct'])}%"] for m in meses],
        "energia": f"{num(p['energia_gj'])} GJ",
        "horas": num(p["horas"], 0),
        "fora_faixa": p["fora_faixa"],
        "cobertura": [
            [MESES.get(m["mes"], m["mes"]), m["horas_comparaveis"], m["horas_validas"]]
            for m in meses
        ],
        "diario": [
            [f"{pd.Timestamp(d):%d/%m}", round(float(v), 3)]
            for d, v in zip(diario["Date"], diario["pct"], strict=True)
        ],
        "verificacoes": [[v["onde"], v["conferir"], v["para_que"]] for v in p["verificacoes"]],
        "sensibilidade": p["sensibilidade_consistente"],
        "tabela": [
            [
                m["mes"],
                num(m["delta_gj"]),
                num(m["preco_usd_gj"], 4),
                num(m["valor_referencia_usd"]),
            ]
            for m in meses
        ],
        "referencia": (
            f"Referência: {u['horas_referencia']} horas; {num(u['carga_min_t_h'])} a "
            f"{num(u['carga_max_t_h'])} t/h. Energia em PCS."
        ),
        "diagnosticos": [_diagnostico(d) for d in ds],
    }


def dados_publicos() -> dict:
    r = executar()
    h = executar_horario()
    aumento = comparar_consumos(
        Grandeza(0.30, "t/t", "estimado"), Grandeza(0.35, "t/t", "estimado"), 1200.0, 26.53, "USD"
    )
    f = r["caso_financeiro"]
    z = r["zhejiang"]
    print("  dados públicos: 5 casos, 4 caldeiras EPA", flush=True)
    return {
        "resumo": linhas_resumo(r, h),
        "aviso": AVISO,
        "epa": {un: _unidade(h, un) for un in UNIDADES},
        "epa_fonte": {k: h["fonte"][k] for k in ("url", "preco_fonte", "calor_fonte")},
        "investigacoes": [[v["onde"], v["dados"], v["resposta"]] for v in INVESTIGACOES],
        "utfpr": {
            "metricas": [
                ["Variação de consumo", f"{num(aumento['aumento_pct'])}%"],
                ["Diferença de biomassa", f"{num(aumento['combustivel_adicional_t'])} t/dia"],
                ["Diferença valorizada", f"US$ {num(aumento['diferenca_valorizada'])}/dia"],
            ],
            "conta": (
                f"Combustível para a mesma produção: {num(aumento['combustivel_referencia_t'])} → "
                f"{num(aumento['combustivel_comparacao_t'])} t/dia. Custo calculado: "
                f"US$ {num(aumento['custo_referencia'])} → US$ {num(aumento['custo_comparacao'])}/dia."
            ),
            "url": r["caso_aumento"]["fonte"]["pdf_url"],
        },
        "unisanta": {
            "metricas": [
                ["Antes · combustível por t de vapor", f"R$ {num(f['antes_brl_t'])}"],
                ["Depois · combustível por t de vapor", f"R$ {num(f['depois_brl_t'])}"],
                ["Redução calculada por t de vapor", f"{num(f['reducao_pct'])}%"],
            ],
            "diferenca": f"R$ {num(f['diferenca_brl_t'])}",
            "tabela": [
                ["2010", "7.562", "119,39", num(f["antes_kg_t"]), num(f["antes_brl_h"])],
                ["2011", "7.458", "123,85", num(f["depois_kg_t"]), num(f["depois_brl_h"])],
            ],
            "bruta": num(f["reducao_bruta_brl_h"]),
            "normalizada": num(f["diferenca_normalizada_brl_h"]),
            "url": f["fonte"]["url"],
        },
        "cargas": {
            "maior": f"{num(max(abs(e['delta_heos_pct']) for e in r['estados']), 3)}%",
            "tabela": [
                [
                    f"{num(c['carga_pct'])}%",
                    num(c["vapor_t_h"], 2),
                    num(c["consumo_kg_t"], 2),
                    num(c["potencia_vapor_mw"], 2),
                ]
                for c in r["cargas"]
            ],
            "estados": [
                [
                    str(e["carga_pct"]),
                    e["ponto"],
                    num(e["h_euler_kj_kg"], 2),
                    num(e["h_fonte_kj_kg"], 2),
                    num(e["h_heos_kj_kg"], 2),
                    num(e["delta_fonte_pct"], 3),
                ]
                for e in r["estados"]
            ],
            "url": r["fonte_subcritica"]["url"],
        },
        "zhejiang": {
            "linhas": num(z["linhas"], 0),
            "tmin": f"{num(z['temperatura_min_c'])} °C",
            "tmax": f"{num(z['temperatura_max_c'])} °C",
            "importados": num(r["importacao"]["linhas"], 0),
            "url": z["url"],
        },
    }
