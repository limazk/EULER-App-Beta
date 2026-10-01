"""Tela inicial da EULER."""

import estado
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

with st.container(border=True):
    st.markdown("### Experimente em 5 minutos")
    st.markdown(
        "Uma caldeira **sintética** de 20 t/h a cavaco, 8 semanas de registros, 3 fornecedores. "
        "Algo mudou no meio do caminho: descubra o quê."
    )
    if st.button(
        "Começar com o caso de demonstração", type="primary", icon=":material/play_circle:"
    ):
        estado.usar_caso_demo()
        st.switch_page("paginas/limites.py")

st.markdown("### Como usar")
passos = [
    ("paginas/importar.py", "1. Importar dados", "Envie os registros que a fábrica já tem (CSV ou planilha). A EULER lista os problemas, sem corrigir nada em silêncio."),
    ("paginas/limites.py", "2. Dados e limites", "Veja o que dá e o que não dá para concluir com esses dados, e por quê."),
    ("paginas/investigacao.py", "3. Investigação", "Compare dois períodos: o que mudou, o que os dados sustentam e o que verificar."),
    ("paginas/extrato.py", "4. Extrato por fornecedor", "Quanto custa a energia de cada fornecedor (R$/GJ), não só a tonelada."),
    ("paginas/relatorio.py", "5. Relatório", "Um relatório em linguagem simples, com 5 blocos, para compartilhar."),
]  # fmt: skip
for pagina, titulo, texto in passos:
    c1, c2 = st.columns([1, 3])
    c1.page_link(pagina, label=titulo)
    c2.markdown(texto)

st.markdown("### Como funciona")
st.markdown(
    "A EULER **soma** aos registros que a fábrica já tem: diário do operador, "
    "recebimentos de combustível, amostras e eventos. Ela não muda nada na caldeira; "
    "ela investiga e indica **verificações**."
)
