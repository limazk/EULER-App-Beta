"""Persistência integrada: sessão nova, isolamento e resultados históricos."""

import importlib
import sys
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[1] / "app"
sys.path.insert(0, str(APP))


@pytest.fixture
def ambiente(tmp_path, monkeypatch):
    import streamlit as st

    monkeypatch.setenv("EULER_DADOS_DIR", str(tmp_path / "plantas"))
    sessao = {}
    monkeypatch.setattr(st, "session_state", sessao)
    estado = importlib.import_module("estado")
    armazenamento = importlib.import_module("armazenamento")
    yield estado, armazenamento, sessao



def test_repositorio_beta_isola_biblioteca_por_organizacao(ambiente, monkeypatch):
    _, arm, _ = ambiente
    auth = importlib.import_module("auth")

    monkeypatch.setattr(
        auth,
        "contexto_atual",
        lambda: {
            "user_id": "usuario-a",
            "is_superadmin": False,
            "memberships": [{"organization_id": "11111111-1111-1111-1111-111111111111"}],
        },
    )
    raiz_a = arm.repositorio().raiz

    monkeypatch.setattr(
        auth,
        "contexto_atual",
        lambda: {
            "user_id": "usuario-b",
            "is_superadmin": False,
            "memberships": [{"organization_id": "22222222-2222-2222-2222-222222222222"}],
        },
    )
    raiz_b = arm.repositorio().raiz

    assert raiz_a != raiz_b
    assert raiz_a.parent.name == "tenants"
    assert raiz_b.parent.name == "tenants"
    assert raiz_a.name == "11111111-1111-1111-1111-111111111111"
    assert raiz_b.name == "22222222-2222-2222-2222-222222222222"


def test_repositorio_beta_recusa_usuario_sem_organizacao(ambiente, monkeypatch):
    _, arm, _ = ambiente
    auth = importlib.import_module("auth")
    monkeypatch.setattr(
        auth,
        "contexto_atual",
        lambda: {"user_id": "usuario", "is_superadmin": False, "memberships": []},
    )
    with pytest.raises(ValueError, match="organização"):
        arm.repositorio()

def test_reabrir_apos_sessao_nova_preserva_original_altitude_e_sintetico(ambiente):
    estado, arm, sessao = ambiente
    planta = arm.repositorio().criar_planta("Planta A")
    arquivos = {"diario.csv": b"caldeira_id,instante_observado\nA,2026-01-01T00:00:00Z\n"}
    estado.definir_arquivos(arquivos, "ensaio", sinteticos=True)
    sessao["altitude_m"] = 123.0
    versao = arm.salvar_sessao(planta, autor="Ana", motivo="Importação inicial")
    sessao.clear()
    arm.abrir_importacao(planta, versao["id"])
    assert dict(sessao["arquivos"]) == arquivos
    assert sessao["altitude_m"] == 123.0
    assert sessao["dados_sinteticos"] is True
    assert sessao["persistencia"]["planta_id"] == planta["id"]


def test_resultado_e_periodos_reabrem_mas_nao_migram_para_outra_planta(ambiente):
    estado, arm, sessao = ambiente
    a, b = [arm.repositorio().criar_planta(n) for n in ("A", "B")]
    estado.definir_arquivos({"diario.csv": b"teste"}, "teste", True)
    v = arm.salvar_sessao(a, autor="Ana", motivo="Inicial")
    sig = estado.assinatura()
    sessao["periodos_escolhidos"] = {"assinatura": sig, "ref": (0, 1), "comp": (2, 3)}
    estado.guardar_investigacao({"teste": "resultado"})
    sessao.clear()
    arm.abrir_importacao(a, v["id"])
    assert estado.investigacao_atual()[0] == {"teste": "resultado"}
    assert sessao["periodos_escolhidos"]["ref"] == (0, 1)
    arm.salvar_sessao(b, autor="Bia", motivo="Outro local")
    assert estado.assinatura() != sig
    assert estado.investigacao_atual()[0] is None
    assert "periodos_escolhidos" not in sessao


def test_limpar_ou_trocar_demo_desvincula_sem_apagar_banco(ambiente):
    estado, arm, sessao = ambiente
    p = arm.repositorio().criar_planta("A")
    estado.definir_arquivos({"diario.csv": b"teste"}, "teste", True)
    v = arm.salvar_sessao(p, autor="Ana", motivo="Inicial")
    estado.definir_arquivos({"diario.csv": b"outro"}, "demo", True)
    assert "persistencia" not in sessao
    estado.guardar_investigacao({"demo": True})
    assert arm.repositorio().listar_analises(p["id"], v["id"]) == []
    estado.limpar_dados()
    assert len(arm.repositorio().listar_importacoes(p["id"])) == 1


def test_mudar_altitude_nao_grava_analise_na_versao_errada(ambiente):
    estado, arm, sessao = ambiente
    p = arm.repositorio().criar_planta("A")
    estado.definir_arquivos({"diario.csv": b"teste"}, "teste", True)
    v = arm.salvar_sessao(p, autor="Ana", motivo="Inicial")
    sessao["altitude_m"] = 500.0
    estado.guardar_investigacao({"modificado": True})
    assert arm.repositorio().listar_analises(p["id"], v["id"]) == []
    assert "não corresponde" in sessao["persistencia_erro"]


def test_codigo_diferente_nao_reutiliza_analise_historica(ambiente):
    estado, arm, sessao = ambiente
    p = arm.repositorio().criar_planta("A")
    estado.definir_arquivos({"diario.csv": b"teste"}, "teste", True)
    v = arm.salvar_sessao(p, autor="Ana", motivo="Inicial")
    arm.repositorio().salvar_analise(
        p["id"],
        v["id"],
        assinatura="motor-antigo",
        resultado={"investigacao": {"antigo": True}, "periodos_escolhidos": None},
    )
    sessao.clear()
    arm.abrir_importacao(p, v["id"])
    assert estado.investigacao_atual()[0] is None
    assert "versão do motor" in sessao["persistencia_aviso"]


def test_falha_ao_salvar_nova_importacao_preserva_dados_ativos(ambiente, monkeypatch):
    estado, arm, sessao = ambiente
    p = arm.repositorio().criar_planta("A")
    estado.definir_arquivos({"diario.csv": b"original"}, "teste", True)
    arm.salvar_sessao(p, autor="Ana", motivo="Inicial")
    anterior = dict(sessao)
    with pytest.raises(ValueError):
        arm.importar_na_planta({"novo.csv": b"novo"}, 500, autor="", motivo="")
    assert sessao == anterior


def test_analise_historica_de_outro_formato_nao_quebra_abertura(ambiente):
    estado, arm, sessao = ambiente
    p = arm.repositorio().criar_planta("A")
    estado.definir_arquivos({"diario.csv": b"teste"}, "teste", True)
    v = arm.salvar_sessao(p, autor="Ana", motivo="Inicial")
    arm.repositorio().salvar_analise(
        p["id"], v["id"], assinatura=estado.assinatura(), resultado={"outro_formato": True}
    )
    sessao.clear()
    arm.abrir_importacao(p, v["id"])
    assert estado.investigacao_atual()[0] is None
    assert "formato" in sessao["persistencia_aviso"]


def test_fluxo_interface_salva_analisa_e_reabre_em_nova_sessao(tmp_path, monkeypatch):
    """Exercita formulários reais e a análise completa, sem simular o motor."""
    from streamlit.testing.v1 import AppTest

    from euler.persistencia import Repositorio

    raiz = tmp_path / "biblioteca"
    monkeypatch.setenv("EULER_DADOS_DIR", str(raiz))

    def abrir():
        return AppTest.from_file(str(APP / "main.py"), default_timeout=60).run()

    def clicar(at, rotulo):
        next(b for b in at.button if b.label == rotulo).click().run()
        assert not at.exception, at.exception

    at = abrir()
    at.switch_page("paginas/importar.py").run()
    clicar(at, "Ato 1 · caso completo")
    originais = at.session_state["arquivos"]
    at.switch_page("paginas/plantas.py").run()
    next(t for t in at.text_input if t.label == "Nome da planta").set_value("Planta sintética QA")
    clicar(at, "Criar planta")
    at.text_input(key="salvar_autor").set_value("Teste automatizado")
    at.text_input(key="salvar_motivo").set_value("Primeira versão")
    clicar(at, "Salvar versão nesta planta")
    ctx = at.session_state["persistencia"]
    repo = Repositorio(raiz)
    assert len(repo.listar_importacoes(ctx["planta_id"])) == 1
    at.switch_page("paginas/investigacao.py").run()
    assert not at.exception, at.exception
    assert "persistencia_erro" not in at.session_state
    resultado = at.session_state["investigacao"]["json"]
    periodos = at.session_state["periodos_escolhidos"]
    assert len(repo.listar_analises(ctx["planta_id"], ctx["importacao_id"])) == 1

    nova = abrir()
    assert "arquivos" not in nova.session_state
    nova.switch_page("paginas/plantas.py").run()
    clicar(nova, "Abrir versão")
    assert nova.session_state["arquivos"] == originais
    assert nova.session_state["altitude_m"] == 1000.0
    assert nova.session_state["investigacao"]["json"] == resultado
    assert nova.session_state["periodos_escolhidos"] == periodos
    nova.switch_page("paginas/financeiro.py").run()
    assert not nova.exception, nova.exception
    assert len(repo.listar_analises(ctx["planta_id"], ctx["importacao_id"])) == 1
