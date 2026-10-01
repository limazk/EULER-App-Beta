"""Balanço direto: energia útil do vapor ÷ energia do combustível (E8, E10, E13, E15; T10).

η_D = Q_s / E_f, no mesmo período e na mesma fronteira, com
Q_s = M_vapor · Δh(p, T_água) (E8) e E_f = M_comb · PCI_u da mistura (E9, E10).

Não circularidade (E13): a eficiência é sempre **resultado**. Nenhuma função deste
módulo (nem de vapor/combustível) recebe eficiência como entrada; um teste garante isso.

Incerteza de primeira ordem (E15), com as incertezas declaradas tratadas como
expandidas (k = 2, D24):
    (u_η/η)² = (u_Mvapor/Mvapor)² + (u_Mcomb/Mcomb)² + (u_PCI/PCI)²
Componentes sem incerteza declarada ficam listados em `sem_incerteza`.
A incerteza de Δh (pressão e temperatura da água) é desprezada (nota em D26).
Purga: fica fora da energia útil (pergunta aberta no E10, D27).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import sqrt

from euler.periodos import ResumoPeriodo
from euler.tipos import AnaliseBloqueada, Grandeza
from euler.vapor import delta_h_mj_kg

MEDICOES_DIRETO = (
    "totalizador de vapor",
    "pressão do vapor",
    "temperatura da água de alimentação",
    "estoques de combustível",
    "pesagem dos recebimentos",
    "umidade das amostras",
    "PCI seco das amostras",
)


@dataclass
class BalancoDireto:
    """Resultado do balanço direto de um período; campos None quando bloqueados."""

    delta_h_mj_kg: Grandeza | None = None
    energia_util_gj: Grandeza | None = None
    energia_combustivel_gj: Grandeza | None = None
    eficiencia: Grandeza | None = None
    consumo_t_por_t: Grandeza | None = None
    intensidade_gj_por_t: Grandeza | None = None
    sem_incerteza: list[str] = field(default_factory=list)
    bloqueios: list[AnaliseBloqueada] = field(default_factory=list)

    @property
    def disponivel(self) -> bool:
        return self.eficiencia is not None


def _rel(g: Grandeza | None) -> float | None:
    if g is None or g.incerteza is None or g.valor == 0:
        return None
    return g.incerteza / abs(g.valor)


def _combinar(*relativas: float | None) -> float | None:
    if any(r is None for r in relativas):
        return None
    return sqrt(sum(r**2 for r in relativas))


def balanco_direto(r: ResumoPeriodo) -> BalancoDireto:
    """Eficiência direta, consumo específico e intensidade energética do período."""
    b = BalancoDireto()
    for chave in ("vapor", "combustivel", "mistura"):
        if chave in r.bloqueios:
            b.bloqueios.append(r.bloqueios[chave])

    p = r.leituras.get("p_vapor_bar_abs")
    t_agua = r.leituras.get("t_agua_alim_c")
    if p is None:
        b.bloqueios.append(
            AnaliseBloqueada(
                "Sem pressão absoluta do vapor: falta a pressão do manômetro ou a altitude do local.",
                ["pressão do vapor e altitude do local"],
            )
        )
    elif t_agua is None:
        b.bloqueios.append(
            AnaliseBloqueada(
                "Sem temperatura da água de alimentação: a energia por tonelada de vapor não é "
                "conhecida.",
                ["temperatura da água de alimentação"],
            )
        )
    else:
        try:
            dh = delta_h_mj_kg(p.media, "saturado_seco", t_agua.media)
            b.delta_h_mj_kg = Grandeza(
                dh,
                "MJ/kg",
                "estimado",
                nota=f"IF97 a {p.media:.2f} bar abs, água a {t_agua.media:.0f} °C; "
                "vapor saturado seco (título x = 1 assumido)",
            )
        except AnaliseBloqueada as bloqueio:
            b.bloqueios.append(bloqueio)

    if r.vapor_t is not None and b.delta_h_mj_kg is not None:
        q = r.vapor_t.valor * b.delta_h_mj_kg.valor  # t × MJ/kg = GJ
        rel = _rel(r.vapor_t)
        b.energia_util_gj = Grandeza(q, "GJ", "estimado", None if rel is None else rel * q)
    if r.combustivel_kg is not None and r.pci_umido_mistura is not None:
        e = r.combustivel_kg.valor * r.pci_umido_mistura.valor / 1000
        rel = _combinar(_rel(r.combustivel_kg), _rel(r.pci_umido_mistura))
        b.energia_combustivel_gj = Grandeza(e, "GJ", "estimado", None if rel is None else rel * e)

    if r.vapor_t is None or r.combustivel_kg is None:
        return b
    for nome, g in (
        ("medidor de vapor", r.vapor_t),
        ("medição de estoque", r.combustivel_kg),
        ("PCI da mistura", r.pci_umido_mistura),
    ):
        if g is not None and g.incerteza is None:
            b.sem_incerteza.append(nome)

    consumo = (r.combustivel_kg.valor / 1000) / r.vapor_t.valor
    rel_c = _combinar(_rel(r.vapor_t), _rel(r.combustivel_kg))
    b.consumo_t_por_t = Grandeza(
        consumo,
        "t de combustível / t de vapor",
        "estimado",
        None if rel_c is None else rel_c * consumo,
        "combustível queimado (E9) ÷ vapor do totalizador",
    )
    if b.energia_combustivel_gj is None:
        return b
    intensidade = b.energia_combustivel_gj.valor / r.vapor_t.valor
    rel_i = _combinar(_rel(r.vapor_t), _rel(b.energia_combustivel_gj))
    b.intensidade_gj_por_t = Grandeza(
        intensidade,
        "GJ de combustível / t de vapor",
        "estimado",
        None if rel_i is None else rel_i * intensidade,
    )
    if b.energia_util_gj is None:
        return b
    eta = b.energia_util_gj.valor / b.energia_combustivel_gj.valor
    rel_eta = _combinar(_rel(r.vapor_t), _rel(r.combustivel_kg), _rel(r.pci_umido_mistura))
    b.eficiencia = Grandeza(
        eta,
        "fração",
        "estimado",
        None if rel_eta is None else rel_eta * eta,
        "energia útil do vapor ÷ energia do combustível (E10), base PCI",
    )
    return b
