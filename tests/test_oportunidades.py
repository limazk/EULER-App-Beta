"""Oportunidades (D90): prioridade de investigação transparente, sem nota nem pesos;
impacto potencial nunca vira economia; ausente nunca vira zero; sobreposição avisada."""

from copy import deepcopy
from math import exp

import pytest
from construtor_caso import Periodo, montar

from euler.investigacao import investigar
from euler.oportunidades import PRIORIDADES, VERIFICACOES, priorizar, projetar_ano
from euler.relatorio import comandos_operacionais

G11, G12 = 11.049, 19.047


def hip(id_, status="sustentada", e=3.0, u=0.5, relevante=True, verificacao=None, faixa=None):
    return {
        "id": id_,
        "titulo": f"Hipótese {id_}",
        "status": status,
        "avaliacao": {"relevante": relevante},
        "efeito": {
            "consumo_pct": e,
            "consumo_pct_incerteza_k2": u,
            "consumo_pct_faixa_patio": faixa,
        },
        "verificacao": verificacao or VERIFICACOES[id_]["acao"] + " (texto do motor).",
        "medicoes": ["leitura"],
        "evidencia": "Uma fonte.",
    }


def caso(hs, separa=(), preco=200.0, valor=None):
    """Investigação mínima: 4.000 t de vapor a 0,25 t/t = 1.000 t esperadas, 14 dias."""
    return {
        "hipoteses": hs,
        "proxima_verificacao": {"acao": "…", "separa": list(separa), "porque": ""},
        "explicacao_conta": {
            "disponivel": True,
            "esperado": {"consumo_referencia_t_t": 0.25},
            "consumido": {"preco_brl_t": preco},
            "variacao": {"combustivel_t": {}},
        },
        "periodos": {
            "comparacao": {
                "inicio": "2026-01-01T00:00:00",
                "fim": "2026-01-15T00:00:00",
                "vapor_t": {"valor": 4000.0},
            }
        },
        "valor_em_jogo": valor,
        "valor_em_jogo_motivo": "Valor em jogo não estimado: aumento não confirmado.",
        "o_que_mudou": {"fechamento": None},
    }


def textos(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from textos(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from textos(v)


def chaves(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from chaves(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from chaves(v)


def test_sem_nota_nem_pesos_so_categorias_documentadas():
    r = priorizar(caso([hip("temperatura_gases"), hip("excesso_ar", status="descartada")]))
    assert not any(k in {"score", "nota", "peso", "pesos"} for k in chaves(r))
    assert {o["prioridade"] for o in r["oportunidades"]} <= set(PRIORIDADES)
    assert r["regras"]["objetivos"] and r["regras"]["propostos"]


def test_impacto_em_toneladas_e_reais_com_faixa_do_indicador():
    o = priorizar(caso([hip("temperatura_gases", e=3.0, u=0.5)]))["oportunidades"][0]
    i = o["impacto"]
    assert i["combustivel_t"] == pytest.approx(1000 * (exp(0.03) - 1))
    assert i["custo_brl"] == pytest.approx(200 * 1000 * (exp(0.03) - 1))
    lo, hi = i["faixa_brl"]
    assert lo == pytest.approx(200 * 1000 * (exp(0.025) - 1))
    assert hi == pytest.approx(200 * 1000 * (exp(0.035) - 1))
    assert i["custo_dia_brl"] == pytest.approx(i["custo_brl"] / 14)


def test_verificacao_simples_e_relevante_vem_antes_de_impacto_maior_e_verificacao_media():
    """Nem sempre o maior impacto é o primeiro: o resíduo além da chaminé (8%) tem
    verificação de complexidade média; a temperatura dos gases (2%), baixa."""
    r = priorizar(
        caso(
            [
                hip("perdas_nao_medidas", status="possivel", e=8.0, relevante=None),
                hip("temperatura_gases", e=2.0),
            ]
        )
    )
    ordem = [o["id"] for o in r["oportunidades"]]
    assert ordem == ["temperatura_gases", "perdas_nao_medidas"]
    assert [o["prioridade"] for o in r["oportunidades"]] == ["alta", "media"]


def test_proxima_verificacao_do_motor_vem_primeiro_para_as_telas_concordarem():
    r = priorizar(
        caso(
            [hip("temperatura_gases", e=5.0), hip("umidade_combustivel", e=1.0)],
            separa=["umidade_combustivel"],
        )
    )
    assert r["oportunidades"][0]["id"] == "umidade_combustivel"
    assert r["resumo"]["primeira"]["id"] == "umidade_combustivel"
    assert "próxima verificação indicada pelo motor" in " ".join(r["oportunidades"][0]["porque"])


def test_enfraquecida_e_nao_avaliavel_nao_viram_prioridade():
    r = priorizar(
        caso(
            [
                hip("excesso_ar", status="descartada"),
                hip("temperatura_gases", status="nao_avaliavel"),
            ]
        )
    )
    p = {o["id"]: o["prioridade"] for o in r["oportunidades"]}
    assert p == {"excesso_ar": "baixa", "temperatura_gases": "sem_base"}
    assert r["resumo"]["em_investigacao"] == 0
    assert r["resumo"]["frase"] == "Dados insuficientes para estabelecer uma prioridade defensável."
    assert all(o["evidencia"]["nivel"] == "INSUFICIENTE" for o in r["oportunidades"])


def test_evidencia_nunca_forte_sem_verificacao_registrada():
    r = priorizar(caso([hip("temperatura_gases"), hip("excesso_ar", status="possivel")]))
    niveis = {o["id"]: o["evidencia"]["nivel"] for o in r["oportunidades"]}
    assert niveis == {"temperatura_gases": "MODERADA", "excesso_ar": "FRACA"}


def test_impacto_ausente_nao_vira_zero_e_fica_depois():
    r = priorizar(
        caso(
            [
                hip("perdas_nao_medidas", status="possivel", e=None, u=None, relevante=None),
                hip("excesso_ar", status="possivel", e=0.5, relevante=None),
            ]
        )
    )
    o = {x["id"]: x for x in r["oportunidades"]}
    assert o["perdas_nao_medidas"]["impacto"]["custo_brl"] is None
    assert o["perdas_nao_medidas"]["impacto"]["motivo"]
    assert [x["id"] for x in r["oportunidades"]] == ["excesso_ar", "perdas_nao_medidas"]


def test_sem_preco_impacto_fica_em_toneladas_com_motivo():
    o = priorizar(caso([hip("temperatura_gases")], preco=None))["oportunidades"][0]
    assert o["impacto"]["combustivel_t"] is not None
    assert o["impacto"]["custo_brl"] is None and o["impacto"]["faixa_brl"] is None
    assert "não pode ser monetizado" in o["impacto"]["motivo"]


def test_mesma_perda_nos_gases_avisa_sobreposicao_e_resumo_nao_soma():
    r = priorizar(
        caso(
            [hip("temperatura_gases", e=3.0), hip("excesso_ar", e=2.0)],
            valor={"valor_brl": 9000.0, "incerteza_brl": 3000.0},
        )
    )
    avisos = " ".join(r["sobreposicao"])
    assert "mesma perda nos gases" in avisos and "Não some" in avisos
    soma = sum(o["impacto"]["custo_brl"] for o in r["oportunidades"])
    assert r["resumo"]["associado"]["custo_brl"] == 9000.0 != pytest.approx(soma)
    assert "não soma das oportunidades" in r["resumo"]["associado"]["base"]


def test_complexidade_nao_classificada_quando_o_motor_escreve_outra_acao():
    """Pontos de gases diferentes: o motor pede novas leituras, não a checagem do termopar.
    A classificação 'baixa' do catálogo não é herdada por outra ação."""
    o = priorizar(
        caso([hip("temperatura_gases", verificacao="Obter leituras dos gases em regime estável.")])
    )["oportunidades"][0]
    assert o["verificacao"]["complexidade"] is None
    assert "não classificada" in o["verificacao"]["origem_complexidade"]
    assert o["prioridade"] == "media"


def test_condicao_do_vapor_fica_fora_das_oportunidades():
    r = priorizar(caso([hip("condicao_vapor", e=2.0)]))
    assert r["oportunidades"][0]["prioridade"] == "fora"
    assert r["resumo"]["em_investigacao"] == 0


def test_intervencao_e_economia_verificada_indisponiveis_com_motivo():
    r = priorizar(caso([hip("temperatura_gases")]))
    assert r["intervencao"]["disponivel"] is False
    assert "payback" in r["intervencao"]["motivo"]
    i = r["oportunidades"][0]["intervencao"]
    assert i["payback_anos"] is None and i["investimento_brl"] is None
    etapas = {c["id"]: c["disponivel"] for c in r["cadeia"]}
    assert etapas["investigacao"] is True
    assert not any(etapas[k] for k in ("causa", "intervencao", "pos", "economia", "persistencia"))


def test_resultado_deterministico():
    j = caso([hip("temperatura_gases", e=2.0), hip("excesso_ar", e=2.0)])
    assert priorizar(j) == priorizar(deepcopy(j))
    # empate de impacto: desempate pelo id, estável
    assert [o["id"] for o in priorizar(j)["oportunidades"]] == ["excesso_ar", "temperatura_gases"]


def test_projecao_anual_so_com_dias_informados():
    assert projetar_ano(14_000, 14, 330) == pytest.approx(330_000)
    assert projetar_ano(14_000, 14, None) is None
    assert projetar_ano(None, 14, 330) is None
    with pytest.raises(ValueError):
        projetar_ano(14_000, 14, 400)


# ------------------------------------------------ integração com o motor


def test_caso_a_gases_mais_quentes_e_prioridade_alta_e_ar_nao():
    pacote, lim = montar(
        [
            Periodo(G11, t_gases_c=180, umidade=0.3104),
            Periodo(G12, t_gases_c=292.2, umidade=0.3104),
        ]
    )
    j = investigar(pacote, lim[0], lim[1])
    r = j["oportunidades"]
    primeira = r["oportunidades"][0]
    assert primeira["id"] == "temperatura_gases" and primeira["prioridade"] == "alta"
    assert primeira["impacto"]["custo_brl"] > 0
    assert {o["id"]: o["prioridade"] for o in r["oportunidades"]}["excesso_ar"] == "baixa"
    assert not comandos_operacionais(" ".join(textos(r)))


def test_ato_1_umidade_e_gases_com_a_mesma_base_da_conta():
    from pathlib import Path

    from euler.io import importar_pasta
    from euler.periodos import periodos_entre_estoques
    from euler.vapor import p_atm_por_altitude_bar

    pasta = Path(__file__).resolve().parents[1] / "demo" / "caso_demo_completo"
    p = importar_pasta(pasta, p_atm_bar=p_atm_por_altitude_bar(1000))
    s = periodos_entre_estoques(p)
    j = investigar(p, (s[0][0], s[3][1]), (s[4][0], s[5][1]))
    r = j["oportunidades"]
    ordem = [(o["id"], o["prioridade"]) for o in r["oportunidades"]]
    assert ordem[:2] == [("umidade_combustivel", "alta"), ("temperatura_gases", "alta")]
    umidade = r["oportunidades"][0]
    qualidade = j["explicacao_conta"]["variacao"]["brl"]["qualidade"]
    assert umidade["impacto"]["custo_brl"] == pytest.approx(qualidade)
    assert r["resumo"]["associado"]["custo_brl"] == pytest.approx(j["valor_em_jogo"]["valor_brl"])
    assert r["resumo"]["primeira"]["acao"] == j["proxima_verificacao"]["acao"]


def test_tela_oportunidades_abre_e_so_projeta_o_ano_com_dias_informados():
    from test_app import abrir_com_demo

    at = abrir_com_demo("oportunidades.py")
    assert not at.exception, at.exception
    assert not at.slider
    textos_tela = " ".join(x.value for x in at.markdown) + " ".join(x.value for x in at.caption)
    assert "Como a priorização funciona" in " ".join(e.label for e in at.expander)
    assert "/ano" not in textos_tela
    at.number_input[0].set_value(330).run()
    assert not at.exception, at.exception
    assert any("/ano" in c.value for c in at.caption)
