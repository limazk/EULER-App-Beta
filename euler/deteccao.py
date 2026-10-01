"""Linha de base e comparação entre períodos (E15) e detecção de degrau (T12).

Uma mudança só é chamada de **detectável** quando é maior que a incerteza da
diferença (k = 2, ~95%). Para leituras do diário, a incerteza da média de um período
vem da variação entre **médias diárias** (leituras de 2 em 2 h são correlacionadas
entre si; dias são mais próximos de independentes) — proposta D25.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

import pandas as pd

from euler.tipos import Grandeza


@dataclass(frozen=True)
class Estatistica:
    """Média de uma leitura no período, com erro-padrão das médias diárias."""

    media: float
    unidade: str
    n_leituras: int
    n_dias: int
    erro_padrao: float | None

    @property
    def incerteza(self) -> float | None:
        """Incerteza expandida da média (k = 2)."""
        return None if self.erro_padrao is None else 2 * self.erro_padrao


def estatistica_diaria(
    valores: pd.Series, instantes: pd.Series, unidade: str
) -> Estatistica | None:
    """Média e erro-padrão (pelas médias diárias) de uma leitura; None sem leituras."""
    df = pd.DataFrame(
        {"v": pd.to_numeric(valores, errors="coerce").astype(float).values, "t": instantes.values}
    ).dropna()
    if df.empty:
        return None
    diarias = df.groupby(pd.to_datetime(df["t"]).dt.date)["v"].mean()
    erro = float(diarias.std(ddof=1) / sqrt(len(diarias))) if len(diarias) >= 2 else None
    return Estatistica(float(df["v"].mean()), unidade, len(df), len(diarias), erro)


@dataclass(frozen=True)
class Comparacao:
    """Diferença entre o período de comparação e o de referência."""

    nome: str
    unidade: str
    referencia: float | None
    comparacao: float | None
    delta: float | None
    incerteza_delta: float | None
    detectavel: bool | None
    """True/False quando há incerteza para decidir; None quando não dá para saber."""

    @property
    def disponivel(self) -> bool:
        return self.delta is not None


def _valor_incerteza(x: Estatistica | Grandeza | None) -> tuple[float | None, float | None]:
    if x is None:
        return None, None
    if isinstance(x, Estatistica):
        return x.media, x.incerteza
    return x.valor, x.incerteza


def comparar(
    nome: str,
    unidade: str,
    referencia: Estatistica | Grandeza | None,
    comparacao: Estatistica | Grandeza | None,
) -> Comparacao:
    """Compara dois períodos; detectável se |Δ| > incerteza da diferença (k = 2)."""
    a, ua = _valor_incerteza(referencia)
    b, ub = _valor_incerteza(comparacao)
    if a is None or b is None:
        return Comparacao(nome, unidade, a, b, None, None, None)
    delta = float(b - a)
    u = float(sqrt(ua**2 + ub**2)) if ua is not None and ub is not None else None
    detectavel = None if u is None else bool(abs(delta) > u)
    return Comparacao(nome, unidade, float(a), float(b), delta, u, detectavel)
