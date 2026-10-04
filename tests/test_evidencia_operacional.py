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
