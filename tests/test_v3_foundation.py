"""Invariantes da fundação v3; não depende de Streamlit ou provedores de IA."""

import re

import pytest
from design_v3.tokens import ESCURO, cor_do_estado
from euler_intelligence.contracts import PedidoExplicacao
from euler_intelligence.gateway import explicar
from euler_intelligence.ml.availability import disponibilidade


def _pedido() -> PedidoExplicacao:
    return PedidoExplicacao("organizacao-teste", "planta-teste", "analise-teste", "O que mudou?")


def test_paleta_escura_e_cores_semanticas():
    assert ESCURO.fundo == "#080C0E"
    assert ESCURO.verde == cor_do_estado("normal")
    assert ESCURO.vermelho == cor_do_estado("alerta")
    assert ESCURO.ambar == cor_do_estado("atencao")
    assert ESCURO.secundario == cor_do_estado("indisponivel")
    assert all(re.fullmatch(r"#[0-9A-Fa-f]{6}", valor) for valor in vars(ESCURO).values())


def test_paleta_nao_introduz_roxo():
    assert all(
        valor.lower() not in {"#8b5cf6", "#a855f7", "#9333ea", "#7c3aed"}
        for valor in vars(ESCURO).values()
    )


def test_estado_desconhecido_nao_recebe_cor_de_normalidade():
    with pytest.raises(ValueError, match="desconhecido"):
        cor_do_estado("nao_classificado")


def test_pedido_exige_escopo_e_pergunta():
    with pytest.raises(ValueError, match="organizacao_id"):
        PedidoExplicacao("", "planta", "analise", "Pergunta")
    with pytest.raises(ValueError, match="pergunta"):
        PedidoExplicacao("org", "planta", "analise", " ")


def test_gateway_nao_ativa_ia_por_variavel_de_ambiente(monkeypatch):
    monkeypatch.setenv("EULER_AI_ENABLED", "true")
    monkeypatch.setenv("EULER_AI_PROVIDER", "online")
    resposta = explicar(_pedido())
    assert resposta.situacao == "desativado"
    assert resposta.provedor is None
    assert resposta.texto is None
    assert resposta.ids_evidencias == ()
    assert "Nenhuma IA foi consultada" in resposta.mensagem


def test_ml_continua_indisponivel():
    estado = disponibilidade()
    assert estado.habilitado is False
    assert estado.modelo is None
    assert "não" in estado.mensagem
