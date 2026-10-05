"""De onde vem a faixa do desvio e o que a estreitaria (D97).

A faixa principal continua a de erros de instrumento independentes (r = 0); a decomposição
fecha exatamente com ela e os cenários (r = 1; fonte dominante com metade da incerteza) só
estreitam, sempre com a condição escrita.
"""

from pathlib import Path

import pytest

from euler.conta import explicar_conta
from euler.incerteza import (
    Componente,
    Orcamento,
    escalar_fonte,
    fontes_diferenca,
    u_diferenca,
)
from euler.investigacao import investigar
from euler.io import importar_pasta
from euler.periodos import periodos_entre_estoques
from euler.vapor import p_atm_por_altitude_bar

DEMO = Path(__file__).resolve().parents[1] / "demo" / "caso_demo_completo"


def _orcamentos():
    a = Orcamento(
        [
            Componente("vapor", -0.0115, "instrumental", "instrumento:V@origem"),
            Componente("estoque 1", 0.0014, "instrumental", "medicao:estoque@1"),
            Componente("estoque 2", -0.0015, "instrumental", "medicao:estoque@2"),
            Componente("borda", -0.0002, "modelo"),
        ]
    )
    b = Orcamento(
        [
            Componente("vapor", -0.0115, "instrumental", "instrumento:V@origem"),
            Componente("estoque 2", 0.0027, "instrumental", "medicao:estoque@2"),
            Componente("estoque 3", -0.0023, "instrumental", "medicao:estoque@3"),
        ]
    )
    return a, b


@pytest.mark.parametrize("r", [0.0, 0.5, 1.0])
def test_fontes_somam_exatamente_a_incerteza_da_diferenca(r):
    a, b = _orcamentos()
    fontes = fontes_diferenca(0.32, a, 0.353, b, r)
    assert sum(f["variancia"] for f in fontes) == pytest.approx(
        u_diferenca(0.32, a, 0.353, b, r) ** 2, rel=1e-12
    )


def test_escalar_fonte_muda_so_a_fonte_pedida_e_nao_altera_o_original():
    a, _ = _orcamentos()
    metade = escalar_fonte(a, "instrumento:V", 0.5)
    assert metade.componentes[0].u_rel == pytest.approx(-0.00575)
    assert [c.u_rel for c in metade.componentes[1:]] == [c.u_rel for c in a.componentes[1:]]
    assert a.componentes[0].u_rel == -0.0115


def test_conta_sem_analise_continua_como_antes():
    c = explicar_conta(
        combustivel_ref_t=100,
        vapor_ref_t=300,
        combustivel_t=110,
        vapor_t=300,
        preco_ref_brl_t=150,
        preco_brl_t=150,
        incerteza_consumo_t_t=0.01,
    )
    assert c["desvio"]["incerteza"] is None


@pytest.fixture(scope="module")
def conta_demo():
    pacote = importar_pasta(DEMO, p_atm_bar=p_atm_por_altitude_bar(1000.0))
    s = periodos_entre_estoques(pacote)
    j = investigar(pacote, (s[0][0], s[3][1]), (s[4][0], s[5][1]))
    return j["explicacao_conta"]["desvio"]


def test_demo_mostra_de_onde_vem_a_faixa(conta_demo):
    inc = conta_demo["incerteza"]
    parcelas = inc["parcelas"]
    assert sum(x["parcela_pct"] for x in parcelas) == pytest.approx(100)
    assert parcelas[0]["nome"] == "medidor de vapor MED-VAPOR-01"
    assert parcelas[0]["parcela_pct"] > 80
    assert "responde por" in inc["frase_origem"]


def test_cenarios_estreitam_sem_mudar_a_conclusao_principal(conta_demo):
    principal = conta_demo["faixa_t"]
    largura = principal[1] - principal[0]
    inc = conta_demo["incerteza"]
    cond, melhor = inc["condicional"], inc["melhor"]
    for cenario in (cond, melhor):
        f = cenario["faixa_t"]
        assert f[1] - f[0] < largura
        # mesmo centro: só a largura muda
        assert (f[0] + f[1]) / 2 == pytest.approx(conta_demo["combustivel_t"])
    # a conclusão principal continua a cautelosa (erros independentes)
    assert conta_demo["estado"] == "nao_estabelecido"
    assert cond["estado"] == "acima"
    assert "repetir o mesmo erro" in cond["frase"]
    assert "confirme com a manutenção" in cond["frase"]
    assert "de ±2,0% para ±1,0%" in melhor["frase"]
