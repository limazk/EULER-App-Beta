"""Auditoria de snapshot publicado: discrepância não é validação de eficiência."""

import json
from pathlib import Path

import pytest

from euler.vapor import h_agua_mj_kg, h_vapor_mj_kg, t_sat_c

WONJI = Path(__file__).resolve().parents[1] / "validation/public/wonji_bagasse_snapshot.json"


def test_if97_confere_com_snapshot_real_de_biomassa_da_wonji():
    """Segundo caso real, agora em biomassa e vapor superaquecido.

    O snapshot vem de valores do process control board transcritos na dissertação da
    Addis Ababa University. A EULER confere apenas propriedades termodinâmicas e não
    transforma o fuel rate derivado do trabalho em medição real.
    """
    caso = json.loads(WONJI.read_text(encoding="utf-8"))
    fw = caso["published_operating_points"]["feedwater_to_boiler"]
    steam = caso["published_operating_points"]["steam_to_cest_turbine"]

    assert steam["state"] == "superheated"
    assert steam["temperature_c"] > t_sat_c(steam["pressure_bar_abs"])

    h_steam = h_vapor_mj_kg(
        steam["pressure_bar_abs"],
        "superaquecido",
        t_vapor_c=steam["temperature_c"],
    )
    h_fw = h_agua_mj_kg(fw["pressure_bar_abs"], fw["temperature_c"])

    # A água concorda em ordem de engenharia, mas o valor publicado para o vapor
    # diverge pouco mais de 2% da IF97 nesta interpretação de P/T. Isso é tratado como
    # discrepância externa a investigar, não como motivo para alargar a tolerância.
    assert h_fw * 1000 == pytest.approx(fw["enthalpy_kj_kg_published"], rel=0.02)
    erro_rel_steam = (
        abs(h_steam * 1000 - steam["enthalpy_kj_kg_published"]) / steam["enthalpy_kj_kg_published"]
    )
    assert 0.02 < erro_rel_steam < 0.03

    # 17,36 kg/s publicados equivalem a 62,496 t/h.
    assert steam["mass_flow_kg_s"] * 3.6 == pytest.approx(62.496, rel=1e-9)


def test_wonji_nao_vira_falsa_validacao_de_eficiencia():
    caso = json.loads(WONJI.read_text(encoding="utf-8"))
    derivado = caso["do_not_treat_as_measured"]
    assert derivado["bagasse_feed_rate_kg_s"] == pytest.approx(7.24)
    assert "not presented as a direct fuel-flow measurement" in derivado["reason"]
    assert (
        "full boiler efficiency reproduction from this snapshot"
        in (caso["euler_validation_boundary"]["not_supported"])
    )
