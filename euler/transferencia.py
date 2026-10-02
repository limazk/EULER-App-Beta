"""Indicador físico de transferência no economizador.

UA aparente é um observável de transferência de calor, não diagnóstico automático de
fouling. Comparações devem considerar carga, bypass, sootblowing, pontos de medição e ΔP.
"""

from dataclasses import dataclass
from math import log

from euler.tipos import AnaliseBloqueada
from euler.vapor import h_agua_mj_kg


@dataclass(frozen=True)
class ResultadoUA:
    q_mw: float
    delta_t_lm_k: float
    ua_mw_k: float


def _lmtd(dt1: float, dt2: float) -> float:
    if dt1 <= 0 or dt2 <= 0:
        raise AnaliseBloqueada(
            "As temperaturas informadas produzem cruzamento térmico no economizador.",
            ["confirmar os quatro pontos de temperatura e o sentido dos fluxos"],
        )
    if abs(dt1 - dt2) < 1e-9:
        return dt1
    return (dt1 - dt2) / log(dt1 / dt2)


def ua_economizador(
    *,
    vazao_agua_t_h: float,
    p_agua_bar_abs: float,
    t_agua_entrada_c: float,
    t_agua_saida_c: float,
    t_gases_entrada_c: float,
    t_gases_saida_c: float,
) -> ResultadoUA:
    """Q pelo lado da água e UA aparente por LMTD, assumindo contracorrente."""
    if vazao_agua_t_h <= 0:
        raise AnaliseBloqueada("Vazão de água do economizador precisa ser positiva.")
    if t_agua_saida_c <= t_agua_entrada_c:
        raise AnaliseBloqueada(
            "A água não aqueceu entre entrada e saída do economizador; confira os pontos."
        )
    if t_gases_saida_c >= t_gases_entrada_c:
        raise AnaliseBloqueada(
            "Os gases não resfriaram entre entrada e saída do economizador; confira os pontos."
        )
    h_in = h_agua_mj_kg(p_agua_bar_abs, t_agua_entrada_c)
    h_out = h_agua_mj_kg(p_agua_bar_abs, t_agua_saida_c)
    mdot_kg_s = vazao_agua_t_h * 1000 / 3600
    q_mw = mdot_kg_s * (h_out - h_in)
    dt1 = t_gases_entrada_c - t_agua_saida_c
    dt2 = t_gases_saida_c - t_agua_entrada_c
    lmtd = _lmtd(dt1, dt2)
    return ResultadoUA(q_mw, lmtd, q_mw / lmtd)
