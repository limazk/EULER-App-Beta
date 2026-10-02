"""Cálculo explícito da energia de purga quando a massa e a pressão são conhecidas.

Número de purgas e duração, sozinhos, não viram massa: seria necessário conhecer a válvula,
abertura, pressão e regime de escoamento. Por isso esta função exige massa já medida/estimada
fora dela e pressão absoluta própria do ponto de purga.
"""

from euler.tipos import AnaliseBloqueada
from euler.vapor import h_agua_mj_kg, h_vapor_mj_kg


def energia_purga_gj(
    *,
    massa_purga_kg: float,
    p_purga_bar_abs: float,
    p_agua_referencia_bar_abs: float,
    t_agua_referencia_c: float,
) -> float:
    """Energia bruta removida pela purga em relação à água de alimentação.

    Q_bd = m_bd · [h_f,sat(p_bd) − h_fw(p_fw, T_fw)].

    Não há crédito de tanque flash nem recuperação de calor; portanto é uma perda bruta na
    fronteira da caldeira, não necessariamente a perda líquida da planta.
    """
    if massa_purga_kg < 0:
        raise AnaliseBloqueada("Massa de purga negativa: confira a medição.")
    if massa_purga_kg == 0:
        return 0.0
    h_bd = h_vapor_mj_kg(p_purga_bar_abs, "umido", titulo=0.0)
    h_fw = h_agua_mj_kg(p_agua_referencia_bar_abs, t_agua_referencia_c)
    if h_bd <= h_fw:
        raise AnaliseBloqueada(
            "A entalpia calculada da purga não supera a da água de alimentação; confira os dados."
        )
    return massa_purga_kg * (h_bd - h_fw) / 1000
