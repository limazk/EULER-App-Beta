"""Financeiro persistido usa o fechamento escolhido, sem misturar dados da sessão."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from euler.fechamento import criar_referencia, produzir_fechamento, registrar_preco
from euler.periodos import periodos_entre_estoques
from euler.persistencia import Repositorio

RAIZ = Path(__file__).resolve().parents[1]


@pytest.fixture
def planta_financeira(tmp_path, monkeypatch):
    monkeypatch.setenv("EULER_DADOS_DIR", str(tmp_path / "dados"))
    repo = Repositorio()
    planta = repo.criar_planta("Planta financeira de teste", classe="sintetico")
    a = repo.armazem(planta["id"])
    eq = "CALD-DEMO-01"
    a.criar_equipamento(eq, "Caldeira A", eq, config={"altitude_m": 1000}, autor="Teste")
    arquivos = {p.name: p.read_bytes() for p in (RAIZ / "demo/caso_demo_completo").glob("*.csv")}
    a.confirmar(a.previa(eq, arquivos), autor="Teste")
    periodos = periodos_entre_estoques(a.pacote(eq))
    criar_referencia(a, eq, periodos[0][0], periodos[3][1], "inicial", "Base teste", "Teste")
    f = produzir_fechamento(a, eq, "Teste")
    yield a, eq, f
    a.fechar()


def abrir_bloco():
    at = AppTest.from_file(str(RAIZ / "app/main.py"), default_timeout=120).run()
    at.switch_page("paginas/financeiro.py").run()
    at.radio(key="fin_origem").set_value("Fechamentos da planta").run()
    assert not at.exception, at.exception
    return at


def test_financeiro_abre_fechamento_sem_importar_sessao(planta_financeira):
    _, _, f = planta_financeira
    at = abrir_bloco()
    from acompanhamento_ui import brl

    custos = f["resultado"]["nucleo"]["explicacao_conta"]
    metrics = {m.label: m.value for m in at.metric}
    assert metrics["Custo do consumo observado"] == brl(custos["consumido"]["custo_brl"])
    assert metrics["Desvio monetizado"] == brl(custos["desvio"]["custo_brl"])
    assert metrics["Economia verificada no histórico"] == "Não apurada"
    textos = " ".join(str(x.value) for g in (at.markdown, at.caption) for x in g)
    assert "não é pagamento" in textos
    assert "Política de custo" in textos
    assert "Próxima verificação" in textos
    assert "arquivos" not in at.session_state

    # Outra planta com o mesmo código de equipamento não pode herdar o fechamento.
    repo = Repositorio()
    outra = repo.criar_planta("Outra planta", classe="sintetico")
    a = repo.armazem(outra["id"])
    a.criar_equipamento("CALD-DEMO-01", "Outra caldeira", "CALD-DEMO-01", autor="Teste")
    a.fechar()
    at.run()
    at.selectbox(key="acomp_planta_sel").set_value(outra["id"]).run()
    assert not at.exception, at.exception
    assert not at.metric
    assert any("Ainda não há conta fechada" in x.value for x in at.info)


def test_mudar_preco_na_config_nao_reescreve_fechamento(planta_financeira):
    a, eq, f = planta_financeira
    registrar_preco(a, eq, "lenha", 999, "2026-01-01T00:00:00-03:00", "Teste", "Teste")
    a.configurar(eq, {"politica_custo": "tabela_de_precos"}, "Teste")
    at = abrir_bloco()
    textos = " ".join(str(x.value) for g in (at.markdown, at.caption) for x in g)
    assert f["resultado"]["nucleo"]["politica_custo"]["descricao"] in textos
    assert "Valores preservados" in textos


def test_financeiro_sem_planta_indica_cadastro(tmp_path, monkeypatch):
    monkeypatch.setenv("EULER_DADOS_DIR", str(tmp_path / "vazio"))
    at = abrir_bloco()
    assert any("Nenhuma planta cadastrada" in x.value for x in at.info)
    assert not at.metric
