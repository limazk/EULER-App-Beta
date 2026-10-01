"""Investigação (T13): casos A, B, C, contraexemplo da purga e abstenção sem vapor."""

import json

import pytest
from construtor_caso import Periodo, montar

from euler.investigacao import investigar

# perdas nos gases da tabela golden (tests/golden/casos_referencia.csv)
G01, G08, G09, G11, G12 = 11.773, 10.979, 12.307, 11.049, 19.047


def rodar(*periodos):
    pacote, limites = montar(list(periodos))
    return investigar(pacote, limites[0], limites[1])


def status(j):
    return {h["id"]: h["status"] for h in j["hipoteses"]}


@pytest.fixture(scope="module")
def caso_a():
    # Caso A (golden G11 → G12): gases de 180 °C para 292,2 °C, umidade 31,04%
    return rodar(
        Periodo(G11, t_gases_c=180, umidade=0.3104),
        Periodo(G12, t_gases_c=292.2, umidade=0.3104),
    )


def test_caso_a_temperatura_dos_gases_sustentada(caso_a):
    s = status(caso_a)
    assert s["temperatura_gases"] == "sustentada"
    assert s["excesso_ar"] == "descartada"
    assert s["umidade_combustivel"] == "descartada"
    assert s["perdas_nao_medidas"] == "descartada"
    assert caso_a["conclusao"]["abstencao"] is False
    h = next(h for h in caso_a["hipoteses"] if h["id"] == "temperatura_gases")
    assert h["efeito"]["perda_gases_pp"] == pytest.approx(G12 - G11, abs=0.1)


def test_caso_a_consumo_subiu_e_valor_em_jogo_tem_base(caso_a):
    assert caso_a["o_que_mudou"]["consumo_especifico"]["detectavel"] is True
    assert caso_a["o_que_mudou"]["frase"].startswith(
        "O consumo de combustível por tonelada de vapor subiu"
    )
    valor = caso_a["valor_em_jogo"]
    assert valor is not None and valor["valor_brl"] > 0
    assert "Não é promessa de economia" in valor["base"]
    assert caso_a["proxima_verificacao"]["separa"] == ["temperatura_gases"]


def test_caso_b_umidade_sustentada():
    j = rodar(Periodo(G08, umidade=0.30), Periodo(G09, umidade=0.45))
    s = status(j)
    assert s["umidade_combustivel"] == "sustentada"
    assert s["temperatura_gases"] == "descartada"
    assert s["perdas_nao_medidas"] == "descartada"
    assert j["conclusao"]["abstencao"] is False


def test_caso_c_so_preco_mudou():
    j = rodar(Periodo(G01, preco_brl_t=180), Periodo(G01, preco_brl_t=220))
    assert j["o_que_mudou"]["consumo_especifico"]["detectavel"] is False
    assert j["conclusao"]["abstencao"] is True
    custo = j["o_que_mudou"]["custo_vapor"]
    # ln(220/180) = 20,07%; a umidade varia um pouco entre lotes e muda o R$/GJ
    assert custo["efeito_preco_pct"] == pytest.approx(20.07, abs=0.4)
    assert abs(custo["efeito_intensidade_pct"]) < 1
    assert "não é perda de eficiência" in custo["frase"]
    assert j["valor_em_jogo"] is None and j["valor_em_jogo_motivo"]


def test_contraexemplo_purga_nao_medida_gera_abstencao():
    j = rodar(
        Periodo(G01, outras_perdas_pp=8, registrar_purgas=False),
        Periodo(G01, outras_perdas_pp=13, registrar_purgas=False),
    )
    s = status(j)
    assert s["perdas_nao_medidas"] == "possivel"
    assert s["temperatura_gases"] == "descartada"
    assert j["conclusao"]["abstencao"] is True
    assert "não é explicada" in j["conclusao"]["motivo"]
    assert any("purgas" in f for f in j["o_que_falta"])
    assert "purgas" in j["proxima_verificacao"]["acao"]


def test_sem_vapor_no_periodo_abstem_e_diz_o_que_falta():
    j = rodar(
        Periodo(G11, t_gases_c=180, umidade=0.3104),
        Periodo(G12, t_gases_c=292.2, umidade=0.3104, totalizador=False),
    )
    assert j["o_que_mudou"]["frase"].startswith("Não dá para saber se o consumo")
    assert j["conclusao"]["abstencao"] is True
    # o caminho indireto ainda sustenta a temperatura dos gases
    assert status(j)["temperatura_gases"] == "sustentada"
    assert status(j)["perdas_nao_medidas"] == "nao_avaliavel"
    assert "totalizador de vapor" in j["proxima_verificacao"]["acao"]
    assert j["valor_em_jogo"] is None


def test_independencia_dos_caminhos_e12(caso_a):
    ind = caso_a["independencia"]
    assert "umidade das amostras" in ind["compartilham"]
    assert ind["independentes"] is False


def test_json_serializavel_e_sem_comando_operacional(caso_a):
    texto = json.dumps(caso_a, ensure_ascii=False).lower()
    proibidos = (
        "abra ",
        "abrir a válvula",
        "feche ",
        "ajuste o",
        "ajustar o queimador",
        "aumente",
        "reduza",
        "mude o setpoint",
        "desligue",
        "ligue ",
    )
    assert not any(p in texto for p in proibidos)


def test_mudanca_pequena_demais_nao_explica():
    # água de alimentação 1 °C mais fria: detectável estatisticamente, mas irrelevante
    j = rodar(
        Periodo(G11, t_gases_c=180, umidade=0.3104),
        Periodo(G12, t_gases_c=292.2, umidade=0.3104, t_agua_alim_c=79),
    )
    assert status(j)["condicao_vapor"] == "descartada"
