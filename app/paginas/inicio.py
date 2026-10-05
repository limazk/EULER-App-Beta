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

st.markdown("### Duas formas de usar")
um, dois = st.columns(2)
with um, cartao("uso-periodo"):
    st.html('<div class="euler-sobrelinha">Analisar um período</div>')
    st.markdown(":material/troubleshoot: **O consumo mudou: o que explica e o que verificar?**")
    st.caption(
        "Com os arquivos desta sessão (demonstração ou enviados): saúde da caldeira, "
        "investigação de dois períodos, a conta em reais, as oportunidades e o relatório."
    )
    st.caption("Importar dados → Saúde → Investigação → Financeiro → Relatório")
    st.page_link(
        "paginas/importar.py", label="Começar pelos dados", icon=":material/arrow_forward:"
    )
with dois, cartao("uso-acompanhar"):
    st.html('<div class="euler-sobrelinha">Acompanhar a planta</div>')
    st.markdown(
        ":material/event_available:  **A cada período: o que mudou, o que fazer e o que deu certo**"
    )
    st.caption(
        "Os dados ficam guardados por planta. A cada atualização a EULER fecha o período, abre "
        "investigações, acompanha as ações da equipe e verifica o resultado depois."
    )
    st.caption("Atualizar dados → Fechamentos → Investigações e ações → Painel")
    st.page_link(
        "paginas/acompanhamento.py",
        label="Cadastrar a planta ou criar a demonstração",
        icon=":material/arrow_forward:",
    )

with cartao("dados-reais"):
    st.html('<div class="euler-sobrelinha">Dados reais testados</div>')
    st.markdown(
        ":material/science: **Além da demonstração: casos reais publicados por empresas, "
        "governos e universidades**"
    )
    st.caption(
        "660 dias reais de uma planta brasileira (cervejaria no RS, caldeiras a casca de arroz), "
        "registros horários de caldeiras nos EUA (EPA), estudos brasileiros de biomassa e de custo "
        "do vapor, uma caldeira a carvão em três cargas e uma série por minuto da China. Nenhum é "
        "de cliente; cada um mostra o que foi possível concluir e o que faltou."
    )
    st.page_link(
        "paginas/dados_publicos.py",
        label="Ver o que foi testado com dados reais",
        icon=":material/arrow_forward:",
    )

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
