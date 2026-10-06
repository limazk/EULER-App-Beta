"""Caminho único da planta nas telas (D102): percurso, dados salvos e análise temporária."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest
from test_app import abrir_com_demo

from euler.fechamento import criar_referencia, produzir_fechamento
from euler.periodos import periodos_entre_estoques
from euler.persistencia import Repositorio

RAIZ = Path(__file__).resolve().parents[1]
EQ = "CALD-DEMO-01"


def textos(at: AppTest) -> str:
    return "\n".join(
        str(x.value) for g in (at.markdown, at.caption, at.info, at.warning) for x in g
    )


@pytest.fixture
def planta(tmp_path, monkeypatch):
    monkeypatch.setenv("EULER_DADOS_DIR", str(tmp_path / "dados"))
    repo = Repositorio()
    p = repo.criar_planta("Planta do percurso", classe="sintetico")
    a = repo.armazem(p["id"])
    a.criar_equipamento(EQ, "Caldeira A", EQ, config={"altitude_m": 1000}, autor="Teste")
    arquivos = {x.name: x.read_bytes() for x in (RAIZ / "demo/caso_demo_completo").glob("*.csv")}
    a.confirmar(a.previa(EQ, arquivos), autor="Teste")
    s = periodos_entre_estoques(a.pacote(EQ))
    criar_referencia(a, EQ, s[0][0], s[3][1], "inicial", "Base", "Teste")
    produzir_fechamento(a, EQ, "Teste")
    a.fechar()
    return p


def abrir(pagina: str) -> AppTest:
    at = AppTest.from_file(str(RAIZ / "app/main.py"), default_timeout=120).run()
    at.switch_page(pagina).run()
    assert not at.exception, at.exception
    return at


def test_minha_planta_mostra_os_cinco_passos_e_o_proximo(planta):
    t = textos(abrir("paginas/painel.py"))
    assert "Percurso da planta" in t
    for i, passo in enumerate(
        ("Enviar registros", "Conferir a conta", "Investigar", "Registrar ação"), 1
    ):
        assert f"**{i}. {passo}**" in t
    assert "Dados salvos da planta" in t
    # com um fechamento que pede verificação e nenhuma investigação, investigar está pendente
    assert "ainda não virou investigação" in t


@pytest.mark.parametrize(
    ("pagina", "destaque"),
    [
        ("paginas/acompanhamento.py", "**1. Enviar registros**"),
        ("paginas/fechamentos.py", "**2. Conferir a conta**"),
        ("paginas/acoes.py", "**3. Investigar**"),
    ],
)
def test_telas_da_planta_dizem_o_passo_e_que_os_dados_sao_salvos(planta, pagina, destaque):
    t = textos(abrir(pagina))
    assert "Dados salvos da planta" in t
    assert "Percurso:" in t and destaque in t


def test_telas_de_analise_avisam_que_a_analise_e_temporaria():
    at = abrir_com_demo("saude.py")
    assert not at.exception, at.exception
    assert any("Análise temporária" in c.value for c in at.caption)
    assert any("Salve em Plantas e histórico" in c.value for c in at.caption)
