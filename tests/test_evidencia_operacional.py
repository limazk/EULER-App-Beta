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
