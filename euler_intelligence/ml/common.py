"""Validações compartilhadas pelos experimentos offline de ML."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
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


def exigir_escopo(modelo: EscopoML, informado: EscopoML | None) -> EscopoML:
    """Falha fechada: inferência exige o escopo e ele deve ser o do treino."""
    if informado is None:
        raise AbstencaoML("Escopo obrigatório para inferência isolada.")
    if informado != modelo:
        raise AbstencaoML("Escopo da inferência diverge do escopo do modelo treinado.")
    return informado


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
    if frame.empty:
        raise AbstencaoML("Série vazia.")
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


def validar_regularidade(dados: pd.DataFrame, *, timestamp: str) -> pd.Timedelta:
    """Exige uma cadência única e positiva para que lags tenham duração conhecida."""
    if len(dados) < 2:
        raise AbstencaoML("Amostras insuficientes para determinar a frequência temporal.")
    passos = dados[timestamp].diff().dropna()
    if (passos <= pd.Timedelta(0)).any() or passos.nunique() != 1:
        raise AbstencaoML("Intervalos temporais irregulares; horizonte em passos é ambíguo.")
    return passos.iloc[0]


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
    y = np.asarray(esperado)
    p = np.asarray(previsto)
    if y.ndim != 1 or p.ndim != 1 or len(y) != len(p) or not len(y):
        raise AbstencaoML("Rótulos binários precisam ter vetores não vazios do mesmo tamanho.")
    if pd.isna(y).any() or pd.isna(p).any():
        raise AbstencaoML("Rótulos binários não aceitam valores ausentes.")
    if y.dtype.kind != "b" or p.dtype.kind != "b":
        raise AbstencaoML("Rótulos e previsões devem ser booleanos, sem coerção implícita.")
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
