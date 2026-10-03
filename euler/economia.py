"""Valorização de variações de consumo (E13), sem atribuir causa ou recuperação.

Comparação agregada: mesma produção e mesmo preço, sem completar uma série temporal.
O valor aritmético continua disponível sem incerteza; sua confirmação é separada.
"""

from dataclasses import asdict
from math import isfinite

from euler.deteccao import comparar
from euler.tipos import Grandeza


def _validar(valor: float | None, nome: str, positivo: bool = False) -> None:
    if valor is not None and (not isfinite(valor) or valor < 0 or (positivo and valor == 0)):
        raise ValueError(
            f"{nome}: informe um número finito {'positivo' if positivo else 'não negativo'}."
        )


def valorizar_diferenca(
    delta_t_t: float | None, vapor_t: float | None, preco_por_t: float | None
) -> float | None:
    """E13: (t combustível/t vapor) × t vapor × moeda/t combustível = moeda.

    Resultado com sinal; nenhum valor ausente vira zero. A função não decide
    detectabilidade e não interpreta a diferença como economia recuperável.
    """
    if delta_t_t is not None and not isfinite(delta_t_t):
        raise ValueError("A diferença precisa ser finita.")
    _validar(vapor_t, "Vapor")
    _validar(preco_por_t, "Preço")
    if delta_t_t is None or vapor_t is None or preco_por_t is None:
        return None
    return delta_t_t * vapor_t * preco_por_t


def comparar_consumos(
    referencia: Grandeza,
    comparacao: Grandeza,
    vapor_t: float,
    preco_por_t: float | None,
    moeda: str,
) -> dict:
    """Consumos em t/t; produção em t e preço na moeda declarada por t de combustível.

    Cada resultado monetário corresponde à quantidade de vapor informada. A base
    temporal (dia, período etc.) deve vir da fonte e ser exibida pelo chamador.
    Não se calculam entalpias, causas, incertezas ausentes ou câmbio nessa rota.
    """
    if referencia.unidade != "t/t" or comparacao.unidade != "t/t":
        raise ValueError("Converta explicitamente ambos os consumos para t/t.")
    if moeda not in ("BRL", "USD", "EUR"):
        raise ValueError("Declare a moeda como BRL, USD ou EUR, sem conversão implícita.")
    _validar(referencia.valor, "Consumo de referência", positivo=True)
    _validar(comparacao.valor, "Consumo de comparação", positivo=True)
    _validar(vapor_t, "Produção", positivo=True)
    c = comparar("Consumo específico agregado", "t/t", referencia, comparacao)
    valor = valorizar_diferenca(c.delta, vapor_t, preco_por_t)
    return {
        "comparacao": asdict(c),
        "vapor_t": vapor_t,
        "moeda": moeda,
        "preco_por_t": preco_por_t,
        "aumento_pct": 100 * c.delta / referencia.valor,
        "combustivel_referencia_t": referencia.valor * vapor_t,
        "combustivel_comparacao_t": comparacao.valor * vapor_t,
        "combustivel_adicional_t": c.delta * vapor_t,
        "custo_referencia": valorizar_diferenca(referencia.valor, vapor_t, preco_por_t),
        "custo_comparacao": valorizar_diferenca(comparacao.valor, vapor_t, preco_por_t),
        "diferenca_valorizada": valor,
        "valor_em_jogo_confirmado": valor if c.detectabilidade == "sim" and c.delta > 0 else None,
        "economia_comprovada": None,
        "causa_comprovada": False,
    }
