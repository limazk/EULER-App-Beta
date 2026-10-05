"""Diagnóstico da evidência: caso público ou investigação dos arquivos ativos."""

import estado
import streamlit as st
from blocos.diagnostico import renderizar
from componentes import cabecalho
from diagnostico_publico import diagnosticos
from ensaio_horario import executar

cabecalho(
    "Diagnóstico de evidências",
    "O que foi observado, o que os dados sustentam e qual verificação vem a seguir.",
    "Dados reais testados",
)
origem = st.selectbox(
    "Conjunto de dados", ["Caso público EPA/PUDL", "Investigação dos arquivos ativos"]
)
if origem == "Caso público EPA/PUDL":
    st.caption(
        "DADOS PÚBLICOS · Ingredion Argo, EUA · 2023 · análise histórica, sem vínculo com a instalação"
    )
    unidade = st.selectbox("Equipamento", ["B10", "B08", "B07", "B06"])
    mes = st.selectbox("Período comparado", ["2023-02", "2023-03"])
    r = executar()
    ds = diagnosticos(r, unidade)
    renderizar(next(d for d in ds if d["periodo"] == mes))
else:
    j, motivo = estado.investigacao_atual()
    if j is None or "diagnostico_evidencias" not in j:
        st.info("Execute a investigação dos arquivos ativos para gerar este diagnóstico.")
        st.page_link("paginas/investigacao.py", label="Abrir investigação")
    else:
        st.caption(
            "DADOS SINTÉTICOS"
            if estado.dados_sinteticos()
            else "Arquivos enviados · origem declarada nos registros"
        )
        renderizar(j["diagnostico_evidencias"])
