"""Tela Importar dados: envio dos arquivos e lista de avisos de qualidade (T03, T05)."""

import estado
import streamlit as st

from euler.formato import num
from euler.io.esquemas import TABELAS
from euler.io.modelos import ARQUIVO_PLANILHA

st.title("Importar dados")
st.markdown(
    "Envie os registros da caldeira: os arquivos CSV (`diario.csv`, `combustivel.csv`, "
    "`amostras.csv`, `eventos.csv`, `instrumentos.csv`) ou a **planilha modelo** preenchida. "
    "A EULER guarda o original e lista o que encontrou. **Nada é corrigido sem avisar.**"
)

with st.container(border=True):
    st.markdown("**1. Local da caldeira**")
    c1, c2 = st.columns([1, 2])
    altitude = c1.number_input(
        "Altitude do local (m)",
        min_value=-500.0,
        max_value=5000.0,
        value=st.session_state.get("altitude_m"),
        step=10.0,
        placeholder="ex.: 1100",
        help="Usada para converter a pressão do manômetro em pressão absoluta.",
    )
    st.session_state["altitude_m"] = altitude
    if altitude is None:
        c2.info("Sem altitude, a pressão absoluta do vapor não é calculada.")
    else:
        c2.success(
            f"Pressão atmosférica: **{num(estado.p_atm_bar(), 3)} bar** "
            "(estimado pela altitude, atmosfera padrão)."
        )

with st.container(border=True):
    st.markdown("**2. Arquivos**")
    enviados = st.file_uploader(
        "Arraste os arquivos aqui", type=["csv", "xlsx"], accept_multiple_files=True
    )
    b1, b2, b3 = st.columns(3)
    if b1.button("Importar os arquivos enviados", type="primary", disabled=not enviados):
        estado.definir_arquivos(
            {f.name: f.getvalue() for f in enviados}, f"{len(enviados)} arquivo(s) enviado(s)"
        )
    if b2.button("Usar os modelos (1 linha de exemplo)"):
        estado.definir_arquivos(
            estado.ler_pasta(estado.RAIZ / "templates"), "modelos de exemplo (sintéticos)"
        )
    if b3.button("Exemplo com problemas (sintético)"):
        estado.definir_arquivos(
            estado.ler_pasta(estado.RAIZ / "demo" / "qualidade"),
            "exemplo com problemas de propósito (sintético)",
        )
    st.download_button(
        "Baixar a planilha modelo (.xlsx)",
        ARQUIVO_PLANILHA.read_bytes(),
        file_name=ARQUIVO_PLANILHA.name,
        icon=":material/download:",
    )


def mostrar_resultado(pacote) -> None:
    st.markdown(f"### Resultado da importação · {estado.rotulo_dados()}")
    avisos = pacote.tabela_avisos()
    contagem = avisos["Gravidade"].value_counts()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Tabelas importadas", len(pacote.importacoes))
    m2.metric("Erros", int(contagem.get("Erro", 0)))
    m3.metric("Avisos de atenção", int(contagem.get("Atenção", 0)))
    m4.metric("Informações", int(contagem.get("Informação", 0)))

    linhas = []
    for nome, tabela in TABELAS.items():
        imp = pacote.importacoes.get(nome)
        if imp is None:
            situacao, n = "não enviada", "—"
        elif imp.bloqueada:
            situacao, n = "bloqueada (ver erros)", str(len(imp.original))
        else:
            situacao, n = "importada", str(len(imp.dados))
        linhas.append(
            {"Tabela": tabela.titulo, "Arquivo": tabela.arquivo, "Linhas": n, "Situação": situacao}
        )
    st.dataframe(linhas, hide_index=True, width="stretch")

    st.markdown("#### Avisos de qualidade")
    if avisos.empty:
        st.success("Nenhum problema encontrado.")
    else:
        filtro = st.pills(
            "Mostrar",
            ["Erro", "Atenção", "Informação"],
            default=["Erro", "Atenção", "Informação"],
            selection_mode="multi",
        )
        visiveis = avisos[avisos["Gravidade"].isin(filtro)][
            ["Gravidade", "Tabela", "Linha", "Aviso"]
        ]
        visiveis = visiveis.astype({"Linha": "string"}).fillna({"Linha": "—"})
        if len(visiveis) <= 80:
            # tabela simples: quebra o texto e mostra a frase inteira
            st.table(visiveis.set_index("Gravidade"))
        else:
            st.dataframe(visiveis, hide_index=True, width="stretch")
        st.caption(
            "**Erro:** a tabela não pôde ser usada. **Atenção:** pode afetar as análises. "
            "**Informação:** registro do que foi interpretado. Os números de linha são os do arquivo "
            "(cabeçalho = linha 1)."
        )

    with st.expander("Ver os dados como a EULER entendeu"):
        nomes = list(pacote.importacoes)
        for aba, nome in zip(st.tabs([TABELAS[n].titulo for n in nomes]), nomes, strict=True):
            with aba:
                st.dataframe(pacote.importacoes[nome].dados, hide_index=True, width="stretch")


pacote = estado.pacote()
if pacote is not None:
    mostrar_resultado(pacote)
