"""Dados das telas "Dados reais testados" para a prévia interativa (scripts/gerar_previa.py).

Executa os mesmos casos públicos da tela do app (EPA/PUDL horário, UTFPR, Unisanta, caldeira
a carvão em três cargas e Zhejiang) e guarda o que as telas mostram, já em texto. A página
não recalcula nada.
"""

from __future__ import annotations

from itertools import pairwise

import pandas as pd
from diagnostico_publico import diagnosticos
from ensaio_cervejaria import executar as executar_cervejaria
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


def _sinal(x: float, casas: int = 1) -> str:
    return f"{'+' if x >= 0 else '−'}{num(abs(x), casas)}"


def _cervejaria(c: dict) -> dict:
    """O que a aba "Planta brasileira · RS" mostra (blocos/ensaio_cervejaria.py), em texto."""
    k, e, cmp = c["conferencia"], c["entalpia"], c["comparacao"]
    a, b = cmp["periodos"]
    m = cmp["comparacao"]
    j = k["razao_vapor_biomassa"]
    cortes = []
    for grupo, nome in (
        ("metades", "Metades do registro"),
        ("epocas_balanca", "Entre calibrações da balança"),
        ("epocas_medidor_vapor", "Entre calibrações dos medidores de vapor"),
    ):
        for x in c["sensibilidade"][grupo]:
            cortes.append([nome, x["rotulo"], str(x["dias"]), num(x["consumo_t_t"], 4)])
    cai = all(
        y["consumo_t_t"] < x["consumo_t_t"]
        for g in c["sensibilidade"].values()
        for x, y in pairwise(g)
    )
    f = c["fonte"]
    return {
        "conclusao": c["conclusao"],
        "metricas": [
            ["1º período", f"{num(a['consumo_t_t'], 4)} t/t"],
            ["2º período", f"{num(b['consumo_t_t'], 4)} t/t"],
            ["Diferença", f"{_sinal(cmp['variacao_pct'])}%"],
            ["Incerteza conhecida", f"±{num(m.incerteza_delta_correlacionada, 4)} t/t"],
        ],
        "periodos": [
            [
                f"{nome} · {pd.Timestamp(p['inicio']):%d/%m/%Y} a {pd.Timestamp(p['fim']):%d/%m/%Y}",
                str(p["dias"]),
                num(p["vapor_t"], 0),
                num(p["biomassa_t"], 0),
                num(p["consumo_t_t"], 4),
                num(p["carga_t_dia"], 0),
                str(p["dias_sem_vapor"]),
            ]
            for nome, p in zip(cmp["nomes"], cmp["periodos"], strict=True)
        ],
        "mensal": [
            [x["mes"], round(x["consumo_t_t"], 4), round(x["carga_t_dia"], 1)]
            for x in c["mensal"]["meses"]
        ],
        "cortes": cortes,
        "cortes_frase": (
            "Em todos os cortes, cada trecho tem menos casca por tonelada de vapor que o anterior. "
            "A diferença não depende da escolha dos períodos; isso não mostra a causa."
            if cai
            else "Os cortes não seguem o mesmo sentido: a diferença depende do período escolhido."
        ),
        "bloqueado": c["bloqueado"],
        "totais": [
            [nome, num(k["totais"][ch], 3), num(k["totais_verificados"][ch], 0)]
            for nome, ch in (
                ("Vapor das caldeiras a biomassa", "vapor_t"),
                ("Casca de arroz e de carvalho", "biomassa_t"),
                ("Óleo equivalente da caldeira reserva", "oleo_equivalente_t"),
            )
        ],
        "totais_conferem": all(k["confere_com_verificacao"].values()),
        "calendario": (
            f"**Calendário:** {k['dias']} dias seguidos, de {k['inicio']} a {k['fim']}; "
            f"{k['dias_fora_do_calendario']} dias faltando e {k['datas_repetidas']} datas repetidas."
        ),
        "lacunas": (
            f"**Lacunas preservadas:** {k['dias_sem_vapor_registrado']} dias sem vapor registrado "
            f"nas duas caldeiras ({k['dias_sem_vapor_fim_de_semana']} em sábados ou domingos); "
            f"neles a casca registrada soma {num(k['casca_nos_dias_sem_vapor_t'], 0)} t. O padrão "
            "é de fábrica parada, mas a planilha não diz: os dias ficam sem vapor, não com zero."
        ),
        "achados": [
            (
                f"**Total diário em branco** em {', '.join(k['total_diario_em_branco'])}, embora "
                "as duas caldeiras tenham registro. Somar só a coluna de total perde "
                f"{num(k['vapor_dos_totais_em_branco_t'], 2)} t; o total oficial só fecha somando "
                "as caldeiras."
            ),
            *(
                f"**Energia em branco** na caldeira {n} em {d}, com vapor e entalpia registrados."
                for n, d in k["energia_em_branco"]
            ),
            (
                f"**{len(k['acima_da_capacidade'])} registros acima da capacidade nominal** "
                f"({num(k['capacidade_t_h'], 0)} t/h por caldeira × horas de operação):"
            ),
        ],
        "acima": [
            [
                x["data"],
                str(x["caldeira"]),
                num(x["horas"], 1),
                num(x["vapor_t"], 2),
                num(x["media_t_h"], 1),
                num(x["pct_capacidade"], 0),
            ]
            for x in k["acima_da_capacidade"]
        ],
        "janelas": [
            [f"{d} {'dia' if d == 1 else 'dias'}", *(num(v, 2) for v in j[d])] for d in (1, 7, 30)
        ],
        "janelas_frase": (
            f"Em 90% dos dias, a razão fica entre {num(j[1][0], 1)} e {num(j[1][2], 1)} t de vapor "
            "por t de casca: uma dispersão dessas vem de entrega ou estoque, não da queima. "
            f"Somando 30 dias, ela cai para {num(j[30][0], 1)} a {num(j[30][2], 1)}. Os documentos "
            "divergem sobre a origem da coluna (volume no galpão × densidade, no PDD; notas fiscais "
            "e balança, na verificação). Por isso a EULER usa só somas longas e chama a razão de "
            "consumo aparente."
        ),
        "entalpia": (
            "A planilha usa a entalpia do vapor saturado de uma tabela própria. Em "
            f"{num(e['dias_caldeira'], 0)} dias-caldeira, ela difere da IF97 da EULER entre "
            f"{num(e['tabela']['min_pct'], 3)}% e {num(e['tabela']['max_pct'], 3)}%, com a pressão "
            "referida a 1 kgf/cm² absoluto, como na tabela da planilha."
        ),
        "entalpia_legenda": (
            "A planilha conta a energia do vapor desde 0 °C. A energia útil desconta a água de "
            "alimentação, cuja temperatura não foi publicada: a cada 10 °C de água, a energia útil "
            f"fica cerca de {num(e['pct_por_10c_de_agua'], 1)}% abaixo da energia da planilha. Por "
            "isso a eficiência fica bloqueada."
        ),
        "hipoteses": [
            [h["titulo"], h["o_que_os_registros_mostram"], h["verificacao"]] for h in c["hipoteses"]
        ],
        "projeto": (
            "Para comparação, o exemplo de projeto do fabricante no PDD indica "
            f"{num(cmp['projeto_vapor_por_biomassa'], 2)} t de vapor por t de casca, com casca a "
            f"12% de umidade. Os registros dão {num(a['vapor_por_biomassa'], 2)} no 1º período e "
            f"{num(b['vapor_por_biomassa'], 2)} no 2º. É contexto, não referência: o exemplo não é "
            "ensaio destas caldeiras."
        ),
        "termos": f["termos_de_uso"]["trecho"],
        "aviso": f["aviso"],
        "links": [
            ["Página do projeto 1202 · UNFCCC", f["projeto_mdl"]["pagina"]],
            ["Pedido de emissão (planilha e verificação)", f["projeto_mdl"]["pedido_de_emissao"]],
            ["Planilha diária original", f["arquivos"]["1202_CER_Calc_Sheet_Rev1.xls"]["url"]],
            [
                "Relatório de verificação · DNV",
                f["documentos_consultados"]["relatorio_de_verificacao"]["url"],
            ],
            ["Termos de uso da UNFCCC", f["termos_de_uso"]["url"]],
        ],
        "sha256": [[nome, info["sha256"]] for nome, info in f["arquivos"].items()],
    }


def dados_publicos() -> dict:
    r = executar()
    h = executar_horario()
    c = executar_cervejaria()
    aumento = comparar_consumos(
        Grandeza(0.30, "t/t", "estimado"), Grandeza(0.35, "t/t", "estimado"), 1200.0, 26.53, "USD"
    )
    f = r["caso_financeiro"]
    z = r["zhejiang"]
    print("  dados públicos: 6 casos (planta brasileira e 4 caldeiras EPA)", flush=True)
    return {
        "resumo": linhas_resumo(r, h, c),
        "aviso": AVISO,
        "cervejaria": _cervejaria(c),
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
