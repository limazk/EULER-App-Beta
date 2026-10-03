"""Ensaio público: contas independentes, exclusões e abstenções."""

from decimal import Decimal

import numpy as np
import pandas as pd
import pytest
from ensaio_horario import DADOS, executar, preparar

from euler.economia import valorizar_energia


def test_serie_real_contra_calculo_independente():
    original = pd.read_csv(DADOS / "ingredion_2023q1.csv", dtype={"Unit ID": str})
    r = executar()
    for unidade in r["unidades"]:
        bruto = original[original["Unit ID"] == unidade]
        valido = bruto[
            (bruto["Operating Time"] == 1)
            & (bruto["Heat Input Measure Indicator"] == "Measured")
            & (bruto["Heat Input (mmBtu)"] > 0)
            & (bruto["Steam Load (1000 lb/hr)"] > 0)
        ]
        ref = valido[valido.Date < "2023-02-01"]
        x = ref["Steam Load (1000 lb/hr)"].to_numpy() * 0.45359237
        y = ref["Heat Input (mmBtu)"].to_numpy() * 1.05505585262
        beta = np.linalg.lstsq(np.column_stack([np.ones(len(x)), x]), y, rcond=None)[0]
        for mes in r["unidades"][unidade]["comparacoes"]:
            c = valido[valido.Date.str.startswith(mes["mes"])]
            vapor = c["Steam Load (1000 lb/hr)"] * 0.45359237
            c = c[vapor.between(x.min(), x.max())]
            energia = c["Heat Input (mmBtu)"] * 1.05505585262
            vapor = c["Steam Load (1000 lb/hr)"] * 0.45359237
            esperado = float((energia - (beta[0] + beta[1] * vapor)).sum())
            assert mes["horas_comparaveis"] == len(c)
            assert mes["delta_gj"] == pytest.approx(esperado, abs=1e-6)
            preco = Decimal(str(mes["preco_usd_mcf"])) / Decimal("1.040")
            esperado_usd = Decimal(str(esperado)) / Decimal("1.05505585262") * preco
            assert mes["valor_referencia_usd"] == pytest.approx(float(esperado_usd), abs=1e-5)
            assert mes["comparacao_motor"]["detectavel"] is None
            assert mes["economia_comprovada_usd"] is None
            assert mes["causa_comprovada"] is False
    assert all(c["delta_gj"] > 0 for c in r["unidades"]["B10"]["comparacoes"])
    assert all(c["delta_gj"] < 0 for c in r["unidades"]["B08"]["comparacoes"])


def test_ausencia_duplicata_substituicao_e_hora_parcial():
    d = pd.read_csv(DADOS / "ingredion_2023q1.csv", dtype={"Unit ID": str})
    d = d[d["Unit ID"] == "B10"].head(8).copy()
    d.loc[d.index[0], "Heat Input (mmBtu)"] = np.nan
    d.loc[d.index[1], "Heat Input Measure Indicator"] = "Substitute"
    d.loc[d.index[2], "Operating Time"] = 0.5
    valido, _ = preparar(d)
    assert len(valido) == 5
    with pytest.raises(ValueError, match="duplicad"):
        preparar(pd.concat([d, d.iloc[[4]]]))


def test_precos_e_sinais_sem_economia_inventada():
    assert valorizar_energia(10, None) is None
    assert valorizar_energia(-10, 5) == -50
    assert valorizar_energia(10, 0) == 0
    for x in [float("nan"), float("inf"), -1]:
        with pytest.raises(ValueError):
            valorizar_energia(10, x)


def test_tela_executa_serie_e_preserva_limites():
    from test_app import abrir_com_demo

    at = abrir_com_demo("dados_publicos.py")
    assert not at.exception
    assert any("Registros horários reais" in h.value for h in at.subheader)
    assert any("referência regional" in c.value for c in at.caption)
    assert [t.label for t in at.tabs] == ["Resultado", "O que verificar", "Fontes e cálculo"]
    at.selectbox[0].select("B08").run()
    assert not at.exception
    assert any("Sem aumento nos períodos" in m.value for m in at.markdown)
    assert any("não sustenta" in m.value for m in at.info)


def test_parecer_separa_desvio_de_causa_e_nao_recomenda_perda_em_reducao():
    from copy import deepcopy

    from parecer_ensaio import parecer

    r = executar()
    p = parecer(r["unidades"]["B10"])
    assert p["status"] == "investigar"
    assert p["horas"] == 994
    assert p["fora_faixa"] == 398
    assert p["perda_confirmada"] is None
    assert p["economia_recuperavel"] is None
    assert not p["intervencao_indicada"]
    assert p["sensibilidade_consistente"]
    assert parecer(r["unidades"]["B08"])["status"] == "sem_aumento"
    misto = deepcopy(r["unidades"]["B10"])
    misto["comparacoes"][1]["delta_gj"] = -1
    assert parecer(misto)["status"] == "variavel"
    divergente = deepcopy(r["unidades"]["B10"])
    divergente["comparacoes"][0]["sensibilidade"][0]["delta_gj"] = -1
    assert not parecer(divergente)["sensibilidade_consistente"]
    assert "método" in parecer(divergente)["conclusao"]


def test_exportacao_contem_origem_calculo_limites_e_unidade_selecionada():
    from parecer_ensaio import relatorio_texto

    r = executar()
    texto = relatorio_texto(r, "B10")
    assert "B10" in texto
    assert "85.006,85" in texto
    assert r["fonte"]["recorte_sha256"] in texto
    assert r["fonte"]["preco_fonte"] in texto
    assert "carvão" in texto
    assert "não apurada" in texto
    assert "B08" in relatorio_texto(r, "B08")
