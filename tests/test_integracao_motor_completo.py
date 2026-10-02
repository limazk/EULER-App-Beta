"""Regressões da integração: rotas novas preservam medições e bloqueios existentes."""

import pandas as pd
import pytest
from construtor_caso import Periodo, montar

from euler.baseline import ObservacaoCarga, ajustar_baseline_carga
from euler.direto import balanco_direto
from euler.investigacao import investigar
from euler.io.diario import importar_diario
from euler.periodos import resumir_periodo
from euler.tipos import AnaliseBloqueada


def caso():
    pacote, limites = montar([Periodo(11.773, dias=3)])
    diario = pacote.importacoes["diario"].dados
    bordas = diario.iloc[[0, -1]].copy()
    # Manter o fuso normalizado pelo importador ao acrescentar leituras artificiais.
    bordas["instante_observado"] = pd.DatetimeIndex(limites[0]).tz_convert(
        diario["instante_observado"].dt.tz
    )
    bordas["linha"] = [1001, 1002]
    bordas["totalizador_vapor_t"] = [
        float(diario.iloc[0]["totalizador_vapor_t"]) - 5,
        float(diario.iloc[-1]["totalizador_vapor_t"]) + 15,
    ]
    diario = pd.concat([diario, bordas], ignore_index=True).sort_values("instante_observado")
    pacote.importacoes["diario"].dados = diario
    return pacote, limites[0], diario


def test_alias_titulo_importado_preserva_original_e_informa_normalizacao():
    csv = b"caldeira_id,instante_observado,estado_vapor,titulo_vapor\nC,2026-01-01T00:00:00-03:00,umido,0.97\n"
    imp = importar_diario(csv)
    assert not imp.bloqueada
    assert imp.dados.iloc[0]["titulo_vapor_frac"] == pytest.approx(0.97)
    assert "titulo_vapor" in imp.original
    assert any(a.tipo == "alias_titulo_vapor" for a in imp.avisos)


def test_alias_titulo_conflitante_bloqueia_importacao():
    csv = b"caldeira_id,instante_observado,titulo_vapor,titulo_vapor_frac\nC,2026-01-01T00:00:00-03:00,0.97,0.99\n"
    assert importar_diario(csv).bloqueada


def test_purga_requer_pressao_propria_e_cobertura_completa():
    pacote, limites, diario = caso()
    diario["massa_purga_kg"] = 10.0
    r = resumir_periodo(pacote, *limites)
    assert balanco_direto(r).energia_purga_gj is None
    assert "purga" in r.bloqueios
    diario["p_purga_bar_abs"] = 10.0
    r = resumir_periodo(pacote, *limites)
    assert balanco_direto(r).energia_purga_gj.valor > 0
    diario.loc[diario.index[1], "massa_purga_kg"] = pd.NA
    r = resumir_periodo(pacote, *limites)
    assert balanco_direto(r).energia_purga_gj is None


def test_purga_usa_leitura_final_nao_inicial_do_intervalo():
    pacote, limites, diario = caso()
    ini, fim = limites
    bordas = diario[diario["instante_observado"].isin([ini, fim])]
    diario["massa_purga_kg"] = 0.0
    diario["p_purga_bar_abs"] = 10.0
    diario.loc[bordas.index[0], "massa_purga_kg"] = 9999.0
    diario.loc[bordas.index[-1], "massa_purga_kg"] = 100.0
    r = resumir_periodo(pacote, ini, fim)
    assert r.massa_purga_kg == pytest.approx(100.0)


def test_purga_sem_borda_inicial_nao_inclui_massa_de_antes_do_periodo():
    pacote, limites, diario = caso()
    diario["massa_purga_kg"] = 10.0
    diario["p_purga_bar_abs"] = 10.0
    pacote.importacoes["diario"].dados = diario[diario["instante_observado"] != limites[0]]
    r = resumir_periodo(pacote, *limites)
    assert r.energia_purga_intervalos_gj is None
    assert "purga" in r.bloqueios


def test_transitorio_nao_gera_titulo_de_melhora_por_gases():
    pacote, limites = montar(
        [Periodo(11.773, dias=3), Periodo(11.773, dias=3, outras_perdas_pp=20)]
    )
    diario = pacote.importacoes["diario"].dados
    diario.loc[diario.index[-1], "regime"] = "transitorio"
    j = investigar(pacote, *limites)
    for h in j["hipoteses"]:
        if h["id"] in ("temperatura_gases", "excesso_ar"):
            assert h["status"] == "nao_avaliavel"
            assert "transit" in h["porque"]
            assert h["titulo"] not in ("O₂ maior nos gases", "O₂ menor nos gases")


def preencher_eco(diario):
    for nome, valor in {
        "vazao_agua_alim_t_h": 20.0,
        "p_agua_eco_bar_abs": 10.0,
        "t_agua_eco_entrada_c": 80.0,
        "t_agua_eco_saida_c": 120.0,
        "t_gases_eco_entrada_c": 260.0,
        "t_gases_eco_saida_c": 170.0,
    }.items():
        diario[nome] = valor


@pytest.mark.parametrize("problema", ["ausencia", "estado_invalido", "transitorio"])
def test_ua_nao_mascara_dado_ausente_invalido_ou_regime(problema):
    pacote, limites, diario = caso()
    preencher_eco(diario)
    assert resumir_periodo(pacote, *limites).ua_economizador_mw_k > 0
    idx = diario.index[1]
    if problema == "ausencia":
        diario.loc[idx, "t_agua_eco_saida_c"] = pd.NA
    elif problema == "estado_invalido":
        diario.loc[idx, "t_agua_eco_saida_c"] = 400.0
    else:
        diario.loc[idx, "regime"] = "transitorio"
    r = resumir_periodo(pacote, *limites)
    assert r.ua_economizador_mw_k is None
    assert "ua_economizador" in r.bloqueios


def test_baseline_perfeito_nao_normaliza_ruido_numerico():
    modelo = ajustar_baseline_carga([ObservacaoCarga(x, 0.8 + 0.22 * x) for x in (5, 7, 9, 11)])
    assert modelo.sigma_predicao_t_h(9.0) is None


def test_baseline_recusa_previsao_negativa_dentro_do_dominio():
    modelo = ajustar_baseline_carga(
        [ObservacaoCarga(x, y) for x, y in [(1, 0.1), (2, 0.1), (3, 100)]]
    )
    with pytest.raises(AnaliseBloqueada):
        modelo.prever_combustivel_t_h(1)
