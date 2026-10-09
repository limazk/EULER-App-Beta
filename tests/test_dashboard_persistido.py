"""Dashboard v3 lê somente o contexto persistido e auditável selecionado."""

from pathlib import Path

import pandas as pd
import pytest
from dashboard_persistido import carregar_dashboard, filtrar_periodo, resumo_fechamento
from streamlit.testing.v1 import AppTest

from euler.fechamento import criar_referencia, produzir_fechamento
from euler.periodos import periodos_entre_estoques
from euler.persistencia import Repositorio

RAIZ = Path(__file__).resolve().parents[1]


@pytest.fixture
def dashboard_salvo(tmp_path):
    repo = Repositorio(tmp_path / "tenant-autorizado")
    planta = repo.criar_planta("Planta persistida", classe="sintetico")
    outra = repo.criar_planta("Outra planta", classe="sintetico")
    equipamento = "CALD-DEMO-01"
    a = repo.armazem(planta["id"])
    a.criar_equipamento(
        equipamento,
        "Caldeira persistida",
        equipamento,
        config={"altitude_m": 1000},
        autor="Teste",
    )
    arquivos = {p.name: p.read_bytes() for p in (RAIZ / "demo/caso_demo_completo").glob("*.csv")}
    a.confirmar(a.previa(equipamento, arquivos), autor="Teste")
    periodos = periodos_entre_estoques(a.pacote(equipamento))
    criar_referencia(
        a,
        equipamento,
        periodos[0][0],
        periodos[3][1],
        "inicial",
        "Base sintética de teste",
        "Teste",
    )
    fechamento = produzir_fechamento(a, equipamento, "Teste")
    a.fechar()
    return repo, planta, outra, equipamento, fechamento


def test_carrega_apenas_planta_e_equipamento_selecionados(dashboard_salvo):
    repo, planta, outra, equipamento, fechamento = dashboard_salvo

    dados = carregar_dashboard(repo, planta["id"], equipamento)

    assert dados.planta["id"] == planta["id"]
    assert dados.equipamento["id"] == equipamento
    assert dados.origem == "sintético"
    assert dados.pacote is not None
    assert [f["id"] for f in dados.fechamentos] == [fechamento["id"]]
    assert len(dados.importacoes) == 1
    with pytest.raises(ValueError, match="Equipamento"):
        carregar_dashboard(repo, outra["id"], equipamento)


def test_resumo_usa_fechamento_vigente_sem_tratar_recebimento_como_consumo(dashboard_salvo):
    repo, planta, _, equipamento, fechamento = dashboard_salvo
    dados = carregar_dashboard(repo, planta["id"], equipamento)

    resumo = resumo_fechamento(dados.fechamentos[-1])
    conta = fechamento["resultado"]["nucleo"]["conta_do_periodo"]

    assert resumo["consumo_t"] == conta["consumido_t"]
    assert resumo["recebido_t"] == conta["recebido_t"]
    assert resumo["consumo_t"] != resumo["recebido_t"]
    assert resumo["consumo_especifico_t_t"] is not None
    assert resumo["custo_brl_t_vapor"] is not None
    assert resumo["custo_esperado_brl_t_vapor"] is None
    assert resumo["periodo"]["inicio"] == fechamento["inicio"]


def test_filtro_de_periodo_mantem_lacunas_e_nao_mistura_datas():
    diario = pd.DataFrame(
        {
            "dia": pd.to_datetime(["2026-01-01", "2026-01-02", "2026-02-01"]),
            "vazao_t_h": [10.0, None, 99.0],
        }
    )

    filtrado = filtrar_periodo(diario, "2026-01-01", "2026-01-31T23:59:59")

    assert filtrado["dia"].dt.month.tolist() == [1, 1]
    assert pd.isna(filtrado.iloc[1]["vazao_t_h"])


def test_interface_exibe_dados_persistidos_com_origem_periodo_e_unidade(
    dashboard_salvo, monkeypatch
):
    repo, planta, _, equipamento, _ = dashboard_salvo
    monkeypatch.setenv("EULER_TEST_BYPASS_AUTH", "1")
    monkeypatch.setenv("EULER_DADOS_DIR", str(repo.raiz))

    at = AppTest.from_file(str(RAIZ / "app/main.py"), default_timeout=120).run()
    at.selectbox(key="dashboard_planta").set_value(planta["id"]).run()

    assert not at.exception, at.exception
    assert at.selectbox(key="dashboard_planta").value == planta["id"]
    assert at.selectbox(key=f"dashboard_equipamento_{planta['id']}").value == equipamento
    metricas = {metrica.label: metrica.value for metrica in at.metric}
    assert metricas["Custo energético"] != "—"
    assert metricas["Custo esperado"] == "—"
    assert metricas["Consumo"] != "—"
    textos = " ".join(str(item.value) for grupo in (at.caption, at.get("html")) for item in grupo)
    assert "registros persistidos da planta" in textos
    assert "Origem" in textos and "sintético" in textos
    assert "Unidade:" in textos
    assert not any("sem dados carregados" in item.value for item in at.caption)
    assert any("dados persistidos selecionados" in item.value for item in at.caption)
    assert "arquivos" not in at.session_state
