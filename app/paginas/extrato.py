"""Tela Extrato de energia por fornecedor (E11, T09)."""

import estado
import graficos
import pandas as pd
import streamlit as st
from componentes import md

from euler.combustivel import extrato_por_fornecedor, extrato_semanal, frase_tonelada_vs_energia
from euler.formato import num, pct

st.title("Extrato de energia por fornecedor")
st.markdown("#### O fornecedor mais barato por tonelada nem sempre é o mais barato por energia.")
st.markdown(
    "A caldeira compra **energia**, não toneladas. Quanto mais úmido o cavaco, menos energia "
    "cada tonelada entrega. Aqui cada lote vira energia (GJ) e custo por energia (R$/GJ)."
)


def mostrar(pacote) -> None:
    combustivel, amostras = pacote.dados("combustivel"), pacote.dados("amostras")
    if combustivel is None:
        st.warning("Para o extrato, envie `combustivel.csv` (e `amostras.csv` com a umidade).")
        return
    receb = combustivel[combustivel["tipo"] == "recebimento"]
    if receb.empty:
        st.warning("Não há recebimentos em `combustivel.csv`.")
        return

    datas = receb["data"].dt.tz_localize(None)
    escolha = st.date_input(
        "Período (data de recebimento)",
        value=(datas.min().date(), datas.max().date()),
        min_value=datas.min().date(),
        max_value=datas.max().date(),
        format="DD/MM/YYYY",
    )
    if not isinstance(escolha, tuple) or len(escolha) != 2:
        st.info("Escolha a data de início e a de fim.")
        return
    fuso = receb["data"].dt.tz
    inicio = pd.Timestamp(escolha[0]).tz_localize(fuso)
    fim = (
        pd.Timestamp(escolha[1]).tz_localize(fuso) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    )

    extrato = extrato_por_fornecedor(combustivel, amostras, inicio=inicio, fim=fim)
    lotes, forn = extrato.lotes, extrato.fornecedores
    if forn.empty:
        st.warning("Nenhum recebimento com fornecedor neste período.")
        return

    frase = frase_tonelada_vs_energia(forn)
    if frase:
        st.info(md(frase), icon=":material/lightbulb:")

    determinados = lotes[lotes["situacao"] == "determinada"]
    com_custo = determinados.dropna(subset=["brl_gj"])
    m1, m2, m3 = st.columns(3)
    m1.metric(
        "Energia entregue (lotes determinados)", f"{num(determinados['energia_gj'].sum(), 0)} GJ"
    )
    m2.metric(
        "Custo médio da energia",
        f"R$ {num(com_custo['preco_brl'].sum() / com_custo['energia_gj'].sum())}/GJ"
        if len(com_custo)
        else "—",
    )
    m3.metric("Lotes com energia determinada", f"{len(determinados)} de {len(lotes)}")

    escala = graficos.escala_cores(list(combustivel["fornecedor_id"].dropna().unique()))
    barras = forn.dropna(subset=["brl_t", "brl_gj"]).copy()
    barras["rotulo_t"] = barras["brl_t"].map(lambda v: f"R$ {num(v)}/t")
    barras["rotulo_gj"] = barras["brl_gj"].map(lambda v: f"R$ {num(v)}/GJ")
    c1, c2 = st.columns(2)
    c1.altair_chart(
        graficos.barras_por_fornecedor(barras, "brl_t", "Preço por tonelada", "rotulo_t", escala),
        width="stretch",
    )
    c2.altair_chart(
        graficos.barras_por_fornecedor(barras, "brl_gj", "Custo por energia", "rotulo_gj", escala),
        width="stretch",
    )
    st.caption("Nos dois gráficos, o mais barato fica no topo.")

    tabela = pd.DataFrame(
        {
            "Posição": forn["posicao_energia"].map(lambda v: f"{v}º" if pd.notna(v) else "—"),
            "Fornecedor": forn["fornecedor_id"],
            "Lotes": forn["lotes"],
            "Massa (t)": forn["massa_t"].map(lambda v: num(v, 1)),
            "R$/t": forn["brl_t"].map(num),
            "Umidade média": forn["umidade_media"].map(pct),
            "Umidade: 10 primeiros → 10 últimos lotes": [
                f"{pct(a)} → {pct(b)}"
                for a, b in zip(forn["umidade_referencia"], forn["umidade_recente"], strict=True)
            ],
            "Energia (GJ)": forn["energia_gj"].map(lambda v: num(v, 0)),
            "R$/GJ": forn["brl_gj"].map(num),
            "Alertas": forn["alertas_umidade"],
        }
    )
    st.dataframe(tabela, hide_index=True, width="stretch")

    semanal = extrato_semanal(lotes)
    if semanal["semana"].nunique() >= 2:
        st.markdown("#### Umidade do cavaco por semana")
        st.altair_chart(
            graficos.linhas_semanais(
                semanal, "umidade_media", "Umidade média (base úmida)", "%", escala
            ),
            width="stretch",
        )

    alertas = extrato.alertas_umidade
    st.markdown(f"#### Umidade fora da faixa histórica · {len(alertas)} lote(s)")
    st.caption(
        "Faixa histórica: média ± 3 desvios-padrão dos primeiros 10 lotes medidos de cada "
        "fornecedor (proposta D20). É um sinal para conferir a amostragem e o lote, não uma "
        "conclusão sobre o fornecedor."
    )
    if len(alertas):
        resumo = []
        for f, g in alertas.groupby("fornecedor_id"):
            acima = int((g["alerta_direcao"] == "acima").sum())
            abaixo = len(g) - acima
            partes = [f"{acima} acima" if acima else "", f"{abaixo} abaixo" if abaixo else ""]
            resumo.append(f"- **{f}**: {' e '.join(x for x in partes if x)} da faixa")
        st.markdown("\n".join(resumo))
        with st.expander("Ver os lotes"):
            st.dataframe(
                pd.DataFrame(
                    {
                        "Data": alertas["data"].dt.strftime("%d/%m/%Y %H:%M"),
                        "Fornecedor": alertas["fornecedor_id"],
                        "Lote": alertas["lote_id"],
                        "Umidade": alertas["umidade_bu_frac"].map(pct),
                        "Situação": alertas["alerta_direcao"],
                        "Faixa histórica": alertas["faixa_historica"],
                    }
                ),
                hide_index=True,
                width="stretch",
            )

    nao_det = extrato.lotes_nao_determinados
    st.markdown(f"#### Energia não determinada · {len(nao_det)} lote(s)")
    if len(nao_det):
        st.caption("A EULER não assume umidade: sem medição, a energia do lote fica em aberto.")
        st.dataframe(
            pd.DataFrame(
                {
                    "Data": nao_det["data"].dt.strftime("%d/%m/%Y %H:%M"),
                    "Fornecedor": nao_det["fornecedor_id"],
                    "Lote": nao_det["lote_id"],
                    "Massa (t)": nao_det["massa_kg"].map(
                        lambda v: num(v / 1000 if pd.notna(v) else None, 1)
                    ),
                    "Motivo": nao_det["motivo"],
                }
            ),
            hide_index=True,
            width="stretch",
        )

    with st.expander("Todos os lotes do período"):
        st.dataframe(
            pd.DataFrame(
                {
                    "Data": lotes["data"].dt.strftime("%d/%m/%Y %H:%M"),
                    "Fornecedor": lotes["fornecedor_id"],
                    "Lote": lotes["lote_id"],
                    "Massa (t)": lotes["massa_kg"].map(
                        lambda v: num(v / 1000 if pd.notna(v) else None, 1)
                    ),
                    "Origem da massa": lotes["massa_origem"],
                    "Umidade": lotes["umidade_bu_frac"].map(pct),
                    "Origem da umidade": lotes["umidade_origem"],
                    "PCI seco (MJ/kg)": lotes["pci_seco_mj_kg"].map(num),
                    "Origem do PCI seco": lotes["pci_seco_origem"],
                    "PCI úmido (MJ/kg)": lotes["pci_umido_mj_kg"].map(lambda v: num(v, 3)),
                    "Energia (GJ)": lotes["energia_gj"].map(lambda v: num(v, 1)),
                    "R$/GJ": lotes["brl_gj"].map(num),
                    "Situação": lotes["situacao"],
                }
            ),
            hide_index=True,
            width="stretch",
        )

    st.caption(
        "Cálculo (E11, em revisão científica): energia do lote = massa × PCI úmido; "
        "PCI úmido = (1 − umidade) × PCI seco − 2,442 × umidade; R$/GJ = preço do lote ÷ energia. "
        "Umidade: **medido** por lote. PCI seco: **medido** na amostra do lote ou **assumido** da "
        "amostra mais próxima do mesmo fornecedor."
    )


pacote = estado.exigir_pacote()
if pacote is not None:
    mostrar(pacote)
