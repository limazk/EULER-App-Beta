"""ML-03: avaliação estatística de resíduos fornecidos pelo motor físico."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .common import AbstencaoML, EscopoML, dividir_temporalmente, validar_serie


def _metricas(erro: np.ndarray) -> dict[str, float]:
    return {
        "vies": float(np.mean(erro)),
        "mae": float(np.mean(np.abs(erro))),
        "rmse": float(np.sqrt(np.mean(erro**2))),
    }


def avaliar_residuos_temporal(
    dados: pd.DataFrame,
    *,
    timestamp: str,
    medido: str,
    fisico: str,
    unidade_medida: str,
    unidade_fisica: str,
    escopo: EscopoML,
) -> dict:
    """Compara saída física original com correção de viés aprendida só no treino."""
    frame = validar_serie(dados, timestamp=timestamp, escopo=escopo)
    if medido not in frame or fisico not in frame:
        raise AbstencaoML("Medição ou saída física ausente.")
    if not unidade_medida or unidade_medida != unidade_fisica:
        raise AbstencaoML("Medição e saída física devem declarar a mesma unidade.")
    frame = frame.copy()
    frame[medido] = pd.to_numeric(frame[medido], errors="coerce")
    frame[fisico] = pd.to_numeric(frame[fisico], errors="coerce")
    valores = frame[[medido, fisico]].to_numpy(float)
    if np.isinf(valores).any():
        raise AbstencaoML("Medição ou saída física contém valores não finitos.")
    if np.isfinite(valores).all(axis=1).sum() < 60:
        raise AbstencaoML("Pares medido/físico insuficientes: mínimo 60.")
    partes = dividir_temporalmente(frame, minimo_treino=30, minimo_validacao=10, minimo_teste=10)

    def completos(parte: pd.DataFrame) -> pd.DataFrame:
        mascara = np.isfinite(parte[[medido, fisico]].to_numpy(float)).all(axis=1)
        return parte[mascara]

    treino = completos(partes.treino)
    validacao = completos(partes.validacao)
    teste = completos(partes.teste)
    if len(treino) < 30 or len(validacao) < 10 or len(teste) < 10:
        raise AbstencaoML("Pares completos insuficientes nas fatias temporais.")
    residuo_treino = (treino[medido] - treino[fisico]).to_numpy(float)
    residuo_teste = (teste[medido] - teste[fisico]).to_numpy(float)
    vies_treino = float(np.mean(residuo_treino))
    escala = float(np.std(residuo_treino, ddof=1))
    if not np.isfinite(escala) or escala <= 1e-12:
        raise AbstencaoML("Resíduo de treino sem variação suficiente.")
    corrigido = residuo_teste - vies_treino
    residuo_validacao = (validacao[medido] - validacao[fisico]).to_numpy(float) - vies_treino
    limite_95 = float(np.quantile(np.abs(residuo_treino - vies_treino), 0.95))
    return {
        "baseline_motor_fisico": _metricas(residuo_teste),
        "modelo_correcao_vies": _metricas(corrigido),
        "validacao_correcao_vies": _metricas(residuo_validacao),
        "vies_aprendido_treino": vies_treino,
        "limite_residuo_95": limite_95,
        "taxa_residuos_fora_95_pct": float(100 * (np.abs(corrigido) > limite_95).mean()),
        "residuo_medio_padronizado_teste": float(np.mean(corrigido / escala)),
        "amostras_treino": len(treino),
        "amostras_teste": len(teste),
        "unidade": unidade_medida,
        "periodo_teste": (
            teste[timestamp].iloc[0].isoformat(),
            teste[timestamp].iloc[-1].isoformat(),
        ),
        "nota": (
            "Associação estatística sem causalidade. A saída original do motor não é alterada; "
            "a correção serve apenas à avaliação offline."
        ),
    }
