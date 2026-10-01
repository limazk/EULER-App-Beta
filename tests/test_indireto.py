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


def test_modo_variavel_e_experimental_e_avisa():
    # Fase R: cp(T) pelos polinômios NASA, experimental até aprovação do revisor (D40)
    r = calcular(modelo_cp="variavel")
    assert any("experimental" in a for a in r.avisos)


@pytest.mark.parametrize("t_g, o2, w", [(180, 8, 0.4), (150, 8, 0.4), (250, 8, 0.4), (180, 4, 0.4),
                                        (180, 10, 0.4), (180, 8, 0.3), (180, 8, 0.5)])  # fmt: skip
def test_modo_variavel_difere_do_constante_menos_de_meio_ponto_t07(t_g, o2, w):
    """Critério de aceite do T07 (até o REV aprovar outro): diferença < 0,5 p.p. em G01–G10."""
    const = calcular(t_gases_c=t_g, o2_seco_pct=o2, umidade_bu_frac=w).perda_pct
    var = calcular(t_gases_c=t_g, o2_seco_pct=o2, umidade_bu_frac=w, modelo_cp="variavel").perda_pct
    assert abs(var - const) < 0.5
    assert var < const  # cp constante de 1,05 kJ/kg·K superestima os gases secos


def test_umidade_do_ar_aumenta_a_perda_e_padrao_nao_muda_o_golden():
    base = calcular()
    com_ar = calcular(umidade_ar_kg_kg=0.0119)
    assert base.perda_pct == pytest.approx(11.773, abs=0.01)
    assert 0.15 < com_ar.perda_pct - base.perda_pct < 0.25


def test_perda_por_co():
    r = calcular()
    assert indireto.perda_co_pct(0, r, 18.5, 0.40) == 0
    # 200 ppm ≈ 0,11% do PCI (ordem de grandeza conferida à mão em docs/matriz_validacao_fisica.md)
    assert indireto.perda_co_pct(200, r, 18.5, 0.40) == pytest.approx(0.111, abs=0.002)


def test_o2_umido_convertido_para_seco_e_maior():
    seco = indireto.o2_seco_equivalente(7.0, REF, 0.40)
    assert 8.0 < seco < 8.8


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
