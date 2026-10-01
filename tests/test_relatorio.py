"""Relatório (T14): 5 blocos fixos, rodapé obrigatório e nenhum comando operacional."""

from pathlib import Path

import pytest
from construtor_caso import Periodo, montar

from euler.investigacao import investigar
from euler.io import importar_pasta
from euler.periodos import periodos_entre_estoques
from euler.relatorio import BLOCOS, comandos_operacionais, gerar_html, texto_visivel
from euler.textos import RODAPE_SEGURANCA
from euler.vapor import p_atm_por_altitude_bar

DEMO = Path(__file__).resolve().parents[1] / "demo" / "caso_demo"
G01, G11, G12 = 11.773, 11.049, 19.047


@pytest.fixture(scope="module")
def relatorios_demo():
    """Referência = semanas 1–4; comparação = cada uma das semanas seguintes e 5–6."""
    pacote = importar_pasta(DEMO, p_atm_bar=p_atm_por_altitude_bar(1000))
    s = periodos_entre_estoques(pacote)
    base = (s[0][0], s[3][1])
    comparacoes = [*s[4:], (s[4][0], s[5][1])]
    return [gerar_html(investigar(pacote, base, c)) for c in comparacoes]


@pytest.fixture(scope="module")
def relatorios_sinteticos():
    casos = [
        [
            Periodo(G11, t_gases_c=180, umidade=0.3104),
            Periodo(G12, t_gases_c=292.2, umidade=0.3104),
        ],
        [Periodo(G01, preco_brl_t=180), Periodo(G01, preco_brl_t=220)],
        [
            Periodo(G01, registrar_purgas=False),
            Periodo(G01, outras_perdas_pp=13, registrar_purgas=False),
        ],
    ]
    saida = []
    for periodos in casos:
        pacote, limites = montar(periodos)
        saida.append(gerar_html(investigar(pacote, limites[0], limites[1])))
    return saida


def test_cinco_blocos_na_ordem_e_rodape(relatorios_demo):
    for html in relatorios_demo:
        texto = texto_visivel(html)
        # o resumo do topo (D63) cita a próxima verificação antes dos blocos
        inicio = texto.index(BLOCOS[0])
        posicoes = [texto.index(b, inicio) for b in BLOCOS]
        assert posicoes == sorted(posicoes)
        assert RODAPE_SEGURANCA in texto


def test_nenhum_relatorio_tem_comando_operacional(relatorios_demo, relatorios_sinteticos):
    for html in relatorios_demo + relatorios_sinteticos:
        assert comandos_operacionais(html) == []


def test_o_detector_de_comandos_funciona():
    assert comandos_operacionais("<p>Ajuste o queimador e abra a válvula.</p>") == [
        "abra",
        "ajuste",
    ]
    assert comandos_operacionais("<p>Conferir a leitura do termopar.</p>") == []


def test_relatorio_de_abstencao_diz_que_nao_da_para_concluir(relatorios_demo):
    semana_sem_vapor = relatorios_demo[2]  # semana 7
    assert "Não dá para concluir" in semana_sem_vapor
    assert "totalizador de vapor" in semana_sem_vapor


def test_dados_sinteticos_tem_selo(relatorios_demo):
    assert "DADOS SINTÉTICOS" in relatorios_demo[0]


def test_texto_e_escapado_contra_html():
    pacote, limites = montar([Periodo(G01, dias=7), Periodo(G01, dias=7)])
    j = investigar(pacote, limites[0], limites[1])
    j["caldeira_id"] = "<script>alert(1)</script>"
    assert "<script>" not in gerar_html(j)
