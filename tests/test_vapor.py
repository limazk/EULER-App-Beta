import pytest

from euler import vapor
from euler.tipos import AnaliseBloqueada


def test_t_sat_10_bar():
    assert vapor.t_sat_c(10) == pytest.approx(179.89, abs=0.01)


def test_conversao_manometrica_para_absoluta():
    assert vapor.p_absoluta_bar(9.0, 1.01325) == pytest.approx(10.01325)


def test_p_atm_por_altitude():
    assert vapor.p_atm_por_altitude_bar(0) == pytest.approx(1.01325)
    # Atmosfera padrão a 1000 m: 89,88 kPa
    assert vapor.p_atm_por_altitude_bar(1000) == pytest.approx(0.8988, abs=1e-3)


def test_altitude_fora_da_faixa_bloqueia():
    with pytest.raises(AnaliseBloqueada):
        vapor.p_atm_por_altitude_bar(9000)


def test_pressao_manometrica_negativa_absurda_bloqueia():
    with pytest.raises(AnaliseBloqueada):
        vapor.p_absoluta_bar(-2.0, 1.01325)


def test_agua_de_alimentacao_acima_da_saturacao_bloqueia():
    with pytest.raises(AnaliseBloqueada, match="saturação"):
        vapor.h_agua_mj_kg(10, 185)


def test_vapor_umido_exige_titulo():
    with pytest.raises(AnaliseBloqueada, match="título"):
        vapor.h_vapor_mj_kg(10, "umido")


def test_vapor_umido_com_titulo_tem_entalpia_menor():
    seco = vapor.h_vapor_mj_kg(10, "saturado_seco")
    umido = vapor.h_vapor_mj_kg(10, "umido", titulo=0.95)
    assert umido < seco


def test_superaquecido_exige_temperatura_acima_da_saturacao():
    with pytest.raises(AnaliseBloqueada):
        vapor.h_vapor_mj_kg(10, "superaquecido", t_vapor_c=170)
    assert vapor.h_vapor_mj_kg(10, "superaquecido", t_vapor_c=250) > vapor.h_vapor_mj_kg(
        10, "saturado_seco"
    )


def test_estado_desconhecido_e_erro_de_programacao():
    with pytest.raises(ValueError):
        vapor.h_vapor_mj_kg(10, "gasoso")


def test_pressao_fora_do_dominio_bloqueia():
    with pytest.raises(AnaliseBloqueada):
        vapor.t_sat_c(250)
