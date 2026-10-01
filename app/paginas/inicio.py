"""Tela inicial da EULER."""

import streamlit as st

from euler.textos import AVISO_PROTOTIPO, FRASE_PRODUTO, PERGUNTA_CENTRAL

st.title("EULER")
st.subheader(FRASE_PRODUTO)
st.info(AVISO_PROTOTIPO, icon=":material/science:")

st.markdown("### A pergunta que a EULER responde")
st.markdown(f"> {PERGUNTA_CENTRAL}")
st.markdown(
    "Às vezes a resposta certa é **“não dá para concluir”**, junto com a próxima medição "
    "que resolveria a dúvida. Isso é uma funcionalidade, não uma falha."
)

st.markdown("### Como funciona")
st.markdown(
    "A EULER **soma** aos registros que a fábrica já tem: diário do operador, "
    "recebimentos de combustível, amostras e eventos. Ela não muda nada na caldeira; "
    "ela investiga e indica **verificações**."
)
