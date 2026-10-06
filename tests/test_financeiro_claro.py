"""A tela financeira não confunde movimentação de estoque, custo e caixa."""

from copy import deepcopy

import pandas as pd
import pytest
from construtor_caso import Periodo, montar

from app.financeiro import movimentacao_periodo, resumo_compras, resumo_variacao
from euler.conta import explicar_conta


def conta(**alteracoes):
    return explicar_conta(
        **{
            "combustivel_ref_t": 1000.0,
            "vapor_ref_t": 4000.0,
            "combustivel_t": 1200.0,
            "vapor_t": 4400.0,
            "preco_ref_brl_t": 300.0,
            "preco_brl_t": 350.0,
            "incerteza_consumo_t_t": 0.001,
            **alteracoes,
        }
    )


def test_ponte_executiva_fecha_e_preserva_parcelas_nao_avaliadas():
    c = conta()
    original = deepcopy(c)
    r = resumo_variacao(c)
    assert r["disponivel"]
    assert {x["id"]: x["custo_brl"] for x in r["grupos"]} == pytest.approx(
        {"preco": 50_000, "producao_ajustes": 35_000, "nao_explicado": 35_000}
    )
    assert r["fechamento_brl"] == pytest.approx(0)
    assert r["variacao_brl"] == pytest.approx(120_000)
    assert r["nao_separados"] == ["Condição do vapor e da água", "Qualidade do combustível"]
    assert c == original


def test_queda_de_consumo_preserva_sinal_sem_promover_para_economia():
    r = resumo_variacao(conta(combustivel_t=900))
    assert r["variacao_brl"] == pytest.approx(15_000)
    assert r["grupos"][-1]["custo_brl"] == pytest.approx(-70_000)
    assert "economia" not in r


def test_sem_preco_de_referencia_nao_inventa_ponte():
    r = resumo_variacao(conta(preco_ref_brl_t=None))
    assert not r["disponivel"] and r["motivo"]
    assert r["grupos"] == []


def test_ponte_inconsistente_nao_aparece_como_explicacao_fechada():
    c = conta()
    c["variacao"]["variacao_brl"] += 1000
    r = resumo_variacao(c)
    assert not r["disponivel"]
    assert "reconciliar" in r["motivo"]


def recebimentos():
    return pd.DataFrame(
        {
            "data": pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"]),
            "tipo": ["recebimento"] * 4,
            "massa_kg": [1000.0, 2000.0, 3000.0, 4000.0],
            "preco_brl": [100.0, 400.0, 900.0, 1600.0],
            "fornecedor_id": ["A", "A", "B", "B"],
        }
    )


def test_compras_seguem_mesmas_fronteiras_do_motor_inicio_exclusivo_fim_inclusivo():
    r = resumo_compras(recebimentos(), "2026-01-01", "2026-01-03")
    assert r["lotes"] == 2
    assert r["recebido_t"] == 5
    assert r["valor_total_brl"] == 1300
    assert r["preco_medio_brl_t"] == 260
    assert r["pagamento_brl"] is None


@pytest.mark.parametrize("valor", [None, float("nan"), float("inf"), -1.0])
def test_preco_invalido_permite_so_subtotal_identificado(valor):
    df = recebimentos()
    df.loc[1, "preco_brl"] = valor
    r = resumo_compras(df, "2026-01-01", "2026-01-03")
    assert r["valor_total_brl"] is None
    assert r["valor_conhecido_brl"] == 900
    assert r["sem_preco"] == 1
    assert r["preco_medio_brl_t"] is None


def test_massa_ausente_nao_e_somada_como_zero():
    df = recebimentos()
    df.loc[1, "massa_kg"] = None
    r = resumo_compras(df, "2026-01-01", "2026-01-03")
    assert r["recebido_t"] is None
    assert r["massa_conhecida_t"] == 3
    assert r["sem_massa"] == 1
    assert r["preco_medio_brl_t"] is None


def test_massa_convertida_por_volume_preserva_origem_estimada():
    df = recebimentos().iloc[:1].copy()
    df["massa_kg"] = None
    df["massa_kg_calc"] = 1000.0
    df["massa_origem"] = "estimado"
    r = resumo_compras(df)
    assert r["recebido_t"] == 1
    assert r["massas_estimadas"] == 1
    assert r["preco_medio_brl_t"] == 100


def test_sem_registros_nao_afirma_ausencia_de_gasto_real():
    r = resumo_compras(None)
    assert r["valor_total_brl"] is None and r["recebido_t"] is None
    assert r["pagamento_brl"] is None
    vazio = resumo_compras(recebimentos(), "2027-01-01", "2027-02-01")
    assert vazio["lotes"] == 0
    assert vazio["valor_total_brl"] is None


def test_recebimento_com_preco_zero_explicito_continua_valido():
    df = recebimentos().iloc[:1].copy()
    df["preco_brl"] = 0.0
    r = resumo_compras(df)
    assert r["valor_total_brl"] == 0
    assert r["preco_medio_brl_t"] == 0


def test_movimentacao_reutiliza_consumo_e_preserva_pagamento_ausente():
    pacote, limites = montar([Periodo(11.773), Periodo(11.773)])
    r = movimentacao_periodo(pacote, *limites[1], preco_brl_t=350)
    assert r["consumido_t"] == pytest.approx(
        r["estoque_inicial_t"] + r["recebido_t"] - r["estoque_final_t"]
    )
    assert r["custo_atribuido_brl"] == pytest.approx(r["consumido_t"] * 350)
    assert r["despesa_ou_pagamento"] is None
