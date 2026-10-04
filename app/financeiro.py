"""Apresentação financeira do resultado existente, sem novas hipóteses físicas.

A explicação da conta (custo consumido, esperado, desvio) vem do motor (`euler.conta`,
D89). Não há simulador de percentual de recuperação: a parcela evitável depende de
verificar um mecanismo específico.
"""

from math import isfinite


def nao_negativo(valor):
    """Número finito >= 0; ausente/inválido permanece None."""
    if valor is None:
        return None
    valor = float(valor)
    return valor if isfinite(valor) and valor >= 0 else None
