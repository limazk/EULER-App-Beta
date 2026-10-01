"""Constrói pacotes sintéticos pequenos para testar a investigação (casos A, B, C...).

Modelo do construtor: rendimento = 1 − (perda nos gases + outras perdas)/100, com a
perda nos gases tirada da tabela golden (valores revisados), nunca do código testado.
Cada período começa e termina numa medição de estoque; uma entrega por dia repõe o
que foi queimado.

Instrumentos (SINTÉTICOS, só para teste): por padrão todos os que o motor usa são
cadastrados, para que os casos testem as regras da investigação com o orçamento de
incerteza completo. `instrumentos="basico"` cadastra só o medidor de vapor e o estoque;
uma tupla de códigos cadastra só esses; `False` não cadastra nenhum.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

from euler.io import Pacote, importar_pacote
from euler.vapor import delta_h_mj_kg, p_absoluta_bar

FUSO = timezone(timedelta(hours=-3))
P_ATM = 1.01325
COMPOSICAO = {"C": 0.50, "H": 0.06, "O": 0.43, "N": 0.003, "S": 0.0005}
PCI_SECO = 18.5


@dataclass
class Periodo:
    perda_gases_pp: float  # da tabela golden para (t_gases, o2, umidade)
    t_gases_c: float = 180.0
    o2_seco_pct: float = 8.0
    umidade: float = 0.40
    outras_perdas_pp: float = 8.0
    preco_brl_t: float = 180.0
    dias: int = 14
    vapor_t_h: float = 10.0
    p_vapor_bar_man: float = 9.0
    t_agua_alim_c: float = 80.0
    t_ar_c: float = 25.0
    registrar_purgas: bool = True
    totalizador: bool = True


INSTRUMENTOS_SINTETICOS = {
    "MED-V": "MED-V,medidor_vazao_vapor,LINHA,pct_da_leitura,0.1,1",
    "EST": "EST,levantamento_estoque,PATIO,pct_da_leitura,100,1",
    "TERMO-G": "TERMO-G,termopar_gases,CHAMINE,c,1,2",
    "ANALIS": "ANALIS,analisador_o2,CHAMINE,pct_seco,0.1,0.3",
    "TERMO-AR": "TERMO-AR,temperatura_ar_combustao,ENTRADA,c,1,1",
    "MANOM": "MANOM,manometro,TUBULAO,bar,0.1,0.2",
    "TERMO-AGUA": "TERMO-AGUA,termometro_agua_alimentacao,LINHA,c,1,1",
    "ESTUFA": "ESTUFA,estufa_umidade,LAB,pct,0.1,0.5",
    "CALOR": "CALOR,calorimetro_pci,LAB,pct_da_leitura,0.01,1",
    "BALANCA": "BALANCA,balanca_rodoviaria,PORTARIA,kg,10,20",
}


def montar(
    periodos: list[Periodo],
    semente: int = 7,
    instrumentos: bool | str | tuple[str, ...] = True,
) -> tuple[Pacote, list[tuple]]:
    """Devolve (pacote, [(início, fim) de cada período])."""
    rng = np.random.default_rng(semente)
    t0 = datetime(2026, 1, 5, 7, 30, tzinfo=FUSO)
    diario = [
        (
            "caldeira_id,instante_observado,instante_registrado,regime,p_vapor_bar_man,t_gases_c,"
            "o2_seco_pct,t_agua_alim_c,t_ar_c,purgas_n,purgas_s,totalizador_vapor_t,origem_dado"
        )
    ]
    comb = ["data,tipo,fornecedor_id,lote_id,massa_kg,preco_brl,origem_dado"]
    amos = ["amostra_id,lote_id,data,umidade_bu_frac,pci_seco_mj_kg,C,H,O,N,S,origem_dado"]
    estoque, totalizador, n_lote = 100_000.0, 1_000.0, 0
    limites = []
    inicio = t0
    comb.append(f"{inicio.isoformat()},estoque,,,{estoque:.0f},,sintetico")
    for p in periodos:
        dh = delta_h_mj_kg(
            p_absoluta_bar(p.p_vapor_bar_man, P_ATM), "saturado_seco", p.t_agua_alim_c
        )
        rendimento = 1 - (p.perda_gases_pp + p.outras_perdas_pp) / 100
        pci_u = (1 - p.umidade) * PCI_SECO - 2.442 * p.umidade
        for d in range(p.dias):
            dia = inicio + timedelta(days=d)
            vapor_dia = 0.0
            for k in range(12):
                t = dia + timedelta(minutes=30) + timedelta(hours=2 * k)
                vapor = p.vapor_t_h * 2
                vapor_dia += vapor
                totalizador += vapor
                purga = (
                    "1,20"
                    if p.registrar_purgas and k % 2 == 0
                    else ("0,0" if p.registrar_purgas else ",")
                )
                tot = f"{totalizador:.2f}" if p.totalizador else ""
                diario.append(
                    f"CALD-T,{t.isoformat()},{(t + timedelta(minutes=5)).isoformat()},estavel,"
                    f"{p.p_vapor_bar_man + rng.normal(0, 0.05):.2f},{p.t_gases_c + rng.normal(0, 1.5):.1f},"
                    f"{p.o2_seco_pct + rng.normal(0, 0.15):.2f},{p.t_agua_alim_c + rng.normal(0, 0.5):.1f},"
                    f"{p.t_ar_c + rng.normal(0, 0.5):.1f},{purga},{tot},sintetico"
                )
            queimado = vapor_dia * 1000 * dh / (rendimento * pci_u)
            n_lote += 1
            lote = f"L{n_lote:03d}"
            chegada = dia + timedelta(hours=2)
            comb.append(
                f"{chegada.isoformat()},recebimento,F1,{lote},{queimado:.0f},"
                f"{queimado / 1000 * p.preco_brl_t:.2f},sintetico"
            )
            w = p.umidade + rng.normal(0, 0.002)
            amos.append(
                f"A{n_lote:03d},{lote},{(chegada + timedelta(hours=1)).isoformat()},{w:.4f},{PCI_SECO},"
                + ",".join(str(COMPOSICAO[e]) for e in "CHONS")
                + ",sintetico"
            )
        fim = inicio + timedelta(days=p.dias)
        comb.append(f"{fim.isoformat()},estoque,,,{estoque:.0f},,sintetico")
        limites.append((inicio, fim))
        inicio = fim

    if instrumentos is True:
        codigos = tuple(INSTRUMENTOS_SINTETICOS)
    elif instrumentos == "basico":
        codigos = ("MED-V", "EST")
    else:
        codigos = tuple(instrumentos or ())
    tabela_instrumentos = "\n".join(
        ["instrumento_id,tipo,ponto,unidade,resolucao,incerteza_declarada"]
        + [INSTRUMENTOS_SINTETICOS[c] for c in codigos]
    )
    arquivos = {
        "diario": "\n".join(diario).encode(),
        "combustivel": "\n".join(comb).encode(),
        "amostras": "\n".join(amos).encode(),
        **({"instrumentos": tabela_instrumentos.encode()} if codigos else {}),
    }
    pacote = importar_pacote(arquivos, p_atm_bar=P_ATM)
    pacote.__dict__["_arquivos_teste"] = arquivos  # para abrir o mesmo caso na tela (AppTest)
    return pacote, [(pd.Timestamp(a), pd.Timestamp(b)) for a, b in limites]
