"""Entrega de cada fechamento (D104): conta preservada, pendências, andamento e resultados."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from euler import acompanhamento as ac
from euler.entrega import SEGURANCA, entrega_do_fechamento, texto_entrega
from euler.fechamento import criar_referencia, produzir_fechamento
from euler.periodos import periodos_entre_estoques
from euler.persistencia import Repositorio

RAIZ = Path(__file__).resolve().parents[1]
EQ = "CALD-DEMO-01"
AGORA = datetime(2026, 10, 6, 12, tzinfo=UTC)


@pytest.fixture
def armazem(tmp_path, monkeypatch):
    monkeypatch.setenv("EULER_DADOS_DIR", str(tmp_path / "dados"))
    repo = Repositorio()
    planta = repo.criar_planta("Entrega de teste", classe="sintetico")
    a = repo.armazem(planta["id"])
    a.criar_equipamento(EQ, "Caldeira A", EQ, config={"altitude_m": 1000.0}, autor="Teste")
    arquivos = {p.name: p.read_bytes() for p in (RAIZ / "demo/caso_demo_completo").glob("*.csv")}
    a.confirmar(a.previa(EQ, arquivos), autor="Teste")
    yield a
    a.fechar()


def _base(a):
    s = periodos_entre_estoques(a.pacote(EQ))
    criar_referencia(a, EQ, s[0][0], s[3][1], "inicial", "Base", "Teste")
    return s


def test_sem_fechamento_nao_ha_entrega(armazem):
    assert entrega_do_fechamento(armazem, EQ) is None


def test_entrega_traz_a_conta_preservada_e_as_cinco_partes(armazem):
    _base(armazem)
    f = produzir_fechamento(armazem, EQ, "Teste")
    e = entrega_do_fechamento(armazem, EQ, agora=AGORA)
    n = f["resultado"]["nucleo"]

    assert e["fechamento_id"] == f["id"]
    assert e["gerada_em"].startswith("2026-10-06")
    # a conta é o mesmo quadro da conclusão (D101), lido do fechamento gravado
    q = e["conta"]
    assert q["consumido"]["custo_brl"] == n["explicacao_conta"]["consumido"]["custo_brl"]
    assert q["sem_explicacao"]["custo_brl"] == n["explicacao_conta"]["desvio"]["custo_brl"]
    assert q["evitavel"]["custo_brl"] is None
    assert e["mudou"] == f["resultado"]["comparacao_anterior"]["frase"]

    texto = texto_entrega(e, "Caldeira A")
    for titulo in (
        "# Entrega do fechamento #",
        "## 1. A conta do período",
        "## 2. O que mudou",
        "## 3. Pendências relevantes",
        "## 4. Verificações e ações em andamento",
        "## 5. Resultados já demonstrados",
    ):
        assert titulo in texto
    assert "Caldeira A" in texto
    assert "entrega gerada em 06/10/2026" in texto
    assert "Parcela evitável: não apurada" in texto
    assert "não apurada (nenhuma avaliação cumpriu o protocolo)" in texto
    assert SEGURANCA in texto
    assert f["resultado"]["nucleo_sha"][:16] in texto


def test_acao_sem_avaliacao_fica_em_andamento_e_avaliada_vai_para_resultados(armazem):
    s = _base(armazem)
    f = produzir_fechamento(armazem, EQ, "Teste")
    inv = ac.abrir_do_fechamento(armazem, f["id"], "Teste")
    it = ac.registrar_intervencao(
        armazem, EQ, s[3][1], "limpeza", "Limpeza dos tubos", "Teste", investigacao_id=inv["id"]
    )
    e = entrega_do_fechamento(armazem, EQ, agora=AGORA)
    assert [v["titulo"] for v in e["verificacoes"]] == [inv["titulo"]]
    assert e["verificacoes"][0]["responsavel"] == "não informado"
    assert [x["descricao"] for x in e["acoes_em_andamento"]] == ["Limpeza dos tubos"]
    assert e["acoes_em_andamento"][0]["situacao"] == "ainda não avaliada"
    assert e["resultados"]["avaliadas"] == []

    av = ac.avaliar_intervencao(armazem, it["id"], "Teste")
    e = entrega_do_fechamento(armazem, EQ, agora=AGORA)
    if av["resultado"]["resultado"] == "nao_avaliavel":
        assert e["acoes_em_andamento"][0]["situacao"].startswith("avaliação sem conclusão")
    else:
        assert e["acoes_em_andamento"] == []
        (x,) = e["resultados"]["avaliadas"]
        assert x["frase"] == av["resultado"]["frase"]
    # nenhuma economia inventada: só a soma do painel, que exige o protocolo (D95)
    assert e["resultados"]["economia_verificada_brl"] is None
    assert "Limpeza dos tubos" in texto_entrega(e)


def test_entrega_de_fechamento_antigo_nao_olha_para_frente(armazem):
    s = _base(armazem)
    f1 = produzir_fechamento(armazem, EQ, "Teste", inicio=s[4][0], fim=s[4][1])
    produzir_fechamento(armazem, EQ, "Teste", inicio=s[5][0], fim=s[5][1])
    e1 = entrega_do_fechamento(armazem, EQ, f1["id"], agora=AGORA)
    assert e1["fechamento_id"] == f1["id"]
    assert e1["periodo"] == f1["resultado"]["nucleo"]["periodo"]
    # a leitura da série é a de um único fechamento: não fala de repetição nem de durações
    assert not any("durações diferentes" in x or "últimos" in x for x in e1["serie"])


def test_pendencias_dizem_o_que_falta_fechar_e_a_conta_incompleta(armazem):
    s = _base(armazem)
    # a semana 7 do caso sintético não tem totalizador de vapor: conta indisponível
    produzir_fechamento(armazem, EQ, "Teste", inicio=s[6][0], fim=s[6][1])
    e = entrega_do_fechamento(armazem, EQ, agora=AGORA)
    texto = " ".join(e["pendencias"])
    assert "Conta deste fechamento: conta indisponível" in texto
    assert "ainda sem fechamento" in texto
    assert e["conta"]["disponivel"] is False
    assert e["conta"]["motivo"] in texto_entrega(e)


def test_fechamento_de_outro_equipamento_e_recusado(armazem):
    _base(armazem)
    f = produzir_fechamento(armazem, EQ, "Teste")
    armazem.criar_equipamento("CALD-B", "Caldeira B", "CALD-B", autor="Teste")
    with pytest.raises(ValueError):
        entrega_do_fechamento(armazem, "CALD-B", f["id"])


def test_telas_oferecem_a_entrega_do_fechamento(armazem):
    from streamlit.testing.v1 import AppTest

    _base(armazem)
    f = produzir_fechamento(armazem, EQ, "Teste")
    at = AppTest.from_file(str(RAIZ / "app/main.py"), default_timeout=120).run()
    at.switch_page("paginas/financeiro.py").run()
    at.radio(key="fin_origem").set_value("Fechamentos da planta").run()
    assert not at.exception, at.exception
    assert any(f"Entrega do fechamento #{f['id']}" in m.value for m in at.markdown)
    assert {m.label for m in at.metric} >= {
        "Pendências",
        "Verificações abertas",
        "Ações sem avaliação",
        "Ações avaliadas",
    }
    rotulos = [b.proto.label for b in at.get("download_button")]
    assert "Baixar a entrega do fechamento" in rotulos

    at.switch_page("paginas/fechamentos.py").run()
    assert not at.exception, at.exception
    rotulos = [b.proto.label for b in at.get("download_button")]
    assert "Baixar a entrega do fechamento" in rotulos
