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


def _tabela(nome: str):
    import io

    import pandas as pd

    return pd.read_csv(io.StringIO(_gerador().gerar()[nome]), dtype=str)


def test_regressao_totalizador_conta_durante_a_lacuna_do_diario():
    """Correção do gerador (Etapa 5): o medidor continua contando quando ninguém anota.

    Antes, o totalizador só avançava nas linhas anotadas; atravessando a lacuna de ~1,5 dia
    ele subia como se fosse um único intervalo de 2 h. Verificação sem o motor: a vazão média
    calculada através da lacuna fica perto da vazão típica das outras leituras."""
    import pandas as pd

    g = _gerador()
    d = _tabela("diario.csv")
    d = d[d["totalizador_vapor_t"].notna()].copy()
    d["t"] = pd.to_datetime(d["instante_observado"], utc=True)
    d["tot"] = d["totalizador_vapor_t"].astype(float)
    antes = d[d["t"] < pd.Timestamp(g.LACUNA[0])].iloc[-1]
    depois = d[d["t"] >= pd.Timestamp(g.LACUNA[1])].iloc[0]
    horas = (depois["t"] - antes["t"]).total_seconds() / 3600
    vazao_lacuna = (depois["tot"] - antes["tot"]) / horas
    normal = d[d["t"] < pd.Timestamp(g.LACUNA[0])]
    vazao_tipica = (normal["tot"].iloc[-1] - normal["tot"].iloc[0]) / (
        (normal["t"].iloc[-1] - normal["t"].iloc[0]).total_seconds() / 3600
    )
    assert horas > 30  # a lacuna existe
    assert vazao_lacuna == pytest.approx(vazao_tipica, rel=0.2)


def test_regressao_entregas_do_dia_antes_da_proxima_medicao_de_estoque():
    """Invariante do gerador (protege a correção da Etapa 5): o estoque simulado soma as
    entregas do dia antes de descontar o consumo, então toda entrega precisa ter horário
    anterior à medição de estoque da manhã seguinte (07:30); senão o balanço E9 do arquivo
    deixa de bater com o combustível simulado. Quem garante isso é o limite de 6 caminhões
    por dia com 3,5 h de intervalo (até ~19h20); a fórmula antiga não tinha limite. Com a
    semente atual a versão antiga não chegou a violar a regra: este teste é uma proteção,
    não a reprodução de uma falha observada."""
    import pandas as pd

    g = _gerador()
    c = _tabela("combustivel.csv")
    t = pd.to_datetime(c.loc[c["tipo"] == "recebimento", "data"], utc=True)
    inicio = pd.Timestamp(g.INICIO)
    dia = ((t - inicio) // pd.Timedelta(days=1)).astype(int)
    proxima_medicao = inicio + pd.to_timedelta(dia + 1, unit="D") - pd.Timedelta(minutes=30)
    assert (t < proxima_medicao).all()
    assert (t > inicio + pd.to_timedelta(dia, unit="D")).all()


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
    assert (
        f.loc["F3", "posicao_energia"] == 3
    )  # o mais barato por tonelada é o mais caro por energia
    assert f.loc["F3", "umidade_recente"] - f.loc["F3", "umidade_referencia"] > 0.08
    alertas = e.alertas_umidade["fornecedor_id"].value_counts()
    assert alertas.get("F3", 0) > 5 * alertas.drop("F3", errors="ignore").sum()
    assert frase_tonelada_vs_energia(e.fornecedores).startswith("F3")


def test_demo_conta_a_historia_da_investigacao(pacote_demo):
    from euler.investigacao import investigar
    from euler.periodos import periodos_entre_estoques

    s = periodos_entre_estoques(pacote_demo)
    base = (s[0][0], s[3][1])

    def sustentadas(comp):
        j = investigar(pacote_demo, base, comp)
        return {h["id"] for h in j["hipoteses"] if h["status"] == "sustentada"}, j

    # Auditoria A3 (01/10/2026): o demo não cadastra a incerteza do método de umidade, então a
    # subida da umidade recebida é só 'condicional' (real se o erro da estufa se repetir).
    # A EULER se abstém e pede o cadastro; a umidade fecharia a mudança se confirmada (D53).
    def umidade(j):
        return next(h for h in j["hipoteses"] if h["id"] == "umidade_combustivel")

    causas, j = sustentadas((s[4][0], s[5][1]))
    assert causas == {"temperatura_gases"}
    assert umidade(j)["avaliacao"]["mudanca_detectavel"] == "condicional"
    assert j["o_que_mudou"]["fechamento"]["veredito_com_condicionais"] == "fecha"
    assert j["conclusao"]["abstencao"] is True
    assert j["proxima_verificacao"]["acao"].startswith("Cadastrar em instrumentos.csv")
    causas, j = sustentadas(s[6])
    assert j["conclusao"]["abstencao"] is True
    causas, j = sustentadas(s[7])
    assert causas == set()
    assert umidade(j)["avaliacao"]["mudanca_detectavel"] == "condicional"
    assert j["o_que_mudou"]["fechamento"]["veredito_com_condicionais"] == "fecha"
