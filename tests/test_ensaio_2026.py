"""Fontes públicas: cálculo condicional, rastreabilidade e abstenção por falta de dados."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from ensaio_publico import comparar_custo_publicado, executar


def test_preco_publicado_separa_diferenca_bruta_de_mesma_producao():
    r = comparar_custo_publicado()
    assert r["antes_brl_t"] == pytest.approx(69.67250188457996)
    assert r["depois_brl_t"] == pytest.approx(66.23980621719823)
    assert r["reducao_bruta_brl_h"] == pytest.approx(114.4)
    # Mesma produção de 2011: compara intensidades, sem confundir com caixa observado.
    assert r["diferenca_normalizada_brl_h"] == pytest.approx((7562 * 123850 / 119390 - 7458) * 1.1)
    assert r["comparacao"]["detectavel"] is None
    assert r["economia_comprovada_brl"] is None


def test_cenario_de_preco_nao_substitui_preco_historico():
    historico = comparar_custo_publicado()
    cenario = comparar_custo_publicado(preco_brl_kg=2.2)
    assert cenario["base_preco"] == "cenario_usuario"
    assert cenario["fonte"]["preco_publicado_brl_kg"] == 1.1
    assert cenario["diferenca_brl_t"] == pytest.approx(2 * historico["diferenca_brl_t"])
    assert cenario["reducao_pct"] == pytest.approx(historico["reducao_pct"])
    for preco in (-1, float("nan"), float("inf")):
        with pytest.raises(ValueError):
            comparar_custo_publicado(preco_brl_kg=preco)


@pytest.fixture(scope="module")
def resultado():
    return executar()


def test_importacao_real_preserva_temperaturas_e_origem(resultado):
    z = resultado["importacao"]
    assert z["linhas"] == 7200
    assert z["origens"] == ["publico"]
    assert z["valores_preservados"]
    assert not z["sintetico"]
    assert z["eficiencia"] == "bloqueada"
    assert z["saude"] == "nao_da_para_dizer"
    assert z["energia_vapor"] == "bloqueada"


def test_entalpias_conferem_com_implementacao_independente(resultado):
    assert len(resultado["estados"]) == 15
    # Guarda numérica entre formulações, não tolerância de medição industrial.
    assert max(abs(e["delta_heos_pct"]) for e in resultado["estados"]) < 0.05
    assert max(abs(e["delta_fonte_pct"]) for e in resultado["estados"]) > 0.9


def test_cargas_nao_viram_tempo_e_diferenca_nao_vira_perda(resultado):
    assert resultado["comparacao"]["detectavel"] is None
    assert resultado["perda_financeira_brl"] is None
    assert resultado["economia_comprovada_brl"] is None
    assert all(c["fluxo_entalpia_mw"] > c["potencia_vapor_mw"] > 0 for c in resultado["cargas"])
    assert [c["vapor_t_h"] for c in resultado["cargas"]] == pytest.approx(
        [96.2316, 125.9064, 136.026]
    )


def test_painel_publico_abre_e_carrega_dados_sem_herdar_demo():
    from test_app import abrir_com_demo

    at = abrir_com_demo("dados_publicos.py")
    assert not at.exception, at.exception
    at.button(key="carregar_zhejiang").click().run(timeout=60)
    assert not at.exception, at.exception
    assert at.session_state["altitude_m"] is None
    assert at.session_state["dados_sinteticos"] is False
    assert len(at.session_state["arquivos"]) == 1
    at.switch_page("paginas/limites.py").run(timeout=60)
    assert not at.exception, at.exception
