"""Saúde da caldeira (D65): consumo por tonelada de vapor período a período, eventos e selo."""

from pathlib import Path

import pytest

from euler.io import importar_pasta
from euler.periodos import periodos_entre_estoques
from euler.saude import avaliar_saude
from euler.vapor import p_atm_por_altitude_bar

RAIZ = Path(__file__).resolve().parents[1]


def _pacote(pasta: str):
    return importar_pasta(RAIZ / pasta, p_atm_bar=p_atm_por_altitude_bar(1000))


@pytest.fixture(scope="module")
def saude_demo():
    return avaliar_saude(_pacote("demo/caso_demo"))


def test_demo_mostra_a_mudanca_das_semanas_de_setembro(saude_demo):
    """Referência = agosto (primeira metade); 31/08 a 14/09 subiu além da incerteza."""
    s = saude_demo
    assert s.selo == "mudou"
    assert s.referencia == (0, 3)
    assert s.mudanca == (4, 5)
    assert s.frase.startswith("O consumo por tonelada de vapor subiu 10,1% de 31/08 a 14/09")
    estados = [p.estado for p in s.periodos]
    assert estados[:4] == ["referencia"] * 4
    assert estados[4:6] == ["mudou", "mudou"]


def test_periodo_sem_vapor_fica_sem_numero_e_com_motivo(saude_demo):
    """Ausente ≠ zero: a semana do medidor em manutenção não ganha consumo."""
    semana = saude_demo.periodos[6]
    assert semana.consumo is None
    assert semana.estado == "nao_da_para_dizer"
    assert semana.motivo


def test_mesmo_numero_da_investigacao(saude_demo):
    """O painel e a Investigação usam a mesma conta: o mesmo consumo da comparação."""
    from euler.investigacao import investigar

    p = _pacote("demo/caso_demo")
    s = periodos_entre_estoques(p)
    j = investigar(p, (s[0][0], s[3][1]), (s[4][0], s[5][1]))
    c = j["o_que_mudou"]["consumo_especifico"]
    assert saude_demo.consumo_referencia.valor == pytest.approx(c["referencia"])
    assert saude_demo.comparacao_mudanca.comparacao == pytest.approx(c["comparacao"])


def test_eventos_em_ordem_e_com_nome_legivel(saude_demo):
    tipos = [e["tipo"] for e in saude_demo.eventos]
    assert tipos == ["Calibração", "Troca de instrumento", "Troca de instrumento", "Limpeza"]
    assert all(e["descricao"] for e in saude_demo.eventos)


def test_os_dois_atos_tem_o_mesmo_painel(saude_demo):
    """O consumo depende do medidor de vapor, do estoque e da balança, cadastrados nos dois."""
    ato1 = avaliar_saude(_pacote("demo/caso_demo_completo"))
    assert (ato1.selo, ato1.mudanca, ato1.frase) == (
        saude_demo.selo,
        saude_demo.mudanca,
        saude_demo.frase,
    )


def test_sem_periodos_suficientes_nao_da_para_dizer():
    s = avaliar_saude(_pacote("templates"))
    assert s.selo == "nao_da_para_dizer"
    assert s.mudanca is None
    assert "Não dá para dizer" in s.frase
