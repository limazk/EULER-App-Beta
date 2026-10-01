"""Resumo de um período de operação a partir das tabelas importadas.

Um período vai de uma medição de estoque a outra (é o que permite saber quanto
combustível foi queimado, E9). Para cada período: médias das leituras do diário,
vapor produzido, combustível queimado, umidade e PCI da mistura recebida, preço,
purgas e eventos. Nada é preenchido: o que não pode ser determinado vira um
**bloqueio** com motivo, em `ResumoPeriodo.bloqueios`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import pairwise
from math import sqrt

import pandas as pd

from euler.combustivel import combustivel_queimado_kg, extrato_por_fornecedor
from euler.deteccao import Estatistica, estatistica_diaria
from euler.io import Pacote
from euler.tipos import AnaliseBloqueada, Grandeza

LEITURAS_DIARIO = {
    "t_gases_c": "°C",
    "o2_seco_pct": "%",
    "co_ppm": "ppm",
    "t_ar_c": "°C",
    "t_agua_alim_c": "°C",
    "p_vapor_bar_abs": "bar abs",
}
ELEMENTOS = ("C", "H", "O", "N", "S")


@dataclass
class ResumoPeriodo:
    inicio: pd.Timestamp
    fim: pd.Timestamp
    leituras: dict[str, Estatistica] = field(default_factory=dict)
    n_leituras_diario: int = 0
    vapor_t: Grandeza | None = None
    combustivel_kg: Grandeza | None = None
    umidade_mistura: Grandeza | None = None
    pci_umido_mistura: Grandeza | None = None
    pci_seco_mistura: float | None = None
    composicao: dict[str, float] | None = None
    composicao_origem: str | None = None
    preco_brl_t: float | None = None
    preco_brl_gj: float | None = None
    lotes: int = 0
    lotes_sem_umidade: int = 0
    fracao_massa_sem_umidade: float | None = None
    umidade_por_fornecedor: dict[str, float] = field(default_factory=dict)
    purgas_n: float | None = None
    purgas_s: float | None = None
    eventos: list[dict] = field(default_factory=list)
    bloqueios: dict[str, AnaliseBloqueada] = field(default_factory=dict)

    @property
    def horas(self) -> float:
        return (self.fim - self.inicio).total_seconds() / 3600

    def rotulo(self) -> str:
        return f"{self.inicio:%d/%m/%Y %H:%M} a {self.fim:%d/%m/%Y %H:%M}"


def medicoes_de_estoque(pacote: Pacote) -> pd.DataFrame:
    """Medições de estoque com massa conhecida, em ordem de data."""
    comb = pacote.dados("combustivel")
    if comb is None:
        return pd.DataFrame(columns=["data", "massa_kg_calc", "linha"])
    estoques = comb[(comb["tipo"] == "estoque") & comb["massa_kg_calc"].notna()]
    return estoques.sort_values("data")[["data", "massa_kg_calc", "linha"]].reset_index(drop=True)


def periodos_entre_estoques(pacote: Pacote) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    """Intervalos entre medições de estoque consecutivas (os períodos possíveis)."""
    datas = list(medicoes_de_estoque(pacote)["data"])
    return list(pairwise(datas))


def incerteza_relativa_instrumento(pacote: Pacote, tipo_contem: str) -> float | None:
    """Incerteza relativa declarada (fração) de um instrumento em % da leitura.

    A incerteza declarada é tratada como expandida (k = 2), proposta D24.
    """
    inst = pacote.dados("instrumentos")
    if inst is None:
        return None
    linhas = inst[
        inst["tipo"].str.contains(tipo_contem, na=False)
        & (inst["unidade"] == "pct_da_leitura")
        & inst["incerteza_declarada"].notna()
    ]
    return None if linhas.empty else float(linhas["incerteza_declarada"].iloc[0]) / 100


def _intervalo_tipico_h(diario: pd.DataFrame) -> float:
    passos = diario["instante_observado"].dropna().sort_values().diff().dt.total_seconds() / 3600
    passos = passos[passos > 0]
    return float(passos.median()) if len(passos) else 2.0


def _vapor(pacote: Pacote, diario: pd.DataFrame, r: ResumoPeriodo) -> None:
    """Vapor produzido no período pelo totalizador (só diferenças, nunca preenchido)."""
    falta = ["leituras do totalizador de vapor no início e no fim do período, sem reinício"]
    tot = diario.dropna(subset=["totalizador_vapor_t"]).sort_values(["instante_observado", "linha"])
    tot = tot[(tot["instante_observado"] >= r.inicio) & (tot["instante_observado"] <= r.fim)]
    if len(tot) < 2:
        r.bloqueios["vapor"] = AnaliseBloqueada(
            "Sem leituras do totalizador de vapor neste período: o vapor produzido não é conhecido.",
            falta,
        )
        return
    valores = tot["totalizador_vapor_t"].astype(float).values
    reinicio = [i for i in range(1, len(valores)) if valores[i] < valores[i - 1]]
    if reinicio:
        linha = int(tot["linha"].iloc[reinicio[0]])
        r.bloqueios["vapor"] = AnaliseBloqueada(
            f"O totalizador de vapor reiniciou dentro do período (linha {linha} do diário): "
            "o vapor produzido entre essas leituras não é conhecido.",
            falta,
        )
        return
    tipico = _intervalo_tipico_h(diario)
    primeira, ultima = tot["instante_observado"].iloc[0], tot["instante_observado"].iloc[-1]
    folga_ini = (primeira - r.inicio).total_seconds() / 3600
    folga_fim = (r.fim - ultima).total_seconds() / 3600
    if folga_ini > tipico or folga_fim > tipico:
        r.bloqueios["vapor"] = AnaliseBloqueada(
            "Faltam leituras do totalizador de vapor perto do início ou do fim do período "
            f"(primeira às {primeira:%d/%m %H:%M}, última às {ultima:%d/%m %H:%M}).",
            falta,
        )
        return
    horas_lidas = (ultima - primeira).total_seconds() / 3600
    medido = float(valores[-1] - valores[0])
    vapor = medido * r.horas / horas_lidas
    rel = incerteza_relativa_instrumento(pacote, "vapor")
    r.vapor_t = Grandeza(
        vapor,
        "t",
        "estimado" if abs(horas_lidas - r.horas) > 1e-6 else "medido",
        incerteza=None if rel is None else rel * vapor,
        nota=(
            f"totalizador lido de {primeira:%d/%m %H:%M} a {ultima:%d/%m %H:%M} "
            f"({horas_lidas:.0f} h de {r.horas:.0f} h); bordas pela vazão média do período"
        ),
    )


def _combustivel(pacote: Pacote, r: ResumoPeriodo) -> None:
    """Combustível queimado no período (E9), com incerteza das medições de estoque."""
    comb = pacote.dados("combustivel")
    if comb is None:
        r.bloqueios["combustivel"] = AnaliseBloqueada(
            "Sem combustivel.csv: o combustível queimado não é conhecido.",
            ["recebimentos e medições de estoque"],
        )
        return
    estoques = medicoes_de_estoque(pacote)
    tol = pd.Timedelta(minutes=1)
    ini = estoques[(estoques["data"] - r.inicio).abs() <= tol]
    fim = estoques[(estoques["data"] - r.fim).abs() <= tol]
    receb = comb[
        (comb["tipo"] == "recebimento") & (comb["data"] > r.inicio) & (comb["data"] <= r.fim)
    ]
    try:
        m = combustivel_queimado_kg(
            None if ini.empty else float(ini["massa_kg_calc"].iloc[0]),
            [None if pd.isna(x) else float(x) for x in receb["massa_kg_calc"]],
            None if fim.empty else float(fim["massa_kg_calc"].iloc[0]),
        )
    except AnaliseBloqueada as b:
        r.bloqueios["combustivel"] = b
        return
    rel_estoque = incerteza_relativa_instrumento(pacote, "estoque")
    incerteza = None
    if rel_estoque is not None:
        e_ini, e_fim = float(ini["massa_kg_calc"].iloc[0]), float(fim["massa_kg_calc"].iloc[0])
        incerteza = sqrt((rel_estoque * e_ini) ** 2 + (rel_estoque * e_fim) ** 2)
    r.combustivel_kg = Grandeza(
        m,
        "kg",
        "medido",
        incerteza=incerteza,
        nota=f"estoque inicial + {len(receb)} recebimentos − estoque final (E9)",
    )


def _mistura(pacote: Pacote, r: ResumoPeriodo) -> None:
    """Umidade, PCI e preço da mistura recebida no período (hipótese D22)."""
    comb, amos = pacote.dados("combustivel"), pacote.dados("amostras")
    if comb is None:
        return
    e = extrato_por_fornecedor(comb, amos, inicio=r.inicio + pd.Timedelta(seconds=1), fim=r.fim)
    lotes = e.lotes.dropna(subset=["massa_kg"])
    r.lotes = len(e.lotes)
    if lotes.empty:
        r.bloqueios["mistura"] = AnaliseBloqueada(
            "Nenhum recebimento com massa conhecida neste período.", ["recebimentos pesados"]
        )
        return
    medidos = lotes.dropna(subset=["umidade_bu_frac"])
    r.lotes_sem_umidade = int(len(e.lotes) - len(e.lotes.dropna(subset=["umidade_bu_frac"])))
    r.fracao_massa_sem_umidade = float(1 - medidos["massa_kg"].sum() / lotes["massa_kg"].sum())
    det = lotes[lotes["situacao"] == "determinada"]
    if len(medidos) < 2 or len(det) < 2:
        r.bloqueios["mistura"] = AnaliseBloqueada(
            "Menos de dois lotes com umidade e PCI conhecidos neste período: a energia da "
            "mistura de combustível não é conhecida.",
            ["umidade medida de cada lote recebido"],
        )
        return

    def media_ponderada(df: pd.DataFrame, col: str) -> tuple[float, float]:
        pesos = df["massa_kg"] / df["massa_kg"].sum()
        media = float((df[col] * pesos).sum())
        erro = float(df[col].std(ddof=1) / sqrt(len(df)))
        return media, erro

    w, erro_w = media_ponderada(medidos, "umidade_bu_frac")
    nota = f"média dos {len(medidos)} lotes recebidos com umidade medida, ponderada pela massa" + (
        f"; {r.fracao_massa_sem_umidade:.0%} da massa sem umidade medida"
        if r.fracao_massa_sem_umidade
        else ""
    )
    r.umidade_mistura = Grandeza(w, "fração", "estimado", 2 * erro_w, nota)
    pci, erro_pci = media_ponderada(det, "pci_umido_mj_kg")
    r.pci_umido_mistura = Grandeza(
        pci,
        "MJ/kg",
        "estimado",
        2 * erro_pci,
        "PCI úmido médio dos lotes recebidos no período (hipótese: o que entra é o que queima)",
    )
    r.pci_seco_mistura, _ = media_ponderada(det, "pci_seco_mj_kg")
    com_preco = lotes.dropna(subset=["preco_brl"])
    if len(com_preco):
        r.preco_brl_t = float(com_preco["preco_brl"].sum() / (com_preco["massa_kg"].sum() / 1000))
    det_preco = det.dropna(subset=["brl_gj"])
    if len(det_preco):
        r.preco_brl_gj = float(det_preco["preco_brl"].sum() / det_preco["energia_gj"].sum())
    for forn, g in medidos.dropna(subset=["fornecedor_id"]).groupby("fornecedor_id"):
        r.umidade_por_fornecedor[forn] = float(
            (g["umidade_bu_frac"] * g["massa_kg"]).sum() / g["massa_kg"].sum()
        )


def _composicao(pacote: Pacote, r: ResumoPeriodo) -> None:
    """Composição elementar média das análises do período (ou a mais próxima, assumida)."""
    amos = pacote.dados("amostras")
    if amos is None:
        return
    completas = amos.dropna(subset=list(ELEMENTOS))
    if completas.empty:
        return
    no_periodo = completas[(completas["data"] >= r.inicio) & (completas["data"] <= r.fim)]
    if len(no_periodo):
        r.composicao = {e: float(no_periodo[e].mean()) for e in ELEMENTOS}
        r.composicao_origem = f"medido ({len(no_periodo)} análises no período)"
    else:
        meio = r.inicio + (r.fim - r.inicio) / 2
        mais_proxima = completas.loc[(completas["data"] - meio).abs().idxmin()]
        r.composicao = {e: float(mais_proxima[e]) for e in ELEMENTOS}
        r.composicao_origem = f"assumido (análise de {mais_proxima['data']:%d/%m/%Y})"


def resumir_periodo(pacote: Pacote, inicio: pd.Timestamp, fim: pd.Timestamp) -> ResumoPeriodo:
    """Resume o período [inicio, fim] (inicio e fim devem ser medições de estoque)."""
    r = ResumoPeriodo(inicio=inicio, fim=fim)
    diario = pacote.dados("diario")
    if diario is None:
        r.bloqueios["diario"] = AnaliseBloqueada(
            "Sem diário do operador: não há leituras da caldeira.", ["diario.csv"]
        )
    else:
        no_periodo = diario[
            (diario["instante_observado"] >= inicio) & (diario["instante_observado"] < fim)
        ]
        operando = no_periodo[no_periodo["regime"].fillna("estavel") != "parada"]
        operando = operando.drop_duplicates(subset=[c for c in operando.columns if c != "linha"])
        r.n_leituras_diario = len(operando)
        for coluna, unidade in LEITURAS_DIARIO.items():
            est = estatistica_diaria(operando[coluna], operando["instante_observado"], unidade)
            if est is not None:
                r.leituras[coluna] = est
        if no_periodo["purgas_n"].notna().any():
            r.purgas_n = float(no_periodo["purgas_n"].sum())
        if no_periodo["purgas_s"].notna().any():
            r.purgas_s = float(no_periodo["purgas_s"].sum())
        _vapor(pacote, diario, r)
    _combustivel(pacote, r)
    _mistura(pacote, r)
    _composicao(pacote, r)
    eventos = pacote.dados("eventos")
    if eventos is not None:
        ev = eventos[(eventos["instante"] >= inicio) & (eventos["instante"] <= fim)]
        r.eventos = [
            {"instante": t, "tipo": tipo, "descricao": d}
            for t, tipo, d in zip(ev["instante"], ev["tipo"], ev["descricao"], strict=True)
        ]
    return r
