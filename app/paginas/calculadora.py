"""Calculadora de referência: perda nos gases, λ e PCI úmido (E1–E7)."""

import streamlit as st
from componentes import cabecalho, cartao

from euler.combustivel import pci_umido
from euler.formato import num
from euler.indireto import COMPOSICAO_REFERENCIA, perda_gases
from euler.tipos import AnaliseBloqueada

cabecalho(
    "Calculadora de referência",
    "Escolha a temperatura dos gases, o oxigênio e a umidade do combustível. "
    "A EULER calcula quanto da energia do combustível sai pela chaminé como calor.",
    "Referência",
)
st.warning(
    "**Simulação.** Valores de referência em revisão científica. Não use para decisões.",
    icon=":material/science:",
)

with cartao("entradas"):
    c1, c2, c3 = st.columns(3, gap="large")
    t_gases = c1.slider("Temperatura dos gases na chaminé (°C)", 60, 400, 180, step=1)
    o2 = c2.slider("O₂ nos gases secos (%)", 0.0, 20.0, 8.0, step=0.1)
    umidade_pct = c3.slider("Umidade do combustível (% base úmida)", 0, 70, 40, step=1)

with st.expander("Combustível e ar (valores de referência, podem ser alterados)"):
    st.caption("Cavaco de referência do documento de revisão. Origem: **assumido**.")
    e1, e2 = st.columns(2)
    t_ar = e1.number_input("Temperatura do ar de combustão (°C)", -10.0, 60.0, 25.0, step=1.0)
    pci_seco = e2.number_input("PCI seco (MJ/kg)", 5.0, 40.0, 18.5, step=0.1)
    colunas = st.columns(5)
    composicao = {
        el: col.number_input(
            f"{el} (fração seca)", 0.0, 1.0, COMPOSICAO_REFERENCIA[el], step=0.001, format="%.4f"
        )
        for el, col in zip(COMPOSICAO_REFERENCIA, colunas, strict=True)
    }

w = umidade_pct / 100


def _calcular(**mudancas):
    entrada = {
        "t_gases_c": t_gases,
        "o2_seco_pct": o2,
        "umidade_bu_frac": w,
        "t_ar_c": t_ar,
        "composicao_seca": composicao,
        "pci_seco_mj_kg": pci_seco,
    }
    return perda_gases(**{**entrada, **mudancas})


try:
    r = _calcular()
    pci_u = pci_umido(pci_seco, w)
except AnaliseBloqueada as bloqueio:
    st.error(f"**Cálculo bloqueado.** {bloqueio.motivo}", icon=":material/block:")
else:
    m1, m2, m3 = st.columns(3)
    m1.metric("Perda nos gases", f"{num(r.perda_pct, 2)} % do PCI", border=True)
    m2.metric("Razão de ar λ", num(r.lambda_ar, 3), border=True)
    m3.metric("PCI úmido", f"{num(pci_u, 2)} MJ/kg", border=True)
    for aviso in r.avisos:
        st.warning(aviso)

    st.markdown("#### Quanto cada variável pesa (a partir deste ponto)")
    variacoes = []
    for rotulo, mudanca in [
        ("+10 °C nos gases", {"t_gases_c": t_gases + 10}),
        ("+1 ponto de O₂", {"o2_seco_pct": o2 + 1}),
        ("+1 ponto de umidade", {"umidade_bu_frac": w + 0.01}),
    ]:
        try:
            delta = _calcular(**mudanca).perda_pct - r.perda_pct
            variacoes.append(
                f"- {rotulo}: perda **{'+' if delta >= 0 else ''}{num(delta, 2)}** p.p."
            )
        except AnaliseBloqueada:
            variacoes.append(f"- {rotulo}: fora da faixa de cálculo")
    st.markdown("\n".join(variacoes))

    with st.expander("Detalhes técnicos do cálculo"):
        st.markdown(
            "Equações: itens E1 a E7 de `docs/fisica_para_revisao.md` (em revisão científica).\n\n"
            f"- O₂ estequiométrico (E1): {num(r.o2_esteq_kmol_kg, 5)} kmol/kg seco\n"
            f"- Gases secos (E3): {num(r.m_gases_secos_kg_kg, 3)} kg/kg seco\n"
            f"- Água nos gases (E4): {num(r.m_h2o_kg_kg, 3)} kg/kg seco\n"
            f"- Orvalho da água nos gases (E7): {num(r.t_orvalho_c, 1)} °C\n"
            f"- Modelo de cp: {r.modelo_cp} (1,05 kJ/kg·K gases secos; 1,90 kJ/kg·K vapor)"
        )
    st.caption(
        "Origem: **calculado** a partir dos valores escolhidos (simulação). Composição, "
        "PCI seco e temperatura do ar: **assumidos** (referência). Hipóteses: combustão "
        "completa, ar seco 21/79, sem umidade do ar."
    )
