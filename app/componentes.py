"""Peças de tela reaproveitadas por todas as páginas do app."""

import streamlit as st

from euler.textos import RODAPE_SEGURANCA


def rodape() -> None:
    """Mostra o rodapé de segurança (obrigatório em todas as telas)."""
    st.divider()
    st.caption(RODAPE_SEGURANCA)
