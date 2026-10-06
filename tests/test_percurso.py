"""Percurso da planta em cinco passos (D102): só lê o que está gravado e aponta o próximo."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from euler import acompanhamento as ac
from euler.fechamento import criar_referencia, produzir_fechamento
from euler.percurso import PASSOS, percurso, proximo_passo
from euler.periodos import periodos_entre_estoques
from euler.persistencia import Repositorio

RAIZ = Path(__file__).resolve().parents[1]
EQ = "CALD-DEMO-01"
AGORA = datetime(2026, 10, 1, tzinfo=UTC)  # alguns dias depois do fim do caso sintético


@pytest.fixture
def armazem(tmp_path, monkeypatch):
    monkeypatch.setenv("EULER_DADOS_DIR", str(tmp_path / "dados"))
    repo = Repositorio()
    planta = repo.criar_planta("Percurso de teste", classe="sintetico")
    a = repo.armazem(planta["id"])
    a.criar_equipamento(EQ, "Caldeira A", EQ, config={"altitude_m": 1000}, autor="Teste")
    yield a
    a.fechar()


def estados(a):
    return {x["id"]: x["estado"] for x in percurso(a, EQ, AGORA)}


def importar(a):
    arquivos = {p.name: p.read_bytes() for p in (RAIZ / "demo/caso_demo_completo").glob("*.csv")}
    a.confirmar(a.previa(EQ, arquivos), autor="Teste")


def test_cinco_passos_na_ordem_do_percurso(armazem):
    itens = percurso(armazem, EQ, AGORA)
    assert [x["titulo"] for x in itens] == [
        "Enviar registros",
        "Conferir a conta",
        "Investigar",
        "Registrar ação",
        "Verificar resultado",
    ]
    assert [x["destino"] for x in itens] == [d for _, _, d in PASSOS]


def test_sem_registros_so_o_primeiro_passo_esta_pendente(armazem):
    e = estados(armazem)
    assert e["registros"] == "pendente"
    assert {e[k] for k in ("conta", "investigar", "acao", "resultado")} == {"bloqueado"}
    assert proximo_passo(percurso(armazem, EQ, AGORA))["id"] == "registros"


def test_com_registros_o_proximo_passo_e_a_referencia(armazem):
    importar(armazem)
    itens = percurso(armazem, EQ, AGORA)
    assert estados(armazem)["registros"] == "feito"
    p = proximo_passo(itens)
    assert p["id"] == "conta" and "referência" in p["frase"]


def test_fechamento_com_verificacao_pede_investigacao_e_depois_acao(armazem):
    importar(armazem)
    s = periodos_entre_estoques(armazem.pacote(EQ))
    criar_referencia(armazem, EQ, s[0][0], s[3][1], "inicial", "Base de teste", "Teste")
    f = produzir_fechamento(armazem, EQ, "Teste")
    e = estados(armazem)
    assert e["investigar"] == "pendente"
    assert e["acao"] == "bloqueado"

    inv = ac.abrir_do_fechamento(armazem, f["id"], "Teste")
    e = estados(armazem)
    assert e["investigar"] == "andamento"
    assert e["acao"] == "pendente"
    assert e["resultado"] == "bloqueado"

    ac.registrar_intervencao(
        armazem,
        EQ,
        s[4][1],
        "limpeza",
        "Limpeza dos tubos (teste)",
        "Teste",
        investigacao_id=inv["id"],
    )
    e = estados(armazem)
    assert e["acao"] == "feito"
    assert e["resultado"] == "pendente", "ação sem avaliação continua pendente"


def test_conflito_de_importacao_volta_o_primeiro_passo_para_pendente(armazem, monkeypatch):
    importar(armazem)
    original = armazem.cobertura

    def com_conflito(equip_id, agora=None):
        return {**original(equip_id, agora=agora), "conflitos_pendentes": 2}

    monkeypatch.setattr(armazem, "cobertura", com_conflito)
    item = percurso(armazem, EQ, AGORA)[0]
    assert item["estado"] == "pendente" and "2 conflito" in item["frase"]
