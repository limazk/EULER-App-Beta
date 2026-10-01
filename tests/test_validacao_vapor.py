"""Verificação independente: água e vapor (Fase R, matriz V-A*).

Valores de referência: tabelas de verificação da IAPWS R7-97(2012) "Revised Release on the
IAPWS Industrial Formulation 1997 for the Thermodynamic Properties of Water and Steam":
Tabela 5 (região 1), Tabela 15 (região 2), Tabela 36 (temperatura de saturação). O site
iapws.org estava bloqueado na sessão; os valores foram conferidos em duas implementações
independentes (pacote `iapws` e CoolProp, backend IF97), com 9 algarismos iguais.
Tolerâncias: 1e-6 MJ/kg e 1e-5 K — muito acima do arredondamento das tabelas (9 algarismos)
e muito abaixo de qualquer efeito prático.
"""

import pytest

from euler import vapor

# (T K, p MPa, h kJ/kg) — IAPWS R7-97(2012), Tabelas 5 e 15
TABELA_5_15 = [
    (300, 3, 115.331273, "agua"),
    (500, 3, 975.542239, "agua"),
    (300, 0.0035, 2549.91145, "vapor"),
    (700, 0.0035, 3335.68375, "vapor"),
]
# (p MPa, T_sat K) — Tabela 36
TABELA_36 = [(0.1, 372.755919), (1, 453.035632), (10, 584.149488)]


@pytest.mark.parametrize(("t_k", "p_mpa", "h_kj", "fase"), TABELA_5_15)
def test_entalpias_iapws_if97_tabelas_5_e_15(t_k, p_mpa, h_kj, fase):
    p_bar, t_c = p_mpa * 10, t_k - 273.15
    if fase == "agua":
        h = vapor.h_agua_mj_kg(p_bar, t_c)
    else:
        h = vapor.h_vapor_mj_kg(p_bar, "superaquecido", t_vapor_c=t_c)
    assert h == pytest.approx(h_kj / 1000, abs=1e-6)


@pytest.mark.parametrize(("p_mpa", "t_sat_k"), TABELA_36)
def test_saturacao_iapws_if97_tabela_36(p_mpa, t_sat_k):
    assert vapor.t_sat_c(p_mpa * 10) == pytest.approx(t_sat_k - 273.15, abs=1e-5)


def test_conversao_de_unidades_bar_mpa_e_kj_mj():
    # 10 bar abs = 1 MPa; Tabela 36: T_sat(1 MPa) = 453,035632 K
    assert vapor.t_sat_c(10) + 273.15 == pytest.approx(453.035632, abs=1e-5)


def test_golden_v01_contra_iapws95_independente():
    """Δh do golden V01 contra a formulação científica IAPWS-95 (CoolProp, HEOS).

    A IF97 é uma aproximação da IAPWS-95; a diferença observada aqui é 0,075 kJ/kg. A
    tolerância de 0,1 kJ/kg (0,004% de Δh) foi escolhida depois de ver essa diferença e se
    justifica pelo efeito prático: é ~200 vezes menor que o efeito de um título x = 0,99 (≈ 20 kJ/kg).
    Conferir com os limites de consistência IF97 × IAPWS-95 da IAPWS R7-97(2012)."""
    coolprop = pytest.importorskip("CoolProp.CoolProp")
    p = 1.0e6
    h_s = coolprop.PropsSI("H", "P", p, "Q", 1, "HEOS::Water") / 1e6
    h_a = coolprop.PropsSI("H", "P", p, "T", 353.15, "HEOS::Water") / 1e6
    assert vapor.delta_h_mj_kg(10, "saturado_seco", 80) == pytest.approx(h_s - h_a, abs=1e-4)


def test_titulo_do_vapor_a_mao():
    """x = 0,98 a 10 bar abs: h = h_f + x·h_fg (IF97, tabela de saturação)."""
    h_f = vapor.h_vapor_mj_kg(10, "umido", titulo=0.0)
    h_g = vapor.h_vapor_mj_kg(10, "saturado_seco")
    assert vapor.h_vapor_mj_kg(10, "umido", titulo=0.98) == pytest.approx(h_f + 0.98 * (h_g - h_f))
