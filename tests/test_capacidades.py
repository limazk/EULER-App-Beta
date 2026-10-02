"""Capacidades (T11): um teste por linha — habilita quando tem, bloqueia com motivo quando falta."""

import copy

import pandas as pd
import pytest
from construtor_caso import Periodo, montar

from euler.capacidades import avaliar

G01 = 11.773


@pytest.fixture(scope="module")
def completo():
    pacote, _ = montar([Periodo(G01, dias=7), Periodo(G01, dias=7)])
    return pacote


def situacao(pacote):
    return {c.id: c for c in avaliar(pacote)}


def sem_coluna(pacote, tabela, *colunas):
    p = copy.deepcopy(pacote)
    for coluna in colunas:
        p.importacoes[tabela].dados[coluna] = pd.NA
    return p


def sem_tabela(pacote, tabela):
    p = copy.deepcopy(pacote)
    del p.importacoes[tabela]
    return p


def com_estoques(pacote, quantos):
    p = copy.deepcopy(pacote)
    d = p.importacoes["combustivel"].dados
    estoques = d.index[d["tipo"] == "estoque"]
    p.importacoes["combustivel"].dados = d.drop(estoques[quantos:])
    return p


def test_com_todos_os_dados_tudo_habilitado(completo):
    # Este caso contém o contrato original completo; as duas extensões são opcionais.
    opcionais = {"purga_quantificada", "ua_economizador"}
    for c in avaliar(completo):
        assert c.situacao == ("bloqueada" if c.id in opcionais else "habilitada")


@pytest.mark.parametrize(
    ("capacidade", "alteracao", "trecho_do_motivo"),
    [
        ("registros", lambda p: sem_tabela(p, "diario"), "diário"),
        ("perda_gases", lambda p: sem_coluna(p, "diario", "t_gases_c"), "temperatura dos gases"),
        ("perda_gases", lambda p: sem_coluna(p, "amostras", "C"), "análise elementar"),
        ("energia_vapor", lambda p: sem_coluna(p, "diario", "totalizador_vapor_t"), "totalizador"),
        (
            "energia_vapor",
            lambda p: setattr(q := copy.deepcopy(p), "p_atm_bar", None) or q,
            "altitude",
        ),
        ("combustivel_queimado", lambda p: com_estoques(p, 1), "estoque"),
        ("energia_combustivel", lambda p: sem_coluna(p, "amostras", "umidade_bu_frac"), "umidade"),
        ("eficiencia_direta", lambda p: sem_coluna(p, "diario", "t_agua_alim_c"), "vapor"),
        ("incerteza", lambda p: sem_tabela(p, "instrumentos"), "incerteza declarada"),
        ("extrato", lambda p: sem_coluna(p, "combustivel", "preco_brl"), "preço"),
        ("comparacao", lambda p: com_estoques(p, 2), "dois períodos"),
        ("investigacao", lambda p: com_estoques(p, 2), "dois períodos"),
        ("custo_vapor", lambda p: sem_coluna(p, "combustivel", "preco_brl"), "preço"),
    ],
)
def test_bloqueia_com_motivo_quando_falta(completo, capacidade, alteracao, trecho_do_motivo):
    c = situacao(alteracao(completo))[capacidade]
    assert c.situacao == "bloqueada"
    assert any(trecho_do_motivo in m.lower() for m in c.motivos), c.motivos
    assert c.o_que_fazer


def test_investigacao_fica_parcial_sem_balanco_direto(completo):
    c = situacao(sem_coluna(completo, "diario", "totalizador_vapor_t"))["investigacao"]
    assert c.situacao == "parcial"
    assert any("balanço direto" in m for m in c.motivos)
