"""Evidência ordinal, sem promover ausência de dados a certeza."""

from copy import deepcopy

import pytest

from euler.evidencias import consolidar, dimensao, robustez_publica, verificar_integridade


def auditoria(sinal=1):
    return {
        "reamostragem": [
            {
                "bloco_dias": b,
                "validas": 2000,
                "invalidas": 0,
                "quantil_025_pct": 1 if sinal > 0 else -3,
                "quantil_975_pct": 3 if sinal > 0 else -1,
            }
            for b in (1, 3, 7)
        ],
        "modelos": {"metodos": [{"delta_pct": sinal * 2}] * 4},
        "referencias": {"metodos": [{"delta_pct": sinal * 2}] * 3},
        "retirada_de_um_dia_pct": {"min": 1 if sinal > 0 else -3, "max": 3 if sinal > 0 else -1},
    }


@pytest.mark.parametrize("sinal", [1, -1])
def test_robustez_preserva_ambos_os_sinais(sinal):
    d = robustez_publica(auditoria(sinal), 2000)
    assert d["nivel"] == "FORTE"
    assert d["sinal"] == ("aumento" if sinal > 0 else "reducao")


def test_zero_reversao_e_incompletude_nao_recebem_selo_forte():
    a = auditoria()
    a["reamostragem"][1]["quantil_025_pct"] = -0.3
    assert robustez_publica(a, 2000)["sinal"] == "inconclusivo"
    assert robustez_publica(a, 2000)["nivel"] == "FRACA"
    a = auditoria()
    a["referencias"]["metodos"][0]["delta_pct"] = -2
    assert robustez_publica(a, 2000)["sinal"] == "inconclusivo"
    a = auditoria()
    a["reamostragem"][0]["validas"] = 1999
    assert robustez_publica(a, 2000)["nivel"] != "FORTE"
    assert robustez_publica(None, None)["nivel"] == "INSUFICIENTE"
    assert robustez_publica({}, 2000)["nivel"] == "INSUFICIENTE"


def test_consolidacao_hash_repetivel_e_deteccao_de_alteracao():
    j = {
        "equipamento": "B",
        "periodo": "2023-03",
        "observacao": {"unidade": "GJ"},
        "dimensoes": {"evidencia_fisica": dimensao("INSUFICIENTE", ["Falta pressão."])},
        "conclusao": "Sem causa determinada.",
        "economia": {
            "desvio_estimado": 25,
            "oportunidade_potencial": None,
            "economia_verificada": None,
        },
        "fontes": {},
    }
    d = consolidar(j)
    assert d == consolidar(j)
    assert verificar_integridade(d)
    assert d["causa_confirmada"] is False
    assert len(d["resultado_sha256"]) == 64
    outro = deepcopy(d)
    outro["conclusao"] = "Mudou"
    assert not verificar_integridade(outro)
    with pytest.raises(ValueError):
        consolidar({**j, "causa_confirmada": True})
    with pytest.raises(ValueError):
        consolidar({**j, "economia": {"economia_verificada": 25}})
    with pytest.raises(ValueError):
        dimensao("87%", ["Indefensável"])
    with pytest.raises(ValueError):
        consolidar({**j, "observacao": {"unidade": "GJ", "valor": float("nan")}})
