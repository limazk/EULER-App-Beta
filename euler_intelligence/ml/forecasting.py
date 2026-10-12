"""ML-02: previsão temporal experimental comparada à persistência."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .common import (
    AbstencaoML,
    EscopoML,
    dividir_temporalmente,
    exigir_escopo,
    validar_regularidade,
    validar_serie,
)


@dataclass(frozen=True)
class ModeloAutoregressivo:
    escopo: EscopoML
    alvo: str
    origem_alvo: str
    unidade: str
    lags: int
    coeficientes: tuple[float, ...]
    amostras_treino: int
    frequencia_segundos: float
    versao: str = "autoregressao-linear/1"


@dataclass(frozen=True)
class PrevisaoFutura:
    valor: float
    timestamp_previsto: pd.Timestamp
    horizonte_passos: int
    unidade: str
    origem_alvo: str
    intervalo_inferior: None = None
    intervalo_superior: None = None
    nota_intervalo: str = "Intervalo não informado: esta inferência não recebeu calibração válida."


def _janelas(serie: pd.Series, lags: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    valores = pd.to_numeric(serie, errors="coerce").to_numpy(float)
    xs, ys, indices = [], [], []
    for i in range(lags, len(valores)):
        janela = valores[i - lags : i]
        if np.isfinite(janela).all() and np.isfinite(valores[i]):
            xs.append([1.0, *janela])
            ys.append(valores[i])
            indices.append(i)
    return np.asarray(xs, float), np.asarray(ys, float), np.asarray(indices, int)


def _validar_alvo(frame: pd.DataFrame, alvo: str) -> None:
    if alvo not in frame:
        raise AbstencaoML(f"Alvo ausente: {alvo}.")
    valores = pd.to_numeric(frame[alvo], errors="coerce").to_numpy(float)
    if np.isinf(valores).any():
        raise AbstencaoML("Alvo contém valores não finitos.")


def treinar_autoregressao(
    treino: pd.DataFrame,
    *,
    timestamp: str,
    alvo: str,
    origem_alvo: str,
    unidade: str,
    lags: int = 3,
    escopo: EscopoML,
    minimo_amostras: int = 30,
) -> ModeloAutoregressivo:
    frame = validar_serie(treino, timestamp=timestamp, escopo=escopo)
    frequencia = validar_regularidade(frame, timestamp=timestamp)
    origens_validas = {"consumo_entre_estoques", "energia_medida"}
    if origem_alvo not in origens_validas:
        raise AbstencaoML(
            "Origem do alvo inválida: recebimento de combustível não representa consumo."
        )
    if not isinstance(unidade, str) or not unidade.strip():
        raise AbstencaoML("Unidade do alvo é obrigatória.")
    _validar_alvo(frame, alvo)
    if lags < 1:
        raise AbstencaoML("Alvo ausente ou quantidade de lags inválida.")
    x, y, _ = _janelas(frame[alvo], lags)
    if len(y) < minimo_amostras:
        raise AbstencaoML(f"Janelas completas insuficientes: {len(y)} < {minimo_amostras}.")
    coef, *_ = np.linalg.lstsq(x, y, rcond=None)
    return ModeloAutoregressivo(
        escopo=escopo,
        alvo=alvo,
        origem_alvo=origem_alvo,
        unidade=unidade,
        lags=lags,
        coeficientes=tuple(map(float, coef)),
        amostras_treino=len(y),
        frequencia_segundos=frequencia.total_seconds(),
    )


def backtest_um_passo(
    modelo: ModeloAutoregressivo,
    dados: pd.DataFrame,
    *,
    timestamp: str,
    escopo: EscopoML | None = None,
) -> pd.DataFrame:
    escopo = exigir_escopo(modelo.escopo, escopo)
    frame = validar_serie(dados, timestamp=timestamp, escopo=escopo)
    frequencia = validar_regularidade(frame, timestamp=timestamp)
    if frequencia.total_seconds() != modelo.frequencia_segundos:
        raise AbstencaoML("Frequência da série diverge da frequência usada no treinamento.")
    _validar_alvo(frame, modelo.alvo)
    x, y, indices = _janelas(frame[modelo.alvo], modelo.lags)
    if not len(y):
        raise AbstencaoML("Nenhuma janela completa para previsão.")
    previsto = x @ np.asarray(modelo.coeficientes)
    baseline = x[:, -1]
    return pd.DataFrame(
        {
            timestamp: frame[timestamp].iloc[indices].to_numpy(),
            "observado": y,
            "previsto": previsto,
            "baseline_persistencia": baseline,
        }
    )


def prever_um_passo(
    modelo: ModeloAutoregressivo,
    dados: pd.DataFrame,
    *,
    timestamp: str,
    escopo: EscopoML | None = None,
) -> pd.DataFrame:
    """Compatibilidade: previsão histórica avaliada contra alvo já observado."""
    return backtest_um_passo(modelo, dados, timestamp=timestamp, escopo=escopo)


def prever_proximo(
    modelo: ModeloAutoregressivo,
    historico: pd.DataFrame,
    *,
    timestamp: str,
    escopo: EscopoML | None = None,
) -> PrevisaoFutura:
    """Prevê o próximo instante usando somente lags passados; o alvo futuro não existe."""
    escopo = exigir_escopo(modelo.escopo, escopo)
    frame = validar_serie(historico, timestamp=timestamp, escopo=escopo)
    frequencia = validar_regularidade(frame, timestamp=timestamp)
    if frequencia.total_seconds() != modelo.frequencia_segundos:
        raise AbstencaoML("Frequência da série diverge da frequência usada no treinamento.")
    _validar_alvo(frame, modelo.alvo)
    if len(frame) < modelo.lags:
        raise AbstencaoML("Histórico insuficiente para formar os lags da previsão futura.")
    janela = pd.to_numeric(frame[modelo.alvo].tail(modelo.lags), errors="coerce").to_numpy(float)
    if not np.isfinite(janela).all():
        raise AbstencaoML("Os lags mais recentes contêm valores ausentes ou não finitos.")
    x = np.asarray([1.0, *janela])
    valor = float(x @ np.asarray(modelo.coeficientes))
    return PrevisaoFutura(
        valor=valor,
        timestamp_previsto=frame[timestamp].iloc[-1] + frequencia,
        horizonte_passos=1,
        unidade=modelo.unidade,
        origem_alvo=modelo.origem_alvo,
    )


def _erros(observado: np.ndarray, previsto: np.ndarray) -> dict[str, float]:
    erro = observado - previsto
    nao_zero = np.abs(observado) > 1e-12
    return {
        "mae": float(np.mean(np.abs(erro))),
        "rmse": float(np.sqrt(np.mean(erro**2))),
        "mape_pct": float(100 * np.mean(np.abs(erro[nao_zero] / observado[nao_zero])))
        if nao_zero.any()
        else float("nan"),
    }


def avaliar_previsao_temporal(
    dados: pd.DataFrame,
    *,
    timestamp: str,
    alvo: str,
    origem_alvo: str,
    unidade: str,
    lags: int = 3,
    escopo: EscopoML,
) -> dict:
    """Treina no passado, calibra intervalo na validação e mede no teste futuro."""
    frame = validar_serie(dados, timestamp=timestamp, escopo=escopo)
    _validar_alvo(frame, alvo)
    validar_regularidade(frame, timestamp=timestamp)
    partes = dividir_temporalmente(frame, minimo_treino=40, minimo_validacao=15, minimo_teste=15)
    modelo = treinar_autoregressao(
        partes.treino,
        timestamp=timestamp,
        alvo=alvo,
        origem_alvo=origem_alvo,
        unidade=unidade,
        lags=lags,
        escopo=escopo,
    )
    # O contexto anterior é anexado somente para formar lags; métricas usam a fatia futura.
    contexto = partes.treino.tail(lags)
    validacao = backtest_um_passo(
        modelo,
        pd.concat([contexto, partes.validacao]),
        timestamp=timestamp,
        escopo=escopo,
    )
    contexto_teste = pd.concat([partes.treino, partes.validacao]).tail(lags)
    teste = backtest_um_passo(
        modelo,
        pd.concat([contexto_teste, partes.teste]),
        timestamp=timestamp,
        escopo=escopo,
    )
    minimo_janelas = 10
    if len(validacao) < minimo_janelas or len(teste) < minimo_janelas:
        raise AbstencaoML(
            "Janelas completas insuficientes na validação ou teste após tratar valores ausentes."
        )
    erro_validacao = np.abs(validacao["observado"] - validacao["previsto"])
    margem_90 = float(np.quantile(erro_validacao, 0.9))
    teste["limite_inferior_90"] = teste["previsto"] - margem_90
    teste["limite_superior_90"] = teste["previsto"] + margem_90
    observado = teste["observado"].to_numpy(float)
    metricas_modelo = _erros(observado, teste["previsto"].to_numpy(float))
    metricas_baseline = _erros(observado, teste["baseline_persistencia"].to_numpy(float))
    return {
        "modelo": modelo,
        "metricas_modelo": metricas_modelo,
        "metricas_baseline_persistencia": metricas_baseline,
        "melhoria_mae_pct": 100
        * (metricas_baseline["mae"] - metricas_modelo["mae"])
        / metricas_baseline["mae"]
        if metricas_baseline["mae"]
        else 0.0,
        "intervalo_erro_90": margem_90,
        "cobertura_90_pct": float(
            100
            * (
                (observado >= teste["limite_inferior_90"])
                & (observado <= teste["limite_superior_90"])
            ).mean()
        ),
        "unidade": unidade,
        "origem_alvo": origem_alvo,
        "horizonte_passos": 1,
        "predicoes_teste": teste,
        "nota": "Previsão experimental; não é comando operacional nem economia verificada.",
    }
