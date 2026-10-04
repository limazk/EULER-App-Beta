"""Entrada incremental por equipamento; arquivos e operações no mesmo banco da planta."""

import json

import armazenamento as arm
import streamlit as st
from componentes import cabecalho

from euler.armazem import CLASSES, POLITICAS_CUSTO
from euler.fechamento import (
    criar_referencia,
    fechamentos,
    p_atm,
    produzir_fechamento,
    referencias,
    reproduzir,
)
from euler.painel import fila_de_atencao, texto_fechamento
from euler.periodos import periodos_entre_estoques

cabecalho(
    "Acompanhamento",
    "Acumule dados de cada equipamento e preserve as decisões ao longo do tempo.",
    "Gestão da planta",
)


def importar_registros(repo, planta, a, eq, autor):
    versoes = repo.listar_importacoes(planta["id"])
    if not versoes:
        st.info("Salve uma versão em Plantas e histórico antes de adicionar seus registros.")
        return
    st.subheader("Adicionar registros ao equipamento")
    v = st.selectbox(
        "Conjunto de arquivos salvo",
        versoes,
        format_func=lambda x: f"{x['rotulo']} · {x['id'][:8]}",
    )
    with st.expander("Mapeamento de colunas e fonte"):
        fonte = st.text_input("Nome da fonte", value="Importação de arquivos")
        st.caption("Use os nomes do contrato de dados. Mapear um nome não converte unidades.")
        mapa_texto = st.text_area(
            "Mapeamento opcional (JSON)", placeholder='{"TempChamine": "t_gases_c"}'
        )
        salvar_perfil = st.checkbox("Guardar este mapeamento para a fonte")
    chave = (planta["id"], eq["id"], v["id"], fonte, mapa_texto)
    if st.button("Preparar prévia"):
        mapa = json.loads(mapa_texto) if mapa_texto.strip() else None
        if mapa is not None and (
            not isinstance(mapa, dict)
            or not all(isinstance(k, str) and isinstance(val, str) for k, val in mapa.items())
        ):
            raise ValueError("O mapeamento deve relacionar nomes de colunas a nomes do contrato.")
        salvo = repo.carregar_importacao(planta["id"], v["id"])
        previa = a.previa(eq["id"], salvo["arquivos"], fonte=fonte, mapeamento=mapa)
        st.session_state["acomp_previa"] = (chave, previa)
    preparada = st.session_state.get("acomp_previa")
    if preparada and preparada[0] == chave:
        previa = preparada[1]
        st.dataframe(
            [{"Tabela": t, **c} for t, c in previa.contagem().items()],
            hide_index=True,
            width="stretch",
        )
        st.caption(
            "Iguais e repetidos não duplicam registros. Valores diferentes ficam pendentes de decisão."
        )
        if previa.avisos:
            st.caption(f"{len(previa.avisos)} avisos de qualidade disponíveis para revisão.")
            for aviso in previa.avisos:
                if aviso.tipo == "unidade_incompativel":
                    st.warning(aviso.mensagem)
            with st.expander("Conferir avisos e campos ausentes"):
                st.dataframe(
                    [
                        {
                            "Tabela": av.tabela,
                            "Linha": av.linha,
                            "Gravidade": av.gravidade,
                            "Aviso": av.mensagem,
                        }
                        for av in previa.avisos
                    ],
                    hide_index=True,
                    width="stretch",
                )
        for tabela, motivos in previa.tabelas_bloqueadas.items():
            st.error(f"{tabela}: {'; '.join(motivos)}")
        recusadas = [
            {"Tabela": x.tabela, "Linha": x.linha, "Motivo": x.motivo}
            for x in previa.linhas
            if x.situacao == "rejeitada"
        ]
        if recusadas:
            with st.expander("Registros recusados"):
                st.dataframe(recusadas, hide_index=True)
        if st.button("Confirmar registros novos", type="primary"):
            r = a.confirmar(previa, autor=autor, salvar_perfil=salvar_perfil, importacao_id=v["id"])
            st.session_state.pop("acomp_previa", None)
            st.success(
                f"{r['novas']} registros adicionados. {r['conflitos_pendentes']} conflitos aguardam decisão."
            )


def resolver_pendencias(a, eq, autor):
    pendentes = a.conflitos(eq["id"])
    if not pendentes:
        return
    with st.expander(f"Resolver {len(pendentes)} conflitos"):
        c = st.selectbox(
            "Registro em conflito",
            pendentes,
            format_func=lambda x: f"#{x['id']} · {x['tabela']} · {x['chave']}",
        )
        st.json({"Atual": c["atual"], "Proposto": c["proposto"]}, expanded=False)
        aceitar = st.checkbox("Substituir pela proposta e guardar a versão anterior")
        motivo = st.text_input("Motivo da decisão", key="acomp_conflito_motivo")
        if st.button("Registrar decisão"):
            a.resolver_conflito(c["id"], aceitar, autor, motivo)
            st.success("Decisão salva com histórico.")
            st.rerun()


def mostrar_fechamentos(a, eq, autor):
    with st.expander("Referência e fechamentos"):
        refs = referencias(a, eq["id"])
        st.caption(
            "A referência é escolhida explicitamente. Um resultado desfavorável não troca a referência."
        )
        pacote = a.pacote(eq["id"], p_atm_bar=p_atm(a, eq["id"]))
        periodos = periodos_entre_estoques(pacote)
        if periodos:
            with st.form("acomp_referencia"):
                indices = list(range(len(periodos)))
                rotulo = lambda i: f"{periodos[i][0]} → {periodos[i][1]}"
                primeiro = st.selectbox(
                    "Primeiro período da referência", indices, format_func=rotulo
                )
                ultimo = st.selectbox("Último período da referência", indices, format_func=rotulo)
                tipo = st.selectbox(
                    "Tipo de referência",
                    ["estrutural", "correcao_de_dados"] if refs else ["inicial"],
                )
                motivo = st.text_input("Justificativa da referência")
                absorver = st.checkbox(
                    "Confirmar mudança estrutural mesmo se ela absorver uma piora"
                )
                if st.form_submit_button("Salvar referência"):
                    criar_referencia(
                        a,
                        eq["id"],
                        periodos[primeiro][0],
                        periodos[ultimo][1],
                        tipo,
                        motivo,
                        autor,
                        confirmar_absorcao=absorver,
                    )
                    st.success("Referência versionada salva.")
            if st.button("Fechar próximos períodos disponíveis"):
                f = produzir_fechamento(a, eq["id"], autor)
                st.success(f"Fechamento #{f['id']} salvo. {f['resultado']['situacao_frase']}")
        fs = fechamentos(a, eq["id"])
        if fs:
            f = st.selectbox(
                "Fechamento para consultar",
                fs[::-1],
                format_func=lambda x: f"#{x['id']} · {x['inicio']} → {x['fim']}",
            )
            st.write(f["resultado"]["situacao_frase"])
            st.download_button(
                "Baixar relatório do fechamento",
                texto_fechamento(f),
                file_name=f"fechamento_{f['id']}.txt",
            )
            if st.button("Conferir reprodução do fechamento"):
                r = reproduzir(a, f["id"])
                (st.success if r["identico"] else st.warning)(r["frase"])
        else:
            st.info("Nenhum fechamento salvo para este equipamento.")


def mostrar():
    repo = arm.repositorio()
    plantas = {p["id"]: p for p in repo.listar_plantas()}
    if not plantas:
        st.info("Cadastre uma planta em Plantas e histórico para começar.")
        st.page_link("paginas/plantas.py", label="Plantas e histórico")
        return
    pid = st.selectbox("Planta", list(plantas), format_func=lambda p: plantas[p]["nome"])
    planta = plantas[pid]
    if planta["classe"] not in CLASSES:
        st.info(
            "Esta planta veio da biblioteca anterior. Classifique a origem em Plantas e histórico antes de acumular registros."
        )
        st.page_link("paginas/plantas.py", label="Classificar planta")
        return
    st.caption(CLASSES[planta["classe"]] + " · salvo no computador, fora da pasta do código")
    autor = st.text_input("Responsável pelos registros", key="acomp_autor")
    a = repo.armazem(pid)
    try:
        with st.expander("Cadastrar equipamento"), st.form("acomp_equip"):
            codigo = st.text_input("Identificador interno", key="equip_id")
            nome = st.text_input("Nome do equipamento", key="equip_nome")
            caldeira = st.text_input("Código caldeira_id no diário", key="equip_caldeira_id")
            altitude = st.number_input("Altitude informada (m)", value=None, key="equip_altitude")
            if st.form_submit_button("Cadastrar equipamento"):
                if not codigo.strip() or not nome.strip() or not caldeira.strip():
                    raise ValueError("Informe os identificadores e o nome do equipamento.")
                a.criar_equipamento(
                    codigo.strip(),
                    nome.strip(),
                    caldeira.strip(),
                    config={"altitude_m": altitude},
                    autor=autor,
                )
                st.success("Equipamento cadastrado.")
        equipamentos = a.equipamentos()
        if not equipamentos:
            st.info("Cadastre o equipamento com o código que aparece no diário.")
            return
        eq = st.selectbox(
            "Equipamento", equipamentos, format_func=lambda e: f"{e['nome']} · {e['caldeira_id']}"
        )
        cobertura = a.cobertura(eq["id"])
        st.info(cobertura["frase"])
        with st.expander("Condições do acompanhamento"):
            with st.form("acomp_config"):
                alt = st.number_input(
                    "Altitude do equipamento (m)", value=eq["config"]["altitude_m"]
                )
                dias = st.number_input(
                    "Avisar desatualização após (dias)",
                    min_value=1,
                    value=eq["config"]["dias_para_desatualizado"],
                )
                politica = st.selectbox(
                    "Política de custo",
                    list(POLITICAS_CUSTO),
                    index=list(POLITICAS_CUSTO).index(eq["config"]["politica_custo"]),
                    format_func=POLITICAS_CUSTO.get,
                )
                if st.form_submit_button("Salvar condições"):
                    a.configurar(
                        eq["id"],
                        {
                            "altitude_m": alt,
                            "dias_para_desatualizado": dias,
                            "politica_custo": politica,
                        },
                        autor=autor,
                    )
                    st.rerun()
            st.caption(
                "Tabela de preços sem preço cadastrado deixa o custo indisponível; não usa outra política em silêncio."
            )
        importar_registros(repo, planta, a, eq, autor)
        resolver_pendencias(a, eq, autor)
        st.divider()
        if st.button("Analisar série acumulada"):
            arm.abrir_serie(planta, a, eq["id"], autor=autor)
            st.success(
                "Série carregada. Abra Investigação para calcular com todos os registros desta revisão."
            )
        st.page_link(
            "paginas/investigacao.py", label="Ir para Investigação", icon=":material/troubleshoot:"
        )
        mostrar_fechamentos(a, eq, autor)
        with st.expander("Fila de atenção e histórico"):
            fila = fila_de_atencao(a, eq["id"])
            if fila:
                st.json(fila, expanded=False)
            st.dataframe(a.eventos(eq["id"]), hide_index=True, width="stretch")
    finally:
        a.fechar()


try:
    mostrar()
except arm.ERROS as exc:
    st.error(f"Operação não concluída: {exc}")
