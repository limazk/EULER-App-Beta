"""Entrada curta: acompanhar a planta, analisar dados ou conhecer a demonstração."""

import estado
import streamlit as st
from componentes import cartao

from euler.textos import AVISO_PROTOTIPO, ESTAGIOS_MODELO

with st.container(key="euler-abertura"):
    st.html('<div class="euler-sobrelinha">Consumo · custo · próximas verificações</div>')
    st.title("EULER", anchor=False)
    st.markdown("### Entenda o que mudou. Saiba o que verificar.")
    st.caption(
        "Acompanhe combustível e vapor, investigue diferenças e registre o resultado das ações."
    )

if st.session_state.get("arquivos"):
    with st.container(border=True):
        st.markdown("**Continue com os dados carregados**")
        origem = "Demonstração sintética" if estado.dados_sinteticos() else "Dados enviados"
        st.caption(f"{origem} · os limites da análise acompanham cada resultado.")
        a, b = st.columns(2)
        a.page_link("paginas/saude.py", label="Ver análise", icon=":material/arrow_forward:")
        b.page_link("paginas/financeiro.py", label="Ver financeiro", icon=":material/payments:")

um, dois = st.columns(2)
with um, cartao("inicio-planta"):
    st.markdown("#### Minha planta")
    st.caption("Reúna os registros, veja pendências e acompanhe as ações ao longo do tempo.")
    st.caption(
        "Enviar registros → conferir a conta → investigar → registrar ação → verificar "
        "resultado. Tudo fica salvo na planta."
    )
    st.page_link(
        "paginas/painel.py", label="Abrir painel da planta", icon=":material/space_dashboard:"
    )
    st.page_link(
        "paginas/acompanhamento.py", label="Cadastrar ou atualizar dados", icon=":material/upload:"
    )
with dois, cartao("inicio-analise"):
    st.markdown("#### Analisar um período")
    st.caption("Use um arquivo ou explore uma demonstração com dados sintéticos.")
    st.page_link("paginas/importar.py", label="Importar um arquivo", icon=":material/upload_file:")
    if st.button(
        "Explorar demonstração", type="primary", icon=":material/play_circle:", key="ato1"
    ):
        estado.usar_caso_demo(completo=True)
        st.switch_page("paginas/saude.py")

with cartao("inicio-evidencias"):
    st.markdown("**Testado com registros públicos de uma planta brasileira · 660 dias**")
    st.caption("Veja os resultados, a origem dos dados e o que ainda não foi possível concluir.")
    st.page_link(
        "paginas/dados_publicos.py", label="Conhecer os testes reais", icon=":material/science:"
    )

with st.expander("Sobre a demonstração e os limites"):
    st.info(AVISO_PROTOTIPO)
    st.markdown(
        "A demonstração usa uma caldeira **sintética**, de 20 t/h a cavaco, com oito semanas "
        "de registros e três fornecedores. O caso público brasileiro é separado dela."
    )
    st.caption(
        "Compare também os mesmos registros sem o cadastro completo de instrumentos: "
        "a EULER explica quais conclusões ficam limitadas."
    )
    if st.button("Ver demonstração com dados incompletos", key="ato2"):
        estado.usar_caso_demo(completo=False)
        st.switch_page("paginas/saude.py")
    for titulo, texto in ESTAGIOS_MODELO:
        st.markdown(f"**{titulo}**")
        st.caption(texto)
    st.caption(
        "A EULER investiga e recomenda verificações. Não comanda nem avalia a segurança da caldeira."
    )
