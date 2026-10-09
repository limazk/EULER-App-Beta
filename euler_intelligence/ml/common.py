"""Validações compartilhadas pelos experimentos offline de ML."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


class AbstencaoML(ValueError):
    """Entrada inadequada: o modelo se abstém em vez de inventar resultado."""


@dataclass(frozen=True)
class EscopoML:
    organizacao_id: str
    planta_id: str
    equipamento_id: str

    def __post_init__(self) -> None:
        if not all(isinstance(v, str) and v.strip() for v in vars(self).values()):
            raise ValueError("O escopo de organização, planta e equipamento é obrigatório.")


@dataclass(frozen=True)
class DivisaoTemporal:
    treino: pd.DataFrame
    validacao: pd.DataFrame
    teste: pd.DataFrame


def validar_serie(
    dados: pd.DataFrame,
    *,
    timestamp: str,
    escopo: EscopoML | None = None,
) -> pd.DataFrame:
    """Valida ordem e isolamento; nunca ordena silenciosamente dados fora de ordem."""
    if timestamp not in dados:
        raise AbstencaoML(f"Coluna temporal ausente: {timestamp}.")
    frame = dados.copy()
    try:
        frame[timestamp] = pd.to_datetime(frame[timestamp], utc=True)
    except (TypeError, ValueError) as exc:
        raise AbstencaoML("Timestamps inválidos.") from exc
    if frame[timestamp].isna().any():
        raise AbstencaoML("Timestamps ausentes.")
    if frame[timestamp].duplicated().any() or not frame[timestamp].is_monotonic_increasing:
        raise AbstencaoML("A série deve ter timestamps únicos e em ordem crescente.")
    if escopo is not None:
        esperados = {
            "organizacao_id": escopo.organizacao_id,
            "planta_id": escopo.planta_id,
            "equipamento_id": escopo.equipamento_id,
        }
        for coluna, esperado in esperados.items():
            if coluna not in frame:
                raise AbstencaoML(f"Escopo ausente: {coluna}.")
            valores = set(frame[coluna].dropna().astype(str))
            if valores != {esperado} or frame[coluna].isna().any():
                raise AbstencaoML(f"Mistura ou divergência de escopo em {coluna}.")
    return frame


def dividir_temporalmente(
    dados: pd.DataFrame,
    *,
    minimo_treino: int,
    minimo_validacao: int,
    minimo_teste: int,
    fracao_treino: float = 0.6,
    fracao_validacao: float = 0.2,
) -> DivisaoTemporal:
    """Fatias contíguas treino → validação → teste, sem embaralhamento."""
    n = len(dados)
    corte_treino = int(n * fracao_treino)
    corte_validacao = int(n * (fracao_treino + fracao_validacao))
    partes = (
        dados.iloc[:corte_treino],
        dados.iloc[corte_treino:corte_validacao],
        dados.iloc[corte_validacao:],
    )
    minimos = (minimo_treino, minimo_validacao, minimo_teste)
    if any(len(parte) < minimo for parte, minimo in zip(partes, minimos, strict=True)):
        raise AbstencaoML(
            f"Amostras insuficientes para divisão temporal: {tuple(map(len, partes))}; "
            f"mínimos {minimos}."
        )
    return DivisaoTemporal(*(parte.copy() for parte in partes))


def metricas_binarias(esperado, previsto) -> dict[str, float | int]:
    y = pd.Series(esperado, dtype=bool)
    p = pd.Series(previsto, dtype=bool)
    tp = int((y & p).sum())
    fp = int((~y & p).sum())
    fn = int((y & ~p).sum())
    tn = int((~y & ~p).sum())
    return {
        "precisao": tp / (tp + fp) if tp + fp else 0.0,
        "revocacao": tp / (tp + fn) if tp + fn else 0.0,
        "taxa_falso_alarme": fp / (fp + tn) if fp + tn else 0.0,
        "verdadeiros_positivos": tp,
        "falsos_positivos": fp,
        "falsos_negativos": fn,
    }
