import pytest

from euler import indireto
from euler.tipos import AnaliseBloqueada

REF = indireto.COMPOSICAO_REFERENCIA


BASE = {
    "t_gases_c": 180,
    "o2_seco_pct": 8,
    "umidade_bu_frac": 0.40,
    "t_ar_c": 25,
    "composicao_seca": REF,
    "pci_seco_mj_kg": 18.5,
    "modelo_cp": "constante",
}


def calcular(**mudancas):
    return indireto.perda_gases(**{**BASE, **mudancas})


def test_oxigenio_estequiometrico_e1():
    # a = C/12 + H/4 + S/32 − O/32
    esperado = 0.50 / 12 + 0.06 / 4 + 0.0005 / 32 - 0.43 / 32
    assert indireto.oxigenio_estequiometrico(REF) == pytest.approx(esperado)


def test_ar_sem_excesso_quando_o2_zero():
    assert indireto.razao_ar(0, REF) == pytest.approx(1.0)


def test_resultado_traz_componentes_intermediarios():
    r = calcular()
    assert r.m_gases_secos_kg_kg > 0
    assert r.m_h2o_kg_kg == pytest.approx(9 * 0.06 + 0.40 / 0.60)
    assert 40 < r.t_orvalho_c < 70
    assert r.avisos == ()


def test_sensibilidade_temperatura_aprox_0076_pp_por_grau():
    d = calcular(t_gases_c=210).perda_pct - calcular(t_gases_c=180).perda_pct
    assert d / 30 == pytest.approx(0.076, abs=0.001)


@pytest.mark.parametrize("o2", [21, 25, -1])
def test_o2_impossivel_bloqueia(o2):
    with pytest.raises(AnaliseBloqueada):
        calcular(o2_seco_pct=o2)


def test_gases_abaixo_do_orvalho_bloqueia_e7():
    with pytest.raises(AnaliseBloqueada, match="orvalho"):
        calcular(t_gases_c=45, t_ar_c=20, umidade_bu_frac=0.55)


def test_gases_mais_frios_que_o_ar_bloqueia():
    with pytest.raises(AnaliseBloqueada):
        calcular(t_gases_c=24)


def test_modo_variavel_bloqueado_ate_revisor_definir_fonte():
    with pytest.raises(AnaliseBloqueada, match="revisor"):
        calcular(modelo_cp="variavel")


def test_modelo_cp_desconhecido_e_erro_de_programacao():
    with pytest.raises(ValueError):
        calcular(modelo_cp="outro")


def test_composicao_incompleta_bloqueia():
    comp = {k: v for k, v in REF.items() if k != "H"}
    with pytest.raises(AnaliseBloqueada, match="H"):
        calcular(composicao_seca=comp)


def test_composicao_somando_mais_que_um_bloqueia():
    with pytest.raises(AnaliseBloqueada):
        calcular(composicao_seca={**REF, "C": 0.9})


def test_co_alto_gera_aviso_sem_bloquear():
    r = calcular(co_ppm=500)
    assert any("CO" in a for a in r.avisos)


def test_alerta_plausibilidade_sem_aproximacao_definida_nao_alerta():
    assert indireto.alerta_temperatura_implausivel(150, 10, aproximacao_minima_c=None) is None


def test_alerta_plausibilidade_com_aproximacao():
    msg = indireto.alerta_temperatura_implausivel(170, 10, aproximacao_minima_c=20)
    assert msg and "saturação" in msg
    assert indireto.alerta_temperatura_implausivel(220, 10, aproximacao_minima_c=20) is None


def test_alerta_plausibilidade_nao_se_aplica_com_recuperador():
    assert (
        indireto.alerta_temperatura_implausivel(
            150, 10, aproximacao_minima_c=20, tem_recuperador=True
        )
        is None
    )
