"""Resumo de um período de operação a partir das tabelas importadas.

Um período vai de uma medição de estoque a outra (é o que permite saber quanto
combustível foi queimado, E9). Para cada período: médias das leituras do diário,
vapor produzido, combustível queimado, qualidade do combustível recebido e do
**provavelmente** queimado, composição, preço, purgas e eventos. Nada é preenchido:
o que não pode ser determinado vira um **bloqueio** com motivo, em `bloqueios`.

Fase R (revisão do motor físico):
- cada grandeza carrega um orçamento de incerteza por componente (euler.incerteza);
- a qualidade do combustível **queimado** não é igualada à do recebido sem aviso:
  calculamos cenários de uso do pátio e os limites possíveis (D38);
- recebimento no mesmo horário de uma medição de estoque bloqueia o E9 (ER-5).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import pairwise
from math import sqrt

import pandas as pd

from euler.combustivel import combustivel_queimado_kg, extrato_por_fornecedor
from euler.deteccao import Estatistica, estatistica_diaria
from euler.incerteza import Componente, Orcamento, incerteza_padrao
from euler.io import Pacote
from euler.io.leitura import FUSO_PADRAO
from euler.tipos import AnaliseBloqueada, Grandeza
from euler.vapor import delta_h_mj_kg

LEITURAS_DIARIO = {
    "t_gases_c": "°C",
    "o2_seco_pct": "%",
    "co_ppm": "ppm",
    "t_ar_c": "°C",
    "t_agua_alim_c": "°C",
    "p_vapor_bar_abs": "bar abs",
}
ELEMENTOS = ("C", "H", "O", "N", "S")
TOLERANCIA_INSTANTE = pd.Timedelta(minutes=1)

# Como reconhecer cada instrumento pelo `tipo` em instrumentos.csv (D23) e pelas palavras
# que o identificam na descrição de um evento de calibração/troca (D37).
INSTRUMENTOS = {
    "vapor": (("vapor",), ("vapor",)),
    "estoque": (("estoque",), ("estoque",)),
    "balanca": (("balanca",), ("balança", "balanca")),
    "umidade": (("umidade", "estufa"), ("estufa", "umidade")),
    "t_gases_c": (("gases",), ("termopar", "temperatura dos gases")),
    "o2_seco_pct": (("o2",), ("o₂", "o2", "oxigênio")),
    "p_vapor_bar_abs": (("manometro", "pressao"), ("manômetro", "manometro", "pressão")),
    "t_agua_alim_c": (("agua",), ("água de alimentação", "agua de alimentacao")),
    "t_ar_c": (("ar_combustao", "temperatura_ar"), ("ar de combustão",)),
}


# ---------------------------------------------------------------- instrumentos


@dataclass(frozen=True)
class Instrumento:
    """Instrumento cadastrado e sua incerteza-padrão (k = 1)."""

    id: str
    tipo: str
    u: float
    relativa: bool
    interpretacao: str


def buscar_instrumento(
    pacote: Pacote, grandeza: str, id_preferido: str | None = None
) -> Instrumento | None:
    """Instrumento cadastrado para a grandeza, com a incerteza convertida (GUM, D35).

    Incerteza em `pct_da_leitura` vira fração relativa; `pct`/`pct_bu` de umidade vira
    fração absoluta; demais unidades ficam na unidade da grandeza.
    """
    inst = pacote.dados("instrumentos")
    if inst is None:
        return None
    candidatos = inst[inst["incerteza_declarada"].notna()]
    if id_preferido is not None and (candidatos["instrumento_id"] == id_preferido).any():
        candidatos = candidatos[candidatos["instrumento_id"] == id_preferido]
    else:
        palavras = INSTRUMENTOS[grandeza][0]
        tipo = candidatos["tipo"].fillna("").str.lower()
        candidatos = candidatos[tipo.apply(lambda t: any(p in t for p in palavras))]
    if candidatos.empty:
        return None
    linha = candidatos.iloc[0]
    tipo_decl = None if pd.isna(linha.get("incerteza_tipo")) else str(linha["incerteza_tipo"])
    k = None if pd.isna(linha.get("incerteza_k")) else float(linha["incerteza_k"])
    u, como = incerteza_padrao(float(linha["incerteza_declarada"]), tipo_decl, k)
    unidade = str(linha["unidade"]).lower()
    relativa = unidade == "pct_da_leitura"
    if relativa or grandeza == "umidade" and unidade.startswith("pct"):
        u /= 100
    return Instrumento(str(linha["instrumento_id"]), str(linha["tipo"]), u, relativa, como)


def chave_instrumento(
    pacote: Pacote,
    inst: Instrumento,
    grandeza: str,
    inicio: pd.Timestamp,
    fim: pd.Timestamp,
    outras_datas: tuple[pd.Timestamp, ...] = (),
) -> str:
    """Chave da "época" do instrumento: muda a cada calibração ou troca (D37).

    Datas consideradas: `ultima_verificacao` do instrumento, eventos de calibração ou
    troca que citam o instrumento (pelo código ou por palavra-chave) e `outras_datas`
    (ex.: reinício do totalizador). Evento dentro do período → época mista, só dele.
    """
    datas: list[pd.Timestamp] = list(outras_datas)
    cadastro = pacote.dados("instrumentos")
    if cadastro is not None:
        linha = cadastro[cadastro["instrumento_id"] == inst.id]
        if len(linha) and pd.notna(linha["ultima_verificacao"].iloc[0]):
            datas.append(pd.Timestamp(linha["ultima_verificacao"].iloc[0]).tz_localize(FUSO_PADRAO))
    eventos = pacote.dados("eventos")
    if eventos is not None:
        palavras = INSTRUMENTOS[grandeza][1]
        for _, ev in eventos[eventos["tipo"].isin(["calibracao", "troca_instrumento"])].iterrows():
            texto = str(ev["descricao"]).lower()
            if inst.id.lower() in texto or any(p in texto for p in palavras):
                datas.append(ev["instante"])
    if any(inicio < d < fim for d in datas):
        return f"instrumento:{inst.id}@misto:{inicio.isoformat()}"
    anteriores = [d for d in datas if d <= inicio]
    return f"instrumento:{inst.id}@{max(anteriores).isoformat() if anteriores else 'origem'}"


# ---------------------------------------------------------------- resumo


@dataclass(frozen=True)
class Cenarios:
    """Grandeza do combustível **queimado** sob hipóteses de uso do pátio (D38).

    recebido: o que entra no período é o que queima (D22, estimativa central).
    fifo: o pátio usa primeiro o material mais antigo (estoque inicial = últimos lotes
        recebidos antes do período). None se os dados não cobrem o estoque inicial.
    minimo/maximo: limites para **qualquer** uso do pátio, com o estoque inicial de
        qualidade desconhecida dentro da faixa observada nos lotes.
    """

    recebido: float
    fifo: float | None
    minimo: float
    maximo: float

    @property
    def faixa_plausivel(self) -> tuple[float, float]:
        valores = [v for v in (self.recebido, self.fifo) if v is not None]
        return min(valores), max(valores)


@dataclass
class ResumoPeriodo:
    inicio: pd.Timestamp
    fim: pd.Timestamp
    leituras: dict[str, Estatistica] = field(default_factory=dict)
    leituras_grandeza: dict[str, Grandeza] = field(default_factory=dict)
    n_leituras_diario: int = 0
    cobertura_diario: float | None = None
    vapor_t: Grandeza | None = None
    energia_util_intervalos_gj: float | None = None
    combustivel_kg: Grandeza | None = None
    estoque_inicial_kg: float | None = None
    estoque_final_kg: float | None = None
    umidade_mistura: Grandeza | None = None
    pci_umido_mistura: Grandeza | None = None
    pci_queimado: Cenarios | None = None
    umidade_queimada: Cenarios | None = None
    fracao_estoque: float | None = None
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
    return list(pairwise(medicoes_de_estoque(pacote)["data"]))


def incerteza_relativa_instrumento(pacote: Pacote, tipo_contem: str) -> float | None:
    """Incerteza-padrão relativa (fração) de um instrumento em % da leitura (D35).

    Mantida por compatibilidade (capacidades); usa a interpretação do GUM, não k = 2 fixo.
    """
    inst = buscar_instrumento(pacote, tipo_contem)
    return inst.u if inst is not None and inst.relativa else None


def _intervalo_tipico_h(diario: pd.DataFrame) -> float:
    passos = diario["instante_observado"].dropna().sort_values().diff().dt.total_seconds() / 3600
    passos = passos[passos > 0]
    return float(passos.median()) if len(passos) else 2.0


def _lotes_todos(pacote: Pacote) -> pd.DataFrame:
    """Todos os lotes recebidos com massa, umidade e PCI úmido (calculado uma vez)."""
    cache = pacote.__dict__.setdefault("_cache_periodos", {})
    if "lotes" not in cache:
        comb, amos = pacote.dados("combustivel"), pacote.dados("amostras")
        lotes = extrato_por_fornecedor(comb, amos).lotes if comb is not None else pd.DataFrame()
        cache["lotes"] = lotes.dropna(subset=["massa_kg"]) if len(lotes) else lotes
    return cache["lotes"]


def _vapor(pacote: Pacote, diario: pd.DataFrame, r: ResumoPeriodo) -> None:
    """Vapor produzido no período pelo totalizador (só diferenças, nunca preenchido)."""
    falta = ["leituras do totalizador de vapor no início e no fim do período, sem reinício"]
    todos = diario.dropna(subset=["totalizador_vapor_t"]).sort_values(
        ["instante_observado", "linha"]
    )
    tot = todos[(todos["instante_observado"] >= r.inicio) & (todos["instante_observado"] <= r.fim)]
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
    _energia_util_intervalos(tot, r, r.horas / horas_lidas)

    orc = Orcamento()
    # bordas: vapor estimado pela vazão média; erro ~ variação da vazão × horas de borda
    horas = tot["instante_observado"].diff().dt.total_seconds().div(3600).iloc[1:].values
    vazoes = pd.Series(valores).diff().iloc[1:].values / horas
    horas_borda = folga_ini + folga_fim
    if horas_borda > 0 and len(vazoes) >= 2:
        orc.componentes.append(
            Componente(
                "vapor nas bordas do período (estimado pela vazão média)",
                float(pd.Series(vazoes).std(ddof=1)) * horas_borda / vapor,
                "modelo",
                nota=f"{horas_borda:.1f} h de borda × variação da vazão entre leituras",
            )
        )
    # medidor: erro sistemático declarado; a época muda com calibração, troca ou reinício
    inst = buscar_instrumento(pacote, "vapor")
    if inst is not None and inst.relativa:
        reinicios = tuple(
            todos["instante_observado"].iloc[i]
            for i in range(1, len(todos))
            if todos["totalizador_vapor_t"].iloc[i] < todos["totalizador_vapor_t"].iloc[i - 1]
        )
        orc.componentes.append(
            Componente(
                f"medidor de vapor {inst.id}",
                inst.u,
                "instrumental",
                chave_instrumento(pacote, inst, "vapor", r.inicio, r.fim, reinicios),
                inst.interpretacao,
            )
        )
        u_rel = orc.u_rel()
    else:
        orc.nao_incluidos.append("incerteza do medidor de vapor (não cadastrada em % da leitura)")
        u_rel = None
    r.vapor_t = Grandeza(
        vapor,
        "t",
        "estimado" if abs(horas_lidas - r.horas) > 1e-6 else "medido",
        incerteza=None if u_rel is None else 2 * u_rel * vapor,
        nota=(
            f"totalizador lido de {primeira:%d/%m %H:%M} a {ultima:%d/%m %H:%M} "
            f"({horas_lidas:.0f} h de {r.horas:.0f} h); bordas pela vazão média do período"
        ),
        orcamento=orc,
    )


def _energia_util_intervalos(tot: pd.DataFrame, r: ResumoPeriodo, escala: float) -> None:
    """Q_s = Σ ΔM_k · Δh(p_k, T_a,k) (E8), intervalo a intervalo entre leituras do
    totalizador, com p e T_a médias das duas leituras do intervalo. Só é usado quando
    todos os intervalos têm pressão e água de alimentação; senão fica None (D26)."""
    soma, cobertos = 0.0, 0
    linhas = list(tot.itertuples())
    for ant, atual in pairwise(linhas):
        massa = float(atual.totalizador_vapor_t) - float(ant.totalizador_vapor_t)
        p = pd.Series([ant.p_vapor_bar_abs, atual.p_vapor_bar_abs]).dropna()
        t = pd.Series([ant.t_agua_alim_c, atual.t_agua_alim_c]).dropna()
        if massa == 0:
            cobertos += 1
            continue
        if p.empty or t.empty:
            continue
        try:
            soma += massa * delta_h_mj_kg(float(p.mean()), "saturado_seco", float(t.mean()))
        except AnaliseBloqueada:
            continue
        cobertos += 1
    if linhas and cobertos == len(linhas) - 1:
        r.energia_util_intervalos_gj = soma * escala


def _combustivel(pacote: Pacote, r: ResumoPeriodo) -> None:
    """Combustível queimado no período (E9), com a incerteza de cada medição de estoque."""
    comb = pacote.dados("combustivel")
    if comb is None:
        r.bloqueios["combustivel"] = AnaliseBloqueada(
            "Sem combustivel.csv: o combustível queimado não é conhecido.",
            ["recebimentos e medições de estoque"],
        )
        return
    estoques = medicoes_de_estoque(pacote)
    ini = estoques[(estoques["data"] - r.inicio).abs() <= TOLERANCIA_INSTANTE]
    fim = estoques[(estoques["data"] - r.fim).abs() <= TOLERANCIA_INSTANTE]
    receb_todos = comb[comb["tipo"] == "recebimento"]
    simultaneos = receb_todos[
        ((receb_todos["data"] - r.inicio).abs() <= TOLERANCIA_INSTANTE)
        | ((receb_todos["data"] - r.fim).abs() <= TOLERANCIA_INSTANTE)
    ]
    if len(simultaneos):
        linhas = ", ".join(str(int(n)) for n in simultaneos["linha"])
        r.bloqueios["combustivel"] = AnaliseBloqueada(
            f"Recebimento registrado no mesmo horário de uma medição de estoque (linha {linhas} "
            "de combustivel.csv): não dá para saber se ele já estava no estoque medido.",
            ["horário do recebimento ou da medição de estoque, com a ordem entre eles"],
        )
        return
    receb = receb_todos[(receb_todos["data"] > r.inicio) & (receb_todos["data"] <= r.fim)]
    s0 = None if ini.empty else float(ini["massa_kg_calc"].iloc[0])
    s1 = None if fim.empty else float(fim["massa_kg_calc"].iloc[0])
    try:
        m = combustivel_queimado_kg(
            s0, [None if pd.isna(x) else float(x) for x in receb["massa_kg_calc"]], s1
        )
    except AnaliseBloqueada as b:
        r.bloqueios["combustivel"] = b
        return
    r.estoque_inicial_kg, r.estoque_final_kg = s0, s1

    orc = Orcamento()
    inst_est = buscar_instrumento(pacote, "estoque")
    if inst_est is not None and inst_est.relativa:
        for sinal, massa, instante in ((+1, s0, r.inicio), (-1, s1, r.fim)):
            orc.componentes.append(
                Componente(
                    f"medição de estoque de {instante:%d/%m %H:%M}",
                    sinal * inst_est.u * massa / m,
                    "instrumental",
                    f"medicao:estoque@{instante.isoformat()}",
                    inst_est.interpretacao,
                )
            )
        orc.nao_incluidos.append(
            "parcela sistemática comum às medições de estoque (método), não declarada à parte"
        )
        u_rel = orc.u_rel()
    else:
        orc.nao_incluidos.append("incerteza da medição de estoque (não cadastrada em % da leitura)")
        u_rel = None
    inst_bal = buscar_instrumento(pacote, "balanca")
    if inst_bal is not None and not inst_bal.relativa and len(receb):
        orc.componentes.append(
            Componente(
                f"pesagem de {len(receb)} recebimentos ({inst_bal.id})",
                sqrt(len(receb)) * inst_bal.u / m,
                "instrumental",
                nota=inst_bal.interpretacao + "; pesagens tratadas como independentes",
            )
        )
        orc.nao_incluidos.append(
            "parcela sistemática da balança (calibração), não declarada à parte"
        )
        u_rel = orc.u_rel() if u_rel is not None else None
    elif len(receb):
        orc.nao_incluidos.append("incerteza da balança dos recebimentos")
    origens = set(receb["massa_origem"].dropna())
    if "estimado" in origens:
        orc.nao_incluidos.append("incerteza da densidade usada nos recebimentos medidos por volume")
    r.combustivel_kg = Grandeza(
        m,
        "kg",
        "medido" if origens <= {"medido"} else "estimado",
        incerteza=None if u_rel is None else 2 * u_rel * m,
        nota=f"estoque inicial + {len(receb)} recebimentos − estoque final (E9)",
        orcamento=orc,
    )


def _media_ponderada(df: pd.DataFrame, col: str) -> float:
    return float((df[col] * df["massa_kg"]).sum() / df["massa_kg"].sum())


def _cenarios(
    lotes_todos: pd.DataFrame, col: str, r: ResumoPeriodo, recebido: float
) -> Cenarios | None:
    """Qualidade do combustível queimado sob uso FIFO do pátio e limites para qualquer uso."""
    if r.estoque_inicial_kg is None or r.estoque_final_kg is None or r.combustivel_kg is None:
        return None
    m_queimado = r.combustivel_kg.valor
    conhecidos = lotes_todos.dropna(subset=[col])
    if conhecidos.empty or m_queimado <= 0:
        return None
    q_min, q_max = float(conhecidos[col].min()), float(conhecidos[col].max())
    antes = lotes_todos[lotes_todos["data"] <= r.inicio].sort_values("data")
    no_periodo = lotes_todos[
        (lotes_todos["data"] > r.inicio) & (lotes_todos["data"] <= r.fim)
    ].sort_values("data")

    # FIFO: estoque inicial = últimos lotes antes do início, até completar S0
    fifo = None
    estoque_ini, falta = [], r.estoque_inicial_kg
    for _, lote in antes.iloc[::-1].iterrows():
        if falta <= 0:
            break
        usar = min(falta, float(lote["massa_kg"]))
        estoque_ini.insert(0, (usar, lote[col]))
        falta -= usar
    if falta <= 1e-6:
        fila = estoque_ini + [(float(x["massa_kg"]), x[col]) for _, x in no_periodo.iterrows()]
        massa_q, soma_q, restante = 0.0, 0.0, m_queimado
        for massa, q in fila:
            if restante <= 0:
                break
            usar = min(massa, restante)
            restante -= usar
            if pd.notna(q):
                massa_q += usar
                soma_q += usar * float(q)
        if massa_q > 0 and restante <= 1e-6:
            fifo = soma_q / massa_q

    def limite(maximo: bool) -> float:
        """Estoque inicial de qualidade desconhecida; o estoque final pode ser qualquer parte
        do material disponível. Para o máximo do queimado, o pior material fica no pátio."""
        desconhecido = q_max if maximo else q_min
        material = [(r.estoque_inicial_kg, desconhecido)] + [
            (float(x["massa_kg"]), float(x[col]) if pd.notna(x[col]) else desconhecido)
            for _, x in no_periodo.iterrows()
        ]
        material.sort(key=lambda par: par[1], reverse=not maximo)
        sobra, no_final = r.estoque_final_kg, 0.0
        for massa, q in material:
            usar = min(massa, sobra)
            no_final += usar * q
            sobra -= usar
            if sobra <= 0:
                break
        total = sum(massa * q for massa, q in material)
        return (total - no_final) / m_queimado

    return Cenarios(recebido, fifo, limite(False), limite(True))


def _mistura(pacote: Pacote, r: ResumoPeriodo) -> None:
    """Qualidade da mistura recebida e do combustível provavelmente queimado (D22, D38)."""
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

    w = _media_ponderada(medidos, "umidade_bu_frac")
    # variação entre lotes: dispersão do PROCESSO (serve para dizer se a umidade recebida
    # mudou além do normal); não é incerteza de medição (ER-1)
    var_lotes = float(medidos["umidade_bu_frac"].std(ddof=1) / sqrt(len(medidos))) / w
    orc_w = Orcamento(
        [Componente("variação entre lotes (dispersão do processo)", var_lotes, "aleatoria")], []
    )
    inst_w = buscar_instrumento(pacote, "umidade")
    chave_w = (
        None
        if inst_w is None or inst_w.relativa
        else chave_instrumento(pacote, inst_w, "umidade", r.inicio, r.fim)
    )
    if chave_w is not None:
        orc_w.componentes.append(
            Componente(f"método de umidade ({inst_w.id})", inst_w.u / w, "instrumental", chave_w)
        )
    else:
        orc_w.nao_incluidos.append("incerteza do método de umidade (estufa) não cadastrada")
    orc_w.nao_incluidos.append("representatividade da amostra de cada lote (E11)")
    nota = f"média dos {len(medidos)} lotes recebidos com umidade medida, ponderada pela massa" + (
        f"; {r.fracao_massa_sem_umidade:.0%} da massa sem umidade medida"
        if r.fracao_massa_sem_umidade
        else ""
    )
    r.umidade_mistura = Grandeza(w, "fração", "estimado", 2 * orc_w.u_rel() * w, nota, orc_w)

    pci = _media_ponderada(det, "pci_umido_mj_kg")
    r.pci_seco_mistura = _media_ponderada(det, "pci_seco_mj_kg")
    orc_pci = Orcamento()
    if chave_w is not None:
        orc_pci.componentes.append(
            Componente(
                f"método de umidade ({inst_w.id})",
                -(r.pci_seco_mistura + 2.442) * inst_w.u / pci,  # ∂PCI_u/∂w (E5)
                "instrumental",
                chave_w,
            )
        )
    else:
        orc_pci.nao_incluidos.append("incerteza do método de umidade (estufa) não cadastrada")
    orc_pci.nao_incluidos += [
        "incerteza da análise de PCI seco",
        "representatividade da amostra de cada lote (E11)",
        "diferença entre o combustível recebido e o queimado (ver cenários do pátio, D38)",
    ]
    r.pci_umido_mistura = Grandeza(
        pci,
        "MJ/kg",
        "estimado",
        None,
        "PCI úmido médio dos lotes recebidos no período (cenário 'o que entra é o que queima')",
        orc_pci,
    )
    todos = _lotes_todos(pacote)
    r.pci_queimado = _cenarios(todos, "pci_umido_mj_kg", r, pci)
    r.umidade_queimada = _cenarios(todos, "umidade_bu_frac", r, w)
    if r.combustivel_kg is not None and r.estoque_inicial_kg is not None:
        r.fracao_estoque = (r.estoque_inicial_kg + r.estoque_final_kg) / r.combustivel_kg.valor
    com_preco = lotes.dropna(subset=["preco_brl"])
    if len(com_preco):
        r.preco_brl_t = float(com_preco["preco_brl"].sum() / (com_preco["massa_kg"].sum() / 1000))
    det_preco = det.dropna(subset=["brl_gj"])
    if len(det_preco):
        r.preco_brl_gj = float(det_preco["preco_brl"].sum() / det_preco["energia_gj"].sum())
    for forn, g in medidos.dropna(subset=["fornecedor_id"]).groupby("fornecedor_id"):
        r.umidade_por_fornecedor[forn] = _media_ponderada(g, "umidade_bu_frac")


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


def grandeza_leitura(
    pacote: Pacote, r: ResumoPeriodo, coluna: str, id_instrumento: str | None = None
) -> Grandeza | None:
    """Média de uma leitura do diário com orçamento: dispersão diária + instrumento."""
    est = r.leituras.get(coluna)
    if est is None or est.media == 0:
        return None
    orc = Orcamento()
    if est.erro_padrao is not None:
        orc.componentes.append(
            Componente("dispersão das médias diárias", est.erro_padrao / est.media, "aleatoria")
        )
    else:
        orc.nao_incluidos.append("dispersão (menos de dois dias com leitura)")
    if coluna in INSTRUMENTOS:
        inst = buscar_instrumento(pacote, coluna, id_instrumento)
        if inst is not None:
            u_abs = inst.u * est.media if inst.relativa else inst.u
            orc.componentes.append(
                Componente(
                    f"instrumento {inst.id}",
                    u_abs / est.media,
                    "instrumental",
                    chave_instrumento(pacote, inst, coluna, r.inicio, r.fim),
                    inst.interpretacao,
                )
            )
        else:
            orc.nao_incluidos.append("incerteza do instrumento (não cadastrado)")
    u = orc.u_rel() * abs(est.media) if est.erro_padrao is not None else None
    return Grandeza(
        est.media, est.unidade, "medido", None if u is None else 2 * u, "média do período", orc
    )


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
        if r.horas > 0 and len(no_periodo):
            r.cobertura_diario = min(1.0, len(no_periodo) * _intervalo_tipico_h(diario) / r.horas)
        for coluna, unidade in LEITURAS_DIARIO.items():
            est = estatistica_diaria(operando[coluna], operando["instante_observado"], unidade)
            if est is not None:
                r.leituras[coluna] = est
        id_o2 = operando["instrumento_o2_id"].dropna()
        for coluna in r.leituras:
            g = grandeza_leitura(
                pacote,
                r,
                coluna,
                id_o2.mode().iloc[0] if coluna == "o2_seco_pct" and len(id_o2) else None,
            )
            if g is not None:
                r.leituras_grandeza[coluna] = g
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
