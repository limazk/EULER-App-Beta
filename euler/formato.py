"""Formatação de números para o usuário final (padrão brasileiro: 1.234,56)."""

import pandas as pd


def num(valor: float | None, casas: int = 2, vazio: str = "—") -> str:
    """Número com vírgula decimal e ponto de milhar; `vazio` quando não há valor.

    Ausente nunca vira zero (AGENTS.md, regra 2).
    """
    if pd.isna(valor):
        return vazio
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "§").replace(".", ",").replace("§", ".")
