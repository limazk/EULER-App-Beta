"""Modelos experimentais com dados exclusivamente sintéticos e seed fixa."""

import numpy as np
import pandas as pd
import pytest

from euler_intelligence.ml.anomaly import avaliar_detector, detectar, treinar_detector
from euler_intelligence.ml.common import AbstencaoML, EscopoML, dividir_temporalmente
from euler_intelligence.ml.forecasting import avaliar_previsao_temporal
from euler_intelligence.ml.residuals import avaliar_residuos_temporal

ESCOPO = EscopoML("org-sintetica", "planta-sintetica", "caldeira-sintetica")


def _base(n: int) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "instante": pd.date_range("2026-01-01", periods=n, freq="h", tz="UTC"),
            "organizacao_id": ESCOPO.organizacao_id,
            "planta_id": ESCOPO.planta_id,
            "equipamento_id": ESCOPO.equipamento_id,
        }
    )


def test_ml01_detecta_anomalias_e_reporta_falsos_alarmes():
    rng = np.random.default_rng(2501)
    treino = _base(100)
    treino["temperatura_c"] = rng.normal(180, 2, len(treino))
    treino["o2_pct"] = rng.normal(7, 0.2, len(treino))
    modelo = treinar_detector(
        treino,
        timestamp="instante",
        variaveis=("temperatura_c", "o2_pct"),
        escopo=ESCOPO,
    )
    teste = _base(60)
    teste["instante"] += pd.Timedelta(days=10)
    teste["temperatura_c"] = rng.normal(180, 2, len(teste))
    teste["o2_pct"] = rng.normal(7, 0.2, len(teste))
    teste["anomalia_real"] = False
    indices = [12, 31, 48]
    teste.loc[indices, "temperatura_c"] += 18
    teste.loc[indices, "o2_pct"] += 2
    teste.loc[indices, "anomalia_real"] = True
    avaliacao = avaliar_detector(
        modelo, teste, timestamp="instante", rotulo="anomalia_real", escopo=ESCOPO
    )
    assert avaliacao["modelo"]["revocacao"] == 1.0
    assert avaliacao["modelo"]["taxa_falso_alarme"] <= 0.1
    assert avaliacao["amostras_avaliadas"] == 60
    assert "não identifica causa" in avaliacao["nota"]


def test_ml01_missing_nao_vira_score_zero_ou_estado_normal():
    rng = np.random.default_rng(2502)
    treino = _base(50)
    treino["x"] = rng.normal(size=50)
    modelo = treinar_detector(treino, timestamp="instante", variaveis=("x",))
    teste = _base(3)
    teste["instante"] += pd.Timedelta(days=5)
    teste["x"] = [0.1, np.nan, 8.0]
    resultado = detectar(modelo, teste, timestamp="instante")
    assert pd.isna(resultado.loc[1, "score"])
    assert pd.isna(resultado.loc[1, "anomalia"])
    assert resultado.loc[1, "motivo_abstencao"]


def test_ml_isola_organizacao_planta_e_equipamento():
    limpos = _base(40)
    limpos["x"] = np.arange(40)
    modelo = treinar_detector(limpos, timestamp="instante", variaveis=("x",))
    dados = limpos.copy()
    dados.loc[20, "organizacao_id"] = "outra-org"
    with pytest.raises(AbstencaoML, match="Mistura"):
        treinar_detector(dados, timestamp="instante", variaveis=("x",), escopo=ESCOPO)
    with pytest.raises(AbstencaoML, match="Mistura"):
        detectar(modelo, dados, timestamp="instante", escopo=ESCOPO)


def test_divisao_temporal_e_ordem_sem_vazamento():
    dados = _base(100)
    partes = dividir_temporalmente(dados, minimo_treino=50, minimo_validacao=15, minimo_teste=15)
    assert partes.treino["instante"].max() < partes.validacao["instante"].min()
    assert partes.validacao["instante"].max() < partes.teste["instante"].min()


def _serie_ar(n: int = 180) -> pd.DataFrame:
    rng = np.random.default_rng(2503)
    y = np.zeros(n)
    y[:2] = [8.0, 12.0]
    for i in range(2, n):
        # Alternância autorregressiva sintética: previsível por modelo, ruim para persistência.
        y[i] = 19.8 - 0.98 * y[i - 1] + rng.normal(0, 0.05)
    dados = _base(n)
    dados["consumo_gj"] = y
    return dados


def test_ml02_previsao_temporal_supera_persistencia_no_caso_sintetico():
    resultado = avaliar_previsao_temporal(
        _serie_ar(),
        timestamp="instante",
        alvo="consumo_gj",
        origem_alvo="consumo_entre_estoques",
        unidade="GJ",
        lags=2,
        escopo=ESCOPO,
    )
    assert resultado["metricas_modelo"]["mae"] < resultado["metricas_baseline_persistencia"]["mae"]
    assert resultado["horizonte_passos"] == 1
    assert 0 <= resultado["cobertura_90_pct"] <= 100
    assert resultado["intervalo_erro_90"] > 0


def test_ml02_teste_futuro_nao_altera_modelo_treinado():
    original = _serie_ar()
    alterado = original.copy()
    alterado.loc[alterado.index[-25:], "consumo_gj"] += 1000
    a = avaliar_previsao_temporal(
        original,
        timestamp="instante",
        alvo="consumo_gj",
        origem_alvo="consumo_entre_estoques",
        unidade="GJ",
        lags=2,
    )
    b = avaliar_previsao_temporal(
        alterado,
        timestamp="instante",
        alvo="consumo_gj",
        origem_alvo="consumo_entre_estoques",
        unidade="GJ",
        lags=2,
    )
    assert a["modelo"].coeficientes == b["modelo"].coeficientes


def test_ml02_abstem_com_amostras_insuficientes():
    dados = _serie_ar(30)
    with pytest.raises(AbstencaoML, match="Amostras insuficientes"):
        avaliar_previsao_temporal(
            dados,
            timestamp="instante",
            alvo="consumo_gj",
            origem_alvo="consumo_entre_estoques",
            unidade="GJ",
        )


def test_ml02_recusa_recebimento_como_se_fosse_consumo():
    with pytest.raises(AbstencaoML, match="recebimento"):
        avaliar_previsao_temporal(
            _serie_ar(),
            timestamp="instante",
            alvo="consumo_gj",
            origem_alvo="combustivel_recebido",
            unidade="GJ",
        )


def test_ml03_avalia_residuo_sem_alterar_saida_fisica():
    rng = np.random.default_rng(2504)
    dados = _base(150)
    fisico = np.linspace(90, 110, len(dados))
    dados["motor_fisico_gj"] = fisico
    dados["medido_gj"] = fisico + 2.5 + rng.normal(0, 0.4, len(dados))
    original = dados["motor_fisico_gj"].copy()
    resultado = avaliar_residuos_temporal(
        dados,
        timestamp="instante",
        medido="medido_gj",
        fisico="motor_fisico_gj",
        unidade="GJ",
        escopo=ESCOPO,
    )
    assert resultado["modelo_correcao_vies"]["mae"] < resultado["baseline_motor_fisico"]["mae"]
    assert dados["motor_fisico_gj"].equals(original)
    assert "sem causalidade" in resultado["nota"]


def test_ml03_missing_em_excesso_causa_abstencao():
    dados = _base(80)
    dados["fisico"] = 10.0
    dados["medido"] = np.nan
    dados.loc[:20, "medido"] = 11.0
    with pytest.raises(AbstencaoML, match="insuficientes"):
        avaliar_residuos_temporal(
            dados, timestamp="instante", medido="medido", fisico="fisico", unidade="GJ"
        )
