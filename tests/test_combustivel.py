import pytest

from euler import combustivel
from euler.tipos import AnaliseBloqueada


def test_pci_umido_referencia():
    # E5: (1 − 0,40)·18,5 − 2,442·0,40
    assert combustivel.pci_umido(18.5, 0.40) == pytest.approx(10.1232)


@pytest.mark.parametrize("w", [-0.1, 1.0, 1.5])
def test_pci_umido_umidade_fora_da_faixa_bloqueia(w):
    with pytest.raises(AnaliseBloqueada):
        combustivel.pci_umido(18.5, w)


def test_pci_umido_com_umidade_em_porcentagem_da_dica():
    with pytest.raises(AnaliseBloqueada, match="fração"):
        combustivel.pci_umido(18.5, 40)


def test_pci_umido_nao_positivo_bloqueia():
    with pytest.raises(AnaliseBloqueada):
        combustivel.pci_umido(18.5, 0.95)


def test_queimado_no_periodo_e9():
    m = combustivel.combustivel_queimado_kg(
        estoque_inicial_kg=50_000, recebimentos_kg=[30_000, 28_000], estoque_final_kg=40_000
    )
    assert m == 68_000


def test_sem_estoque_final_bloqueia_com_motivo():
    with pytest.raises(AnaliseBloqueada) as erro:
        combustivel.combustivel_queimado_kg(50_000, [30_000], None)
    assert "estoque final" in erro.value.motivo
    assert erro.value.falta


def test_sem_estoque_inicial_bloqueia():
    with pytest.raises(AnaliseBloqueada, match="estoque inicial"):
        combustivel.combustivel_queimado_kg(None, [30_000], 10_000)


def test_recebimento_sem_massa_bloqueia():
    with pytest.raises(AnaliseBloqueada, match="recebimento"):
        combustivel.combustivel_queimado_kg(50_000, [30_000, None], 10_000)


def test_balanco_negativo_bloqueia():
    with pytest.raises(AnaliseBloqueada, match="inconsistentes"):
        combustivel.combustivel_queimado_kg(10_000, [5_000], 20_000)


def test_energia_do_combustivel_e10():
    e = combustivel.energia_combustivel_mj([1000, 2000], [10.0, 9.0])
    assert e == pytest.approx(28_000)


def test_energia_sem_pci_bloqueia():
    with pytest.raises(AnaliseBloqueada):
        combustivel.energia_combustivel_mj([1000, 2000], [10.0, None])
