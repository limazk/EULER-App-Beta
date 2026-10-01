"""Verificação independente: combustão e perda nos gases (Fase R, matriz V-B*).

Cada teste usa um método diferente do usado no motor: balanço de massa por elemento,
solução numérica de λ, outra formulação (IAPWS-95) para o orvalho, outra fonte de dados
(equações de estado de referência do CoolProp) para a entalpia dos gases.
"""

import random

import pytest

from euler import indireto
from euler.indireto import COMPOSICAO_REFERENCIA as REF


def _massas(comp, o2, w):
    a = indireto.oxigenio_estequiometrico(comp)
    lam = indireto.razao_ar(o2, comp)
    r = indireto.perda_gases(180, o2, w, 25, comp, 18.5)
    return a, lam, r


@pytest.mark.parametrize("semente", range(5))
def test_conservacao_de_massa_por_elemento(semente):
    """Entra (combustível seco + ar + água) = sai (gases secos + água), em kg/kg seco.

    Ar e produtos com as mesmas massas molares inteiras de E3/E4 (32, 28, 44, 64, 18)."""
    rng = random.Random(semente)
    comp = {"C": rng.uniform(0.45, 0.52), "H": rng.uniform(0.05, 0.065), "N": 0.003, "S": 0.0005}
    comp["O"] = 0.985 - sum(comp.values())  # 1,5% de cinzas
    w = rng.uniform(0.2, 0.55)
    a, lam, r = _massas(comp, rng.uniform(4, 12), w)
    entra = sum(comp.values()) + 32 * lam * a + 28 * 79 / 21 * lam * a + w / (1 - w)
    sai = r.m_gases_secos_kg_kg + r.m_h2o_kg_kg
    assert sai == pytest.approx(entra, rel=1e-12)


@pytest.mark.parametrize("o2", [2, 4, 8, 12, 16])
def test_lambda_por_solucao_numerica_independente(o2):
    """Resolve y_O₂(λ) = O₂ medido por bissecção (sem usar a forma fechada do motor)."""
    c, h, o, n, s = (REF[k] for k in "CHONS")
    a = c / 12 + h / 4 + s / 32 - o / 32

    def y(lam):
        n_o2 = (lam - 1) * a
        return n_o2 / (c / 12 + s / 32 + n_o2 + 79 / 21 * lam * a + n / 28)

    lo, hi = 1.0, 20.0
    for _ in range(200):
        meio = (lo + hi) / 2
        lo, hi = (meio, hi) if y(meio) < o2 / 100 else (lo, meio)
    assert indireto.razao_ar(o2, REF) == pytest.approx(lo, rel=1e-9)


def test_g01_recalculado_a_mao():
    """G01 passo a passo, com as equações do documento (E1–E6), sem chamar o motor."""
    c, h, o, n, s, w = 0.50, 0.06, 0.43, 0.003, 0.0005, 0.40
    a = c / 12 + h / 4 + s / 32 - o / 32  # 0,0416667 + 0,015 + 0,0000156 − 0,0134375
    y = 0.08
    lam = (a + y * (c / 12 + s / 32 + n / 28) - y * a) / (1 - y - y * 79 / 21) / a
    m_gs = 44 * c / 12 + 64 * s / 32 + 32 * (lam - 1) * a + 28 * (79 / 21 * lam * a + n / 28)
    m_h2o = 9 * h + w / (1 - w)
    perda = 100 * (m_gs * 1.05e-3 + m_h2o * 1.90e-3) * (180 - 25) / (18.5 - 2.442 * w / (1 - w))
    assert a == pytest.approx(0.0432448, abs=1e-7)
    assert lam == pytest.approx(1.611, abs=1e-3)
    assert perda == pytest.approx(11.773, abs=0.001)
    assert indireto.perda_gases(180, 8, w, 25, REF, 18.5).perda_pct == pytest.approx(
        perda, abs=1e-9
    )


def test_orvalho_contra_iapws95():
    """T_orvalho = T_sat na pressão parcial do vapor; conferido com IAPWS-95 (CoolProp)."""
    coolprop = pytest.importorskip("CoolProp.CoolProp")
    _, _, r = _massas(REF, 8, 0.40)
    n_h2o = r.m_h2o_kg_kg / 18.015
    n_secos = r.n_gases_secos_kmol_kg
    p_h2o = n_h2o / (n_h2o + n_secos) * 101325
    t_95 = coolprop.PropsSI("T", "P", p_h2o, "Q", 0, "HEOS::Water") - 273.15
    assert r.t_orvalho_c == pytest.approx(t_95, abs=0.05)


@pytest.mark.parametrize(
    ("especie", "fluido"),
    [("N2", "Nitrogen"), ("O2", "Oxygen"), ("CO2", "CarbonDioxide"), ("H2O", "Water")],
)
@pytest.mark.parametrize(("t1", "t2"), [(25, 180), (25, 300), (1, 450)])  # 0 °C é o ponto triplo
def test_entalpia_nasa_contra_equacoes_de_referencia(especie, fluido, t1, t2):
    """ΔH (NASA TM-4513) contra as equações de estado de referência (CoolProp) a 100 Pa,
    onde o gás é praticamente ideal. Tolerância 0,3%: os dois ajustes vêm de dados e
    métodos diferentes; diferenças típicas ficam abaixo de 0,1%."""
    coolprop = pytest.importorskip("CoolProp.CoolProp")
    from euler.propriedades_gases import entalpia_sensivel_kj_kmol

    p = 100.0  # Pa: abaixo da pressão de saturação da água a 1 °C (611 Pa) → gás
    m = coolprop.PropsSI("M", fluido) * 1000  # kg/kmol
    ref = (
        (
            coolprop.PropsSI("H", "T", t2 + 273.15, "P", p, fluido)
            - coolprop.PropsSI("H", "T", t1 + 273.15, "P", p, fluido)
        )
        / 1000
        * m
    )  # kJ/kmol
    assert entalpia_sensivel_kj_kmol(especie, t1, t2) == pytest.approx(ref, rel=3e-3)


def test_coeficientes_nasa_iguais_ao_arquivo_de_origem():
    """Rastreabilidade: os coeficientes copiados são os do nasa_gas.yaml (NASA TM-4513)."""
    ct = pytest.importorskip("cantera")
    from euler.propriedades_gases import NASA7

    especies = {s.name: s for s in ct.Species.list_from_file("nasa_gas.yaml")}
    for nome, (faixas, baixo, alto) in NASA7.items():
        coef = especies[nome].thermo.input_data["data"]
        assert tuple(especies[nome].thermo.input_data["temperature-ranges"]) == faixas
        assert tuple(coef[0]) == pytest.approx(baixo, rel=1e-12)
        assert tuple(coef[1]) == pytest.approx(alto, rel=1e-12)


def test_entalpia_de_combustao_do_co_contra_valores_de_formacao():
    """ΔH_c(CO) = ΔfH(CO₂) − ΔfH(CO) = −393,51 − (−110,53) = −282,98 kJ/mol (valores de
    formação do NIST-JANAF a 298,15 K, citados de memória técnica: conferir)."""
    from euler.propriedades_gases import entalpia_combustao_co_kj_kmol

    assert entalpia_combustao_co_kj_kmol() / 1000 == pytest.approx(393.51 - 110.53, abs=0.05)


def test_umidade_absoluta_do_ar_a_mao():
    """25 °C, UR 60%: p_sat = 3,1699 kPa (IF97) → W = 0,622·0,6·3,1699/(101,325 − 0,6·3,1699)."""
    w = 0.622 * 0.6 * 3.1699 / (101.325 - 0.6 * 3.1699)
    assert indireto.umidade_absoluta_ar(25, 0.6) == pytest.approx(w, rel=1e-3)


def test_o2_umido_e_seco_ida_e_volta():
    """Converte seco → úmido pelas próprias quantidades de gás e volta com a função do motor."""
    a, lam, r = _massas(REF, 8, 0.40)
    n_o2 = (lam - 1) * a
    n_h2o = r.m_h2o_kg_kg / 18.015
    o2_umido = 100 * n_o2 / (r.n_gases_secos_kmol_kg + n_h2o)
    assert indireto.o2_seco_equivalente(o2_umido, REF, 0.40) == pytest.approx(8.0, abs=1e-6)


def test_perda_por_co_a_mao():
    """200 ppm de CO: 2e-4 × n_gases_secos × 282,98 MJ/kmol ÷ PCI por kg seco."""
    _, _, r = _massas(REF, 8, 0.40)
    esperado = 100 * 200e-6 * r.n_gases_secos_kmol_kg * 282.978 / (18.5 - 2.442 * 0.4 / 0.6)
    assert indireto.perda_co_pct(200, r, 18.5, 0.40) == pytest.approx(esperado, rel=1e-4)


def test_motor_nao_importa_as_ferramentas_de_verificacao():
    """A verificação só é independente se o motor não usar CoolProp nem Cantera."""
    from pathlib import Path

    raiz = Path(__file__).resolve().parents[1] / "euler"
    for arquivo in raiz.rglob("*.py"):
        codigo = arquivo.read_text(encoding="utf-8").lower()
        assert "import coolprop" not in codigo and "from coolprop" not in codigo, arquivo
        assert "import cantera" not in codigo and "from cantera" not in codigo, arquivo
