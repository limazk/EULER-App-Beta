"""Tela inicial da EULER."""

import estado
import streamlit as st
from componentes import cartao

from euler.textos import AVISO_PROTOTIPO, ESTAGIOS_MODELO, FRASE_PRODUTO, PERGUNTA_CENTRAL

with st.container(key="euler-abertura"):
    st.html('<div class="euler-sobrelinha">Investigação física de caldeiras industriais</div>')
    st.title("EULER", anchor=False)
    st.markdown(f"### {FRASE_PRODUTO}")
    st.markdown(
        f"{PERGUNTA_CENTRAL} Às vezes a resposta certa é **“não dá para concluir”**, junto com "
        "a próxima medição que resolveria a dúvida. Isso é uma funcionalidade, não uma falha."
    )
    st.markdown(
        "**A demonstração tem dois atos, com a mesma caldeira sintética.** No ato 1 a fábrica "
        "cadastrou a incerteza de todos os instrumentos e a EULER conclui. No ato 2 falta esse "
        "cadastro e a EULER explica por que não conclui."
    )
    with st.container(horizontal=True, vertical_alignment="center", gap="medium"):
        if st.button(
            "Ato 1 · a EULER conclui", type="primary", icon=":material/play_circle:", key="ato1"
        ):
            estado.usar_caso_demo(completo=True)
            st.switch_page("paginas/saude.py")
        if st.button(
            "Ato 2 · a EULER explica por que não conclui", icon=":material/play_circle:", key="ato2"
        ):
            estado.usar_caso_demo(completo=False)
            st.switch_page("paginas/saude.py")
        st.page_link(
            "paginas/importar.py", label="Importar meus dados", icon=":material/upload_file:"
        )

st.info(
    f"{AVISO_PROTOTIPO} O caso de demonstração é uma caldeira **sintética** (dados inventados "
    "para teste) de 20 t/h a cavaco, com 8 semanas de registros e 3 fornecedores. Os dois atos "
    "têm os mesmos registros de operação; muda só o cadastro de instrumentos.",
    icon=":material/science:",
)

st.markdown("### Como funciona, em 6 passos")
passos = [
    (":material/upload_file:", "paginas/importar.py", "Importar", "Os registros que a fábrica já tem (CSV ou planilha). Nada é corrigido em silêncio."),
    (":material/monitor_heart:", "paginas/saude.py", "Saúde da caldeira", "O consumo por tonelada de vapor semana a semana: mudou ou ficou estável?"),
    (":material/rule:", "paginas/limites.py", "Dados e limites", "O que dá e o que não dá para concluir com esses dados, e por quê."),
    (":material/troubleshoot:", "paginas/investigacao.py", "Investigação", "Dois períodos lado a lado: o que mudou, o que explica e o que verificar."),
    (":material/receipt_long:", "paginas/extrato.py", "Extrato", "Quanto custa a energia de cada fornecedor (R$/GJ), não só a tonelada."),
    (":material/description:", "paginas/relatorio.py", "Relatório", "Linguagem simples, 5 blocos fixos, pronto para compartilhar."),
]  # fmt: skip
for n, ((icone, pagina, titulo, texto), coluna) in enumerate(
    zip(passos, st.columns(6), strict=True), start=1
):
    with coluna, cartao(f"passo-{n}"):
        st.html(f'<div class="euler-sobrelinha">Passo {n}</div>')
        st.markdown(f"{icone} **{titulo}**")
        st.caption(texto)
        st.page_link(pagina, label="Abrir", icon=":material/arrow_forward:")

st.markdown("### Em que pé está a EULER")
icones = (":material/verified:", ":material/rate_review:", ":material/hourglass_empty:")
for n, ((titulo, texto), icone, coluna) in enumerate(
    zip(ESTAGIOS_MODELO, icones, st.columns(3), strict=True)
):
    with coluna, cartao(f"estagio-{n}"):
        st.markdown(f"{icone} **{titulo}**")
        st.caption(texto)

st.markdown("### O que a EULER não faz")
st.markdown(
    "A EULER **soma** aos registros que a fábrica já tem: diário do operador, recebimentos de "
    "combustível, amostras e eventos. Ela **não muda nada na caldeira** e não emite comandos: "
    "investiga e indica **verificações**."
)
