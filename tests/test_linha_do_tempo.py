"""Linha do tempo financeira (D103): lê os fechamentos gravados, sem número novo."""

from pathlib import Path

import pytest

from euler import acompanhamento as ac
from euler.fechamento import criar_referencia, produzir_fechamento
from euler.linha_do_tempo import _leitura, linha_do_tempo
from euler.periodos import periodos_entre_estoques
from euler.persistencia import Repositorio

RAIZ = Path(__file__).resolve().parents[1]
EQ = "CALD-DEMO-01"


@pytest.fixture
def armazem(tmp_path, monkeypatch):
    monkeypatch.setenv("EULER_DADOS_DIR", str(tmp_path / "dados"))
    repo = Repositorio()
    planta = repo.criar_planta("Linha do tempo", classe="sintetico")
    a = repo.armazem(planta["id"])
    a.criar_equipamento(EQ, "Caldeira A", EQ, config={"altitude_m": 1000.0}, autor="Teste")
    arquivos = {p.name: p.read_bytes() for p in (RAIZ / "demo/caso_demo_completo").glob("*.csv")}
    a.confirmar(a.previa(EQ, arquivos), autor="Teste")
    yield a
    a.fechar()


def test_sem_fechamento_a_linha_do_tempo_diz_onde_comeca(armazem):
    lt = linha_do_tempo(armazem, EQ)
    assert lt["periodos"] == []
    assert "primeiro período fechado" in lt["leitura"][0]


def test_fechamentos_gravados_viram_periodos_comparaveis(armazem):
    s = periodos_entre_estoques(armazem.pacote(EQ))
    criar_referencia(armazem, EQ, s[0][0], s[3][1], "inicial", "Base", "Teste")
    f1 = produzir_fechamento(armazem, EQ, "Teste")
    inv = ac.abrir_do_fechamento(armazem, f1["id"], "Teste")
    meio = s[5][0] + (s[5][1] - s[5][0]) / 2
    ac.registrar_intervencao(
        armazem, EQ, meio, "limpeza", "Limpeza dos tubos", "Teste", investigacao_id=inv["id"]
    )
    produzir_fechamento(armazem, EQ, "Teste")
    lt = linha_do_tempo(armazem, EQ)
    p1, p2 = lt["periodos"]

    c = f1["resultado"]["nucleo"]["explicacao_conta"]
    assert p1["custo_brl"] == c["consumido"]["custo_brl"]
    assert p1["desvio_brl"] == c["desvio"]["custo_brl"]
    assert p1["dias"] == pytest.approx(14)
    assert p1["custo_por_dia_brl"] == pytest.approx(p1["custo_brl"] / 14)
    assert p1["custo_por_t_vapor_brl"] == pytest.approx(p1["custo_brl"] / p1["vapor_t"])
    assert [x["descricao"] for x in p1["acoes"]] == ["Limpeza dos tubos"]
    assert p1["acoes"][0]["avaliacao"] is None

    # o caso sintético não tem totalizador de vapor nessa semana: a conta não é inventada
    assert p2["custo_brl"] is None and p2["estado"] is None
    assert p2["qualidade"] == "conta indisponível"

    texto = " ".join(lt["leitura"])
    assert "não tem conta disponível" in texto
    assert "ainda não avaliada" in texto
    assert "durações diferentes" in texto
    assert "conta incompleta" in texto


def _p(estado, versao=1, dias=7.0, qualidade="completa", acoes=()):
    return {
        "estado": estado,
        "referencia_versao": versao,
        "dias": dias,
        "qualidade": qualidade,
        "qualidade_motivo": "x.",
        "acoes": list(acoes),
    }


def test_leitura_distingue_repetindo_apareceu_agora_e_dentro_da_incerteza():
    assert "Está se repetindo" in _leitura([_p("acima"), _p("acima"), _p("acima")])[0]
    assert "últimos 3 fechamentos" in _leitura([_p("acima")] * 3)[0]
    assert "Apareceu agora" in _leitura([_p("nao_estabelecido"), _p("acima")])[0]
    assert "cabe na incerteza" in _leitura([_p("acima"), _p("nao_estabelecido")])[0]
    assert "não é economia verificada" in _leitura([_p("abaixo")])[0]
    assert "não pode ser classificado" in _leitura([_p("sem_faixa")])[0]


def test_leitura_avisa_quando_a_referencia_muda_de_versao():
    texto = " ".join(_leitura([_p("acima", versao=1), _p("acima", versao=2)]))
    assert "não são diretamente comparáveis" in texto


def test_melhora_so_e_afirmada_pela_avaliacao_registrada():
    acao = {"id": 1, "data": "2026-09-10", "descricao": "Limpeza", "avaliacao": None}
    texto = " ".join(_leitura([_p("acima"), _p("nao_estabelecido", acoes=[acao])]))
    assert "ainda não avaliada" in texto
    avaliada = {**acao, "avaliacao": "Diferença observada dentro da incerteza."}
    texto = " ".join(_leitura([_p("acima"), _p("nao_estabelecido", acoes=[avaliada])]))
    assert "Diferença observada dentro da incerteza." in texto


def test_desvio_por_tonelada_e_o_mesmo_desvio_dividido_pelo_vapor(armazem):
    s = periodos_entre_estoques(armazem.pacote(EQ))
    criar_referencia(armazem, EQ, s[0][0], s[1][1], "inicial", "Base", "Teste")
    produzir_fechamento(armazem, EQ, "Teste", inicio=s[2][0], fim=s[2][1])
    (p,) = linha_do_tempo(armazem, EQ)["periodos"]
    assert p["desvio_brl"] is not None and p["vapor_t"]
    assert p["desvio_por_t_vapor_brl"] == pytest.approx(p["desvio_brl"] / p["vapor_t"])
    assert p["faixa_por_t_vapor_brl"] == pytest.approx([x / p["vapor_t"] for x in p["faixa_brl"]])


def test_tela_mostra_linha_do_tempo_sem_inventar_valor(armazem):
    from streamlit.testing.v1 import AppTest

    s = periodos_entre_estoques(armazem.pacote(EQ))
    criar_referencia(armazem, EQ, s[0][0], s[1][1], "inicial", "Base", "Teste")
    for ini, fim in s[2:]:
        produzir_fechamento(armazem, EQ, "Teste", inicio=ini, fim=fim)
    at = AppTest.from_file(str(RAIZ / "app/main.py"), default_timeout=120).run()
    at.switch_page("paginas/financeiro.py").run()
    at.radio(key="fin_origem").set_value("Fechamentos da planta").run()
    assert not at.exception, at.exception
    textos = " ".join(str(x.value) for g in (at.markdown, at.caption) for x in g)
    assert "Linha do tempo dos fechamentos" in textos
    assert "conta incompleta (conta indisponível)" in textos
    assert "ficam fora do gráfico, sem zero" in textos
    (tabela,) = [d.value for d in at.dataframe if "Situação" in d.value.columns]
    assert len(tabela) == len(s) - 2
    sem_conta = tabela[tabela["Qualidade da conta"] == "conta indisponível"]
    assert len(sem_conta) == 1
    assert sem_conta.iloc[0]["Desvio"] == "—" and sem_conta.iloc[0]["Situação"] == (
        "Conta indisponível"
    )

    at.radio(key=f"lt_modo_{EQ}").set_value("Por tonelada de vapor (R$/t)").run()
    assert not at.exception, at.exception


def test_serie_ate_um_fechamento_nao_olha_para_frente(armazem):
    s = periodos_entre_estoques(armazem.pacote(EQ))
    criar_referencia(armazem, EQ, s[0][0], s[1][1], "inicial", "Base", "Teste")
    f1 = produzir_fechamento(armazem, EQ, "Teste", inicio=s[2][0], fim=s[2][1])
    produzir_fechamento(armazem, EQ, "Teste", inicio=s[3][0], fim=s[3][1])
    ate = linha_do_tempo(armazem, EQ, ate_fechamento=f1["id"])
    assert [p["fechamento_id"] for p in ate["periodos"]] == [f1["id"]]
    assert len(linha_do_tempo(armazem, EQ)["periodos"]) == 2


def test_padrao_e_a_leitura_sem_as_linhas_das_acoes():
    acao = {"id": 1, "data": "2026-09-10", "descricao": "Limpeza", "avaliacao": None}
    ps = [_p("acima"), _p("acima", acoes=[acao])]
    assert any("Limpeza" in x for x in _leitura(ps))
    assert not any("Limpeza" in x for x in _leitura(ps, com_acoes=False))
    assert _leitura(ps, com_acoes=False)[0] == _leitura(ps)[0]
