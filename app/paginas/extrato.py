"""Tela Extrato de energia por fornecedor (E11, T09)."""

import estado
import graficos
import pandas as pd
import streamlit as st
from componentes import cabecalho, cartao, md, proximo_passo

from euler.combustivel import extrato_por_fornecedor, extrato_semanal, frase_tonelada_vs_energia
from euler.formato import num, pct, plural

cabecalho(
    "Extrato por fornecedor",
    "**O fornecedor mais barato por tonelada nem sempre é o mais barato por energia.** "
    "Compare o custo do combustível considerando a energia que ele contém.",
    "Analisar um período",
)


def mostrar(pacote) -> None:
    combustivel, amostras = pacote.dados("combustivel"), pacote.dados("amostras")
    if combustivel is None:
        st.warning(
            "Para o extrato, envie os recebimentos de combustível (e as amostras com a umidade)."
        )
        return
    receb = combustivel[combustivel["tipo"] == "recebimento"]
    if receb.empty:
        st.warning("Não há recebimentos nos registros de combustível.")
        return

    datas = receb["data"].dt.tz_localize(None)
    escolha = st.columns([1, 2])[0].date_input(
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

    determinados = lotes[lotes["situacao"] == "determinada"]
    com_custo = determinados.dropna(subset=["brl_gj"])
    precos = lotes["preco_brl"].dropna()
    m1, m2, m3 = st.columns(3)
    m1.metric(
        "Compras registradas",
        f"R$ {num(precos.sum())}" if len(precos) else "—",
        border=True,
        help=f"Soma dos preços informados em {len(precos)} de {len(lotes)} lotes. "
        "Refere-se aos recebimentos selecionados, não ao combustível consumido.",
    )
    m2.metric(
        "Custo médio da energia",
        f"R$ {num(com_custo['preco_brl'].sum() / com_custo['energia_gj'].sum())}/GJ"
        if len(com_custo)
        else "—",
        border=True,
        help="Soma dos preços dividida pela energia dos mesmos lotes. "
        "Inclui somente lotes com preço e energia calculáveis.",
    )
    m3.metric("Lotes com custo por energia", f"{len(com_custo)} de {len(lotes)}", border=True)
    st.caption(
        "R$/GJ = reais por gigajoule de energia no combustível. Quanto menor, menor o custo "
        "por energia. Não é o custo do vapor produzido."
    )
    if len(precos) < len(lotes) or len(com_custo) < len(lotes):
        st.caption(
            f"Cobertura parcial: preço informado em {len(precos)} de {len(lotes)} lotes; "
            f"preço e energia disponíveis em {len(com_custo)} de {len(lotes)}. "
            "Os valores ausentes não entram nas médias."
        )

    st.markdown("### Comparar fornecedores")
    frase = frase_tonelada_vs_energia(forn)
    if frase:
        st.info(md(frase), icon=":material/lightbulb:")

    escala = graficos.escala_cores(list(combustivel["fornecedor_id"].dropna().unique()))
    modo = st.radio(
        "Comparação",
        ["Por energia · R$/GJ", "Por tonelada · R$/t"],
        horizontal=True,
        label_visibility="collapsed",
    )
    campo, unidade = ("brl_gj", "GJ") if modo.startswith("Por energia") else ("brl_t", "t")
    barras = forn.dropna(subset=[campo]).copy()
    barras["rotulo"] = barras[campo].map(lambda v: f"R$ {num(v)}/{unidade}")
    if barras.empty:
        st.info(
            "Ainda não é possível comparar por este critério. "
            "Veja os dados pendentes nos detalhes abaixo."
        )
    else:
        with cartao("comparacao-fornecedores"):
            st.altair_chart(
                graficos.barras_por_fornecedor(
                    barras,
                    campo,
                    "Custo por energia" if unidade == "GJ" else "Preço por tonelada",
                    "rotulo",
                    escala,
                ),
                width="stretch",
            )
    st.caption(
        "Menor valor no topo, entre os lotes calculáveis. As médias por tonelada e por "
        "energia podem usar conjuntos diferentes de lotes. Não é uma recomendação de compra."
    )

    cobertura = com_custo.groupby("fornecedor_id").size()
    st.dataframe(
        pd.DataFrame(
            {
                "Fornecedor": forn["fornecedor_id"],
                "Custo por energia (R$/GJ)": forn["brl_gj"].map(num),
                "Preço por tonelada (R$/t)": forn["brl_t"].map(num),
                "Lotes com custo por energia": [
                    f"{cobertura.get(f, 0)} de {n}"
                    for f, n in zip(forn["fornecedor_id"], forn["lotes"], strict=True)
                ],
            }
        ),
        hide_index=True,
        width="stretch",
    )

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
            "Lotes fora da faixa de umidade": forn["alertas_umidade"],
        }
    )
    with st.expander("Detalhes por fornecedor"):
        st.caption(
            "Energia calculada nos lotes disponíveis; umidade média ponderada pela massa "
            "desses lotes. Consulte a origem das medições na lista de recebimentos."
        )
        st.dataframe(tabela, hide_index=True, width="stretch")

    alertas = extrato.alertas_umidade
    with st.expander(f"Umidade e alertas · {len(alertas)} lotes sinalizados"):
        semanal = extrato_semanal(lotes)
        if semanal["semana"].nunique() >= 2:
            st.markdown("#### Umidade do cavaco por semana")
            with cartao("umidade-semanal"):
                st.altair_chart(
                    graficos.linhas_semanais(
                        semanal, "umidade_media", "Umidade média (base úmida)", "%", escala
                    ),
                    width="stretch",
                )

        st.caption(
            "Faixa histórica: média ± 3 desvios-padrão dos primeiros 10 lotes medidos de cada "
            "fornecedor (proposta em revisão). É um sinal para conferir a amostragem e o lote, não "
            "uma conclusão sobre o fornecedor."
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

        if not len(alertas):
            st.caption(
                "Nenhum alerta de umidade nos registros analisados. Isso não certifica a qualidade dos lotes."
            )

    nao_det = extrato.lotes_nao_determinados
    with st.expander(f"Energia não calculável · {plural(len(nao_det), 'lote', 'lotes')}"):
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

        else:
            st.caption(
                "Todos os lotes têm energia calculável. Preços ausentes ainda podem impedir a comparação de custos."
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

    with st.expander("Como ler estes valores"):
        st.markdown(
            "- **Compras registradas:** soma dos preços dos recebimentos no período. "
            "Pode ser parcial se houver preços ausentes.\n"
            "- **Energia do combustível:** calculada pela massa e pelo poder calorífico "
            "inferior (PCI), considerando a umidade. Não é a energia efetivamente "
            "transferida ao vapor.\n"
            "- **Custo médio por energia:** valor dos lotes dividido pela energia desses "
            "mesmos lotes; não é uma média simples dos preços unitários.\n"
            "- **Origem dos valores:** massa medida ou estimada; umidade medida por lote; "
            "PCI seco medido no lote ou assumido da amostra mais próxima do mesmo fornecedor. "
            "Sem base suficiente, o valor fica em aberto.\n"
            "- **Decisão de compra:** considere também a cobertura dos dados, a origem do PCI, "
            "o frete incluído ou não no preço, o contrato e a compatibilidade do combustível. "
            "Uma diferença de R$/GJ não comprova economia recuperável."
        )
        st.caption(
            "Cálculo em revisão científica: energia (GJ) = massa (kg) × PCI úmido (MJ/kg) ÷ 1.000. "
            "PCI úmido = (1 − umidade) × PCI seco − 2,442 × umidade, com umidade em fração "
            "da massa úmida."
        )
        with st.expander("Detalhes técnicos · referências do cálculo"):
            st.caption("Referências internas: E11 e E5 (física); D19 e D20 (decisões).")


pacote = estado.exigir_pacote()
if pacote is not None:
    mostrar(pacote)
    proximo_passo("paginas/relatorio.py", "Relatório")
