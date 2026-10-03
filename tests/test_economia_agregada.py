"""Caso público de aumento: gabarito independente com Decimal, sem criar medições."""

from decimal import Decimal

import pytest

from euler.economia import comparar_consumos, valorizar_diferenca
from euler.tipos import Grandeza


def test_formulario_executa_o_motor_e_identifica_cenario():
    from test_app import abrir_com_demo

    at = abrir_com_demo("dados_publicos.py")
    assert not at.exception
    assert any(m.value == "US$ 1.591,80/dia" for m in at.metric)
    entrada = next(n for n in at.number_input if n.label.startswith("Consumo na chuva"))
    entrada.set_value(0.40)
    next(b for b in at.button if b.label == "Executar comparação na EULER").click().run(timeout=60)
    assert not at.exception
    assert any(m.value == "US$ 3.183,60/dia" for m in at.metric)
    assert any("Cenário editado por você" in w.value for w in at.warning)


def test_investigacao_completa_chama_a_mesma_rotina(monkeypatch):
    """Regressão: o caminho confirmado da investigação usa a rotina ensaiada."""
    from test_investigacao import G11, G12, Periodo, rodar

    from euler import investigacao

    chamadas = []

    def observar(*args):
        chamadas.append(args)
        return valorizar_diferenca(*args)

    monkeypatch.setattr(investigacao, "valorizar_diferenca", observar)
    j = rodar(
        Periodo(G11, t_gases_c=180, umidade=0.3104), Periodo(G12, t_gases_c=292.2, umidade=0.3104)
    )
    assert len(chamadas) == 1
    delta, vapor, preco = chamadas[0]
    esperado = Decimal(str(delta)) * Decimal(str(vapor)) * Decimal(str(preco))
    assert j["valor_em_jogo"]["valor_brl"] == pytest.approx(float(esperado))


def test_diniz_reproduz_aumento_com_gabarito_decimal():
    r = comparar_consumos(
        Grandeza(0.30, "t/t", "estimado"), Grandeza(0.35, "t/t", "estimado"), 1200, 26.53, "USD"
    )
    esperado = (Decimal("0.35") - Decimal("0.30")) * Decimal(1200) * Decimal("26.53")
    assert r["diferenca_valorizada"] == pytest.approx(float(esperado))
    assert r["combustivel_adicional_t"] == pytest.approx(60)
    assert r["aumento_pct"] == pytest.approx(100 / 6)
    assert r["custo_referencia"] == pytest.approx(9550.8)
    assert r["custo_comparacao"] == pytest.approx(11142.6)
    assert r["moeda"] == "USD"
    assert r["comparacao"]["detectavel"] is None
    assert r["valor_em_jogo_confirmado"] is None
    assert r["economia_comprovada"] is None


def test_diferenca_descritiva_nao_relaxa_confirmacao_e_nao_inventa_preco():
    a, b = Grandeza(0.3, "t/t", "medido", 0.001), Grandeza(0.35, "t/t", "medido", 0.001)
    r = comparar_consumos(a, b, 1200, 26.53, "USD")
    assert r["valor_em_jogo_confirmado"] == pytest.approx(1591.8)
    assert r["economia_comprovada"] is None
    assert comparar_consumos(a, b, 1200, None, "USD")["diferenca_valorizada"] is None
    reverso = comparar_consumos(b, a, 1200, 26.53, "USD")
    assert reverso["diferenca_valorizada"] == pytest.approx(-1591.8)
    assert reverso["valor_em_jogo_confirmado"] is None


def test_unidades_e_numeros_invalidos_sao_recusados():
    with pytest.raises(ValueError):
        comparar_consumos(
            Grandeza(300, "kg/t", "medido"), Grandeza(350, "kg/t", "medido"), 1200, 26.53, "USD"
        )
    for valor in [-1, float("nan"), float("inf")]:
        with pytest.raises(ValueError):
            valorizar_diferenca(0.05, 1200, valor)
    assert valorizar_diferenca(0.05, 1200, 0) == 0
