"""Combustível: PCI úmido, combustível queimado no período e energia (E5, E9, E10).

Convenções (docs/fisica_para_revisao.md): umidade `w` em base úmida (kg de água
por kg de combustível úmido, fração de 0 a 1); PCI em MJ/kg; massas em kg.
"""

from collections.abc import Sequence

from euler.tipos import AnaliseBloqueada

H_VAP_25C_MJ_KG = 2.442
"""Calor de vaporização da água a 25 °C usado no PCI (E5, pendente de revisão)."""


def _checar_umidade(umidade_bu_frac: float) -> None:
    if 1 < umidade_bu_frac <= 100:
        raise AnaliseBloqueada(
            f"Umidade {umidade_bu_frac:g} parece estar em %; o contrato pede fração "
            f"(ex.: 0,40 para 40%)."
        )
    if not 0 <= umidade_bu_frac < 1:
        raise AnaliseBloqueada(f"Umidade {umidade_bu_frac:g} fora da faixa (0 a 1, base úmida).")


def pci_umido(pci_seco_mj_kg: float, umidade_bu_frac: float) -> float:
    """PCI do combustível como recebido (MJ/kg úmido), E5.

    PCI_u = (1 − w)·PCI_seco − 2,442·w

    Entradas: PCI em base seca (MJ/kg seco) e umidade em base úmida (fração).
    Hipótese (pergunta aberta no E5): PCI_seco já desconta a água formada pelo H.
    """
    _checar_umidade(umidade_bu_frac)
    if pci_seco_mj_kg <= 0:
        raise AnaliseBloqueada(f"PCI seco de {pci_seco_mj_kg:g} MJ/kg não é positivo.")
    pci = (1 - umidade_bu_frac) * pci_seco_mj_kg - H_VAP_25C_MJ_KG * umidade_bu_frac
    if pci <= 0:
        raise AnaliseBloqueada(
            f"Com umidade {umidade_bu_frac:.0%} o PCI úmido fica sem energia líquida "
            f"({pci:.2f} MJ/kg). Confira a umidade."
        )
    return pci


def combustivel_queimado_kg(
    estoque_inicial_kg: float | None,
    recebimentos_kg: Sequence[float | None],
    estoque_final_kg: float | None,
) -> float:
    """Combustível queimado no período (kg), E9.

    M_f = estoque_inicial + Σ recebimentos − estoque_final

    Todas as massas na mesma base de umidade (como recebido). Sem estoque medido
    no início ou no fim, a análise é bloqueada: nunca se assume estoque.
    """
    if estoque_inicial_kg is None:
        raise AnaliseBloqueada(
            "Sem estoque inicial medido, não dá para saber quanto combustível foi queimado.",
            falta=["medição de estoque no início do período"],
        )
    if estoque_final_kg is None:
        raise AnaliseBloqueada(
            "Sem estoque final medido, não dá para saber quanto combustível foi queimado.",
            falta=["medição de estoque no fim do período"],
        )
    if any(m is None for m in recebimentos_kg):
        raise AnaliseBloqueada(
            "Há recebimento sem massa conhecida no período; o total recebido não é conhecido.",
            falta=["massa de todos os recebimentos (ou volume com densidade declarada)"],
        )
    queimado = estoque_inicial_kg + sum(recebimentos_kg) - estoque_final_kg
    if queimado < 0:
        raise AnaliseBloqueada(
            "Estoque final maior que estoque inicial mais recebimentos: os registros estão "
            "inconsistentes (recebimento faltando ou medição de estoque errada)."
        )
    return queimado


def energia_combustivel_mj(
    massas_kg: Sequence[float | None], pcis_umidos_mj_kg: Sequence[float | None]
) -> float:
    """Energia do combustível queimado: E_f = Σ M_f,i · PCI_u,i (MJ), parte de E10.

    Cada parcela i é uma porção de combustível com PCI úmido próprio (ex.: lote).
    Bloqueia se alguma parcela não tiver massa ou PCI conhecidos.
    """
    if len(massas_kg) != len(pcis_umidos_mj_kg):
        raise ValueError("massas e PCIs precisam ter o mesmo tamanho")
    if any(m is None for m in massas_kg) or any(p is None for p in pcis_umidos_mj_kg):
        raise AnaliseBloqueada(
            "Há combustível sem massa ou sem PCI conhecido; a energia total não é conhecida.",
            falta=["umidade medida de cada lote queimado"],
        )
    return sum(m * p for m, p in zip(massas_kg, pcis_umidos_mj_kg, strict=True))
