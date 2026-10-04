"""Adapter do diagnóstico físico existente; não recalcula perdas ou hipóteses."""

from copy import deepcopy
from dataclasses import asdict
from hashlib import sha256
from math import isfinite
from pathlib import Path

import pandas as pd

from euler.evidencias import assinatura, consolidar, dimensao
from euler.periodos import periodos_entre_estoques, vapor_e_combustivel
from euler.referencia import avaliar_referencia

ESTADOS = {
    "sustentada": "compatível",
    "oposta": "incompatível com o sentido do desvio",
    "possivel": "parcialmente compatível",
    "descartada": "enfraquecida",
    "nao_avaliavel": "não avaliável",
}


def fontes_pacote(pacote) -> dict:
    """Hash de representação CSV das tabelas originais preservadas, não do arquivo bruto."""
    return {
        "tabelas_originais": {
            nome: {
                "sha256": sha256(
                    imp.original.to_csv(index=False, lineterminator="\n").encode("utf-8")
                ).hexdigest(),
                "linhas": len(imp.original),
                "colunas": list(imp.original.columns),
            }
            for nome, imp in pacote.importacoes.items()
        },
        "formato_hash": "CSV UTF-8 LF da tabela original preservada pelo importador; não bytes do arquivo enviado",
        "p_atm_bar": pacote.p_atm_bar,
        "avisos": [asdict(a) for a in pacote.avisos],
        "metodo_sha256": {
            str(p.relative_to(Path(__file__).resolve().parent)): sha256(
                p.read_text(encoding="utf-8").encode("utf-8")
            ).hexdigest()
            for p in sorted(Path(__file__).resolve().parent.rglob("*.py"))
        },
    }


def diagnosticar_investigacao(j: dict, fontes: dict, referencia: dict | None = None) -> dict:
    """Avalia suficiência de uma comparação agregada sem inventar diagnósticos temporais.

    `referencia`: resultado de `avaliar_referencia_operacional` (D88). Sem ele, a
    dimensão da referência fica INSUFICIENTE, como antes.
    """
    c = deepcopy(j["o_que_mudou"]["consumo_especifico"])
    ref, comp = j["periodos"]["referencia"], j["periodos"]["comparacao"]
    hs = [
        {**deepcopy(h), "estado_interpretacao": ESTADOS[h["status"]], "causa_comprovada": False}
        for h in j["hipoteses"]
    ]
    sustentada = any(h["status"] == "sustentada" for h in hs)
    faltas = j["o_que_falta"]
    avisos = fontes.get("avisos", [])
    erros = [a for a in avisos if a.get("gravidade") == "erro"]
    dims = {
        "qualidade_dados": dimensao(
            "FRACA" if erros else "MODERADA",
            [
                "Importação preserva originais e avisos; qualidade depende de cobertura e metrologia.",
                f"{len(avisos)} avisos no pacote; {len(erros)} classificados como erro.",
            ],
            {
                "cobertura_referencia": ref["cobertura_diario"],
                "cobertura_comparacao": comp["cobertura_diario"],
            },
        ),
        "referencia": referencia
        if referencia is not None
        else dimensao(
            "INSUFICIENTE",
            [
                "Comparação agregada: estabilidade estatística da referência ainda não avaliada nesta rota."
            ],
        ),
        "robustez_estatistica": dimensao(
            "INSUFICIENTE",
            [
                "Incerteza física não substitui validação temporal, resíduos ou reamostragem de uma série."
            ],
        ),
        "consistencia_temporal": dimensao(
            "INSUFICIENTE", ["Dois agregados não demonstram persistência temporal."]
        ),
        "evidencia_fisica": dimensao(
            "MODERADA" if sustentada else "INSUFICIENTE",
            [
                "Há explicação compatível segundo o modelo físico e suas hipóteses; não é causa confirmada."
                if sustentada
                else "A comparação não sustenta atribuição física específica."
            ],
        ),
        "cobertura_variaveis": dimensao(
            "FRACA" if faltas else "MODERADA",
            [
                "Pré-requisitos físicos avaliados pelo motor; variáveis ausentes não foram completadas."
            ],
            {"pendencias": faltas},
        ),
        "incerteza": dimensao(
            "INSUFICIENTE"
            if c["detectabilidade"] is None
            else "FRACA"
            if c["faltam_na_incerteza"]
            else "MODERADA",
            [
                "Orçamento determinístico e hipóteses de correlação preservados; completude deve ser revisada."
            ],
            {"detectabilidade": c["detectabilidade"], "faltam": c["faltam_na_incerteza"]},
        ),
    }
    prox = j["proxima_verificacao"]
    acoes = [
        {
            "ordem": 1,
            "acao": prox["acao"],
            "porque": prox["porque"],
            "separa": prox["separa"],
            "origem": "Regra de investigação física existente",
        }
    ]
    # Mesma regra do "valor em jogo" da investigação (D87): só um aumento confirmado pelas
    # incertezas é valorizado; senão o valor fica ausente, com o motivo do motor. Antes a
    # diferença era valorizada sempre, e o Diagnóstico mostrava R$ para uma alta não
    # confirmada (ou para uma queda) enquanto a Investigação dizia "não estimado".
    valor_jogo = j.get("valor_em_jogo")
    valor = valor_jogo["valor_brl"] if valor_jogo else None
    motivo_sem_valor = None if valor_jogo else (j.get("valor_em_jogo_motivo") or None)
    return consolidar(
        {
            "equipamento": j["caldeira_id"],
            "periodo": comp["rotulo"],
            "observacao": c,
            "origem_dados": j["origem_dados"],
            "dimensoes": dims,
            "conclusao": j["conclusao"]["texto"] + " Causa física não confirmada.",
            "hipoteses": hs,
            "dados_faltantes": faltas,
            "proximas_medicoes": acoes,
            "economia": {
                "desvio_estimado": valor,
                "motivo_sem_valor": motivo_sem_valor,
                "moeda": "BRL",
                "preco": comp["preco_brl_t"],
                "unidade_preco": "BRL/t de combustível",
                "periodo": comp["rotulo"],
                "origem_preco": "Preço por tonelada recebido pelo motor, derivado dos registros de combustível.",
                "premissas": [
                    "Mesmo preço e mesma produção de vapor na comparação.",
                    "Valorização aritmética do desvio, sem confirmação de prejuízo ou recuperação.",
                    (
                        "Só é calculada quando o aumento de consumo está confirmado pelas "
                        "incertezas (mesma regra do valor em jogo da investigação)."
                    ),
                ],
                "oportunidade_potencial": None,
                "economia_verificada": None,
            },
            "limitacoes": [
                "Classificação não substitui revisão física nem validação de campo.",
                (
                    "Referência avaliada período a período (entre medições de estoque) com a "
                    "rubrica de triagem; não substitui validação de campo."
                    if referencia is not None
                    else "A análise estatística temporal da referência agregada ainda não está "
                    "disponível."
                ),
                "Não há balanço completo de todas as perdas: radiação, CO/incombustos e outras parcelas podem faltar.",
                "Registro formal de intervenção e verificação de economia ainda não implementados.",
            ],
            "metodos": {
                "criterios": j["criterios"],
                "periodos": j["periodos"],
                "baseline": "Comparação física agregada existente, não modelo temporal multivariável",
                "referencia": (referencia or {}).get("modelo"),
                "hipoteses": "Regras existentes euler/investigacao.py; estados legados preservados",
                "economia": "E13: diferença t/t × vapor t × preço BRL/t",
            },
            "fontes": {**fontes, "resultado_fisico_sha256": assinatura(j)},
        }
    )


def _f(x) -> float | None:
    """Número finito como float; ausente, NaN ou infinito vira None (nunca zero)."""
    return float(x) if x is not None and isfinite(x) else None


def _regime(regimes_presentes: tuple[str, ...]) -> str | None:
    """Regime do período pelo diário: 'estavel', 'transitorio' (partida, parada ou
    transitório) ou None (sem leitura, ou alguma leitura sem regime informado)."""
    if not regimes_presentes or "nao_informado" in regimes_presentes:
        return None
    return "estavel" if set(regimes_presentes) == {"estavel"} else "transitorio"


def _serie(pacote, periodos) -> list[dict]:
    linhas = []
    for a, b in periodos:
        r = vapor_e_combustivel(pacote, a, b)
        horas = (b - a).total_seconds() / 3600
        vapor = _f(r.vapor_t.valor) if r.vapor_t else None
        comb = _f(r.combustivel_kg.valor / 1000) if r.combustivel_kg else None
        linhas.append(
            {
                "periodo": f"{a:%d/%m} a {b:%d/%m}",
                "inicio": a.isoformat(),
                "fim": b.isoformat(),
                "horas": horas,
                "combustivel_t": comb,
                "vapor_t": vapor,
                "consumo_t_t": comb / vapor if comb is not None and vapor else None,
                "carga_t_h": vapor / horas if vapor is not None and horas > 0 else None,
                "regime": _regime(r.regimes_presentes),
                "motivo_ausente": " ".join(x.motivo for x in r.bloqueios.values()) or None,
            }
        )
    return linhas


def avaliar_referencia_operacional(
    pacote,
    referencia: tuple[pd.Timestamp, pd.Timestamp],
    comparacao: tuple[pd.Timestamp, pd.Timestamp],
    consumo_referencia: float | None = None,
) -> dict:
    """Avalia a referência da investigação com a série que a fábrica enviou (D88).

    Série: um ponto por período entre medições de estoque dentro da referência — a menor
    resolução em que o combustível queimado é conhecido (E9). Observado: combustível
    queimado no período (t). Previsto: o mesmo modelo da comparação agregada, consumo
    específico da referência do motor (t/t) × vapor do período (t); nenhum modelo novo é
    ajustado. Resíduo = observado − previsto. Período sem vapor ou sem combustível fica
    inválido (contado, nunca preenchido).

    Validação cronológica: o último período válido da referência é previsto pela razão
    combustível/vapor dos períodos válidos anteriores (fora do modelo). Carga: vazão média
    de vapor do período (t/h), na referência e nos períodos da comparação. Regime: pelo
    diário; se algum período não tem regime informado, o regime não é avaliado.

    Os limiares são os da rubrica de triagem (`euler.referencia.PARAMETROS`), pensados para
    registros horários: com poucos períodos a referência fica no máximo FRACA. Só o mínimo
    de comparações no suporte de carga é 1, porque a comparação também é medida em períodos.
    """
    todos = periodos_entre_estoques(pacote)
    dentro = [p for p in todos if referencia[0] <= p[0] and p[1] <= referencia[1]]
    comp = [p for p in todos if comparacao[0] <= p[0] and p[1] <= comparacao[1]]
    if not dentro:
        return {
            **dimensao(
                "INSUFICIENTE",
                [
                    (
                        "Nenhum período entre medições de estoque dentro da referência; "
                        "a série não pode ser montada."
                    )
                ],
            ),
            "serie": [],
            "modelo": None,
        }
    serie, serie_comp = _serie(pacote, dentro), _serie(pacote, comp)
    validos = [x for x in serie if x["combustivel_t"] is not None and x["vapor_t"]]
    k, origem_k = _f(consumo_referencia), "consumo específico da referência calculado pelo motor"
    if k is None and validos:
        k = sum(x["combustivel_t"] for x in validos) / sum(x["vapor_t"] for x in validos)
        origem_k = "soma do combustível ÷ soma do vapor dos períodos válidos"
    for x in serie:
        x["previsto_t"] = k * x["vapor_t"] if k is not None and x["vapor_t"] is not None else None
        x["residuo_t"] = (
            x["combustivel_t"] - x["previsto_t"]
            if x["previsto_t"] is not None and x["combustivel_t"] is not None
            else None
        )
    validacao = None
    if len(validos) >= 3:
        antes, ultimo = validos[:-1], validos[-1]
        k0 = sum(x["combustivel_t"] for x in antes) / sum(x["vapor_t"] for x in antes)
        previsto = k0 * ultimo["vapor_t"]
        validacao = [
            {
                "periodo": ultimo["periodo"],
                "vies_pct": 100 * (ultimo["combustivel_t"] - previsto) / previsto,
                "horas_comparaveis": ultimo["horas"],
                "metodo": "último período previsto pela razão combustível/vapor dos anteriores",
            }
        ]
    duracoes = {round(x["horas"], 2) for x in serie}
    regimes = [x["regime"] for x in serie]
    nan = float("nan")
    resultado = avaliar_referencia(
        observado=[nan if x["combustivel_t"] is None else x["combustivel_t"] for x in serie],
        previsto=[nan if x["previsto_t"] is None else x["previsto_t"] for x in serie],
        unidade="t de combustível por período",
        instantes=[x["fim"] for x in serie],
        carga=[nan if x["carga_t_h"] is None else x["carga_t_h"] for x in serie],
        carga_comparacao=[nan if x["carga_t_h"] is None else x["carga_t_h"] for x in serie_comp],
        unidade_carga="t/h (vazão média de vapor do período)",
        intervalo_horas=duracoes.pop() if len(duracoes) == 1 else None,
        validacao_temporal=validacao,
        regimes=None if None in regimes else regimes,
        minimo_comparacao=1,
    )
    resultado["limitacoes"] = resultado["limitacoes"] + [
        (
            f"Um ponto por período entre medições de estoque ({len(serie)} na referência): "
            "medir o estoque com mais frequência aumenta a série e a capacidade de avaliar "
            "a referência."
        ),
        "Limiares da rubrica pensados para registros horários; aplicados sem adaptação aos períodos.",
    ]
    resultado["serie"] = serie
    resultado["serie_comparacao"] = serie_comp
    resultado["modelo"] = {
        "descricao": "previsto = consumo específico da referência × vapor do período",
        "consumo_especifico_t_t": k,
        "origem_consumo_especifico": origem_k if k is not None else None,
        "resolucao": "um ponto por período entre medições de estoque",
    }
    return resultado
