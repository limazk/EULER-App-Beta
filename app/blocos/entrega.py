"""Entrega de cada fechamento (D104): o resumo recorrente para a gestão da planta.

Só apresenta `euler.entrega`; o mesmo texto vai para a tela e para o arquivo baixado.
"""

import streamlit as st
from componentes import md

from euler.entrega import entrega_do_fechamento, texto_entrega


def renderizar(a, eq: dict, fechamento_id: int) -> None:
    """Resumo da entrega com contagens, botão para baixar e o texto completo recolhido."""
    e = entrega_do_fechamento(a, eq["id"], fechamento_id)
    if e is None:
        return
    texto = texto_entrega(e, eq.get("nome"))
    res = e["resultados"]
    with st.container(border=True, key=f"entrega-{fechamento_id}"):
        st.markdown(f"**Entrega do fechamento #{fechamento_id}**")
        st.caption(
            "O resumo de cada fechamento para a gestão: a conta e o que mudou, as pendências, "
            "as verificações e ações em andamento e os resultados já demonstrados. A conta vem "
            "preservada do fechamento; o restante é o registrado até hoje."
        )
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Pendências", len(e["pendencias"]))
        c2.metric("Verificações abertas", len(e["verificacoes"]))
        c3.metric("Ações sem avaliação", len(e["acoes_em_andamento"]))
        c4.metric("Ações avaliadas", len(res["avaliadas"]))
        st.download_button(
            "Baixar a entrega do fechamento",
            texto,
            f"entrega-fechamento-{fechamento_id}.md",
            "text/markdown",
            icon=":material/download:",
            key=f"baixar-entrega-{fechamento_id}",
        )
        with st.expander("Ver a entrega completa"):
            st.markdown(md(texto.split("\n", 1)[1]))
