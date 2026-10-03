"""Fontes públicas: cálculo condicional, rastreabilidade e abstenção por falta de dados."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from ensaio_publico import executar


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
