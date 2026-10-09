"""Testes da integração independente dos PRs #23 (fundação) e #24 (interface).

Não altera o motor científico nem requer provedor externo de IA ou de ML.
"""

from componentes import ESTILO
from design_v3.tokens import ESCURO
from euler_intelligence.contracts import PedidoExplicacao
from euler_intelligence.gateway import explicar
from euler_intelligence.ml.availability import disponibilidade
from navegacao import PRINCIPAIS, todas_as_paginas


def test_paleta_da_interface_e_da_fundacao_coincidem():
    cores_esperadas = {
        "--euler-fundo": ESCURO.fundo,
        "--euler-lateral": ESCURO.lateral,
        "--euler-cartao": ESCURO.cartao,
        "--euler-linha": ESCURO.borda,
        "--euler-hover": ESCURO.hover,
        "--euler-texto": ESCURO.texto,
        "--euler-suave": ESCURO.secundario,
        "--euler-verde": ESCURO.verde,
        "--euler-vermelho": ESCURO.vermelho,
        "--euler-ambar": ESCURO.ambar,
    }
    for variavel, cor in cores_esperadas.items():
        assert f"{variavel}: {cor};" in ESTILO, variavel


def test_v3_pode_navegar_sem_ativar_ml_ou_ia():
    assert PRINCIPAIS[0][0] == "paginas/inicio.py"
    rotas = [pagina[0] for pagina in todas_as_paginas()]
    assert "paginas/financeiro.py" in rotas
    assert "paginas/admin.py" in rotas

    estado = disponibilidade()
    assert estado.habilitado is False
    assert estado.modelo is None

    pedido = PedidoExplicacao(
        organizacao_id="org-sintetica",
        planta_id="planta-sintetica",
        analise_id="analise-sintetica",
        pergunta="O que mudou?",
    )
    resposta = explicar(pedido)
    assert resposta.situacao == "desativado"
    assert resposta.provedor is None
    assert resposta.texto is None
    assert not resposta.ids_evidencias
