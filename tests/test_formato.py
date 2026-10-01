import math

from euler.formato import num


def test_virgula_decimal_e_ponto_de_milhar():
    assert num(1234.567) == "1.234,57"
    assert num(11.773, 3) == "11,773"
    assert num(-0.5, 1) == "-0,5"


def test_ausente_nao_vira_zero():
    assert num(None) == "—"
    assert num(math.nan) == "—"
