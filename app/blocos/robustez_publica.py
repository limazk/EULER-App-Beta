"""Leitura executiva e detalhes da auditoria, sem selo de validação causal."""

import json

import pandas as pd
import streamlit as st
from robustez_ensaio import carregar_auditoria

from euler.formato import num


def renderizar(unidade: str, diagnosticos: list[dict]):
    r = carregar_auditoria()
    st.markdown("**O resultado resiste a outras formas de comparar?**")
    if r is None:
        st.info(
            "Auditoria de robustez ainda não disponível para estes dados e esta versão do cálculo."
        )
        return
    u = r["unidades"][unidade]
    for col, m, d in zip(st.columns(2), u["meses"], diagnosticos, strict=True):
        evid = d["dimensoes"]["robustez_estatistica"]
        titulo = evid["conclusao"]
        with col.container(border=True):
            st.markdown(f"**{'Fevereiro' if m['mes'].endswith('02') else 'Março'} · {titulo}**")
            st.write(" ".join(evid["motivos"]))
    st.caption(
        "2.000 repetições por tamanho de bloco: 1, 3 e 7 dias. Faixas de sensibilidade, "
        "não probabilidade de causa nem incerteza dos instrumentos. Estudo retrospectivo."
    )
    with st.expander("Auditoria · métodos, referência e limites"):
        linhas = []
        for m in u["meses"]:
            for v in m["modelos"]["metodos"]:
                linhas.append(
                    {
                        "Mês": m["mes"],
                        "Método": v["metodo"],
                        "Diferença (%)": num(v["delta_pct"])
                        if v["delta_pct"] is not None
                        else "Indisponível",
                        "Mesmas horas": v["horas"],
                    }
                )
        st.dataframe(pd.DataFrame(linhas), hide_index=True, width="stretch")
        st.caption(
            "As quatro formas de cálculo usam exatamente as mesmas horas em cada mês. "
            "Esse subconjunto é menor que o da conta original; seus valores não substituem o total."
        )
        st.markdown("**A própria referência também varia**")
        for v in u["diagnostico"]["validacao_temporal"]:
            if v["vies_pct"] is None:
                st.write(f"Teste a partir de {v['teste_inicio']}: dados insuficientes.")
            else:
                st.write(
                    f"Treino até {v['treino_fim']}, teste de {v['teste_inicio']} a {v['teste_fim']}: "
                    f"diferença de {num(v['vies_pct'])}% em {v['horas_comparaveis']} horas."
                )
        st.caption(
            "Janeiro não foi certificado como operação ideal. Esses testes revelam variação "
            "que pode ser do processo ou do modelo. Mais repetições não resolvem variáveis ausentes."
        )
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Mês": m["mes"],
                        "Bloco (dias)": b["bloco_dias"],
                        "Limite inferior (%)": num(b["quantil_025_pct"])
                        if b["quantil_025_pct"] is not None
                        else "Indisponível",
                        "Limite superior (%)": num(b["quantil_975_pct"])
                        if b["quantil_975_pct"] is not None
                        else "Indisponível",
                        "Repetições válidas": b["validas"],
                    }
                    for m in u["meses"]
                    for b in m["reamostragem"]
                ]
            ),
            hide_index=True,
            width="stretch",
        )
        st.write(
            "**O que conferir primeiro:** calibração das medições, condições da água e do vapor "
            "e combustível efetivamente usado. Uma mudança nessas condições pode explicar parte "
            "ou todo o desvio, mesmo quando o sinal persiste estatisticamente."
        )
        for m in u["meses"]:
            st.caption(
                f"{m['mes']}: mantendo a referência, uma redução de "
                f"{num(m['reducao_energia_reportada_para_zerar_pct'])}% da energia reportada "
                "zeraria o desvio; valor negativo indica aumento necessário. "
                "É uma sensibilidade calculada, não erro de medição identificado."
            )
        st.download_button(
            "Baixar auditoria das quatro caldeiras",
            json.dumps(r, ensure_ascii=False, indent=2, allow_nan=False),
            "EULER_auditoria_robustez.json",
            "application/json",
        )
