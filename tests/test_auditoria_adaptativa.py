"""Regressões da auditoria: dados parciais não podem virar falhas ou hipóteses ocultas."""

import pandas as pd
import pytest

from euler.fluxos import balanco_por_vazoes, fluxo_entalpia_vapor
from euler.io import importar_pacote
from euler.io.diario import importar_diario
from euler.planta import mapear_planta
from euler.tipos import AnaliseBloqueada


def diario(n=7):
    return pd.DataFrame(
        {
            "linha": range(2, n + 2),
            "caldeira_id": ["C1"] * n,
            "instante_observado": pd.date_range("2026-10-01", periods=n, freq="h", tz="UTC"),
            "regime": ["estavel"] * n,
            "estado_vapor": ["superaquecido"] * n,
            "p_vapor_bar_abs": [10.0] * n,
            "p_agua_referencia_bar_abs": [2.0] * n,
            "t_vapor_c": [250.0] * n,
            "t_agua_alim_c": [80.0] * n,
            "vazao_vapor_t_h": [10.0] * n,
            "potencia_combustivel_mw": [8.4] * n,
        }
    )


def test_lacuna_combustivel_preserva_intervalos_validos():
    d = diario()
    d.loc[3, "potencia_combustivel_mw"] = float("nan")
    b = balanco_por_vazoes(d)
    assert b.intervalos_usados == 4
    assert b.intervalos_pulados == 2
    assert b.cobertura == pytest.approx(4 / 6)
    assert b.motivos_exclusao


@pytest.mark.parametrize("regime", ["parada", "partida", "transitorio", None])
def test_nao_integra_atraves_de_regime_inadequado(regime):
    d = diario()
    d.loc[3, "regime"] = regime
    b = balanco_por_vazoes(d)
    assert b.intervalos_usados == 4
    assert b.horas_totais == 6
    assert b.cobertura == pytest.approx(4 / 6)


def test_sem_estado_nao_inventa_vapor_seco():
    d = diario().drop(columns=["estado_vapor", "t_vapor_c"])
    with pytest.raises(AnaliseBloqueada):
        balanco_por_vazoes(d)
    with pytest.raises(AnaliseBloqueada):
        fluxo_entalpia_vapor(d)


def test_cenario_seco_exige_opt_in_e_publica_hipotese():
    d = diario().drop(columns=["estado_vapor", "t_vapor_c"])
    b = balanco_por_vazoes(d, assumir_saturado_seco=True)
    assert any("x = 1" in h for h in b.hipoteses)


def test_agua_precisa_pressao_propria():
    with pytest.raises(AnaliseBloqueada):
        balanco_por_vazoes(diario().drop(columns=["p_agua_referencia_bar_abs"]))


def test_pressao_agua_independente_altera_energia():
    a = diario()
    b = a.copy()
    b["p_agua_referencia_bar_abs"] = 10.0
    assert balanco_por_vazoes(a).energia_vapor_gj != balanco_por_vazoes(b).energia_vapor_gj


@pytest.mark.parametrize("coluna", ["vazao_vapor_t_h", "t_vapor_c", "potencia_combustivel_mw"])
def test_nao_publica_infinito(coluna):
    d = diario()
    d[coluna] = float("inf")
    with pytest.raises(AnaliseBloqueada):
        balanco_por_vazoes(d)


def test_nao_mistura_caldeiras():
    d = diario()
    d.loc[3, "caldeira_id"] = "C2"
    with pytest.raises(AnaliseBloqueada, match="caldeira"):
        balanco_por_vazoes(d)


def test_nao_descarta_duplicata_silenciosamente():
    d = diario()
    d.loc[3, "instante_observado"] = d.loc[2, "instante_observado"]
    with pytest.raises(AnaliseBloqueada, match="duplicad"):
        balanco_por_vazoes(d)


def test_troca_de_estado_nao_e_unida_por_trapezio():
    d = diario()
    d.loc[3:, "estado_vapor"] = "umido"
    d["titulo_vapor_frac"] = 0.98
    b = balanco_por_vazoes(d)
    assert b.intervalos_usados == 5
    assert b.intervalos_pulados == 1


def test_lado_vapor_continua_util_sem_combustivel():
    d = diario().drop(columns=["potencia_combustivel_mw"])
    assert fluxo_entalpia_vapor(d).n == len(d)
    with pytest.raises(AnaliseBloqueada):
        balanco_por_vazoes(d)


def test_purga_mapa_exige_pressao_da_agua():
    d = diario()
    d["massa_purga_kg"] = 10.0
    d["p_purga_bar_man"] = 9.0
    p = importar_pacote({"diario": d}, p_atm_bar=1.0)
    r = mapear_planta(p).rota("purga")
    assert r.situacao == "parcial"
    assert any("referência" in s for s in r.faltam)


@pytest.mark.parametrize(
    "extras",
    [
        {"steam_flow_t_h": [10.0, 10.0], "vazao_vapor_t_h": [11.0, 11.0]},
        {"steam_flow_t_h": [10.0, 10.0], "steam_flow_tph": [10.0, 10.0]},
    ],
)
def test_aliases_duplicados_bloqueiam_com_motivo(extras):
    d = diario(2).drop(columns=["vazao_vapor_t_h"])
    d = d.assign(**extras)
    imp = importar_diario(d, p_atm_bar=1.0)
    assert imp.bloqueada
    assert any(a.tipo == "aliases_ambiguos" for a in imp.avisos)
