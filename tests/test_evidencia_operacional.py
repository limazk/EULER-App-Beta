"""Integração da evidência com a física existente, sem alterar seus resultados."""

from construtor_caso import Periodo, montar

from euler.evidencias import verificar_integridade
from euler.investigacao import investigar
from euler.relatorio import gerar_html


def test_investigacao_expoe_evidencia_e_fontes_sem_alegar_serie_estatistica():
    pacote, limites = montar(
        [
            Periodo(11.049, t_gases_c=180, umidade=0.3104),
            Periodo(19.047, t_gases_c=292.2, umidade=0.3104),
        ]
    )
    j = investigar(pacote, limites[0], limites[1])
    d = j["diagnostico_evidencias"]
    assert verificar_integridade(d)
    assert d["dimensoes"]["robustez_estatistica"]["nivel"] == "INSUFICIENTE"
    assert d["dimensoes"]["evidencia_fisica"]["nivel"] == "MODERADA"
    assert d["economia"]["economia_verificada"] is None
    assert d["proximas_medicoes"][0]["acao"] == j["proxima_verificacao"]["acao"]
    assert d["fontes"]["tabelas_originais"]
    assert d["analise_id"] in gerar_html(j)
    assert all(h["causa_comprovada"] is False for h in d["hipoteses"])
    assert j["periodos"]["comparacao"]["energia_combustivel"]["unidade"] == "GJ"


def _demo_completo():
    from pathlib import Path

    from euler.io import importar_pasta
    from euler.periodos import periodos_entre_estoques
    from euler.vapor import p_atm_por_altitude_bar

    pasta = Path(__file__).resolve().parents[1] / "demo" / "caso_demo_completo"
    p = importar_pasta(pasta, p_atm_bar=p_atm_por_altitude_bar(1000))
    return p, periodos_entre_estoques(p)


def test_valorizacao_segue_a_regra_do_valor_em_jogo_do_motor():
    """D87: a tela Investigação e o Diagnóstico dão a mesma resposta sobre dinheiro. Antes,
    uma alta não confirmada (+2,9%) aparecia como R$ 7.803 no Diagnóstico enquanto a
    Investigação dizia "valor em jogo não estimado"; uma queda virava valor negativo."""
    from euler.relatorio_evidencias import texto_diagnostico

    p, s = _demo_completo()
    for ref, comp in (((0, 1), (2, 3)), ((4, 5), (7, 7))):  # condicional; queda
        j = investigar(p, (s[ref[0]][0], s[ref[1]][1]), (s[comp[0]][0], s[comp[1]][1]))
        e = j["diagnostico_evidencias"]["economia"]
        assert j["valor_em_jogo"] is None
        assert e["desvio_estimado"] is None
        assert e["motivo_sem_valor"] == j["valor_em_jogo_motivo"]
        texto = texto_diagnostico(j["diagnostico_evidencias"])
        assert "não estimado" in texto and "—" not in texto.split("### Impacto")[1][:80]
    j = investigar(p, (s[0][0], s[3][1]), (s[4][0], s[5][1]))
    e = j["diagnostico_evidencias"]["economia"]
    assert e["desvio_estimado"] == j["valor_em_jogo"]["valor_brl"]
    assert e["motivo_sem_valor"] is None


def test_referencia_operacional_avaliada_com_a_serie_de_periodos():
    """D88: a referência da investigação é avaliada com a série que a fábrica enviou (um ponto
    por período entre medições de estoque), com o mesmo modelo da comparação agregada.
    Antes a dimensão era sempre INSUFICIENTE ("não avaliada nesta rota")."""
    import pytest

    p, s = _demo_completo()
    j = investigar(p, (s[0][0], s[3][1]), (s[4][0], s[5][1]))
    ref = j["diagnostico_evidencias"]["dimensoes"]["referencia"]
    m = ref["metricas"]
    assert ref["nivel"] == "FRACA"
    assert m["observacoes_validas"] == 4 and m["observacoes_invalidas"] == 0
    assert any("menos de 30" in x for x in ref["motivos"])
    # o degrau de +2,9% dentro de agosto (semanas 1–2 × 3–4) aparece como deriva da referência
    assert any("metades" in x for x in ref["motivos"])
    assert m["mudanca_residual_metades_pct"] == pytest.approx(2.85, abs=0.05)
    assert m["cobertura_carga_frac"] == 1.0
    assert len(m["validacao_temporal"]) == 1
    # nenhum modelo novo: o previsto usa o consumo específico da referência do próprio motor
    k = ref["modelo"]["consumo_especifico_t_t"]
    assert k == j["o_que_mudou"]["consumo_especifico"]["referencia"]
    assert [x["periodo"] for x in ref["serie"]] == [
        "03/08 a 10/08",
        "10/08 a 17/08",
        "17/08 a 24/08",
        "24/08 a 31/08",
    ]
    assert all(x["previsto_t"] == pytest.approx(k * x["vapor_t"]) for x in ref["serie"])
    assert "ainda não avaliada" not in " ".join(ref["motivos"])
    assert verificar_integridade(j["diagnostico_evidencias"])


def test_referencia_operacional_nao_preenche_periodo_sem_vapor():
    """Ausente ≠ zero: a semana com o medidor de vapor fora fica inválida, sem valor previsto,
    e com só 2 semanas válidas a referência é INSUFICIENTE."""
    p, s = _demo_completo()
    j = investigar(p, (s[4][0], s[6][1]), (s[7][0], s[7][1]))
    ref = j["diagnostico_evidencias"]["dimensoes"]["referencia"]
    assert ref["nivel"] == "INSUFICIENTE"
    assert ref["metricas"]["observacoes_invalidas"] == 1
    semana = next(x for x in ref["serie"] if x["periodo"] == "14/09 a 21/09")
    assert semana["vapor_t"] is None
    assert semana["previsto_t"] is None and semana["residuo_t"] is None
    assert semana["combustivel_t"] is not None  # o combustível medido continua registrado


def test_vapor_e_combustivel_igual_ao_resumo_completo():
    """O cálculo leve por período dá os mesmos números do resumo completo (só não calcula o
    resto: gases, mistura, composição)."""
    from euler.periodos import resumir_periodo, vapor_e_combustivel

    p, s = _demo_completo()
    for a, b in s:
        leve, completo = vapor_e_combustivel(p, a, b), resumir_periodo(p, a, b)
        for campo in ("vapor_t", "combustivel_kg"):
            x, y = getattr(leve, campo), getattr(completo, campo)
            assert (x is None) == (y is None)
            if x is not None:
                assert x.valor == y.valor and x.incerteza == y.incerteza
