"""Garantias da auditoria, sem usar fixtures como evidência de planta real."""

import json

import numpy as np
import pandas as pd
import pytest
from ensaio_horario import DADOS, executar, preparar
from robustez_ensaio import _reamostrar, auditar, avaliar_temporal, blocos_moveis, comparar_modelos


def test_blocos_conservam_vizinhos_e_nao_atravessam_borda():
    indices = blocos_moveis(31, 3, 7, np.random.default_rng(4))
    assert indices.shape == (7, 31)
    assert indices.min() >= 0 and indices.max() < 31
    for inicio in range(0, 30, 3):
        assert np.all(np.diff(indices[:, inicio : inicio + 3], axis=1) == 1)


def test_modelos_mesmas_horas_e_avaliacao_sem_futuro():
    bruto = pd.read_csv(DADOS / "ingredion_2023q1.csv")
    d, _ = preparar(bruto[bruto["Unit ID"] == "B10"])
    ref = d[d.mes == "2023-01"]
    comp = d[d.mes == "2023-02"]
    m = comparar_modelos(ref, comp)
    assert len(m["metodos"]) == 4
    assert len({v["horas"] for v in m["metodos"]}) == 1
    assert m["horas_comuns"] <= 441
    for v in avaliar_temporal(ref):
        assert v["treino_fim"] < v["teste_inicio"]
        assert v["horas_comparaveis"] <= v["horas_teste"]


def test_auditoria_reconcilia_todas_as_linhas_e_valores_sem_filtrar_sinal():
    r = executar()
    audit, linhas = auditar(repeticoes=80)
    assert len(linhas) == 8034
    original = pd.read_csv(DADOS / "ingredion_2023q1.csv", dtype={"Unit ID": str})
    pd.testing.assert_frame_equal(original, linhas[original.columns])
    assert linhas.motivo.str.len().gt(0).all()
    assert not linhas.duplicated(["Facility ID", "Unit ID", "Date", "Hour"]).any()
    assert set(audit["unidades"]) == set(r["unidades"])
    for unidade, u in r["unidades"].items():
        for mes in u["comparacoes"]:
            c = linhas[(linhas["Unit ID"] == unidade) & (linhas.mes == mes["mes"])]
            c = c[c.decisao == "comparavel"]
            assert len(c) == mes["horas_comparaveis"]
            assert c.delta_gj.sum() == pytest.approx(mes["delta_gj"], abs=1e-6)
            assert c.valor_condicional_usd.sum() == pytest.approx(mes["valor_referencia_usd"])
    json.dumps(audit, allow_nan=False)
    for u in audit["unidades"].values():
        for m in u["meses"]:
            assert len(m["reamostragem"]) == 3
            for b in m["reamostragem"]:
                assert b["validas"] + b["invalidas"] == 80
                assert b["quantil_025_pct"] <= b["quantil_975_pct"]
            assert m["causa_comprovada"] is False
            assert m["economia_recuperavel_usd"] is None


def test_repetibilidade_e_integridade_sem_alterar_dados():
    a, _ = auditar(repeticoes=40)
    b, _ = auditar(repeticoes=40)
    assert a == b
    assert a["repeticoes"] == 40
    assert a["fonte_sha256"] == json.loads((DADOS / "fontes.json").read_text())["recorte_sha256"]


def test_reamostragem_contra_ajuste_independente_das_linhas_sorteadas():
    bruto = pd.read_csv(DADOS / "ingredion_2023q1.csv")
    d, _ = preparar(bruto[bruto["Unit ID"] == "B10"])
    ref = d[d.mes == "2023-01"]
    comp = d[(d.mes == "2023-03") & d.vapor_t.between(ref.vapor_t.min(), ref.vapor_t.max())]
    resultados = _reamostrar(ref, comp, "2023-03", 20, np.random.default_rng(42))
    rng = np.random.default_rng(42)
    for tamanho, resultado in zip((1, 3, 7), resultados, strict=True):
        r_idx = blocos_moveis(31, tamanho, 20, rng)
        c_idx = blocos_moveis(31, tamanho, 20, rng)
        pcts = []
        for ri, ci in zip(r_idx, c_idx, strict=True):
            r = pd.concat([ref[ref.Date == f"2023-01-{dia + 1:02d}"] for dia in ri])
            c = pd.concat([comp[comp.Date == f"2023-03-{dia + 1:02d}"] for dia in ci])
            beta = np.linalg.lstsq(
                np.column_stack([np.ones(len(r)), r.vapor_t]), r.energia_gj, rcond=None
            )[0]
            previsto = float((beta[0] + beta[1] * c.vapor_t).sum())
            pcts.append(100 * (float(c.energia_gj.sum()) - previsto) / previsto)
        esperado = np.quantile(pcts, [0.025, 0.975])
        assert resultado["quantil_025_pct"] == pytest.approx(esperado[0], abs=1e-8)
        assert resultado["quantil_975_pct"] == pytest.approx(esperado[1], abs=1e-8)


def test_auditoria_antiga_nao_e_exibida(monkeypatch, tmp_path):
    import robustez_ensaio as modulo

    a, _ = auditar(repeticoes=20)
    (tmp_path / "ingredion_2023q1.csv").write_bytes((DADOS / "ingredion_2023q1.csv").read_bytes())
    arquivo = tmp_path / "auditoria_robustez.json"
    arquivo.write_text(json.dumps(a), encoding="utf-8")
    monkeypatch.setattr(modulo, "DADOS", tmp_path)
    assert modulo.carregar_auditoria() is not None
    a["assinaturas"]["app/ensaio_horario.py"] = "desatualizado"
    arquivo.write_text(json.dumps(a), encoding="utf-8")
    assert modulo.carregar_auditoria() is None
