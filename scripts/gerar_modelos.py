"""Gera docs/dados/contrato_dados.md e templates/planilha_modelo_euler.xlsx a partir dos esquemas.

Uso: python scripts/gerar_modelos.py
"""

from euler.io.modelos import RAIZ, gerar_tudo

if __name__ == "__main__":
    for caminho in gerar_tudo():
        print(caminho.relative_to(RAIZ))
