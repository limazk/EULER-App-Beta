"""Pressões de dois pontos físicos não podem ser intercambiadas no cálculo da purga."""

import pandas as pd
import pytest
from test_integracao_motor_completo import caso

from euler.io.diario import importar_diario
from euler.periodos import resumir_periodo
from euler.purga import energia_purga_gj
from euler.tipos import AnaliseBloqueada
from euler.vapor import h_agua_mj_kg, h_liquido_saturado_mj_kg


def test_pressao_da_agua_altera_so_a_entalpia_de_referencia():
    q = energia_purga_gj(
        massa_purga_kg=1000,
        p_purga_bar_abs=10,
        p_agua_referencia_bar_abs=2,
        t_agua_referencia_c=80,
    )
    esperado = h_liquido_saturado_mj_kg(10) - h_agua_mj_kg(2, 80)
    assert q == pytest.approx(esperado)
    assert q != pytest.approx(h_liquido_saturado_mj_kg(10) - h_agua_mj_kg(10, 80))


@pytest.mark.parametrize("pressao", [float("nan"), float("inf"), 0.0])
def test_pressao_de_referencia_invalida_bloqueia(pressao):
    with pytest.raises(AnaliseBloqueada):
        energia_purga_gj(
            massa_purga_kg=1000,
            p_purga_bar_abs=10,
            p_agua_referencia_bar_abs=pressao,
            t_agua_referencia_c=80,
        )


def test_periodo_exige_pressao_da_agua_em_cada_massa_positiva():
    pacote, limites, diario = caso()
    diario["massa_purga_kg"] = 10.0
    diario["p_purga_bar_abs"] = 10.0
    r = resumir_periodo(pacote, *limites)
    assert r.energia_purga_intervalos_gj is None
    assert "purga" in r.bloqueios
    diario["p_agua_referencia_bar_abs"] = 2.0
    r = resumir_periodo(pacote, *limites)
    assert r.energia_purga_intervalos_gj > 0
    diario.loc[diario.index[1], "p_agua_referencia_bar_abs"] = pd.NA
    r = resumir_periodo(pacote, *limites)
    assert r.energia_purga_intervalos_gj is None
    assert "purga" in r.bloqueios


def test_importador_converte_pressao_da_agua_sem_emprestar_outro_ponto():
    csv = b"caldeira_id,instante_observado,p_purga_bar_man,p_agua_referencia_bar_man\nC,2026-01-01T00:00:00-03:00,9,1\n"
    imp = importar_diario(csv, p_atm_bar=0.9)
    assert imp.dados.iloc[0]["p_purga_bar_abs"] == pytest.approx(9.9)
    assert imp.dados.iloc[0]["p_agua_referencia_bar_abs"] == pytest.approx(1.9)
    assert importar_diario(csv).dados["p_agua_referencia_bar_abs"].isna().all()
