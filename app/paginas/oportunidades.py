"""Oportunidades: onde vale colocar tempo e dinheiro primeiro (D90).

Só apresenta o que o motor calculou (`euler.oportunidades`). Não há nota nem pesos; a
prioridade é de investigação, não de intervenção.
"""

import estado
import pandas as pd
import streamlit as st
from componentes import cabecalho, md

from euler.formato import num
from euler.oportunidades import projetar_ano

NIVEL = {
    "INSUFICIENTE": "Insuficiente",
    "FRACA": "Fraca",
    "MODERADA": "Moderada",
    "FORTE": "Forte",
}
COMPLEXIDADE = {"baixa": "Baixa", "media": "Média", "alta": "Alta", None: "Não classificada"}
COR = {"alta": "blue", "media": "gray"}


def brl(v):
    return "—" if v is None else ("−" if v < 0 else "") + f"R$ {num(abs(v), 0)}"


def faixa(par):
    return None if not par else f"{brl(par[0])} a {brl(par[1])}"


def cartao(o: dict, dias: float | None, dias_ano: float | None) -> None:
    i, v = o["impacto"], o["verificacao"]
    with st.container(border=True):
        st.markdown(f"**{o['ordem']}. {o['titulo']}**")
        st.badge(o["prioridade_rotulo"], color=COR.get(o["prioridade"], "gray"))
        a, b, c = st.columns(3)
        a.metric("Impacto potencial associado", brl(i["custo_brl"]))
        legenda = []
        if i["combustivel_t"] is not None:
            legenda.append(f"{num(i['combustivel_t'], 1)} t de combustível no período")
        if faixa(i["faixa_brl"]):
            legenda.append(f"faixa {faixa(i['faixa_brl'])}")
        if dias_ano and i["custo_brl"] is not None:
            ano = projetar_ano(i["custo_brl"], dias, dias_ano)
            par = [projetar_ano(x, dias, dias_ano) for x in i["faixa_brl"] or []]
            legenda.append(
                f"{brl(ano)}/ano" + (f" ({faixa(par)})" if par else "") + " na projeção informada"
            )
        if i["custo_brl"] is None and i.get("motivo"):
            legenda.append(i["motivo"])
        a.caption(md(" · ".join(legenda)))
        b.metric("Evidência", NIVEL[o["evidencia"]["nivel"]])
        b.caption(o["evidencia"]["motivo"])
        c.metric("Complexidade da verificação", COMPLEXIDADE[v["complexidade"]])
        c.caption(
            ("Sem parada. " if v["exige_parada"] is False else "")
            + (f"{v['recurso'][:1].upper()}{v['recurso'][1:]}." if v["recurso"] else "")
            + f" Fonte: {v['origem_complexidade']}."
        )
        st.markdown(md(f"**Próxima verificação:** {v['acao']}"))
        detalhes = []
        if v["distingue"]:
            detalhes.append(f"Distingue: {v['distingue']}.")
        if v["etapa_seguinte"]:
            detalhes.append(v["etapa_seguinte"])
        detalhes.append(f"{o['natureza_rotulo']}. Intervenção: {o['intervencao']['motivo']}")
        for d in detalhes:
            st.caption(md(d))


def mostrar(pacote) -> None:
    j = estado.investigacao_ou_padrao(pacote)
    if j is None:
        st.info(
            "As oportunidades aparecem quando dá para comparar dois períodos (combustível, vapor "
            "e medições de estoque). Veja o que falta em Dados e limites."
        )
        return
    o = j.get("oportunidades")
    if o is None:
        st.info("Refaça a investigação para ver as oportunidades desta versão.")
        return
    p = j["periodos"]
    datas = {k: (pd.Timestamp(v["inicio"]), pd.Timestamp(v["fim"])) for k, v in p.items()}
    st.caption(
        f"Período analisado: {datas['comparacao'][0]:%d/%m/%Y} a "
        f"{datas['comparacao'][1]:%d/%m/%Y} · Referência: {datas['referencia'][0]:%d/%m/%Y} a "
        f"{datas['referencia'][1]:%d/%m/%Y}"
    )
    st.page_link(
        "paginas/investigacao.py",
        label="Escolher períodos e ver investigação",
        icon=":material/tune:",
    )
    r = o["resumo"]
    st.markdown(f"### {r['frase']}")
    assoc = r["associado"]
    dias = assoc["dias"]
    a, b = st.columns(2)
    with a:
        st.metric(
            f"Associado ao desvio no período ({num(dias, 0)} dias)" if dias else "No período",
            brl(assoc["custo_brl"]),
            border=True,
        )
        st.caption(
            md(
                (
                    f"Incerteza ±{brl(assoc['incerteza_brl'])} (k = 2). "
                    if assoc["incerteza_brl"] is not None
                    else ""
                )
                + assoc["base"]
            )
        )
    with b:
        dias_ano = st.number_input(
            "Dias de operação por ano (informado pela fábrica, opcional)",
            min_value=1,
            max_value=366,
            value=None,
            step=1,
            key=f"oport_dias_ano_{estado.assinatura()}",
            help="Só para projetar o valor do período para um ano, supondo o mesmo regime, "
            "carga e preço. Sem esse dado, a EULER não projeta.",
        )
        if dias_ano and assoc["custo_brl"] is not None:
            st.caption(
                md(
                    f"Projeção linear: {brl(projetar_ano(assoc['custo_brl'], dias, dias_ano))}"
                    "/ano, dadas as premissas informadas. Não é economia recuperável confirmada."
                )
            )
    if r["primeira"]:
        with st.container(border=True):
            st.markdown(f"**Verificar primeiro: {r['primeira']['titulo']}**")
            st.write(r["primeira"]["acao"])
    for aviso in o["sobreposicao"]:
        st.warning(md(aviso), icon=":material/stacks:")

    ativos = [x for x in o["oportunidades"] if x["prioridade"] in ("alta", "media")]
    outros = [x for x in o["oportunidades"] if x not in ativos]
    if ativos:
        st.markdown("### Em investigação")
        for x in ativos:
            cartao(x, dias, dias_ano)
    if outros:
        with st.expander(f"Não priorizadas agora ({len(outros)})"):
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "Hipótese": x["titulo"],
                            "Situação": x["prioridade_rotulo"],
                            "Por quê": " ".join(x["porque"]),
                        }
                        for x in outros
                    ]
                ),
                hide_index=True,
                width="stretch",
            )

    st.markdown("### Intervenção")
    st.info(o["intervencao"]["motivo"])
    st.caption(" → ".join(("✓ " if c["disponivel"] else "○ ") + c["etapa"] for c in o["cadeia"]))
    with st.expander("Como a priorização funciona"):
        st.markdown("**Critérios objetivos (calculados pelo motor)**")
        for x in o["regras"]["objetivos"]:
            st.write(f"- {x}")
        st.markdown("**Regras de triagem propostas (pendentes de revisão, D90)**")
        for x in o["regras"]["propostos"]:
            st.write(f"- {x}")
        st.markdown("**Termos que não são sinônimos**")
        st.write(
            "- Desvio monetizado: diferença de consumo em reais (Financeiro).\n"
            "- Impacto potencial associado: o efeito de uma hipótese em reais, se ela se "
            "confirmar.\n"
            "- Parcela evitável: o que uma ação concreta evitaria; ainda não apurada.\n"
            "- Economia estimada: depende de intervenção definida; ainda não disponível.\n"
            "- Economia verificada: medida depois da intervenção; ainda não disponível."
        )


cabecalho(
    "Oportunidades",
    "Onde vale colocar tempo e dinheiro primeiro — sem passar do que os dados sustentam.",
    "Prioridade de investigação",
)
pacote = estado.exigir_pacote()
if pacote is not None:
    mostrar(pacote)
