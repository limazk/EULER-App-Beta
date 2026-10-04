"""Fixtures didáticas para diagnósticos; não são evidência do caso público."""

import numpy as np
import pandas as pd
import pytest

from euler.referencia import avaliar_referencia


def entradas():
    rng = np.random.default_rng(7)
    carga = np.tile(np.arange(10, 20), 10)
    previsto = 20 + 2 * carga
    return {
        "observado": previsto + rng.normal(0, 0.05, 100),
        "previsto": previsto,
        "unidade": "GJ",
        "instantes": pd.date_range("2023-01-01", periods=100, freq="h"),
        "carga": carga,
        "carga_comparacao": carga,
        "unidade_carga": "t/h",
        "intervalo_horas": 1,
        "regimes": ["estavel"] * 100,
        "validacao_temporal": [{"vies_pct": 0.1, "horas_comparaveis": 30}],
    }


def test_referencia_estavel_e_instavel_sem_selecionar_ou_excluir():
    kw = entradas()
    assert avaliar_referencia(**kw)["nivel"] == "FORTE"
    original = kw["observado"].copy()
    kw["observado"][50:] += 6
    d = avaliar_referencia(**kw)
    assert d["nivel"] == "FRACA"
    assert d["metricas"]["observacoes_validas"] == 100
    assert not np.array_equal(original, kw["observado"])
    assert any("temporal" in x for x in d["motivos"])


def test_insuficiencia_ausencias_unidades_e_degeneracao():
    assert avaliar_referencia(observado=[1, None], unidade="GJ")["nivel"] == "INSUFICIENTE"
    d = avaliar_referencia(observado=[1] * 100, unidade="GJ")
    assert d["nivel"] != "FORTE"
    assert d["metricas"]["outliers_mad"] is None
    kw = entradas()
    kw["observado"][:20] = np.nan
    d = avaliar_referencia(**kw)
    assert d["metricas"]["observacoes_invalidas"] == 20
    assert d["nivel"] == "FRACA"
    with pytest.raises(ValueError):
        avaliar_referencia(observado=[1, 2, 3], previsto=[1], unidade="GJ")
    with pytest.raises(ValueError):
        avaliar_referencia(observado=[1, 2, 3], unidade="")


def test_cobertura_regime_e_invariancia_de_escala():
    kw = entradas()
    a = avaliar_referencia(**kw)
    kw["observado"] *= 1000
    kw["previsto"] = kw["previsto"] * 1000
    kw["unidade"] = "MJ"
    b = avaliar_referencia(**kw)
    assert a["nivel"] == b["nivel"]
    assert a["metricas"]["rmse_relativo_pct"] == pytest.approx(b["metricas"]["rmse_relativo_pct"])
    kw["carga_comparacao"] = [100, 200]
    assert avaliar_referencia(**kw)["nivel"] == "INSUFICIENTE"
    kw = entradas()
    kw["regimes"][1] = "transitorio"
    assert avaliar_referencia(**kw)["nivel"] == "FRACA"
    kw = entradas()
    kw["instantes"] = [pd.Timestamp("2023-01-01")] * 100
    assert avaliar_referencia(**kw)["nivel"] == "FRACA"
