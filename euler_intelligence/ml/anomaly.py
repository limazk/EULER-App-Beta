"""ML-01: detecção robusta de observações incomuns, sem diagnóstico de causa."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .common import AbstencaoML, EscopoML, metricas_binarias, validar_serie


@dataclass(frozen=True)
class DetectorAnomalias:
    variaveis: tuple[str, ...]
    centro: tuple[float, ...]
    escala: tuple[float, ...]
    limiar: float
    amostras_treino: int
    inicio_treino: str
    fim_treino: str
    versao: str = "robust-mad/1"


def treinar_detector(
    treino: pd.DataFrame,
    *,
    timestamp: str,
    variaveis: tuple[str, ...],
    escopo: EscopoML | None = None,
    minimo_amostras: int = 30,
) -> DetectorAnomalias:
    frame = validar_serie(treino, timestamp=timestamp, escopo=escopo)
    if not variaveis or any(c not in frame for c in variaveis):
        raise AbstencaoML("Variáveis do detector ausentes ou não informadas.")
    completos = frame.loc[:, variaveis].apply(pd.to_numeric, errors="coerce").dropna()
    if len(completos) < minimo_amostras:
        raise AbstencaoML(
            f"Amostras completas insuficientes: {len(completos)} < {minimo_amostras}."
        )
    valores = completos.to_numpy(dtype=float)
    if not np.isfinite(valores).all():
        raise AbstencaoML("Valores não finitos no treino.")
    centro = np.median(valores, axis=0)
    escala = 1.4826 * np.median(np.abs(valores - centro), axis=0)
    if np.any(escala <= 1e-12):
        constantes = [v for v, s in zip(variaveis, escala, strict=True) if s <= 1e-12]
        raise AbstencaoML(f"Variáveis sem variação robusta: {', '.join(constantes)}.")
    scores = np.sqrt(np.mean(((valores - centro) / escala) ** 2, axis=1))
    limiar = max(3.5, float(np.quantile(scores, 0.99)))
    return DetectorAnomalias(
        variaveis,
        tuple(map(float, centro)),
        tuple(map(float, escala)),
        limiar,
        len(completos),
        frame[timestamp].iloc[0].isoformat(),
        frame[timestamp].iloc[-1].isoformat(),
    )


def detectar(
    modelo: DetectorAnomalias,
    dados: pd.DataFrame,
    *,
    timestamp: str,
    escopo: EscopoML | None = None,
) -> pd.DataFrame:
    frame = validar_serie(dados, timestamp=timestamp, escopo=escopo)
    x = frame.loc[:, modelo.variaveis].apply(pd.to_numeric, errors="coerce")
    completos = x.notna().all(axis=1) & np.isfinite(x).all(axis=1)
    saida = pd.DataFrame({timestamp: frame[timestamp], "score": np.nan})
    saida["anomalia"] = pd.Series(pd.NA, index=frame.index, dtype="boolean")
    saida["motivo_abstencao"] = "medição ausente ou inválida"
    if completos.any():
        z = (x.loc[completos].to_numpy(float) - np.array(modelo.centro)) / np.array(modelo.escala)
        scores = np.sqrt(np.mean(z**2, axis=1))
        saida.loc[completos, "score"] = scores
        saida.loc[completos, "anomalia"] = scores > modelo.limiar
        saida.loc[completos, "motivo_abstencao"] = None
        contribuicoes = np.abs(z)
        nomes = np.array(modelo.variaveis)
        saida.loc[completos, "variavel_mais_incomum"] = nomes[np.argmax(contribuicoes, axis=1)]
    return saida


def avaliar_detector(
    modelo: DetectorAnomalias,
    teste: pd.DataFrame,
    *,
    timestamp: str,
    rotulo: str,
    escopo: EscopoML | None = None,
) -> dict:
    if rotulo not in teste:
        raise AbstencaoML(f"Rótulo de avaliação ausente: {rotulo}.")
    resultado = detectar(modelo, teste, timestamp=timestamp, escopo=escopo)
    validos = resultado["anomalia"].notna() & teste[rotulo].notna()
    if not validos.any():
        raise AbstencaoML("Nenhuma amostra avaliável.")
    metricas = metricas_binarias(teste.loc[validos, rotulo], resultado.loc[validos, "anomalia"])
    x_treino_media = np.array(modelo.centro)
    x_treino_escala = np.array(modelo.escala)
    x = teste.loc[validos, modelo.variaveis].to_numpy(float)
    baseline = np.any(np.abs((x - x_treino_media) / x_treino_escala) > 3.0, axis=1)
    return {
        "modelo": metricas,
        "baseline_mad_univariado_3": metricas_binarias(teste.loc[validos, rotulo], baseline),
        "amostras_avaliadas": int(validos.sum()),
        "limiar": modelo.limiar,
        "nota": "Anomalia estatística não identifica causa, falha ou risco operacional.",
    }
