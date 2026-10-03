"""Apresentação financeira do resultado existente, sem novas hipóteses físicas."""

from math import isfinite


def nao_negativo(valor):
    """Número finito >= 0; ausente/inválido permanece None."""
    if valor is None:
        return None
    valor = float(valor)
    return valor if isfinite(valor) and valor >= 0 else None


def resumo_financeiro(j: dict) -> dict:
    """BRL no período comparado, à mesma base de preço do valor em jogo do motor.

    Consumo valorizado = kg consumidos / 1000 × BRL/t dos recebimentos.
    Não equivale a pagamento, custo contábil de estoque ou economia realizada.
    Referência só aparece quando o motor liberou o valor em jogo (E13).
    """
    comp = j["periodos"]["comparacao"]
    massa = nao_negativo((comp.get("combustivel_kg") or {}).get("valor"))
    preco = nao_negativo(comp.get("preco_brl_t"))
    total = nao_negativo(massa / 1000 * preco) if massa is not None and preco is not None else None
    diferenca = nao_negativo((j.get("valor_em_jogo") or {}).get("valor_brl"))
    referencia = None
    if total is not None and diferenca is not None and diferenca <= total:
        referencia = total - diferenca
    return {"consumido_brl": total, "referencia_brl": referencia, "diferenca_brl": diferenca}


def simular_recuperacao(diferenca_brl: float | None, percentual: float) -> float | None:
    """Cenário escolhido pelo usuário: BRL × percentual / 100, no mesmo período.

    Não define fração recuperável nem registra economia comprovada.
    """
    if not isfinite(percentual) or not 0 <= percentual <= 100:
        raise ValueError("Escolha um percentual entre 0 e 100.")
    valor = nao_negativo(diferenca_brl)
    return valor * percentual / 100 if valor is not None else None
