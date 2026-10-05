"""Extrai o diário da planilha pública do MDL (projeto 1202) para um CSV legível.

Fonte: planilha `1202_CER_Calc_Sheet_Rev1.xls`, publicada pela UNFCCC no pedido de emissão
do projeto 1202 (cervejaria AmBev, filial Águas Claras do Sul, Viamão/RS). A planilha fica
no repositório sem nenhuma alteração; este script só copia as colunas diárias para
`diario.csv`, com os nomes das grandezas e unidades **como publicadas**.

Regras: nenhum valor é preenchido, arredondado ou convertido. Célula vazia continua vazia
(ausente ≠ zero). Cada linha guarda o número da linha na planilha original para conferência.
As conversões de unidade (kgf/cm² → bar absoluto etc.) acontecem na análise, explícitas.

Uso: python scripts/extrair_cervejaria.py   (precisa de xlrd: pip install -e ".[validacao]")
"""

from __future__ import annotations

import hashlib
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

PASTA = Path(__file__).resolve().parents[1] / "validation/public/cervejaria_rs"
PLANILHA = PASTA / "1202_CER_Calc_Sheet_Rev1.xls"
SHA256 = "38fd1e5e2e7be58da9f54a7eaa1bed8c6d5a301ec43adb41bd8566c6db046283"
ABA = "Emission Reduction Calculation"

# coluna da planilha → nome no CSV (unidade como publicada no cabeçalho da planilha)
COLUNAS = {
    2: "oleo_pesado_t",  # Heavy Oil Consumption [ton]
    3: "sebo_t",  # Animal Tallow Consumption [Ton]
    4: "oleo_equivalente_t",  # Total Heavy Oil Equivalent Consumption [Ton]
    5: "caldeira_oleo_energia_tj",  # ATA AWN-30 Boilers · Total Energy Generated [TJ/day]
    6: "casca_arroz_t",  # Rice Husk [Ton]
    7: "casca_carvalho_t",  # Oak Husk [Ton]
    8: "cald1_horas",  # Bremer HBFR-4 Nº1 · Nº of working hours
    9: "cald1_p_vapor_kgf_cm2",  # Steam Pressure (Kg/cm²)
    10: "cald1_vapor_t",  # Steam Generated (ton/day)
    11: "cald1_entalpia_tj_t",  # Heat Enthalpy (TJ/ton)
    12: "cald1_energia_tj",  # Energy (TJ/day)
    13: "cald2_horas",
    14: "cald2_p_vapor_kgf_cm2",
    15: "cald2_vapor_t",
    16: "cald2_entalpia_tj_t",
    17: "cald2_energia_tj",
    18: "vapor_total_t",  # Bremer HBFR Boilers · Total Steam Generated [Ton/day]
    19: "energia_biomassa_tj",  # Total Energy Generated [TJ/day]
}


def sha256(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def extrair(planilha: Path = PLANILHA) -> pd.DataFrame:
    """Linhas diárias da aba de cálculo, valores exatamente como estão na planilha."""
    if sha256(planilha) != SHA256:
        raise ValueError("A planilha não é a versão publicada conferida (SHA-256 diferente).")
    bruto = pd.read_excel(planilha, sheet_name=ABA, header=None, engine="xlrd")
    # só as células de data são dias; os totais mensais ("AUG09 TOTAL") são texto
    datas = pd.to_datetime(bruto[0].where(bruto[0].map(lambda v: isinstance(v, datetime))))
    linhas = bruto.index[datas.notna()]
    d = pd.DataFrame({"linha_planilha": linhas + 1, "data": datas[linhas].dt.strftime("%Y-%m-%d")})
    for coluna, nome in COLUNAS.items():
        d[nome] = pd.to_numeric(bruto.loc[linhas, coluna], errors="raise").to_numpy()
    return d.reset_index(drop=True)


def main() -> int:
    d = extrair()
    destino = PASTA / "diario.csv"
    d.to_csv(destino, index=False)  # repr completo: a leitura devolve o mesmo float
    print(f"{len(d)} dias ({d.data.iloc[0]} a {d.data.iloc[-1]}) → {destino}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
