"""Percurso da planta em cinco passos (D102): em que pé está cada um e qual é o próximo.

Só apresenta `euler.percurso`; não decide nada pela equipe.
"""

import streamlit as st
from componentes import md

from euler.percurso import PASSOS, percurso, proximo_passo

PAGINA = {
    "dados": "paginas/acompanhamento.py",
    "fechamentos": "paginas/fechamentos.py",
    "acoes": "paginas/acoes.py",
}
ESTADO = {
    "feito": ("Feito", "green"),
    "andamento": ("Em andamento", "blue"),
    "pendente": ("Pendente", "orange"),
    "bloqueado": ("Aguarda o passo anterior", "gray"),
}


def renderizar(a, equip_id: str) -> None:
    """Os cinco passos lado a lado (empilham no celular) e o atalho para o próximo."""
    itens = percurso(a, equip_id)
    prox = proximo_passo(itens)
    with st.container(border=True, key="percurso-planta"):
        st.markdown("**Percurso da planta**")
        st.caption(
            "Enviar registros → conferir a conta → investigar → registrar ação → verificar "
            "resultado. Tudo aqui usa os dados salvos desta planta."
        )
        for i, (coluna, x) in enumerate(zip(st.columns(len(itens)), itens), 1):
            with coluna:
                rotulo, cor = ESTADO[x["estado"]]
                st.badge(rotulo, color=cor)
                st.markdown(f"**{i}. {x['titulo']}**")
                st.caption(md(x["frase"]))
        if prox:
            st.page_link(
                PAGINA[prox["destino"]],
                label=f"Próximo passo: {prox['titulo'].lower()}",
                icon=":material/arrow_forward:",
            )
        else:
            st.caption("Nada pendente no percurso agora.")


def marcador(*passos: str) -> None:
    """Uma linha que mostra em qual passo do percurso a tela atual está."""
    st.caption(
        "Percurso: "
        + " › ".join(
            f"**{i}. {t}**" if k in passos else f"{i}. {t}" for i, (k, t, _) in enumerate(PASSOS, 1)
        )
    )
