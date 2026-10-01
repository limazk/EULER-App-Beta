"""Quais análises estão habilitadas ou bloqueadas com os dados enviados, e por quê (T11).

Toda análise tem pré-requisitos (AGENTS.md, regra 4). Se falta dado, a análise
fica **bloqueada** com motivo legível e com o que medir para desbloquear.
`parcial` = roda, mas com limites (ex.: investigação sem balanço direto).

Tabela proposta (D30): a seção 4 da spec v0.3 não estava disponível.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import pandas as pd

from euler.io import Pacote
from euler.periodos import incerteza_relativa_instrumento, medicoes_de_estoque

Situacao = Literal["habilitada", "parcial", "bloqueada"]
ELEMENTOS = ("C", "H", "O", "N", "S")


@dataclass(frozen=True)
class Capacidade:
    id: str
    nome: str
    pergunta: str
    situacao: Situacao
    motivos: tuple[str, ...] = ()
    o_que_fazer: tuple[str, ...] = ()
    requisitos: tuple[str, ...] = field(default_factory=tuple)

    @property
    def habilitada(self) -> bool:
        return self.situacao != "bloqueada"


def _tem(df: pd.DataFrame | None, coluna: str) -> bool:
    return df is not None and coluna in df and bool(df[coluna].notna().any())


class _Verificador:
    """Acumula requisitos que faltam: (motivo legível, o que fazer)."""

    def __init__(self) -> None:
        self.faltas: list[tuple[str, str]] = []

    def exigir(self, ok: bool, motivo: str, o_que_fazer: str) -> bool:
        if not ok:
            self.faltas.append((motivo, o_que_fazer))
        return ok

    def capacidade(
        self, id_: str, nome: str, pergunta: str, requisitos: tuple[str, ...]
    ) -> Capacidade:
        return Capacidade(
            id_,
            nome,
            pergunta,
            "bloqueada" if self.faltas else "habilitada",
            tuple(dict.fromkeys(m for m, _ in self.faltas)),
            tuple(dict.fromkeys(o for _, o in self.faltas)),
            requisitos,
        )


def avaliar(pacote: Pacote) -> list[Capacidade]:
    """Avalia todas as análises para o pacote de dados importado."""
    diario = pacote.dados("diario")
    comb = pacote.dados("combustivel")
    amos = pacote.dados("amostras")
    receb = None if comb is None else comb[comb["tipo"] == "recebimento"]
    n_estoques = len(medicoes_de_estoque(pacote))
    caps: list[Capacidade] = []

    def tem_diario(v: _Verificador) -> bool:
        return v.exigir(diario is not None, "Sem diário do operador.", "Enviar diario.csv.")

    # 1. qualidade dos registros
    v = _Verificador()
    tem_diario(v)
    caps.append(
        v.capacidade(
            "registros",
            "Qualidade dos registros",
            "Os registros têm lacunas, duplicatas ou unidades suspeitas?",
            ("diario.csv",),
        )
    )

    # 2. perda nos gases (indireto)
    v = _Verificador()
    if tem_diario(v):
        v.exigir(
            _tem(diario, "t_gases_c"),
            "Sem temperatura dos gases no diário.",
            "Registrar t_gases_c a cada leitura.",
        )
        v.exigir(
            _tem(diario, "o2_seco_pct"),
            "Sem O₂ nos gases no diário.",
            "Registrar o2_seco_pct (analisador de O₂).",
        )
        v.exigir(_tem(diario, "t_ar_c"), "Sem temperatura do ar de combustão.", "Registrar t_ar_c.")
    v.exigir(
        _tem(amos, "umidade_bu_frac"),
        "Sem umidade medida do combustível.",
        "Medir a umidade dos lotes (estufa).",
    )
    completas = amos is not None and bool(amos.dropna(subset=list(ELEMENTOS)).shape[0])
    v.exigir(
        completas and _tem(amos, "pci_seco_mj_kg"),
        "Sem análise elementar (C, H, O, N, S) e PCI seco do combustível.",
        "Enviar ao menos uma análise elementar com PCI seco por fornecedor.",
    )
    caps.append(
        v.capacidade(
            "perda_gases",
            "Perda nos gases (caminho indireto, E1–E7)",
            "Quanto da energia do combustível sai pela chaminé?",
            ("temperatura dos gases", "O₂", "temperatura do ar", "umidade", "análise elementar"),
        )
    )

    # 3. energia útil do vapor
    v = _Verificador()
    if tem_diario(v):
        v.exigir(
            _tem(diario, "totalizador_vapor_t"),
            "Sem leitura do totalizador de vapor.",
            "Registrar totalizador_vapor_t.",
        )
        v.exigir(
            _tem(diario, "p_vapor_bar_man"), "Sem pressão do vapor.", "Registrar p_vapor_bar_man."
        )
        v.exigir(
            pacote.p_atm_bar is not None,
            "Sem pressão atmosférica do local (altitude ou barômetro).",
            "Informar a altitude do local na tela Importar dados.",
        )
        v.exigir(
            _tem(diario, "t_agua_alim_c"),
            "Sem temperatura da água de alimentação.",
            "Registrar t_agua_alim_c.",
        )
    caps.append(
        v.capacidade(
            "energia_vapor",
            "Energia útil do vapor (E8)",
            "Quanta energia virou vapor?",
            ("totalizador de vapor", "pressão", "altitude", "água de alimentação"),
        )
    )

    # 4. combustível queimado
    v = _Verificador()
    v.exigir(
        receb is not None and len(receb) > 0,
        "Sem recebimentos de combustível.",
        "Enviar combustivel.csv com os recebimentos.",
    )
    v.exigir(
        receb is not None and _tem(receb, "massa_kg_calc"),
        "Recebimentos sem massa conhecida.",
        "Pesar os recebimentos (ou declarar a densidade para volume).",
    )
    v.exigir(
        n_estoques >= 2,
        f"Só {n_estoques} medição(ões) de estoque: é preciso uma no início e outra no fim do período.",
        "Medir o estoque do pátio no início e no fim de cada período (linha tipo = estoque).",
    )
    caps.append(
        v.capacidade(
            "combustivel_queimado",
            "Combustível queimado no período (E9)",
            "Quanto combustível foi queimado?",
            ("recebimentos pesados", "estoque inicial e final"),
        )
    )
    ok_queimado = caps[-1].habilitada

    # 5. energia do combustível
    v = _Verificador()
    v.exigir(
        ok_queimado,
        "Combustível queimado não é conhecido (ver acima).",
        "Resolver o item combustível queimado.",
    )
    v.exigir(
        _tem(amos, "umidade_bu_frac"),
        "Sem umidade medida dos lotes.",
        "Medir a umidade de cada lote recebido.",
    )
    v.exigir(
        _tem(amos, "pci_seco_mj_kg"),
        "Sem PCI seco do combustível.",
        "Enviar análise de PCI seco por fornecedor.",
    )
    caps.append(
        v.capacidade(
            "energia_combustivel",
            "Energia do combustível (E10)",
            "Quanta energia a fábrica comprou e queimou?",
            ("combustível queimado", "umidade por lote", "PCI seco"),
        )
    )

    # 6. eficiência direta
    v = _Verificador()
    v.exigir(
        caps[2].habilitada,
        "Energia útil do vapor não é conhecida.",
        "Resolver o item energia útil do vapor.",
    )
    v.exigir(
        caps[4].habilitada,
        "Energia do combustível não é conhecida.",
        "Resolver o item energia do combustível.",
    )
    caps.append(
        v.capacidade(
            "eficiencia_direta",
            "Eficiência direta (E10, E13)",
            "Quanto da energia comprada virou vapor?",
            ("energia útil do vapor", "energia do combustível"),
        )
    )

    # 7. faixa de incerteza (E15)
    v = _Verificador()
    v.exigir(
        caps[5].habilitada, "Eficiência direta bloqueada.", "Resolver o item eficiência direta."
    )
    v.exigir(
        incerteza_relativa_instrumento(pacote, "vapor") is not None,
        "Sem incerteza declarada do medidor de vapor.",
        "Cadastrar o medidor de vapor em instrumentos.csv (unidade pct_da_leitura).",
    )
    v.exigir(
        incerteza_relativa_instrumento(pacote, "estoque") is not None,
        "Sem incerteza declarada da medição de estoque.",
        "Cadastrar o levantamento de estoque em instrumentos.csv (unidade pct_da_leitura).",
    )
    caps.append(
        v.capacidade(
            "incerteza",
            "Faixa de incerteza da eficiência (E15)",
            "Quanto o resultado pode estar errado?",
            ("eficiência direta", "incerteza do medidor de vapor", "incerteza do estoque"),
        )
    )

    # 8. extrato por fornecedor
    v = _Verificador()
    v.exigir(
        receb is not None and _tem(receb, "fornecedor_id"),
        "Sem recebimentos com fornecedor.",
        "Informar fornecedor_id em cada recebimento.",
    )
    v.exigir(
        _tem(amos, "umidade_bu_frac"),
        "Sem umidade por lote.",
        "Medir a umidade de cada lote recebido.",
    )
    v.exigir(
        receb is not None and _tem(receb, "preco_brl"),
        "Sem preço dos lotes.",
        "Informar preco_brl de cada recebimento.",
    )
    caps.append(
        v.capacidade(
            "extrato",
            "Extrato de energia por fornecedor (M1, E11)",
            "Quem entrega a energia mais barata?",
            ("recebimentos com fornecedor", "umidade por lote", "preço"),
        )
    )

    # 9. comparação entre períodos
    v = _Verificador()
    tem_diario(v)
    v.exigir(
        n_estoques >= 3,
        f"Com {n_estoques} medição(ões) de estoque há menos de dois períodos para comparar.",
        "Medir o estoque em datas fixas (ex.: toda segunda-feira).",
    )
    caps.append(
        v.capacidade(
            "comparacao",
            "Comparação entre períodos",
            "O que mudou de um período para outro?",
            ("diário", "três ou mais medições de estoque"),
        )
    )

    # 10. investigação (parcial quando falta um dos caminhos)
    if not caps[8].habilitada:
        inv = Capacidade(
            "investigacao",
            "Investigação de mudança de consumo",
            "O consumo mudou? O que explica? O que verificar?",
            "bloqueada",
            caps[8].motivos,
            caps[8].o_que_fazer,
        )
    else:
        limites, fazer = [], []
        if not caps[5].habilitada:
            limites.append("Sem balanço direto: não dá para medir o consumo por tonelada de vapor.")
            fazer += caps[5].o_que_fazer
        if not caps[1].habilitada:
            limites.append("Sem perda nos gases: não dá para testar as causas na chaminé.")
            fazer += caps[1].o_que_fazer
        inv = Capacidade(
            "investigacao",
            "Investigação de mudança de consumo",
            "O consumo mudou? O que explica? O que verificar?",
            "parcial" if limites else "habilitada",
            tuple(limites),
            tuple(dict.fromkeys(fazer)),
        )
    caps.append(inv)

    # 11. custo do vapor (E14)
    v = _Verificador()
    v.exigir(
        caps[5].habilitada, "Eficiência direta bloqueada.", "Resolver o item eficiência direta."
    )
    v.exigir(
        receb is not None and _tem(receb, "preco_brl"),
        "Sem preço dos lotes.",
        "Informar preco_brl de cada recebimento.",
    )
    caps.append(
        v.capacidade(
            "custo_vapor",
            "Custo do vapor e efeito do preço (E14)",
            "O custo do vapor mudou por preço ou por consumo?",
            ("eficiência direta", "preço"),
        )
    )
    return caps
