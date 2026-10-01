"""Testes golden da EULER.

SOMENTE LEITURA para agentes de programação: valores revisados pela equipe científica
(ver docs/fisica_para_revisao.md). Se falhar, o código está errado até prova em contrário.
Ajuste apenas os imports/assinaturas quando os módulos existirem (tickets T06, T07, T08).
"""
from pathlib import Path

import pandas as pd
import pytest

AQUI = Path(__file__).parent

indireto = pytest.importorskip("euler.indireto")
vapor = pytest.importorskip("euler.vapor")
combustivel = pytest.importorskip("euler.combustivel")


@pytest.mark.parametrize("linha", pd.read_csv(AQUI / "casos_referencia.csv").to_dict("records"))
def test_perda_gases_modo_referencia(linha):
    comp = {k: linha[k] for k in ("C", "H", "O", "N", "S")}
    res = indireto.perda_gases(
        t_gases_c=linha["t_gases_c"],
        o2_seco_pct=linha["o2_seco_pct"],
        umidade_bu_frac=linha["umidade_bu_frac"],
        t_ar_c=linha["t_ar_c"],
        composicao_seca=comp,
        pci_seco_mj_kg=linha["pci_seco_mj_kg"],
        modelo_cp=linha["modelo_cp"],
    )
    assert res.perda_pct == pytest.approx(linha["perda_gases_pct_esperada"], abs=linha["tolerancia_pp"])
    assert res.lambda_ar == pytest.approx(linha["lambda_esperado"], abs=1e-3)


@pytest.mark.parametrize("linha", pd.read_csv(AQUI / "vapor_referencia.csv").to_dict("records"))
def test_delta_h_vapor(linha):
    dh = vapor.delta_h_mj_kg(
        p_bar_abs=linha["p_vapor_bar_abs"],
        estado=linha["estado_vapor"],
        t_agua_alim_c=linha["t_agua_alim_c"],
    )
    assert dh == pytest.approx(linha["delta_h_mj_kg_esperado"], abs=linha["tolerancia"])


@pytest.mark.parametrize("linha", pd.read_csv(AQUI / "pci_umido_referencia.csv").to_dict("records"))
def test_pci_umido(linha):
    pci = combustivel.pci_umido(linha["pci_seco_mj_kg"], linha["umidade_bu_frac"])
    assert pci == pytest.approx(linha["pci_umido_mj_kg_esperado"], abs=linha["tolerancia"])
