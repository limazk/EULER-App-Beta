"""Vista executiva do contrato central; sem classificar nem recalcular na tela."""

import json

import pandas as pd
import streamlit as st

from euler.evidencias import ROTULOS
from euler.formato import num
from euler.relatorio_evidencias import casas, texto_diagnostico, texto_valor


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
    for col, rotulo, chave in (
        (a, "Referência calculada", "referencia"),
        (b, "Observado", "comparacao"),
        (c, "Diferença observada", "variacao"),
    ):
        v = o.get(chave)
        col.metric(rotulo, f"{num(v, casas(v))} {o['unidade']}", border=True)
    st.caption(
        "Comparação restrita às condições e horas declaradas; referência não significa operação ideal."
    )
    _serie_referencia(d["dimensoes"]["referencia"])
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
    valor = e.get("desvio_estimado")
    st.metric(
        "Valorização do desvio observado",
        f"{e.get('moeda', '')} {num(valor)}" if valor is not None else "não estimado",
        border=True,
    )
    if valor is None and e.get("motivo_sem_valor"):
        st.caption(texto_valor(e).removeprefix("não estimado. "))
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


def _serie_referencia(ref: dict) -> None:
    """Série usada para avaliar a referência na rota operacional (D88), quando existe.

    Só mostra o que o diagnóstico já calculou: período a período, observado, previsto pelo
    consumo específico da referência e resíduo. Período sem dado aparece como "—"."""
    serie = ref.get("serie")
    if not serie:
        return
    modelo = ref.get("modelo") or {}
    with st.expander(f"Como a referência foi avaliada · {len(serie)} períodos"):
        st.markdown(f"**{ref['nivel'].capitalize()}** · {ref.get('resumo', '')}")
        for motivo in ref.get("motivos", []):
            st.write(f"- {motivo}")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Período": x["periodo"],
                        "Combustível (t)": num(x["combustivel_t"], 1),
                        "Vapor (t)": num(x["vapor_t"], 1),
                        "Consumo (t/t)": num(x["consumo_t_t"], 3),
                        "Previsto (t)": num(x["previsto_t"], 1),
                        "Diferença (t)": num(x["residuo_t"], 1),
                        "Regime": {"estavel": "estável", "transitorio": "transitório"}.get(
                            x["regime"], "não informado"
                        ),
                    }
                    for x in serie
                ]
            ),
            hide_index=True,
            width="stretch",
        )
        k = modelo.get("consumo_especifico_t_t")
        st.caption(
            "Previsto = consumo da referência "
            + (f"({num(k, 3)} t/t) " if k is not None else "")
            + "× vapor de cada período, o mesmo modelo da comparação. Um ponto por período entre "
            "medições de estoque; nada foi preenchido nem removido."
        )
        for v in ref.get("metricas", {}).get("validacao_temporal") or []:
            st.caption(
                f"Validação: {v['periodo']} previsto pelos períodos anteriores, diferença de "
                f"{num(v['vies_pct'], 1)}%."
            )
