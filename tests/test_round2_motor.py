"""Segunda rodada do motor físico: regime, baseline por carga, purga e transferência."""

import pytest
from construtor_caso import Periodo, montar

from euler.baseline import ObservacaoCarga, ajustar_baseline_carga, residual_normalizado
from euler.periodos import resumir_periodo
from euler.purga import energia_purga_gj
from euler.tipos import AnaliseBloqueada
from euler.transferencia import ua_economizador


G01 = 11.773


def test_transitorio_nao_serve_de_referencia_estacionaria():
    pacote, limites = montar([Periodo(G01, dias=3)])
    diario = pacote.importacoes["diario"].dados
    ini, fim = limites[0]
    idx = diario.index[
        (diario["instante_observado"] >= ini) & (diario["instante_observado"] < fim)
    ]
    diario.loc[idx[0], "regime"] = "transitorio"
    r = resumir_periodo(pacote, ini, fim)
    assert "transitorio" in r.regimes_presentes
    assert r.apto_baseline_carga is False


def test_periodo_exclusivamente_estavel_e_elegivel_para_baseline():
    pacote, limites = montar([Periodo(G01, dias=3)])
    r = resumir_periodo(pacote, *limites[0])
    assert r.regimes_presentes == ("estavel",)
    assert r.apto_baseline_carga is True


def test_baseline_recupera_reta_e_recusa_extrapolacao():
    obs = [
        ObservacaoCarga(carga_t_h=x, combustivel_t_h=0.8 + 0.22 * x)
        for x in (5.0, 7.0, 9.0, 11.0, 13.0)
    ]
    modelo = ajustar_baseline_carga(obs)
    assert modelo.intercepto_t_h == pytest.approx(0.8, abs=1e-10)
    assert modelo.inclinacao_t_t == pytest.approx(0.22, abs=1e-10)
    assert modelo.prever_combustivel_t_h(10.0) == pytest.approx(3.0)
    with pytest.raises(AnaliseBloqueada):
        modelo.prever_combustivel_t_h(20.0)


def test_residual_normalizado_so_sai_com_ruido_estimavel():
    perfeito = [
        ObservacaoCarga(carga_t_h=x, combustivel_t_h=0.8 + 0.22 * x)
        for x in (5.0, 7.0, 9.0, 11.0)
    ]
    assert residual_normalizado(
        ajustar_baseline_carga(perfeito), carga_t_h=9.0, combustivel_t_h=3.2
    ) is None

    realista = [
        ObservacaoCarga(5.0, 1.90),
        ObservacaoCarga(7.0, 2.36),
        ObservacaoCarga(9.0, 2.75),
        ObservacaoCarga(11.0, 3.27),
        ObservacaoCarga(13.0, 3.62),
    ]
    z = residual_normalizado(
        ajustar_baseline_carga(realista), carga_t_h=9.0, combustivel_t_h=3.2
    )
    assert z is not None and z > 0


def test_purga_quantificada_exige_massa_e_usa_entalpia_do_liquido():
    q = energia_purga_gj(
        massa_purga_kg=1000.0,
        p_bar_abs=10.0,
        t_agua_referencia_c=80.0,
    )
    assert 0 < q < 1.0
    with pytest.raises(AnaliseBloqueada):
        energia_purga_gj(
            massa_purga_kg=-1.0,
            p_bar_abs=10.0,
            t_agua_referencia_c=80.0,
        )


def test_ua_economizador_e_indicador_e_bloqueia_cruzamento_termico():
    r = ua_economizador(
        vazao_agua_t_h=20.0,
        p_agua_bar_abs=10.0,
        t_agua_entrada_c=80.0,
        t_agua_saida_c=120.0,
        t_gases_entrada_c=260.0,
        t_gases_saida_c=170.0,
    )
    assert r.q_mw > 0
    assert r.ua_mw_k > 0
    assert r.delta_t_lm_k > 0

    with pytest.raises(AnaliseBloqueada):
        ua_economizador(
            vazao_agua_t_h=20.0,
            p_agua_bar_abs=10.0,
            t_agua_entrada_c=80.0,
            t_agua_saida_c=190.0,
            t_gases_entrada_c=180.0,
            t_gases_saida_c=170.0,
        )
