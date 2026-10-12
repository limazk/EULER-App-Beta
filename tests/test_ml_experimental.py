"""Modelos experimentais com dados exclusivamente sintéticos e seed fixa."""

import ast
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from euler_intelligence.ml.anomaly import avaliar_detector, detectar, treinar_detector
from euler_intelligence.ml.common import (
    AbstencaoML,
    EscopoML,
    dividir_temporalmente,
    metricas_binarias,
)
from euler_intelligence.ml.forecasting import avaliar_previsao_temporal, prever_proximo
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
    modelo = treinar_detector(treino, timestamp="instante", variaveis=("x",), escopo=ESCOPO)
    teste = _base(3)
    teste["instante"] += pd.Timedelta(days=5)
    teste["x"] = [0.1, np.nan, 8.0]
    resultado = detectar(modelo, teste, timestamp="instante", escopo=ESCOPO)
    assert pd.isna(resultado.loc[1, "score"])
    assert pd.isna(resultado.loc[1, "anomalia"])
    assert resultado.loc[1, "motivo_abstencao"]


def test_ml_isola_organizacao_planta_e_equipamento():
    limpos = _base(40)
    limpos["x"] = np.arange(40)
    modelo = treinar_detector(limpos, timestamp="instante", variaveis=("x",), escopo=ESCOPO)
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
        escopo=ESCOPO,
    )
    b = avaliar_previsao_temporal(
        alterado,
        timestamp="instante",
        alvo="consumo_gj",
        origem_alvo="consumo_entre_estoques",
        unidade="GJ",
        lags=2,
        escopo=ESCOPO,
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
            escopo=ESCOPO,
        )


def test_ml02_recusa_recebimento_como_se_fosse_consumo():
    with pytest.raises(AbstencaoML, match="recebimento"):
        avaliar_previsao_temporal(
            _serie_ar(),
            timestamp="instante",
            alvo="consumo_gj",
            origem_alvo="combustivel_recebido",
            unidade="GJ",
            escopo=ESCOPO,
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
        unidade_medida="GJ",
        unidade_fisica="GJ",
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
            dados,
            timestamp="instante",
            medido="medido",
            fisico="fisico",
            unidade_medida="GJ",
            unidade_fisica="GJ",
            escopo=ESCOPO,
        )


def test_ml01_modelo_exige_mesmo_escopo_na_inferencia():
    rng = np.random.default_rng(2505)
    treino = _base(50)
    treino["x"] = rng.normal(size=50)
    modelo = treinar_detector(treino, timestamp="instante", variaveis=("x",), escopo=ESCOPO)
    futuro = _base(5)
    futuro["instante"] += pd.Timedelta(days=5)
    futuro["x"] = rng.normal(size=5)
    assert detectar(modelo, futuro, timestamp="instante", escopo=ESCOPO)["score"].notna().all()
    with pytest.raises(AbstencaoML, match="obrigatório"):
        detectar(modelo, futuro, timestamp="instante")
    outro = EscopoML("outra-org", ESCOPO.planta_id, ESCOPO.equipamento_id)
    with pytest.raises(AbstencaoML, match="diverge"):
        detectar(modelo, futuro, timestamp="instante", escopo=outro)


def test_ml01_valida_variaveis_periodo_constantes_e_nao_finitos():
    rng = np.random.default_rng(2506)
    treino = _base(50)
    treino["x"] = rng.normal(size=50)
    modelo = treinar_detector(treino, timestamp="instante", variaveis=("x",), escopo=ESCOPO)
    futuro = _base(4)
    futuro["instante"] += pd.Timedelta(days=5)
    with pytest.raises(AbstencaoML, match="Variáveis ausentes"):
        detectar(modelo, futuro, timestamp="instante", escopo=ESCOPO)
    com_x = treino.copy()
    with pytest.raises(AbstencaoML, match="posterior"):
        detectar(modelo, com_x, timestamp="instante", escopo=ESCOPO)
    constante = _base(40)
    constante["x"] = 1.0
    with pytest.raises(AbstencaoML, match="sem variação"):
        treinar_detector(constante, timestamp="instante", variaveis=("x",), escopo=ESCOPO)
    treino.loc[10, "x"] = np.inf
    with pytest.raises(AbstencaoML, match="não finitos"):
        treinar_detector(treino, timestamp="instante", variaveis=("x",), escopo=ESCOPO)


def test_metricas_binarias_recusam_coercao_missing_e_tamanhos_diferentes():
    with pytest.raises(AbstencaoML, match="booleanos"):
        metricas_binarias(["sim", "não"], [True, False])
    with pytest.raises(AbstencaoML, match="ausentes"):
        metricas_binarias([True, None], [True, False])
    with pytest.raises(AbstencaoML, match="mesmo tamanho"):
        metricas_binarias([True], [True, False])


def test_ml02_preve_proximo_valor_sem_rotulo_futuro():
    dados = _serie_ar()
    avaliacao = avaliar_previsao_temporal(
        dados,
        timestamp="instante",
        alvo="consumo_gj",
        origem_alvo="consumo_entre_estoques",
        unidade="GJ",
        lags=2,
        escopo=ESCOPO,
    )
    historico_separado = _serie_ar(12)
    historico_separado["instante"] += pd.Timedelta(days=30)
    previsao = prever_proximo(
        avaliacao["modelo"], historico_separado, timestamp="instante", escopo=ESCOPO
    )
    assert previsao.timestamp_previsto == historico_separado["instante"].iloc[-1] + pd.Timedelta(
        hours=1
    )
    assert previsao.horizonte_passos == 1
    assert previsao.unidade == "GJ"
    assert previsao.origem_alvo == "consumo_entre_estoques"
    assert previsao.intervalo_inferior is None and previsao.intervalo_superior is None


def test_ml02_previsao_futura_falha_fechada_por_escopo():
    avaliacao = avaliar_previsao_temporal(
        _serie_ar(),
        timestamp="instante",
        alvo="consumo_gj",
        origem_alvo="energia_medida",
        unidade="GJ",
        lags=2,
        escopo=ESCOPO,
    )
    with pytest.raises(AbstencaoML, match="obrigatório"):
        prever_proximo(avaliacao["modelo"], _serie_ar(), timestamp="instante")
    outro = EscopoML("outra-org", "outra-planta", "outra-caldeira")
    with pytest.raises(AbstencaoML, match="diverge"):
        prever_proximo(avaliacao["modelo"], _serie_ar(), timestamp="instante", escopo=outro)
    dados_de_outro_cliente = _serie_ar()
    dados_de_outro_cliente["organizacao_id"] = "outra-org"
    with pytest.raises(AbstencaoML, match="Mistura ou divergência"):
        prever_proximo(
            avaliacao["modelo"],
            dados_de_outro_cliente,
            timestamp="instante",
            escopo=ESCOPO,
        )


def test_ml02_recusa_cadencia_irregular_inf_e_janelas_incompletas():
    irregular = _serie_ar()
    irregular.loc[50:, "instante"] += pd.Timedelta(minutes=30)
    with pytest.raises(AbstencaoML, match="irregulares"):
        avaliar_previsao_temporal(
            irregular,
            timestamp="instante",
            alvo="consumo_gj",
            origem_alvo="energia_medida",
            unidade="GJ",
            escopo=ESCOPO,
        )
    nao_finito = _serie_ar()
    nao_finito.loc[10, "consumo_gj"] = np.inf
    with pytest.raises(AbstencaoML, match="não finitos"):
        avaliar_previsao_temporal(
            nao_finito,
            timestamp="instante",
            alvo="consumo_gj",
            origem_alvo="energia_medida",
            unidade="GJ",
            escopo=ESCOPO,
        )
    incompleto = _serie_ar()
    incompleto.loc[110:142, "consumo_gj"] = np.nan
    with pytest.raises(AbstencaoML, match="Janelas completas insuficientes"):
        avaliar_previsao_temporal(
            incompleto,
            timestamp="instante",
            alvo="consumo_gj",
            origem_alvo="energia_medida",
            unidade="GJ",
            lags=3,
            escopo=ESCOPO,
        )


def test_ml03_recusa_nao_finitos_e_unidades_divergentes():
    dados = _base(100)
    dados["fisico"] = np.linspace(10, 12, 100)
    dados["medido"] = dados["fisico"] + 1
    dados.loc[70, "medido"] = np.inf
    with pytest.raises(AbstencaoML, match="não finitos"):
        avaliar_residuos_temporal(
            dados,
            timestamp="instante",
            medido="medido",
            fisico="fisico",
            unidade_medida="GJ",
            unidade_fisica="GJ",
            escopo=ESCOPO,
        )
    dados.loc[70, "medido"] = 12
    with pytest.raises(AbstencaoML, match="mesma unidade"):
        avaliar_residuos_temporal(
            dados,
            timestamp="instante",
            medido="medido",
            fisico="fisico",
            unidade_medida="GJ",
            unidade_fisica="kWh",
            escopo=ESCOPO,
        )


def test_modulos_ml_nao_importam_clientes_de_rede():
    raiz = Path(__file__).parents[1] / "euler_intelligence" / "ml"
    proibidos = {"requests", "httpx", "urllib", "socket", "openai", "anthropic"}
    encontrados = set()
    for caminho in raiz.glob("*.py"):
        arvore = ast.parse(caminho.read_text(encoding="utf-8"))
        for no in ast.walk(arvore):
            if isinstance(no, ast.Import):
                encontrados.update(alias.name.split(".")[0] for alias in no.names)
            elif isinstance(no, ast.ImportFrom) and no.module:
                encontrados.add(no.module.split(".")[0])
    assert encontrados.isdisjoint(proibidos)
