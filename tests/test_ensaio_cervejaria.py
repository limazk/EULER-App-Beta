"""Planta brasileira real (MDL 1202): contas independentes, lacunas preservadas e abstenção.

As contas de conferência usam só a biblioteca padrão (csv) e a IAPWS direto, não as funções
do módulo testado. Os totais são conferidos contra o relatório de verificação publicado.
"""

import csv
import hashlib
import json
from itertools import pairwise
from math import isclose, sqrt

import pytest
from ensaio_cervejaria import DADOS, PERIODOS, carregar, executar
from iapws import IAPWS97

FONTES = json.loads((DADOS / "fontes.json").read_text(encoding="utf-8"))


def _linhas() -> list[dict]:
    with open(DADOS / "diario.csv", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _f(texto: str) -> float | None:
    return None if texto == "" else float(texto)


@pytest.fixture(scope="module")
def r():
    return executar()


def test_arquivos_sao_os_publicados_e_conferidos():
    for nome, info in FONTES["arquivos"].items():
        assert hashlib.sha256((DADOS / nome).read_bytes()).hexdigest() == info["sha256"], nome


def test_csv_e_copia_fiel_da_planilha_original():
    """Sem alterar valores: cada célula do CSV é a da planilha (vazia continua vazia)."""
    pytest.importorskip("xlrd")
    import math
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    from extrair_cervejaria import extrair

    planilha = extrair()
    csv_ = carregar()
    assert len(planilha) == len(csv_) == 660
    for coluna in planilha.columns:
        if coluna == "data":
            assert list(planilha.data) == [f"{x:%Y-%m-%d}" for x in csv_.data]
            continue
        for a, b in zip(planilha[coluna], csv_[coluna], strict=True):
            assert (math.isnan(a) and math.isnan(b)) or a == b, coluna


def test_totais_reproduzem_o_relatorio_de_verificacao(r):
    linhas = _linhas()
    vapor = sum(_f(x[c]) or 0 for x in linhas for c in ("cald1_vapor_t", "cald2_vapor_t"))
    casca = sum(_f(x[c]) or 0 for x in linhas for c in ("casca_arroz_t", "casca_carvalho_t"))
    oleo = sum(_f(x["oleo_equivalente_t"]) or 0 for x in linhas)
    verificado = FONTES["fatos_documentados"]["totais_verificados"]
    assert round(vapor) == verificado["vapor_t"] == 218123
    assert round(casca) == verificado["biomassa_t"] == 49566
    assert round(oleo) == verificado["oleo_equivalente_t"] == 1530
    t = r["conferencia"]["totais"]
    assert t["vapor_t"] == pytest.approx(vapor) and t["biomassa_t"] == pytest.approx(casca)
    assert all(r["conferencia"]["confere_com_verificacao"].values())


def test_lacunas_sao_contadas_e_nunca_viram_zero(r):
    linhas = _linhas()
    c = r["conferencia"]
    assert c["dias"] == 660 and c["dias_fora_do_calendario"] == 0 and c["datas_repetidas"] == 0
    sem_vapor = [x for x in linhas if x["cald1_vapor_t"] == "" and x["cald2_vapor_t"] == ""]
    assert c["dias_sem_vapor_registrado"] == len(sem_vapor) == 31
    assert c["celulas_vazias"]["casca de arroz"] == sum(x["casca_arroz_t"] == "" for x in linhas)
    # a coluna de total da planilha tem 3 dias em branco: somar só ela perde 805,79 t
    assert c["total_diario_em_branco"] == ["30/11/2008", "30/12/2008", "30/01/2009"]
    assert c["vapor_dos_totais_em_branco_t"] == pytest.approx(805.79)
    assert c["totais"]["vapor_t"] - c["totais"]["vapor_coluna_total_t"] == pytest.approx(805.79)
    assert c["energia_em_branco"] == [(1, "30/11/2008")]


def test_registros_acima_da_capacidade_nominal(r):
    cap = FONTES["fatos_documentados"]["caldeiras"]["capacidade_t_h"]
    esperado = []
    for x in _linhas():
        for n in (1, 2):
            h, v = _f(x[f"cald{n}_horas"]), _f(x[f"cald{n}_vapor_t"])
            if h is not None and v is not None and v > cap * h:
                esperado.append((x["data"], n))
    achados = r["conferencia"]["acima_da_capacidade"]
    assert len(achados) == len(esperado) == 7
    pior = max(achados, key=lambda a: a["pct_capacidade"])
    assert (pior["data"], pior["caldeira"]) == ("07/04/2008", 2)
    assert pior["media_t_h"] == pytest.approx(593.92 / 19)
    assert any(a["data"] == "10/04/2008" and a["vapor_t"] == 709.64 for a in achados)


def test_casca_do_dia_nao_e_a_queimada_no_dia(r):
    """A dispersão diária só cabe em entrega/estoque; em 30 dias ela quase some."""
    p5_1, _, p95_1 = r["conferencia"]["razao_vapor_biomassa"][1]
    p5_30, _, p95_30 = r["conferencia"]["razao_vapor_biomassa"][30]
    assert p95_1 / p5_1 > 5
    assert p95_30 / p5_30 < 1.3


def test_entalpia_da_planilha_confere_com_iapws(r):
    maior = 0.0
    for x in _linhas():
        for n in (1, 2):
            p, h = _f(x[f"cald{n}_p_vapor_kgf_cm2"]), _f(x[f"cald{n}_entalpia_tj_t"])
            if p and h:
                # tabela da planilha: 0 kgf/cm² a 99,09 °C, isto é, 1 kgf/cm² absoluto
                hg = IAPWS97(P=(p + 1) * 0.0980665, x=1).h
                maior = max(maior, abs(h * 1e6 / hg - 1))
    assert maior < 1e-3
    e = r["entalpia"]
    assert max(abs(e["tabela"]["min_pct"]), abs(e["tabela"]["max_pct"])) == pytest.approx(
        100 * maior
    )
    assert e["dias_caldeira"] == 1171


def _periodo(linhas, inicio, fim):
    x = [y for y in linhas if inicio <= y["data"] <= fim]
    vapor = sum(_f(y[c]) or 0 for y in x for c in ("cald1_vapor_t", "cald2_vapor_t"))
    casca = sum(_f(y[c]) or 0 for y in x for c in ("casca_arroz_t", "casca_carvalho_t"))
    return x, vapor, casca


def test_comparacao_entre_periodos_conferida_a_mao(r):
    linhas = _linhas()
    (_, (ia, fa)), (_, (ib, fb)) = PERIODOS.items()
    _, va, ma = _periodo(linhas, ia, fa)
    xb, vb, mb = _periodo(linhas, ib, fb)
    ca, cb = ma / va, mb / vb
    c = r["comparacao"]
    assert c["comparacao"].referencia == pytest.approx(ca)
    assert c["comparacao"].comparacao == pytest.approx(cb)
    assert c["variacao_pct"] == pytest.approx(100 * (cb / ca - 1))
    assert c["variacao_pct"] == pytest.approx(-8.53, abs=0.01)
    # estoque que explicaria a diferença inteira, em cada período
    assert c["estoque_2o_periodo_t"] == pytest.approx(ca * vb - mb)
    assert c["estoque_1o_periodo_t"] == pytest.approx(ma - cb * va)
    assert c["estoque_2o_periodo_dias"] == pytest.approx((ca * vb - mb) / (mb / len(xb)))
    assert c["medidor_vapor_pct"] == pytest.approx(100 * (ca / cb - 1))


def test_incerteza_da_balanca_por_epoca_conferida_a_mao(r):
    """2% sem tipo → limite, u = 2/√3 % (D35); a época comum aos dois períodos tem r = 1."""
    linhas = _linhas()
    (_, (ia, fa)), (_, (ib, fb)) = PERIODOS.items()
    cortes = ["2007-11-05", *FONTES["fatos_documentados"]["balanca"]["calibracoes"], "9999"]
    u = 0.02 / sqrt(3)

    def contribs(inicio, fim, sinal):
        x, v, m = _periodo(linhas, inicio, fim)
        out = {}
        for a, b in pairwise(cortes):
            massa = sum(
                _f(y[c]) or 0
                for y in x
                if a <= y["data"] < b
                for c in ("casca_arroz_t", "casca_carvalho_t")
            )
            if massa:
                out[a] = sinal * (m / v) * (massa / m) * u
        return out

    ka, kb = contribs(ia, fa, -1), contribs(ib, fb, +1)
    comuns = set(ka) & set(kb)
    assert comuns == {"2008-03-28"}  # a mesma calibração da balança vale nos dois períodos
    var_r0 = sum(x * x for x in [*ka.values(), *kb.values()])
    var_r1 = sum(x * x for k, x in ka.items() if k not in comuns) + sum(
        x * x for k, x in kb.items() if k not in comuns
    )
    var_r1 += sum((ka[k] + kb[k]) ** 2 for k in comuns)
    cmp = r["comparacao"]["comparacao"]
    assert cmp.incerteza_delta_correlacionada == pytest.approx(2 * sqrt(min(var_r0, var_r1)))
    assert abs(cmp.delta) > cmp.incerteza_delta_correlacionada


def test_abstencao_honesta(r):
    """Estoque e medidor de vapor sem incerteza: a diferença não fica estabelecida."""
    cmp = r["comparacao"]["comparacao"]
    assert cmp.detectabilidade is None and cmp.detectavel is None
    assert cmp.incerteza_delta is None
    assert any("estoque" in f for f in cmp.faltam)
    assert any("medidores de vapor" in f for f in cmp.faltam)
    texto = r["conclusao"]
    assert "não basta" in texto and "estoque do galpão" in texto
    for proibido in ("comprovad", "economia", "garantid", "R$"):
        assert proibido not in texto
    assert any("dinheiro" in b for b in r["bloqueado"])
    assert any("Eficiência" in b for b in r["bloqueado"])


def test_sensibilidade_a_escolha_dos_periodos(r):
    """Outros cortes do mesmo registro, conferidos à mão: nenhum depende do corte escolhido."""
    linhas = _linhas()
    s = r["sensibilidade"]
    meio = linhas[len(linhas) // 2]["data"]
    _, v1, m1 = _periodo(linhas, linhas[0]["data"], "2008-09-29")
    _, v2, m2 = _periodo(linhas, meio, linhas[-1]["data"])
    assert meio == "2008-09-30"
    assert [b["consumo_t_t"] for b in s["metades"]] == pytest.approx([m1 / v1, m2 / v2])
    assert [b["dias"] for b in s["metades"]] == [330, 330]
    assert sum(b["dias"] for b in s["epocas_balanca"]) == 660
    assert sum(b["dias"] for b in s["epocas_medidor_vapor"]) == 660


def test_hipoteses_tem_verificacao_e_nenhuma_e_causa(r):
    hs = r["hipoteses"]
    assert len(hs) == 6
    assert all(h["verificacao"] for h in hs)
    textos = " ".join(h["o_que_os_registros_mostram"] for h in hs)
    assert "causa" not in textos
    assert "Compatível, não é prova" in textos
    m = r["mensal"]
    assert m["n_meses"] == 22
    assert isclose(sum(x["dias"] for x in m["meses"]), 660)


def test_tela_mostra_a_planta_brasileira_primeiro_e_se_abstem():
    from test_app import abrir_com_demo

    at = abrir_com_demo("dados_publicos.py")
    assert not at.exception, at.exception
    abas = [t.label for t in at.tabs]  # inclui as abas internas, na ordem da página
    assert abas[:5] == [
        "Planta brasileira · RS",
        "Resposta",
        "Conferência dos registros",
        "Hipóteses e próximas medições",
        "Fontes",
    ]
    assert abas[5] == "Caldeiras EPA · EUA"
    assert any("660 dias de duas caldeiras" in h.value for h in at.subheader)
    assert any("não basta para dizer" in m.value for m in at.markdown)
    assert any(m.label == "Diferença" and m.value == "−8,5%" for m in at.metric)
    assert any("reproduzem os totais do relatório" in s.value for s in at.success)
    tabela = next(d.value for d in at.dataframe if "Caso" in d.value.columns)
    assert tabela["Caso"].iloc[0] == "Planta brasileira · cervejaria, RS"
