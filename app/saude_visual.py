"""Visão executiva do consumo; unidades de tela em kg de combustível/t de vapor."""

import altair as alt
import pandas as pd
import streamlit as st
from graficos import TINTA_SECUNDARIA, _configurar

from euler.formato import num

ROTULOS = {
    "referencia": "Referência",
    "mudou": "Mudança detectada",
    "estavel": "Sem mudança detectável",
    "nao_da_para_dizer": "Sem conclusão",
}


def consumo_kg(p):
    """Somente conversão de apresentação: t/t × 1000 = kg/t."""
    if p.consumo is None:
        return "Não calculado"
    valor = num(p.consumo.valor * 1000, 1)
    return valor + (
        f" ± {num(p.consumo.incerteza * 1000, 1)}"
        if p.consumo.incerteza is not None
        else " · incerteza incompleta"
    )


def dados_grafico(s):
    """Mantém lacunas e intervalo de cada média, sem interpolar períodos ausentes."""
    linhas = []
    for p in s.periodos:
        v = None if p.consumo is None else p.consumo.valor * 1000
        u = None if p.consumo is None or p.consumo.incerteza is None else p.consumo.incerteza * 1000
        linhas.append(
            {
                "inicio": p.inicio.tz_localize(None),
                "fim": p.fim.tz_localize(None),
                "meio": (p.inicio + (p.fim - p.inicio) / 2).tz_localize(None),
                "valor": v,
                "baixo": None if u is None else v - u,
                "alto": None if u is None else v + u,
                "periodo": f"{p.inicio:%d/%m/%Y} a {p.fim:%d/%m/%Y}",
                "consumo": consumo_kg(p),
                "situacao": ROTULOS[p.estado],
                "cor": "#efbd80" if p.estado == "mudou" else "#9cb5ca",
            }
        )
    return pd.DataFrame(linhas).astype({"valor": float, "baixo": float, "alto": float})


def grafico(s):
    df = dados_grafico(s)
    validos = df.dropna(subset=["valor"])
    if validos.empty:
        st.info("Ainda não há consumo calculável. Abra os dados de cada período para ver o motivo.")
        return
    st.markdown("## Consumo ao longo do tempo")
    st.caption("kg de combustível por tonelada de vapor · estimado a partir das medições")
    incerteza = st.toggle("Mostrar incerteza das medições", value=False, key="saude_incerteza")
    x = alt.X(
        "inicio:T",
        title=None,
        scale=alt.Scale(domain=[df.inicio.min(), df.fim.max()]),
        axis=alt.Axis(format="%d/%m", tickCount=6, grid=False, labelOverlap=True),
    )
    y = alt.Y(
        "valor:Q",
        title="kg/t de vapor",
        scale=alt.Scale(zero=True),
        axis=alt.Axis(format=".0f", tickCount=4),
    )
    dicas = [
        alt.Tooltip("periodo:N", title="Período"),
        alt.Tooltip("consumo:N", title="kg/t de vapor (± U)"),
        alt.Tooltip("situacao:N", title="Leitura"),
    ]
    base = alt.Chart(validos)
    camadas = []
    if s.consumo_referencia is not None:
        camadas.append(
            alt.Chart(pd.DataFrame({"valor": [s.consumo_referencia.valor * 1000]}))
            .mark_rule(color=TINTA_SECUNDARIA, strokeDash=[5, 5], strokeWidth=1)
            .encode(y=y, tooltip=[alt.Tooltip("valor:Q", title="Referência (kg/t)", format=".1f")])
        )
    camadas.append(
        base.mark_rule(strokeWidth=3).encode(
            x=x, x2="fim:T", y=y, color=alt.Color("cor:N", scale=None, legend=None), tooltip=dicas
        )
    )
    camadas.append(
        base.mark_point(filled=True, size=55).encode(
            x=alt.X("meio:T", title=None),
            y=y,
            color=alt.Color("cor:N", scale=None, legend=None),
            tooltip=dicas,
        )
    )
    if incerteza:
        camadas.append(
            base.mark_rule(color="#d5dce2", strokeWidth=1.5).encode(
                x="meio:T", y="baixo:Q", y2="alto:Q", tooltip=dicas
            )
        )
    st.altair_chart(_configurar(alt.layer(*camadas).properties(height=240)), width="stretch")
    st.caption(
        "Cada segmento é a média de um período. Âmbar: mudança detectada; "
        "linha pontilhada: referência. Valores e situação estão também na tabela abaixo."
    )
    sem = df[df.valor.isna()]
    if len(sem):
        st.info(
            f"{len(sem)} período(s) sem consumo calculável: "
            + "; ".join(sem.periodo)
            + ". A lacuna não representa consumo zero.",
            icon=":material/info:",
        )


def indicadores(s):
    """Destaque é a primeira sequência de mudança, não a condição atual da caldeira."""
    a, b, c = st.columns(3)
    if s.consumo_referencia is not None:
        i, f = s.referencia
        a.metric(
            "Consumo de referência", f"{num(s.consumo_referencia.valor * 1000, 1)} kg/t de vapor"
        )
        a.caption(f"{s.periodos[i].inicio:%d/%m} a {s.periodos[f].fim:%d/%m} · estimado")
    else:
        a.metric("Consumo de referência", "Não calculado")
    cmp = s.comparacao_mudanca
    if s.mudanca is not None and cmp is not None and cmp.disponivel:
        i, f = s.mudanca
        b.metric(
            "Período em destaque",
            f"{num(cmp.comparacao * 1000, 1)} kg/t de vapor",
            f"{'+' if cmp.delta >= 0 else '−'}{num(abs(100 * cmp.delta / cmp.referencia), 1)}% vs. referência",
            delta_color="inverse",
        )
        b.caption(f"{s.periodos[i].inicio:%d/%m} a {s.periodos[f].fim:%d/%m} · estimado")
    else:
        b.metric("Mudança detectada", "Nenhuma" if s.selo == "estavel" else "Sem conclusão")
    n = sum(p.consumo is not None for p in s.periodos)
    c.metric("Períodos com consumo calculado", f"{n} de {len(s.periodos)}")
    c.caption("Cobertura dos cálculos; não é uma nota de eficiência.")


def explicacao(s):
    """Não transforma incerteza em estabilidade física ou em garantia de eficiência."""
    if s.selo == "mudou":
        return "Mudança detectada", (
            "Há períodos com consumo diferente da referência, além da incerteza declarada. "
            "O destaque mostra a primeira sequência identificada. Investigue a causa antes de agir."
        )
    if s.selo == "estavel":
        return "Sem mudança detectável", (
            "As diferenças ficaram dentro da incerteza das medições. "
            "Isso não prova ausência de perdas nem indica eficiência ideal."
        )
    return "Não dá para dizer ainda", s.frase
