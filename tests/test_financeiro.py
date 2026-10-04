"""Guardas financeiras: ausência não vira zero nem economia comprovada.

A valorização do consumo saiu desta camada da tela e foi para o motor (`euler.conta`,
D89; testes em test_conta.py). O simulador de percentual de recuperação foi retirado:
a parcela evitável não é estimada por percentual escolhido.
"""

import pytest
from test_app import abrir_com_demo

from app.financeiro import nao_negativo


@pytest.mark.parametrize("valor", [None, float("nan"), float("inf"), -1])
def test_valor_invalido_fica_ausente(valor):
    assert nao_negativo(valor) is None


def test_zero_explicito_e_preservado():
    assert nao_negativo(0) == 0


def test_tela_explica_a_conta_sem_percentual_de_recuperacao():
    at = abrir_com_demo("financeiro.py")
    assert not at.exception, at.exception
    assert not at.slider, "nenhum percentual de recuperação escolhido na tela"
    textos = " ".join(m.value for m in at.markdown)
    assert "Parcela evitável: não apurada" in textos
    assert "Por que a conta mudou em relação à referência" in textos
    assert "referência ajustada" in textos
    tabela = at.dataframe[0].value
    assert list(tabela["Parcela"]) == [
        "Produção de vapor",
        "Condição do vapor e da água",
        "Qualidade do combustível",
        "Preço do combustível",
        "Desvio ainda não explicado",
    ]
