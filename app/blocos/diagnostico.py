"""Vista executiva do contrato central; sem classificar nem recalcular na tela."""

import json

import pandas as pd
import streamlit as st

from euler.evidencias import ROTULOS
from euler.formato import num
from euler.relatorio_evidencias import texto_diagnostico


def renderizar(d: dict, *, completo: bool = True):
    st.info(d["conclusao"])
    cols = st.columns(3)
    for col, k in zip(
        cols, ("robustez_estatistica", "referencia", "evidencia_fisica"), strict=True
    ):
        col.metric(ROTULOS[k], d["dimensoes"][k]["nivel"].capitalize(), border=True)
    st.caption(
        "Causa confirmada: não · Avaliações qualitativas independentes, sem nota global de confiança."
    )
    acoes = d.get("proximas_medicoes", [])
    if acoes:
        with st.container(border=True):
            st.markdown("**Próxima verificação recomendada**")
            st.write(acoes[0]["acao"])
            st.caption(acoes[0]["porque"])
    with st.expander("Por que a EULER recomenda isso?"):
        for k, v in d["dimensoes"].items():
            st.markdown(f"**{ROTULOS[k]} · {v['nivel'].capitalize()}**")
            for motivo in v["motivos"]:
                st.write(motivo)
        st.caption(d["escopo_classificacao"])
    if not completo:
        return
    o = d["observacao"]
    a, b, c = st.columns(3)
    a.metric("Referência calculada", f"{num(o.get('referencia'))} {o['unidade']}", border=True)
    b.metric("Observado", f"{num(o.get('comparacao'))} {o['unidade']}", border=True)
    c.metric("Diferença observada", f"{num(o.get('variacao'))} {o['unidade']}", border=True)
    st.caption(
        "Comparação restrita às condições e horas declaradas; referência não significa operação ideal."
    )
    st.markdown("### Explicações a investigar")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Hipótese": h.get("titulo", h["id"]),
                    "Situação": h.get("estado_interpretacao", h.get("status")),
                }
                for h in d.get("hipoteses", [])
            ]
        ),
        hide_index=True,
        width="stretch",
    )
    with st.expander("Evidências e próximas medições"):
        for h in d.get("hipoteses", []):
            st.markdown(f"**{h.get('titulo', h['id'])}**")
            for e in h.get("evidencias", []):
                st.write(e)
        for v in acoes:
            st.markdown(f"**{v['ordem']}. {v['acao']}**")
            st.write(v["porque"])
        st.caption(
            "Ordem qualitativa por dependências diagnósticas; não é um cálculo do valor da informação."
        )
    e = d["economia"]
    st.markdown("### O que o dinheiro significa")
    st.metric(
        "Valorização do desvio observado",
        f"{e.get('moeda', '')} {num(e.get('desvio_estimado'))}",
        border=True,
    )
    st.caption("Oportunidade recuperável: não apurada · Economia verificada: não apurada")
    for premissa in e.get("premissas", []):
        st.caption(premissa)
    with st.expander("Limitações, referência e rastreabilidade"):
        for lim in d.get("limitacoes", []):
            st.write(lim)
        st.json(
            {
                "referencia": d["dimensoes"]["referencia"],
                "metodos": d.get("metodos"),
                "fontes": d.get("fontes"),
            },
            expanded=False,
        )
        st.code(d["resultado_sha256"], language=None)
        st.caption("Hash do conteúdo; detecta alterações, não certifica medições.")
    st.caption(f"Análise {d['analise_id']} · {d['versao_rubrica']}")
    a, b = st.columns(2)
    a.download_button(
        "Baixar relatório do diagnóstico",
        texto_diagnostico(d),
        f"{d['analise_id']}.md",
        "text/markdown",
    )
    b.download_button(
        "Baixar dados e rastreabilidade",
        json.dumps(d, ensure_ascii=False, indent=2, allow_nan=False),
        f"{d['analise_id']}.json",
        "application/json",
    )
