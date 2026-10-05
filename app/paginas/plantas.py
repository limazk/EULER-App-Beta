"""Biblioteca local de plantas: versões de arquivos, análises e cópia de segurança."""

import json

import armazenamento as arm
import estado
import streamlit as st
from componentes import cabecalho

from euler.armazem import CLASSES

cabecalho(
    "Plantas e histórico",
    "Guarde os dados no computador e retome a análise em outra sessão.",
    "Biblioteca local",
)


def mostrar():
    repo = arm.repositorio()
    restaurada = st.session_state.pop("biblioteca_restaurada", None)
    if restaurada:
        st.session_state["biblioteca_planta"] = restaurada["id"]
        st.success(f"Cópia restaurada: {restaurada['nome']}. Abra a versão que deseja analisar.")
    st.caption(
        "Os bancos ficam fora da pasta do código. Esta biblioteca é local e compartilhada "
        "por quem acessa esta instalação; ainda não é uma área de clientes com login."
    )
    with st.expander("Cadastrar uma planta"), st.form("nova_planta"):
        nome = st.text_input("Nome da planta", max_chars=160)
        classe = st.selectbox("Origem dos dados da planta", list(CLASSES), format_func=CLASSES.get)
        autorizacao = st.text_input(
            "Autorização para dados de cliente",
            help="Obrigatória para cliente: quem autorizou e quando.",
        )
        if st.form_submit_button("Criar planta"):
            planta = repo.criar_planta(nome, classe=classe, autorizacao=autorizacao)
            st.session_state["biblioteca_planta"] = planta["id"]
            st.success("Planta criada. Selecione os dados que deseja salvar nela.")

    plantas = {p["id"]: p for p in repo.listar_plantas()}
    if plantas:
        escolhido = st.selectbox(
            "Planta",
            list(plantas),
            key="biblioteca_planta",
            format_func=lambda pid: f"{plantas[pid]['nome']} · {pid[:8]}",
        )
        planta = plantas[escolhido]
        st.caption("Origem: " + CLASSES.get(planta.get("classe"), "Ainda não classificada"))
        if planta.get("classe") == "nao_classificado":
            with st.expander("Classificar biblioteca anterior"), st.form("classificar_planta"):
                classe = st.selectbox(
                    "Classe dos arquivos já salvos", list(CLASSES), format_func=CLASSES.get
                )
                autorizacao = st.text_input("Registro da autorização, se forem dados de cliente")
                if st.form_submit_button("Confirmar classe"):
                    repo.classificar_planta(escolhido, classe, autorizacao)
                    st.rerun()
        st.page_link(
            "paginas/acompanhamento.py",
            label="Equipamentos e acompanhamento",
            icon=":material/history:",
        )
        st.caption(
            "Selecionar uma planta não troca os dados ativos. Use Abrir versão para carregá-los."
        )
        if st.session_state.get("arquivos"):
            with st.expander("Salvar os dados em uso nesta planta"):
                st.write("Dados em uso: " + estado.rotulo_dados())
                if estado.dados_sinteticos():
                    st.warning(
                        "Este conjunto será preservado com a identificação de dados sintéticos."
                    )
                st.caption(
                    "Cada versão contém o conjunto completo de arquivos de uma análise. "
                    "Não unimos linhas nem misturamos caldeiras. As versões anteriores permanecem."
                )
                with st.form("salvar_versao"):
                    autor = st.text_input(
                        "Responsável pelo registro",
                        # o mesmo nome digitado nas telas de acompanhamento, se houver
                        value=st.session_state.get("acomp_autor_salvo", ""),
                        key="salvar_autor",
                    )
                    motivo = st.text_input("Motivo ou descrição da versão", key="salvar_motivo")
                    if st.form_submit_button("Salvar versão nesta planta", type="primary"):
                        v = arm.salvar_sessao(planta, autor=autor, motivo=motivo)
                        st.success("Dados salvos no banco. Versão: " + v["id"][:8])

        versoes = repo.listar_importacoes(escolhido)
        st.subheader("Versões salvas")
        if not versoes:
            st.info(
                "Esta planta ainda não tem arquivos salvos. Importe dados e salve a primeira versão."
            )
            st.page_link(
                "paginas/importar.py", label="Importar dados", icon=":material/upload_file:"
            )
        else:
            st.dataframe(
                [
                    {
                        "Versão": v["id"][:8],
                        "Registro (UTC)": v["criado_em"],
                        "Descrição": v["rotulo"],
                        "Responsável": v["autor"],
                        "Motivo": v["motivo"],
                        "Versão anterior": (v.get("anterior_id") or "—")[:8],
                    }
                    for v in versoes
                ],
                hide_index=True,
                width="stretch",
            )
            indice = st.selectbox(
                "Versão para abrir",
                range(len(versoes)),
                key=f"versao_{escolhido}_{len(versoes)}",
                format_func=lambda i: (
                    f"{versoes[i]['criado_em']} · {versoes[i]['motivo']} · {versoes[i]['id'][:8]}"
                ),
            )
            v = versoes[indice]
            if st.button("Abrir versão", type="primary"):
                arm.abrir_importacao(planta, v["id"])
                st.success("Versão carregada. Os dados e a altitude salvos estão em uso.")
            st.page_link(
                "paginas/investigacao.py",
                label="Ir para Investigação",
                icon=":material/troubleshoot:",
            )
            with st.expander("Análises arquivadas desta versão"):
                analises = repo.listar_analises(escolhido, v["id"])
                st.caption(
                    "As investigações são arquivadas quando calculadas com uma versão salva. "
                    "O histórico não muda com atualizações do motor."
                )
                if not analises:
                    st.info("Nenhuma análise arquivada para esta versão.")
                else:
                    st.dataframe(
                        [
                            {
                                "Análise": a["id"][:8],
                                "Registro (UTC)": a["criado_em"],
                                "Assinatura": a["assinatura"],
                            }
                            for a in analises
                        ],
                        hide_index=True,
                        width="stretch",
                    )
                    st.download_button(
                        "Baixar análises históricas (JSON)",
                        json.dumps(analises, ensure_ascii=False, indent=2),
                        file_name=f"euler_analises_{v['id'][:8]}.json",
                        mime="application/json",
                    )
            with st.expander("Cópia de segurança desta planta"):
                st.caption(
                    "Inclui arquivos originais, versões e análises. Guarde em um local protegido."
                )
                if st.button("Preparar backup"):
                    st.session_state["backup_biblioteca"] = (
                        escolhido,
                        repo.exportar_backup(escolhido),
                    )
                backup = st.session_state.get("backup_biblioteca")
                if backup and backup[0] == escolhido:
                    st.download_button(
                        "Baixar backup preparado",
                        backup[1],
                        file_name=f"euler_backup_{escolhido[:8]}.json",
                        mime="application/json",
                    )
                    st.caption("Se novos dados foram salvos depois, prepare o backup novamente.")
    else:
        st.info("Cadastre a primeira planta para salvar e reabrir seus dados.")

    with st.expander("Restaurar uma cópia de segurança"):
        st.caption("A restauração cria uma nova planta. Nenhum banco existente é substituído.")
        arquivo = st.file_uploader("Backup EULER (.json)", type=["json"], key="restaurar_backup")
        if st.button("Restaurar como nova planta", disabled=arquivo is None):
            nova = repo.restaurar_backup(arquivo.getvalue())
            st.session_state["biblioteca_restaurada"] = nova
            st.rerun()
    with st.expander("Local de armazenamento"):
        st.code(str(repo.raiz))
        st.caption("Atualizar o código ou limpar a sessão não apaga estes bancos.")


try:
    mostrar()
except arm.ERROS as exc:
    st.error(f"Não foi possível concluir a operação no banco: {exc}")
    st.caption(
        "Nenhuma confirmação de salvamento foi emitida. Verifique o local e tente novamente."
    )
