"""Perda sensível nos gases de chaminé, base PCI, por kg de combustível seco (E1–E7).

Referência das equações: docs/fisica_para_revisao.md, Bloco A.
Convenções: composição em fração mássica base seca (C, H, O, N, S); umidade `w`
em base úmida (fração); temperaturas em °C; PCI em MJ/kg; cp em MJ/(kg·K).
Hipóteses: combustão completa; ar seco com 21% O₂ / 79% N₂; umidade do ar de
combustão desprezada (pergunta aberta no E4).

Este módulo não compartilha código com o benchmark `euler-bench` (AGENTS.md, regra 7).
"""

from collections.abc import Mapping
from dataclasses import dataclass

from iapws import IAPWS97

from euler.combustivel import H_VAP_25C_MJ_KG, pci_umido
from euler.tipos import AnaliseBloqueada
from euler.vapor import P_ATM_NIVEL_DO_MAR_BAR, t_sat_c

CP_GASES_SECOS_MJ_KG_K = 1.05e-3
"""cp constante dos gases secos, modo referência (E6, só para teste)."""
CP_VAPOR_AGUA_MJ_KG_K = 1.90e-3
"""cp constante do vapor d'água, modo referência (E6, só para teste)."""
RAZAO_N2_O2_AR = 79 / 21
MASSA_MOLAR_H2O = 18.015  # kg/kmol
CO_LIMITE_AVISO_PPM = 200
"""Acima disso, ignorar CO no cálculo de λ pode errar (pergunta aberta no E2)."""
MODELOS_CP = ("constante", "variavel")
ELEMENTOS = ("C", "H", "O", "N", "S")

COMPOSICAO_REFERENCIA = {"C": 0.50, "H": 0.06, "O": 0.43, "N": 0.003, "S": 0.0005}
"""Cavaco de referência do documento de revisão (base seca). Origem: assumido."""


@dataclass(frozen=True)
class ResultadoPerdaGases:
    """Resultado da perda nos gases e grandezas intermediárias.

    perda_pct: perda sensível nos gases, % do PCI (E6).
    lambda_ar: razão de ar (E2).
    o2_esteq_kmol_kg: O₂ estequiométrico, kmol/kg seco (E1).
    m_gases_secos_kg_kg: massa de gases secos, kg/kg seco (E3).
    m_h2o_kg_kg: água nos gases, kg/kg seco (E4).
    t_orvalho_c: orvalho da água nos gases, °C (E7).
    avisos: alertas que não impedem o cálculo.
    """

    perda_pct: float
    lambda_ar: float
    o2_esteq_kmol_kg: float
    m_gases_secos_kg_kg: float
    m_h2o_kg_kg: float
    t_orvalho_c: float
    modelo_cp: str
    avisos: tuple[str, ...] = ()


def _checar_composicao(comp: Mapping[str, float]) -> tuple[float, ...]:
    faltando = [e for e in ELEMENTOS if comp.get(e) is None]
    if faltando:
        raise AnaliseBloqueada(
            f"Composição do combustível incompleta: falta {', '.join(faltando)}.",
            falta=["análise elementar do combustível (C, H, O, N, S em base seca)"],
        )
    valores = tuple(float(comp[e]) for e in ELEMENTOS)
    if any(v < 0 or v > 1 for v in valores) or sum(valores) > 1.0001:
        raise AnaliseBloqueada(
            "Composição do combustível inválida: frações devem ficar entre 0 e 1 "
            "e somar no máximo 1 (o resto são cinzas)."
        )
    return valores


def oxigenio_estequiometrico(comp: Mapping[str, float]) -> float:
    """O₂ estequiométrico, kmol de O₂ por kg de combustível seco (E1).

    a = C/12 + H/4 + S/32 − O/32
    """
    c, h, o, _n, s = _checar_composicao(comp)
    a = c / 12 + h / 4 + s / 32 - o / 32
    if a <= 0:
        raise AnaliseBloqueada("Composição sem demanda de oxigênio: confira a análise elementar.")
    return a


def razao_ar(o2_seco_pct: float, comp: Mapping[str, float]) -> float:
    """Razão de ar λ a partir do O₂ medido nos gases secos (E2).

    Gases secos por kg seco: n_CO2 = C/12, n_SO2 = S/32, n_O2 = (λ−1)a,
    n_N2 = (79/21)λa + N/28. Resolvendo y_O2 = n_O2/Σn para X = λa:
    X·(1 − y − y·79/21) = a + y·(C/12 + S/32 + N/28) − y·a
    """
    if not 0 <= o2_seco_pct < 21:
        raise AnaliseBloqueada(
            f"O₂ de {o2_seco_pct:g}% fora da faixa de combustão (0 a 21%). "
            "Leitura de 21% indica ar ambiente ou analisador fora do ponto."
        )
    c, _h, _o, n, s = _checar_composicao(comp)
    a = oxigenio_estequiometrico(comp)
    y = o2_seco_pct / 100
    x = (a + y * (c / 12 + s / 32 + n / 28) - y * a) / (1 - y - y * RAZAO_N2_O2_AR)
    return x / a


def _t_orvalho_agua_c(n_h2o: float, n_secos: float, p_gases_bar_abs: float) -> float:
    """Orvalho da água nos gases (°C): T_sat na pressão parcial do vapor (E7).

    Não inclui orvalho ácido (SO₃) nem a umidade do ar de combustão.
    """
    p_h2o_bar = n_h2o / (n_h2o + n_secos) * p_gases_bar_abs
    return IAPWS97(P=p_h2o_bar / 10, x=0).T - 273.15


def perda_gases(
    t_gases_c: float,
    o2_seco_pct: float,
    umidade_bu_frac: float,
    t_ar_c: float,
    composicao_seca: Mapping[str, float],
    pci_seco_mj_kg: float,
    modelo_cp: str = "constante",
    p_gases_bar_abs: float = P_ATM_NIVEL_DO_MAR_BAR,
    co_ppm: float | None = None,
) -> ResultadoPerdaGases:
    """Perda sensível nos gases de chaminé, % do PCI (E1–E7).

    q_g = [m_gs·cp_gs + m_H2O·cp_H2O] · (T_g − T_ar) / (PCI_seco − 2,442·w/(1−w))

    com m_gs = 44·n_CO2 + 64·n_SO2 + 32·n_O2 + 28·n_N2 (E3) e
    m_H2O = 9H + w/(1−w) (E4), tudo por kg de combustível seco.

    Entradas:
        t_gases_c, t_ar_c: temperaturas dos gases na chaminé e do ar de combustão, °C.
        o2_seco_pct: O₂ medido nos gases secos, %.
        umidade_bu_frac: umidade do combustível, base úmida, fração.
        composicao_seca: frações C, H, O, N, S em base seca.
        pci_seco_mj_kg: PCI em base seca, MJ/kg.
        modelo_cp: "constante" (referência, reproduz o golden) ou "variavel"
            (bloqueado até o revisor definir a fonte de cp(T), E6).
        p_gases_bar_abs: pressão dos gases para o orvalho (padrão: nível do mar).
        co_ppm: CO medido; acima de 200 ppm gera aviso (E2).

    Bloqueia (E7) se os gases estiverem abaixo do orvalho da água ou não estiverem
    mais quentes que o ar de combustão.
    """
    if modelo_cp not in MODELOS_CP:
        raise ValueError(f"modelo_cp desconhecido: {modelo_cp!r} (use {MODELOS_CP})")
    if modelo_cp == "variavel":
        raise AnaliseBloqueada(
            "Modo cp variável ainda indisponível: a fonte de cp(T) será definida pelo "
            "revisor científico (E6). Use o modo de referência (cp constante)."
        )
    c, h, _o, n, s = _checar_composicao(composicao_seca)
    pci_umido(pci_seco_mj_kg, umidade_bu_frac)  # valida umidade e PCI
    if t_gases_c <= t_ar_c:
        raise AnaliseBloqueada(
            f"Gases a {t_gases_c:g} °C não estão mais quentes que o ar de combustão "
            f"({t_ar_c:g} °C): a perda sensível não se aplica. Confira as leituras."
        )

    a = oxigenio_estequiometrico(composicao_seca)
    lam = razao_ar(o2_seco_pct, composicao_seca)
    n_co2, n_so2 = c / 12, s / 32
    n_o2 = (lam - 1) * a
    n_n2 = RAZAO_N2_O2_AR * lam * a + n / 28
    m_gs = 44 * n_co2 + 64 * n_so2 + 32 * n_o2 + 28 * n_n2
    agua_por_seco = umidade_bu_frac / (1 - umidade_bu_frac)
    m_h2o = 9 * h + agua_por_seco

    t_orvalho = _t_orvalho_agua_c(
        m_h2o / MASSA_MOLAR_H2O, n_co2 + n_so2 + n_o2 + n_n2, p_gases_bar_abs
    )
    if t_gases_c < t_orvalho:
        raise AnaliseBloqueada(
            f"Gases a {t_gases_c:g} °C estão abaixo do orvalho estimado ({t_orvalho:.0f} °C): "
            "há condensação e a fórmula de perda sensível não vale (E7)."
        )

    calor = (m_gs * CP_GASES_SECOS_MJ_KG_K + m_h2o * CP_VAPOR_AGUA_MJ_KG_K) * (t_gases_c - t_ar_c)
    pci_por_kg_seco = pci_seco_mj_kg - H_VAP_25C_MJ_KG * agua_por_seco

    avisos = []
    if co_ppm is not None and co_ppm > CO_LIMITE_AVISO_PPM:
        avisos.append(
            f"CO de {co_ppm:g} ppm: acima de {CO_LIMITE_AVISO_PPM} ppm, o λ calculado sem "
            "considerar CO pode ter erro (E2, em revisão)."
        )

    return ResultadoPerdaGases(
        perda_pct=100 * calor / pci_por_kg_seco,
        lambda_ar=lam,
        o2_esteq_kmol_kg=a,
        m_gases_secos_kg_kg=m_gs,
        m_h2o_kg_kg=m_h2o,
        t_orvalho_c=t_orvalho,
        modelo_cp=modelo_cp,
        avisos=tuple(avisos),
    )


def alerta_temperatura_implausivel(
    t_gases_c: float,
    p_vapor_bar_abs: float,
    aproximacao_minima_c: float | None,
    tem_recuperador: bool = False,
) -> str | None:
    """Alerta de plausibilidade da temperatura dos gases (E7).

    Sem economizador ou pré-aquecedor, os gases devem sair acima de
    T_sat(p) + aproximação mínima. O valor da aproximação ainda não foi definido
    pelo revisor: sem ele (None), nenhum alerta é emitido (nunca inventar número).
    Retorna a mensagem do alerta ou None.
    """
    if aproximacao_minima_c is None or tem_recuperador:
        return None
    limite = t_sat_c(p_vapor_bar_abs) + aproximacao_minima_c
    if t_gases_c < limite:
        return (
            f"Gases a {t_gases_c:g} °C abaixo de saturação + aproximação mínima "
            f"({limite:.0f} °C) sem recuperador de calor: confira o ponto de medição "
            "e o instrumento."
        )
    return None
