"""Extrato de energia por fornecedor (E11, T09)."""

import pandas as pd
import pytest

from euler.combustivel import extrato_por_fornecedor, frase_tonelada_vs_energia
from euler.io import importar_pacote

CAB_COMB = "data,tipo,fornecedor_id,lote_id,massa_kg,volume_m3,densidade_kg_m3,origem_densidade,preco_brl,origem_dado\n"
CAB_AMOS = "amostra_id,lote_id,data,umidade_bu_frac,pci_seco_mj_kg,origem_dado\n"


def extrato(recebimentos: list[str], amostras: list[str], **periodo):
    p = importar_pacote(
        {
            "combustivel": (CAB_COMB + "\n".join(recebimentos) + "\n").encode(),
            "amostras": (CAB_AMOS + "\n".join(amostras) + "\n").encode(),
        }
    )
    return extrato_por_fornecedor(p.dados("combustivel"), p.dados("amostras"), **periodo)


@pytest.fixture(scope="module")
def tabela_f1_f3():
    # docs/fisica/fisica_para_revisao.md, E11: PCI seco 18,5; 30 t por lote
    return extrato(
        [
            "2026-10-05T10:00-03:00,recebimento,F1,L1,30000,,,,5400,sintetico",
            "2026-10-05T11:00-03:00,recebimento,F2,L2,30000,,,,5100,sintetico",
            "2026-10-05T12:00-03:00,recebimento,F3,L3,30000,,,,4800,sintetico",
        ],
        [
            "A1,L1,2026-10-05T13:00-03:00,0.38,18.5,sintetico",
            "A2,L2,2026-10-05T13:00-03:00,0.45,18.5,sintetico",
            "A3,L3,2026-10-05T13:00-03:00,0.52,18.5,sintetico",
        ],
    )


@pytest.mark.parametrize(
    ("forn", "pci_u", "energia_gj", "brl_gj", "brl_t"),
    [
        ("F1", 10.542, 316.3, 17.07, 180),
        ("F2", 9.076, 272.3, 18.73, 170),
        ("F3", 7.610, 228.3, 21.02, 160),
    ],
)
def test_reproduz_tabela_f1_f3_do_documento(tabela_f1_f3, forn, pci_u, energia_gj, brl_gj, brl_t):
    lote = tabela_f1_f3.lotes.set_index("fornecedor_id").loc[forn]
    assert lote["pci_umido_mj_kg"] == pytest.approx(pci_u, abs=0.001)
    assert lote["energia_gj"] == pytest.approx(energia_gj, abs=0.05)
    assert lote["brl_gj"] == pytest.approx(brl_gj, abs=0.005)
    assert lote["preco_brl_t"] == pytest.approx(brl_t)
    assert lote["umidade_origem"] == "medido (1 amostra)"
    assert lote["pci_seco_origem"] == "medido"


def test_ranking_por_energia_inverte_o_ranking_por_tonelada(tabela_f1_f3):
    f = tabela_f1_f3.fornecedores.set_index("fornecedor_id")
    assert list(f["posicao_energia"]) == [1, 2, 3]
    assert f.loc["F1", "posicao_energia"] == 1 and f.loc["F1", "posicao_tonelada"] == 3
    frase = frase_tonelada_vs_energia(tabela_f1_f3.fornecedores)
    assert frase.startswith("F3 tem o menor preço por tonelada (R$ 160,00/t)")
    assert "F1: R$ 17,07/GJ" in frase


def test_lote_sem_umidade_medida_fica_com_energia_nao_determinada():
    e = extrato(
        [
            "2026-10-05T10:00-03:00,recebimento,F1,L1,30000,,,,5400,sintetico",
            "2026-10-06T10:00-03:00,recebimento,F1,L2,30000,,,,5400,sintetico",
        ],
        ["A1,L1,2026-10-05T13:00-03:00,0.38,18.5,sintetico"],
    )
    l2 = e.lotes.set_index("lote_id").loc["L2"]
    assert l2["situacao"] == "não determinada"
    assert pd.isna(l2["energia_gj"]) and pd.isna(l2["umidade_bu_frac"])
    assert "umidade do lote não medida" in l2["motivo"]
    f1 = e.fornecedores.set_index("fornecedor_id").loc["F1"]
    assert f1["lotes"] == 2 and f1["lotes_determinados"] == 1
    assert f1["energia_gj"] == pytest.approx(316.26, abs=0.01)  # só o lote determinado


def test_umidade_em_porcentagem_nao_e_usada():
    e = extrato(
        ["2026-10-05T10:00-03:00,recebimento,F1,L1,30000,,,,5400,sintetico"],
        ["A1,L1,2026-10-05T13:00-03:00,38,18.5,sintetico"],
    )
    assert e.lotes["situacao"].iloc[0] == "não determinada"
    assert "unidade" in e.lotes["motivo"].iloc[0]


def test_pci_seco_de_outro_lote_do_fornecedor_e_marcado_como_assumido():
    e = extrato(
        [
            "2026-10-05T10:00-03:00,recebimento,F1,L1,30000,,,,5400,sintetico",
            "2026-10-08T10:00-03:00,recebimento,F1,L2,30000,,,,5400,sintetico",
        ],
        [
            "A1,L1,2026-10-05T13:00-03:00,0.38,18.5,sintetico",
            "A2,L2,2026-10-08T13:00-03:00,0.40,,sintetico",
        ],
    )
    l2 = e.lotes.set_index("lote_id").loc["L2"]
    assert l2["situacao"] == "determinada"
    assert l2["pci_seco_mj_kg"] == 18.5
    assert l2["pci_seco_origem"].startswith("assumido")


def test_sem_pci_seco_do_fornecedor_energia_nao_determinada():
    e = extrato(
        ["2026-10-05T10:00-03:00,recebimento,F1,L1,30000,,,,5400,sintetico"],
        ["A1,L1,2026-10-05T13:00-03:00,0.38,,sintetico"],
    )
    assert e.lotes["situacao"].iloc[0] == "não determinada"
    assert "PCI seco" in e.lotes["motivo"].iloc[0]


def test_sem_preco_tem_energia_mas_nao_custo():
    e = extrato(
        ["2026-10-05T10:00-03:00,recebimento,F1,L1,30000,,,,,sintetico"],
        ["A1,L1,2026-10-05T13:00-03:00,0.38,18.5,sintetico"],
    )
    lote = e.lotes.iloc[0]
    assert lote["situacao"] == "determinada" and pd.isna(lote["brl_gj"])
    assert "sem preço" in lote["motivo"]


def _historico(umidades):
    receb = [
        f"2026-10-{d:02d}T10:00-03:00,recebimento,F1,L{d},30000,,,,5400,sintetico"
        for d in range(1, len(umidades) + 1)
    ]
    amos = [
        f"A{d},L{d},2026-10-{d:02d}T13:00-03:00,{w},18.5,sintetico"
        for d, w in enumerate(umidades, start=1)
    ]
    return extrato(receb, amos)


def test_alerta_quando_umidade_foge_da_faixa_historica():
    e = _historico([0.40, 0.41, 0.39, 0.40, 0.41, 0.39, 0.52])
    alertas = e.alertas_umidade
    assert list(alertas["lote_id"]) == ["L7"]
    texto = alertas["alerta_umidade"].iloc[0]
    assert texto.startswith("Umidade de 52,0% acima da faixa histórica do fornecedor")


def test_faixa_vem_dos_primeiros_lotes_e_pega_subida_gradual():
    # subida lenta: a faixa não "acompanha" a subida, porque vem dos primeiros lotes
    umidades = [0.40, 0.41, 0.39, 0.40, 0.41, 0.39, 0.40, 0.41, 0.39, 0.40]
    umidades += [0.42, 0.44, 0.46, 0.48]
    e = _historico(umidades)
    # referência: média 40%, desvio 0,8 p.p. → faixa até 42,4%
    assert list(e.alertas_umidade["lote_id"]) == ["L12", "L13", "L14"]
    f1 = e.fornecedores.iloc[0]
    assert f1["umidade_referencia"] == pytest.approx(0.40)
    assert f1["umidade_recente"] > f1["umidade_referencia"]


def test_sem_historico_suficiente_nao_alerta():
    e = _historico([0.40, 0.41, 0.39, 0.60])
    assert e.alertas_umidade.empty
    assert e.lotes["faixa_historica"].iloc[-1].startswith("referência insuficiente")


def test_texto_dos_alertas_e_neutro():
    e = _historico([0.40, 0.41, 0.39, 0.40, 0.41, 0.39, 0.52, 0.20])
    proibidas = ("fraude", "culpa", "irregular", "engan", "má-fé", "ruim", "suspeit")
    for texto in e.alertas_umidade["alerta_umidade"]:
        assert not any(p in texto.lower() for p in proibidas), texto


def test_filtro_de_periodo():
    p = importar_pacote(
        {
            "combustivel": (
                CAB_COMB
                + "2026-10-01T10:00-03:00,recebimento,F1,L1,30000,,,,5400,sintetico\n"
                + "2026-10-09T10:00-03:00,recebimento,F1,L2,30000,,,,5400,sintetico\n"
            ).encode()
        }
    )
    e = extrato_por_fornecedor(
        p.dados("combustivel"), None, inicio=pd.Timestamp("2026-10-05T00:00-03:00")
    )
    assert list(e.lotes["lote_id"]) == ["L2"]


def test_extrato_semanal_mostra_a_subida_de_umidade():
    from euler.combustivel import extrato_semanal

    umidades = [0.40] * 7 + [0.50] * 7  # 14 dias: 2 semanas
    e = _historico(umidades)
    semanal = extrato_semanal(e.lotes)
    assert list(semanal["semana"].dt.weekday.unique()) == [0]
    assert semanal["umidade_media"].is_monotonic_increasing
