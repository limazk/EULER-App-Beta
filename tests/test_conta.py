"""Explicação da conta de combustível (D89): quanto custou, quanto seria esperado nas
condições analisadas e quanto continua sem explicação. Ausente nunca vira zero; nenhum
percentual de recuperação é aplicado."""

import pytest
from construtor_caso import Periodo, montar

from euler.conta import explicar_conta
from euler.investigacao import investigar
from euler.relatorio import comandos_operacionais

G01, G08, G09, G11, G12 = 11.773, 10.979, 12.307, 11.049, 19.047


def conta(**kw):
    base = {
        "combustivel_ref_t": 1000.0,
        "vapor_ref_t": 4000.0,
        "combustivel_t": 1200.0,
        "vapor_t": 4400.0,
        "preco_ref_brl_t": 300.0,
        "preco_brl_t": 350.0,
        "incerteza_consumo_t_t": 0.001,
    }
    return explicar_conta(**{**base, **kw})


def textos(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from textos(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from textos(v)


def test_exemplo_do_adryan_custo_consumido_esperado_e_desvio():
    """1.200 t consumidas, 1.100 t esperadas nas mesmas condições, R$ 350/t."""
    c = conta(combustivel_ref_t=1100.0, vapor_ref_t=4400.0, preco_ref_brl_t=350.0)
    assert c["consumido"]["custo_brl"] == pytest.approx(420_000)
    assert c["esperado"]["custo_brl"] == pytest.approx(385_000)
    assert c["desvio"]["combustivel_t"] == pytest.approx(100)
    assert c["desvio"]["custo_brl"] == pytest.approx(35_000)
    assert c["desvio"]["estado"] == "acima"
    assert "100,0 t acima da referência ajustada" in c["desvio"]["frase"]
    assert "R$ 35.000" in c["desvio"]["frase"]
    assert "quanto dessa diferença pode ser evitado" in c["desvio"]["frase"]


@pytest.mark.parametrize(
    "politica, rotulo", [("fifo", "FIFO"), ("tabela_de_precos", "tabela de preços")]
)
def test_textos_financeiros_respeitam_a_politica_de_preco(politica, rotulo):
    c = conta(politica_custo=politica)
    preco = next(x for x in c["variacao"]["componentes"] if x["id"] == "preco")
    assert rotulo in c["desvio"]["frase"]
    assert rotulo in preco["base"]
    assert any(rotulo in p for p in c["premissas"])
    assert "média ponderada dos recebimentos" not in " ".join(textos(c))
    assert c["entradas"]["politica_custo"] == politica
    assert c["desvio"]["custo_brl"] == conta()["desvio"]["custo_brl"]


def test_politica_alternativa_sem_preco_nao_diz_que_faltou_recebimento():
    c = conta(politica_custo="fifo", preco_brl_t=None)
    assert "FIFO" in c["desvio"]["frase"]
    assert "FIFO" in c["variacao"]["motivo"]
    assert "preço dos recebimentos" not in " ".join(textos(c))


def test_politica_desconhecida_nao_e_rotulada_como_recebimentos():
    with pytest.raises(ValueError, match="Política de custo"):
        conta(politica_custo="desconhecida")


def test_parcelas_fecham_a_variacao_da_conta_exatamente():
    c = conta(efeito_condicao_vapor_pct=1.0, efeito_qualidade_pct=5.0)
    v = c["variacao"]
    assert v["variacao_brl"] == pytest.approx(1200 * 350 - 1000 * 300)
    assert sum(x["custo_brl"] for x in v["componentes"]) == pytest.approx(v["variacao_brl"])
    porid = {x["id"]: x for x in v["componentes"]}
    assert porid["preco"]["custo_brl"] == pytest.approx(1000 * 50)
    assert porid["producao"]["combustivel_t"] == pytest.approx(0.25 * 4400 - 1000)
    # o desvio em reais é (observado − esperado ajustado) × preço do período
    assert porid["nao_explicado"]["custo_brl"] == pytest.approx(
        (1200 - c["esperado"]["combustivel_t"]) * 350
    )
    assert c["desvio"]["custo_brl"] == porid["nao_explicado"]["custo_brl"]


def test_parcela_sem_dado_fica_misturada_ao_desvio_e_nao_vira_zero():
    c = conta(efeito_qualidade_pct=None, motivo_qualidade="umidade não medida")
    q = next(x for x in c["variacao"]["componentes"] if x["id"] == "qualidade")
    assert q["separado"] is False
    assert q["custo_brl"] is None and q["combustivel_t"] is None
    assert "umidade não medida" in q["base"] and "Permanece no desvio" in q["base"]
    assert c["desvio"]["combustivel_t"] == pytest.approx(1200 - 0.25 * 4400)
    assert any("Qualidade do combustível" in x for x in c["esperado"]["nao_ajustado"])
    assert any("Carga e regime" in x for x in c["esperado"]["nao_ajustado"])


@pytest.mark.parametrize(
    "kw, estado, trecho",
    [
        ({"incerteza_consumo_t_t": 0.05}, "nao_estabelecido", "não ficou bem estabelecido"),
        ({"incerteza_consumo_t_t": None}, "sem_faixa", "erro de medição"),
        ({"combustivel_t": 1000.0}, "abaixo", "abaixo do esperado"),
    ],
)
def test_estado_do_desvio_vem_da_faixa(kw, estado, trecho):
    d = conta(**kw)["desvio"]
    assert d["estado"] == estado
    assert trecho in d["frase"]
    if estado == "sem_faixa":
        assert d["faixa_brl"] is None


def test_cenario_do_patio_que_inverte_o_sinal_impede_conclusao():
    sem = conta(efeito_qualidade_pct=5.0)
    assert sem["desvio"]["estado"] == "acima"
    com = conta(efeito_qualidade_pct=5.0, cenarios_qualidade_pct=(0.0, 20.0))
    assert com["desvio"]["estado"] == "nao_estabelecido"
    lo, hi = com["desvio"]["cenarios_qualidade_brl"]
    assert lo < 0 < hi
    assert "em um cenário do pátio" in com["desvio"]["frase"]
    assert "inclui zero" not in com["desvio"]["frase"]  # a faixa das medições não inclui
    # cenários iguais ao central não são apresentados como faixa
    igual = conta(efeito_qualidade_pct=5.0, cenarios_qualidade_pct=(5.0, 5.0))
    assert igual["desvio"]["cenarios_qualidade_brl"] is None


def test_sem_preco_nao_estima_reais_nem_decompoe():
    c = conta(preco_brl_t=None)
    assert c["consumido"]["custo_brl"] is None and c["desvio"]["custo_brl"] is None
    assert c["desvio"]["combustivel_t"] == pytest.approx(100)
    assert "valor em reais não foi estimado" in c["desvio"]["frase"]
    assert c["variacao"]["disponivel"] is False
    so_ref = conta(preco_ref_brl_t=None)
    assert so_ref["desvio"]["custo_brl"] == pytest.approx(100 * 350)
    assert so_ref["variacao"]["disponivel"] is False
    assert "num dos períodos" in so_ref["variacao"]["motivo"]


@pytest.mark.parametrize("preco", [None, float("nan"), float("inf"), -1.0])
def test_preco_invalido_nao_vira_valor(preco):
    c = conta(preco_brl_t=preco)
    assert c["consumido"]["custo_brl"] is None and c["desvio"]["custo_brl"] is None


def test_sem_massa_ou_vapor_nao_ha_consumo_esperado():
    c = conta(vapor_t=None)
    assert c["disponivel"] is False and c["motivo"]


def test_parcela_evitavel_nao_e_estimada_e_nao_ha_percentual_de_recuperacao():
    c = conta(verificacao="Medir o O₂ nos gases com analisador calibrado.")
    assert c["evitavel"]["custo_brl"] is None
    assert "Nenhum percentual de recuperação" in c["evitavel"]["motivo"]
    assert c["evitavel"]["verificacao"].startswith("Medir")
    assert not comandos_operacionais(" ".join(textos(c)))


def test_cenarios_de_preco_vem_dos_lotes_e_nao_viram_intervalo_de_confianca():
    c = conta(preco_min_brl_t=320.0, preco_max_brl_t=380.0)
    lo, hi = c["desvio"]["cenarios_preco_brl"]
    d = c["desvio"]["combustivel_t"]
    assert (lo, hi) == pytest.approx((d * 320, d * 380))
    assert any("não intervalos de confiança" in p for p in c["premissas"])


# ------------------------------------------------ integração com o motor


def test_so_o_preco_mudou_a_conta_explica_pelo_preco():
    j = investigar(*_caso(Periodo(G01, preco_brl_t=180), Periodo(G01, preco_brl_t=220)))
    c = j["explicacao_conta"]
    porid = {x["id"]: x for x in c["variacao"]["componentes"]}
    massa_ref = j["periodos"]["referencia"]["combustivel_kg"]["valor"] / 1000
    assert porid["preco"]["custo_brl"] == pytest.approx(massa_ref * 40, rel=0.01)
    assert abs(porid["nao_explicado"]["custo_brl"]) < 0.05 * porid["preco"]["custo_brl"]
    assert c["desvio"]["estado"] == "nao_estabelecido"


def test_umidade_maior_gastou_mais_sem_perder_eficiencia():
    """Caso B: o consumo por tonelada sobe porque o combustível chegou mais úmido. A conta
    separa a qualidade; o desvio não explicado fica pequeno perto dela."""
    j = investigar(*_caso(Periodo(G08, umidade=0.30), Periodo(G09, umidade=0.45)))
    c = j["explicacao_conta"]
    q = next(x for x in c["variacao"]["componentes"] if x["id"] == "qualidade")
    assert q["separado"] and q["custo_brl"] > 0
    assert abs(c["desvio"]["custo_brl"]) < 0.1 * q["custo_brl"]


def test_ponte_com_o_valor_em_jogo_da_investigacao():
    """Gases mais quentes (caso A): mecanismo de eficiência, fica no desvio. O valor em jogo
    da investigação = condição do vapor + qualidade + desvio não explicado."""
    j = investigar(
        *_caso(
            Periodo(G11, t_gases_c=180, umidade=0.3104),
            Periodo(G12, t_gases_c=292.2, umidade=0.3104),
        )
    )
    c = j["explicacao_conta"]
    porid = {x["id"]: x for x in c["variacao"]["componentes"]}
    ponte = sum(porid[k]["custo_brl"] for k in ("condicao_vapor", "qualidade", "nao_explicado"))
    assert ponte == pytest.approx(j["valor_em_jogo"]["valor_brl"])
    assert c["desvio"]["estado"] == "acima"
    assert c["evitavel"]["verificacao"] == j["proxima_verificacao"]["acao"]


def test_preco_por_tonelada_nao_depende_de_umidade_medida():
    """Antes, sem umidade e PCI dos lotes o preço do período ficava ausente e nada era
    valorizado, embora o preço só dependa de massa e valor do lote."""
    pacote, limites = montar([Periodo(G01), Periodo(G01, preco_brl_t=200)])
    sem_amostras = {k: v for k, v in pacote._arquivos_teste.items() if k != "amostras"}
    from euler.io import importar_pacote

    p2 = importar_pacote(sem_amostras, p_atm_bar=pacote.p_atm_bar)
    j = investigar(p2, limites[0], limites[1])
    assert j["periodos"]["comparacao"]["preco_brl_t"] == pytest.approx(200, rel=0.01)
    c = j["explicacao_conta"]
    q = next(x for x in c["variacao"]["componentes"] if x["id"] == "qualidade")
    assert q["separado"] is False and q["custo_brl"] is None
    assert c["consumido"]["custo_brl"] is not None and c["desvio"]["custo_brl"] is not None


def _caso(*periodos):
    pacote, limites = montar(list(periodos))
    return pacote, limites[0], limites[1]
