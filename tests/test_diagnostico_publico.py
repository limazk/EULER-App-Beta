"""Contrato entre o caso real, parecer, relatório e diagnóstico."""

from copy import deepcopy

from diagnostico_publico import diagnosticos
from ensaio_horario import executar
from parecer_ensaio import parecer, relatorio_texto

from euler.evidencias import verificar_integridade


def test_b10_fevereiro_inconclusivo_marco_persiste_sem_mudar_contas():
    r = executar()
    antes = deepcopy(r)
    ds = diagnosticos(r, "B10")
    fev, mar = ds
    assert fev["dimensoes"]["robustez_estatistica"]["nivel"] == "FRACA"
    assert mar["dimensoes"]["robustez_estatistica"]["nivel"] == "FORTE"
    assert all(d["dimensoes"]["referencia"]["nivel"] == "MODERADA" for d in ds)
    assert all(d["dimensoes"]["evidencia_fisica"]["nivel"] == "INSUFICIENTE" for d in ds)
    assert "menos conclusivo" in fev["conclusao"]
    assert "persiste" in mar["conclusao"]
    for d, m in zip(ds, r["unidades"]["B10"]["comparacoes"], strict=True):
        assert d["observacao"]["variacao"] == m["delta_gj"]
        assert d["economia"]["desvio_estimado"] == m["valor_referencia_usd"]
        assert d["economia"]["economia_verificada"] is None
        assert not d["causa_confirmada"]
        assert d["proximas_medicoes"][0]["separa"]
        assert verificar_integridade(d)
    assert r == antes
    p = parecer(r["unidades"]["B10"], ds)
    assert "menos conclusivo" in p["conclusao"] and "persiste" in p["conclusao"]
    texto = relatorio_texto(r, "B10")
    for d in ds:
        assert d["analise_id"] in texto
        assert d["conclusao"] in texto


def test_sem_auditoria_nao_herda_confianca_e_negativos_preservados(monkeypatch):
    import diagnostico_publico as modulo

    r = executar()
    monkeypatch.setattr(modulo, "carregar_auditoria", lambda: None)
    for unidade in r["unidades"]:
        for d in diagnosticos(r, unidade):
            assert d["dimensoes"]["robustez_estatistica"]["nivel"] == "INSUFICIENTE"
            if unidade == "B08":
                assert d["economia"]["desvio_estimado"] < 0
                assert "redução" in d["conclusao"].lower()


def test_hash_muda_com_preco_e_auditoria_de_outro_resultado_nao_vaza():
    r = executar()
    a = diagnosticos(r, "B10")
    r["unidades"]["B10"]["comparacoes"][0]["delta_gj"] += 1
    b = diagnosticos(r, "B10")
    assert b[0]["dimensoes"]["robustez_estatistica"]["nivel"] == "INSUFICIENTE"
    assert a[0]["analise_id"] != b[0]["analise_id"]


def test_pagina_diagnostico_abre_e_troca_periodo():
    from test_app import abrir

    at = abrir("diagnostico.py")
    assert not at.exception
    assert any("Diagnóstico EULER" in t.value for t in at.title)
    assert any("menos conclusivo" in m.value for m in at.info)
    at.selectbox[2].select("2023-03").run()
    assert not at.exception
    assert any("persiste" in m.value for m in at.info)


def test_b06_menos_verificacao_nao_melhora_nota_e_retirada_de_um_dia_conta():
    """D87 com dados reais: na B06 todas as faixas de reamostragem cruzam zero e a auditoria
    está incompleta; antes recebia robustez MODERADA (acima da B10 de fevereiro, FRACA). Em
    março, retirar um único dia muda o sinal, então a consistência temporal não é MODERADA.
    Energia e valores condicionais não mudam."""
    r = executar()
    fev, mar = diagnosticos(r, "B06")
    assert fev["dimensoes"]["robustez_estatistica"]["nivel"] == "FRACA"
    assert mar["dimensoes"]["robustez_estatistica"]["nivel"] == "FRACA"
    assert mar["dimensoes"]["consistencia_temporal"]["nivel"] == "FRACA"
    assert fev["dimensoes"]["consistencia_temporal"]["nivel"] == "MODERADA"
    for d, m in zip((fev, mar), r["unidades"]["B06"]["comparacoes"], strict=True):
        assert d["observacao"]["variacao"] == m["delta_gj"]
        assert d["economia"]["desvio_estimado"] == m["valor_referencia_usd"]
    b10 = diagnosticos(r, "B10")
    assert [d["dimensoes"]["consistencia_temporal"]["nivel"] for d in b10] == [
        "MODERADA",
        "MODERADA",
    ]
