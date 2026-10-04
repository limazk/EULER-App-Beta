"""Contrato central da evidência: rubrica ordinal, abstenção e integridade.

Não calcula termodinâmica nem probabilidades. As dimensões não são somadas.
FORTE qualifica somente o escopo explicitado nos motivos, nunca causalidade.
"""

import json
from copy import deepcopy
from hashlib import sha256
from math import isfinite

VERSAO = "evidencias/1.0"
NIVEIS = ("INSUFICIENTE", "FRACA", "MODERADA", "FORTE")
ROTULOS = {
    "qualidade_dados": "Qualidade dos dados",
    "referencia": "Qualidade da referência",
    "robustez_estatistica": "Robustez estatística",
    "consistencia_temporal": "Consistência temporal",
    "evidencia_fisica": "Evidência física",
    "cobertura_variaveis": "Cobertura das variáveis",
    "incerteza": "Conhecimento da incerteza",
}


def assinatura(obj: dict) -> str:
    """SHA-256 do JSON canônico UTF-8; rejeita NaN/inf, sem depender de timestamps."""
    texto = json.dumps(
        obj, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":")
    )
    return sha256(texto.encode("utf-8")).hexdigest()


def dimensao(nivel: str, motivos: list[str], metricas: dict | None = None) -> dict:
    """Classificação ordinal acompanhada de justificativa verificável."""
    if nivel not in NIVEIS or not motivos or any(not isinstance(m, str) for m in motivos):
        raise ValueError("A dimensão exige nível válido e motivos explícitos.")
    return {"nivel": nivel, "motivos": motivos, "metricas": metricas or {}}


def consolidar(diagnostico: dict) -> dict:
    """Consolida adapters existentes; bloqueia promoção automática a causa/economia.

    P2 ainda não implementado: oportunidade e economia verificadas ficam ausentes.
    Este hash detecta alterações; não é assinatura digital ou certificação da fonte.
    """
    d = deepcopy(diagnostico)
    if d.get("causa_confirmada") or any(h.get("causa_comprovada") for h in d.get("hipoteses", [])):
        raise ValueError("Esta versão não confirma causas.")
    if not d.get("observacao", {}).get("unidade"):
        raise ValueError("A observação exige unidade explícita.")
    for k, v in d["dimensoes"].items():
        if k not in ROTULOS:
            raise ValueError(f"Dimensão desconhecida: {k}")
        dimensao(v["nivel"], v["motivos"], v.get("metricas"))
    for k in ROTULOS:
        d["dimensoes"].setdefault(
            k, dimensao("INSUFICIENTE", ["Avaliação não disponível nesta rota."])
        )
    economia = d.setdefault("economia", {})
    for k in ("oportunidade_potencial", "economia_verificada"):
        if economia.get(k) is not None:
            raise ValueError(
                "Oportunidade recuperável e economia exigem verificação ainda não implementada."
            )
        economia[k] = None
    for k in ("analise_id", "resultado_sha256"):
        d.pop(k, None)
    d["versao_rubrica"] = VERSAO
    d["causa_confirmada"] = False
    d["escopo_classificacao"] = (
        "Rubrica qualitativa revisável; não é probabilidade, nota global ou certificação."
    )
    digest = assinatura(d)
    d["analise_id"] = "EULER-" + digest[:16]
    d["resultado_sha256"] = digest
    return d


def verificar_integridade(diagnostico: dict) -> bool:
    d = deepcopy(diagnostico)
    esperado = d.pop("resultado_sha256", None)
    identificador = d.pop("analise_id", None)
    try:
        calculado = assinatura(d)
    except (ValueError, TypeError):
        return False
    return esperado == calculado and identificador == "EULER-" + calculado[:16]


def _finito(x) -> bool:
    return isinstance(x, (int, float)) and isfinite(x)


def robustez_publica(auditoria_mes: dict | None, repeticoes: int | None) -> dict:
    """Interpreta D85 sem mudar ajuste, amostra ou selecionar teste favorável.

    FORTE: sinal igual nos três blocos completos, quatro modelos, três referências
    e retirada de um dia. FRACA: reversão/zero. MODERADA: verificações incompletas.
    Ausência da auditoria -> INSUFICIENTE. Faixas são sensibilidades retrospectivas.
    """
    a = auditoria_mes or {}
    blocos = a.get("reamostragem", [])
    if not blocos or not repeticoes:
        return {
            **dimensao(
                "INSUFICIENTE", ["Auditoria de robustez ausente ou incompatível com esta execução."]
            ),
            "sinal": "nao_avaliavel",
            "conclusao": "Robustez não avaliável.",
        }
    intervalos = [(b.get("quantil_025_pct"), b.get("quantil_975_pct")) for b in blocos]
    completas = (
        len(blocos) == 3
        and {b.get("bloco_dias") for b in blocos} == {1, 3, 7}
        and all(b.get("validas") == repeticoes and b.get("invalidas") == 0 for b in blocos)
        and all(_finito(lo) and _finito(hi) and lo <= hi for lo, hi in intervalos)
    )
    if not completas:
        return {
            **dimensao(
                "MODERADA",
                [
                    "Reamostragem incompleta; não tratar os resultados disponíveis como confirmação do sinal."
                ],
            ),
            "sinal": "inconclusivo",
            "conclusao": "Sinal menos conclusivo: verificações incompletas.",
        }
    modelos = a.get("modelos", {}).get("metodos", [])
    refs = a.get("referencias", {}).get("metodos", [])
    retirada = a.get("retirada_de_um_dia_pct", {})
    valores = [m.get("delta_pct") for m in modelos + refs] + [
        retirada.get("min"),
        retirada.get("max"),
    ]
    extras = len(modelos) == 4 and len(refs) == 3 and all(_finito(v) for v in valores)
    todos = [x for par in intervalos for x in par] + [v for v in valores if _finito(v)]
    positivo, negativo = all(x > 0 for x in todos), all(x < 0 for x in todos)
    if not (positivo or negativo):
        return {
            **dimensao(
                "FRACA",
                [
                    "Há faixa incluindo zero ou mudança de sinal entre verificações; preservar o resultado inconclusivo."
                ],
            ),
            "sinal": "inconclusivo",
            "conclusao": "Sinal menos conclusivo nas verificações realizadas.",
        }
    if not extras:
        return {
            **dimensao(
                "MODERADA",
                [
                    "Sinal consistente nas verificações disponíveis, mas faltam comparações de modelos/referências."
                ],
            ),
            "sinal": "inconclusivo",
            "conclusao": "Sinal menos conclusivo: comparações incompletas.",
        }
    return {
        **dimensao(
            "FORTE",
            [
                "Sinal preservado nos blocos de 1/3/7 dias, modelos, referências e retirada de um dia.",
                "Força descritiva dentro do protocolo; não confirma causa nem detectabilidade metrológica.",
            ],
        ),
        "sinal": "aumento" if positivo else "reducao",
        "conclusao": "Aumento persiste nas verificações realizadas."
        if positivo
        else "Redução persiste nas verificações realizadas.",
    }
