"""Contraprovas da revisão de 6402198: cobertura, estado e fronteira física."""

import pandas as pd
import pytest
from construtor_caso import Periodo, montar

from euler.direto import balanco_direto
from euler.investigacao import investigar
from euler.periodos import resumir_periodo


@pytest.mark.parametrize(
    ("estado", "coluna", "valor"),
    [("superaquecido", "t_vapor_c", 250.0), ("umido", "titulo_vapor_frac", 0.95)],
)
@pytest.mark.parametrize("cobertura", ["uma_leitura", "uma_lacuna"])
def test_medicao_parcial_do_estado_bloqueia_energia(estado, coluna, valor, cobertura):
    pacote, limites = montar([Periodo(11.773, dias=3)])
    diario = pacote.importacoes["diario"].dados
    diario["estado_vapor"] = estado
    diario[coluna] = valor
    if cobertura == "uma_leitura":
        diario.loc[diario.index[1:], coluna] = float("nan")
    else:
        diario.loc[diario.index[10], coluna] = float("nan")
    resumo = resumir_periodo(pacote, *limites[0])
    balanco = balanco_direto(resumo)
    assert "estado_vapor" in resumo.bloqueios
    assert balanco.energia_util_gj is None
    assert balanco.eficiencia is None
    assert balanco.consumo_t_por_t is not None
    assert "ausente" in resumo.bloqueios["estado_vapor"].motivo


@pytest.mark.parametrize(
    ("estado", "coluna", "valores"),
    [
        ("superaquecido", "t_vapor_c", [100.0, 300.0]),
        ("umido", "titulo_vapor_frac", [0.6, 1.2]),
    ],
)
def test_media_nao_esconde_leitura_fisicamente_invalida(estado, coluna, valores):
    pacote, limites = montar([Periodo(11.773, dias=3)])
    diario = pacote.importacoes["diario"].dados
    diario["estado_vapor"] = estado
    diario[coluna] = [valores[i % 2] for i in range(len(diario))]
    resumo = resumir_periodo(pacote, *limites[0])
    balanco = balanco_direto(resumo)
    assert "estado_vapor" in resumo.bloqueios
    assert resumo.energia_util_intervalos_gj is None
    assert balanco.eficiencia is None
    assert "linha" in resumo.bloqueios["estado_vapor"].motivo


@pytest.mark.parametrize("coluna", ["p_vapor_bar_abs", "t_agua_alim_c", "t_vapor_c"])
def test_estado_medido_exige_condicoes_conjuntas_finitas(coluna):
    pacote, limites = montar([Periodo(11.773, dias=3)])
    diario = pacote.importacoes["diario"].dados
    diario["estado_vapor"] = "superaquecido"
    diario["t_vapor_c"] = 250.0
    diario.loc[diario.index[10], coluna] = float("inf")
    assert balanco_direto(resumir_periodo(pacote, *limites[0])).eficiencia is None


def test_leitura_na_borda_usada_pelo_totalizador_tambem_e_validada():
    pacote, limites = montar([Periodo(11.773, dias=3)])
    diario = pacote.importacoes["diario"].dados
    diario["estado_vapor"] = "superaquecido"
    diario["t_vapor_c"] = 250.0
    borda = diario.iloc[-1].copy()
    borda["instante_observado"] = limites[0][1]
    borda["totalizador_vapor_t"] += 5
    borda["t_vapor_c"] = float("nan")
    borda["linha"] += 1
    pacote.importacoes["diario"].dados = pd.concat([diario, borda.to_frame().T], ignore_index=True)
    resumo = resumir_periodo(pacote, *limites[0])
    assert balanco_direto(resumo).eficiencia is None
    assert "estado_vapor" in resumo.bloqueios


@pytest.mark.parametrize("ponto_comp", ["POS-ECONOMIZADOR", "SAIDA-CALDEIRA", None])
def test_comparacao_exige_mesmo_ponto_de_gases(ponto_comp):
    pacote, limites = montar([Periodo(11.773, dias=3), Periodo(11.773, dias=3)])
    diario = pacote.importacoes["diario"].dados
    referencia = diario["instante_observado"] < limites[0][1]
    diario.loc[referencia, "ponto_gases_id"] = "SAIDA-CALDEIRA"
    diario.loc[~referencia, "ponto_gases_id"] = ponto_comp
    diario.loc[referencia, "t_gases_c"] = 240.0
    diario.loc[~referencia, "t_gases_c"] = 150.0
    resultado = investigar(pacote, *limites)
    for periodo in resultado["periodos"].values():
        assert periodo["perda_gases"] is not None
        assert periodo["consumo_t_por_t"] is not None
    hip = next(h for h in resultado["hipoteses"] if h["id"] == "temperatura_gases")
    if ponto_comp == "SAIDA-CALDEIRA":
        assert hip["efeito"]["perda_gases_pp"] is not None
        assert hip["avaliacao"]["mudanca_detectavel"] == "sim"
    else:
        assert hip["efeito"]["perda_gases_pp"] is None
        assert hip["avaliacao"]["mudanca_detectavel"] is None
        assert "pontos" in hip["porque"].lower()
        assert "Menos calor" not in hip["titulo"]
        assert any("ponto" in item.lower() for item in resultado["o_que_falta"])
        assert resultado["o_que_mudou"]["bloqueio_comparacao_gases"]
        o2 = next(h for h in resultado["hipoteses"] if h["id"] == "excesso_ar")
        assert o2["efeito"]["perda_gases_pp"] is None
        assert o2["avaliacao"]["mudanca_detectavel"] is None


def test_investigacao_explica_medicao_do_vapor_ausente():
    pacote, limites = montar([Periodo(11.773, dias=3), Periodo(11.773, dias=3)])
    diario = pacote.importacoes["diario"].dados
    diario["estado_vapor"] = "superaquecido"
    diario["t_vapor_c"] = 250.0
    diario.loc[diario.index[-1], "t_vapor_c"] = float("nan")
    resultado = investigar(pacote, *limites)
    hip = next(h for h in resultado["hipoteses"] if h["id"] == "condicao_vapor")
    assert "temperatura do vapor" in hip["porque"]
    assert "ausente" in hip["porque"]
