"""Caso de demonstração: gerado de forma determinística e coerente com o gabarito (T18)."""

import importlib.util
from pathlib import Path

import pytest

from euler.combustivel import extrato_por_fornecedor, frase_tonelada_vs_energia
from euler.io import importar_pasta
from euler.vapor import p_atm_por_altitude_bar

DEMO = Path(__file__).resolve().parents[1] / "demo"


def _gerador():
    spec = importlib.util.spec_from_file_location("gerar_caso_demo", DEMO / "gerar_caso_demo.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def test_arquivos_do_demo_estao_em_dia_com_o_gerador():
    for nome, conteudo in _gerador().gerar().items():
        atual = (DEMO / "caso_demo" / nome).read_text(encoding="utf-8")
        assert atual == conteudo, f"rode: python demo/gerar_caso_demo.py ({nome})"


def test_gerador_nao_usa_o_motor_euler():
    codigo = (DEMO / "gerar_caso_demo.py").read_text(encoding="utf-8")
    assert "import euler" not in codigo and "from euler" not in codigo


@pytest.fixture(scope="module")
def pacote_demo():
    return importar_pasta(DEMO / "caso_demo", p_atm_bar=p_atm_por_altitude_bar(1000))


def test_demo_importa_sem_erros(pacote_demo):
    assert not [a for a in pacote_demo.avisos if a.gravidade == "erro"]
    tipos = {a.tipo for a in pacote_demo.avisos}
    assert {"lacuna", "totalizador_reiniciado", "registro_tardio", "lote_sem_umidade"} <= tipos


def test_demo_conta_a_historia_do_extrato(pacote_demo):
    e = extrato_por_fornecedor(pacote_demo.dados("combustivel"), pacote_demo.dados("amostras"))
    f = e.fornecedores.set_index("fornecedor_id")
    assert f.loc["F3", "posicao_tonelada"] == 1
    assert f.loc["F1", "posicao_energia"] == 1
    assert f.loc["F3", "umidade_recente"] - f.loc["F3", "umidade_referencia"] > 0.08
    alertas = e.alertas_umidade["fornecedor_id"].value_counts()
    assert alertas.get("F3", 0) > 5 * alertas.drop("F3", errors="ignore").sum()
    assert frase_tonelada_vs_energia(e.fornecedores).startswith("F3")
