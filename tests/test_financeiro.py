"""Guardas financeiras: ausência não vira zero nem economia comprovada."""

import pytest

from app.financeiro import resumo_financeiro, simular_recuperacao


def caso(valor=200.0):
    return {
        "periodos": {
            "comparacao": {
                "combustivel_kg": {"valor": 12000.0},
                "preco_brl_t": 100.0,
            }
        },
        "valor_em_jogo": None if valor is None else {"valor_brl": valor},
    }


def test_unidades_e_reconciliacao():
    r = resumo_financeiro(caso())
    assert r == {"consumido_brl": 1200.0, "referencia_brl": 1000.0, "diferenca_brl": 200.0}
    assert simular_recuperacao(r["diferenca_brl"], 25) == 50.0


def test_sem_detectabilidade_nao_inventa_oportunidade():
    r = resumo_financeiro(caso(None))
    assert r["consumido_brl"] == 1200.0
    assert r["diferenca_brl"] is None
    assert r["referencia_brl"] is None
    assert simular_recuperacao(None, 100) is None


@pytest.mark.parametrize("preco", [None, float("nan"), float("inf"), -1])
def test_preco_invalido_bloqueia_estimativa(preco):
    j = caso(None)
    j["periodos"]["comparacao"]["preco_brl_t"] = preco
    assert resumo_financeiro(j)["consumido_brl"] is None


def test_zero_explicito_e_limites_do_cenario():
    assert simular_recuperacao(200, 0) == 0
    assert simular_recuperacao(200, 100) == 200
    with pytest.raises(ValueError):
        simular_recuperacao(200, 101)
