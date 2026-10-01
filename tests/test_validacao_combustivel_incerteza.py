"""Verificação independente: combustível, estoque, pátio e incerteza (Fase R, matriz V-C*, V-D*).

- Cenários do pátio conferidos com um exemplo resolvido à mão.
- Fórmulas de incerteza (primeira ordem, GUM) conferidas por Monte Carlo (JCGM 101:2008),
  um método independente: sorteia os erros e mede a dispersão do resultado.
- Casos de dados problemáticos: recebimento no horário do estoque, totalizador reiniciado,
  períodos sobrepostos ou desalinhados, explicações concorrentes.
"""

import importlib.util
from math import sqrt
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from construtor_caso import Periodo, montar

from euler.incerteza import Componente, Orcamento, incerteza_padrao, u_combinada, u_diferenca
from euler.investigacao import investigar
from euler.periodos import ResumoPeriodo, _cenarios, resumir_periodo
from euler.tipos import AnaliseBloqueada, Grandeza

G01, G11, G12 = 11.773, 11.049, 19.047
FUSO = "America/Sao_Paulo"


# ---------------------------------------------------------------- pátio: recebido × queimado


def test_cenarios_do_patio_exemplo_resolvido_a_mao():
    """Antes do período: L0 = 10 t a 10 MJ/kg. Estoque inicial S0 = 10 t; no período chegam
    L1 = 20 t a 8 e L2 = 20 t a 9; estoque final S1 = 10 t → queimado M = 40 t.

    recebido = (20·8 + 20·9)/40 = 8,50
    FIFO     = 10 t de L0 + 20 t de L1 + 10 t de L2 = (100 + 160 + 90)/40 = 8,75
    máximo   = S0 a 10 (melhor possível), fica no pátio o pior (10 t de L1 a 8):
               (10·10 + 10·8 + 20·9)/40 = 9,00
    mínimo   = S0 a 8 (pior possível), fica no pátio o melhor (10 t de L2 a 9):
               (10·8 + 20·8 + 10·9)/40 = 8,25
    """
    t = pd.Timestamp("2026-01-05T07:30", tz=FUSO)
    lotes = pd.DataFrame(
        {
            "data": [
                t - pd.Timedelta(days=1),
                t + pd.Timedelta(hours=2),
                t + pd.Timedelta(hours=5),
            ],
            "massa_kg": [10_000.0, 20_000.0, 20_000.0],
            "pci_umido_mj_kg": [10.0, 8.0, 9.0],
        }
    )
    r = ResumoPeriodo(inicio=t, fim=t + pd.Timedelta(days=1))
    r.estoque_inicial_kg, r.estoque_final_kg = 10_000.0, 10_000.0
    r.combustivel_kg = Grandeza(40_000.0, "kg", "medido")
    c = _cenarios(lotes, "pci_umido_mj_kg", r, recebido=8.5)
    assert (c.recebido, c.fifo, c.minimo, c.maximo) == pytest.approx((8.50, 8.75, 8.25, 9.00))


def test_qualidade_muda_entre_recebimento_e_queima():
    """Degrau de umidade com estoque no pátio: o FIFO queima o combustível antigo primeiro,
    então o PCI queimado difere do recebido e a eficiência ganha uma faixa de cenários."""
    pacote, lim = montar([Periodo(G01, umidade=0.30), Periodo(G01, umidade=0.45)])
    r = resumir_periodo(pacote, *lim[1])
    cen = r.pci_queimado
    assert cen.fifo > cen.recebido  # combustível antigo (mais seco) queimado primeiro
    assert cen.minimo <= min(cen.recebido, cen.fifo) <= max(cen.recebido, cen.fifo) <= cen.maximo
    assert r.fracao_estoque == pytest.approx(200_000 / r.combustivel_kg.valor)


def test_recebimento_no_horario_do_estoque_bloqueia():
    pacote, lim = montar([Periodo(G01, dias=3)])
    comb = pacote.importacoes["combustivel"].dados
    i = comb.index[comb["tipo"] == "recebimento"][0]
    comb.loc[i, "data"] = lim[0][0]  # mesmo instante da medição de estoque inicial
    r = resumir_periodo(pacote, *lim[0])
    assert "combustivel" in r.bloqueios
    assert "mesmo horário" in r.bloqueios["combustivel"].motivo


def test_periodo_sem_estoque_no_limite_bloqueia():
    pacote, lim = montar([Periodo(G01, dias=3)])
    inicio = lim[0][0] + pd.Timedelta(hours=1)  # não é instante de medição de estoque
    r = resumir_periodo(pacote, inicio, lim[0][1])
    assert "combustivel" in r.bloqueios and "estoque inicial" in r.bloqueios["combustivel"].motivo


def test_totalizador_reiniciado_dentro_do_periodo_bloqueia_o_vapor():
    pacote, lim = montar([Periodo(G01, dias=3)])
    d = pacote.importacoes["diario"].dados
    meio = len(d) // 2
    d.loc[d.index[meio:], "totalizador_vapor_t"] = (
        d.loc[d.index[meio:], "totalizador_vapor_t"] - 1_000
    )
    r = resumir_periodo(pacote, *lim[0])
    assert r.vapor_t is None and "reiniciou" in r.bloqueios["vapor"].motivo


def test_periodos_sobrepostos_sao_recusados():
    pacote, lim = montar([Periodo(G01, dias=3), Periodo(G01, dias=3)])
    with pytest.raises(AnaliseBloqueada, match="sobrep"):
        investigar(pacote, (lim[0][0], lim[1][1]), lim[1])


# ---------------------------------------------------------------- GUM


def test_conversao_da_incerteza_declarada_gum():
    assert incerteza_padrao(2.0, "padrao")[0] == 2.0
    assert incerteza_padrao(2.0, "expandida", 2)[0] == 1.0  # GUM 4.3.3
    assert incerteza_padrao(2.0, "limite")[0] == pytest.approx(2 / sqrt(3))  # GUM 4.3.7
    u, como = incerteza_padrao(2.0)
    assert u == pytest.approx(2 / sqrt(3)) and "4.3.7" in como


def test_mesma_medicao_em_dois_periodos_monte_carlo():
    """Consumo = M/V; o estoque E que fecha o período A abre o período B.
    Erro ε em E: M_A = ... − E (sinal −), M_B = E + ... (sinal +). Na diferença dos consumos
    os efeitos se SOMAM. Primeira ordem (u_diferenca) × Monte Carlo (JCGM 101)."""
    rng = np.random.default_rng(1)
    m_a, m_b, e, v = 800.0, 820.0, 260.0, 2500.0
    u_e = 0.02 * e  # incerteza-padrão da medição de estoque
    orc_a = Orcamento([Componente("estoque fim A", -u_e / m_a, "instrumental", "medicao:E")])
    orc_b = Orcamento([Componente("estoque início B", +u_e / m_b, "instrumental", "medicao:E")])
    analitico = u_diferenca(m_a / v, orc_a, m_b / v, orc_b, r_instrumento=0.0)
    eps = rng.normal(0, u_e, 400_000)
    diferencas = (m_b + eps) / v - (m_a - eps) / v
    assert analitico == pytest.approx(diferencas.std(), rel=0.01)
    # e é maior que tratar como independentes (o erro aparece duas vezes com o mesmo sinal)
    assert analitico > sqrt((u_e / v) ** 2 * 2) * 0.99


def test_mesmo_instrumento_sem_calibracao_cancela_na_variacao_monte_carlo():
    """Medidor de vapor com viés b comum aos dois períodos: a variação do consumo quase não
    depende de b (r = 1); se o medidor foi trocado (biases independentes), depende."""
    rng = np.random.default_rng(2)
    m_a, m_b, v_a, v_b, u_b = 800.0, 880.0, 2500.0, 2500.0, 0.0115
    a = Orcamento([Componente("medidor", -u_b, "instrumental", "instrumento:MV@x")])
    b = Orcamento([Componente("medidor", -u_b, "instrumental", "instrumento:MV@x")])
    c_a, c_b = m_a / v_a, m_b / v_b
    vies = rng.normal(0, u_b, 400_000)
    comum = (m_b / (v_b * (1 + vies))) - (m_a / (v_a * (1 + vies)))
    independente = (m_b / (v_b * (1 + rng.normal(0, u_b, 400_000)))) - (
        m_a / (v_a * (1 + rng.normal(0, u_b, 400_000)))
    )
    assert u_diferenca(c_a, a, c_b, b, 1.0) == pytest.approx(comum.std(), rel=0.03)
    assert u_diferenca(c_a, a, c_b, b, 0.0) == pytest.approx(independente.std(), rel=0.03)


def test_hipotese_compartilhada_no_residuo_monte_carlo():
    """A mesma umidade w entra nos dois caminhos: η_direto ∝ 1/PCI(w) e perda(w).
    O resíduo r = −100·η − perda recebe o erro de w pelos dois lados (E12)."""
    rng = np.random.default_rng(3)
    w0, u_w, pci_s = 0.45, 0.01, 18.5

    def pci(w):
        return (1 - w) * pci_s - 2.442 * w

    def eta(w):  # Q/E fixo: η = 0,80 · PCI(w0)/PCI(w)
        return 0.80 * pci(w0) / pci(w)

    def perda(w):  # sensibilidade linear de ~0,16 p.p. por ponto de umidade
        return 12.0 + 16.0 * (w - w0)

    s = -(100 * (eta(w0 + 1e-6) - eta(w0)) / 1e-6) - (perda(w0 + 1e-6) - perda(w0)) / 1e-6
    analitico = u_combinada([(s * u_w, None)], 0.0)
    w = rng.normal(w0, u_w, 400_000)
    mc = (-100 * eta(w) - perda(w)).std()
    assert analitico == pytest.approx(mc, rel=0.02)
    # tratar os dois caminhos como independentes daria outro valor (errado)
    independentes = sqrt((100 * (eta(w0 + 1e-6) - eta(w0)) / 1e-6 * u_w) ** 2 + (16.0 * u_w) ** 2)
    assert abs(independentes - mc) / mc > 0.05


def test_componente_sistematico_nao_cai_com_raiz_de_n():
    """O medidor de vapor entra com a mesma incerteza relativa, não importa quantas leituras."""
    curto, lim_c = montar([Periodo(G01, dias=3)])
    longo, lim_l = montar([Periodo(G01, dias=21)])
    medidor = []
    for pacote, lim in ((curto, lim_c), (longo, lim_l)):
        r = resumir_periodo(pacote, *lim[0])
        medidor.append(
            next(c.u_rel for c in r.vapor_t.orcamento.componentes if "medidor" in c.nome)
        )
    assert medidor[0] == pytest.approx(medidor[1])


# ---------------------------------------------------------------- explicações concorrentes


def _referencia_lab():
    """Calculadora de referência do lab/ (escrita à parte do motor), carregada sem alterá-la."""
    caminho = Path(__file__).resolve().parents[1] / "lab" / "referencia_perda_gases.py"
    spec = importlib.util.spec_from_file_location("referencia_perda_gases", caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo.perda_gases


def test_explicacoes_concorrentes_que_se_compensam():
    """Gases mais quentes (+perda) e combustível mais seco (+PCI) ao mesmo tempo.

    A perda do período de comparação vem da calculadora do lab/ (independente do motor).
    Esperado: as duas mudanças são detectáveis e empurram o consumo para lados opostos;
    o consumo cai (o combustível mais seco pesa mais); a umidade fica como explicação
    compatível; a temperatura dos gases NÃO pode ser 'descartada' (ela mudou de verdade),
    nem 'sustentada' (empurrou para o lado contrário): fica 'oposta'. O fechamento soma os
    dois efeitos e cobre a mudança medida.
    """
    p_quente_seco = 100 * _referencia_lab()(230, 8, 0.36)[0]
    pacote, lim = montar(
        [Periodo(G01, umidade=0.40), Periodo(p_quente_seco, t_gases_c=230, umidade=0.36)]
    )
    j = investigar(pacote, lim[0], lim[1])
    s = {h["id"]: h for h in j["hipoteses"]}
    tg, w = s["temperatura_gases"], s["umidade_combustivel"]
    assert tg["avaliacao"]["mudanca_detectavel"] == "sim"
    assert w["avaliacao"]["mudanca_detectavel"] == "sim"
    assert tg["efeito"]["consumo_pct"] > 0 > w["efeito"]["consumo_pct"]
    assert j["o_que_mudou"]["consumo_especifico"]["variacao"] < 0

    assert tg["status"] == "oposta"
    assert w["status"] == "sustentada"
    assert w["titulo"].startswith("Combustível mais seco")
    assert j["o_que_mudou"]["fechamento"]["veredito"] == "fecha"
    assert not j["conclusao"]["abstencao"]
    assert "compensou" in j["conclusao"]["texto"]
    # a próxima verificação aponta as duas: a explicação e o fator que compensou
    assert j["proxima_verificacao"]["separa"] == ["umidade_combustivel", "temperatura_gases"]


def test_erro_da_balanca_nao_cai_com_raiz_de_n():
    """Sem separação entre parte aleatória e sistemática no cadastro, o erro da balança é
    tratado como comum a todas as pesagens do período: n·u, não √n·u (D45).

    Demo: BALANCA-01 declara 50 kg sem tipo → limite, u = 50/√3 kg (GUM 4.3.7)."""
    from euler.io import importar_pasta
    from euler.periodos import periodos_entre_estoques
    from euler.vapor import p_atm_por_altitude_bar

    demo = Path(__file__).resolve().parents[1] / "demo" / "caso_demo"
    pacote = importar_pasta(demo, p_atm_bar=p_atm_por_altitude_bar(1000))
    inicio, fim = periodos_entre_estoques(pacote)[0]
    r = resumir_periodo(pacote, inicio, fim)
    comp = next(c for c in r.combustivel_kg.orcamento.componentes if "pesagem" in c.nome)
    n = int(comp.nome.split()[2])
    assert n > 10
    assert comp.u_rel == pytest.approx(n * 50 / sqrt(3) / r.combustivel_kg.valor, rel=1e-12)
    assert comp.chave.startswith("instrumento:BALANCA-01@")
