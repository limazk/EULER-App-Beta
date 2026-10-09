"""Dashboard EULER 3.0: contexto, dados sustentados e próximos passos."""

from html import escape

import altair as alt
import armazenamento as arm
import estado
import pandas as pd
import streamlit as st
from componentes import (
    cartao,
    cartao_indicador,
    chip_status,
    painel_intelligence_desativado,
    secao,
)
from dashboard_persistido import carregar_dashboard, filtrar_periodo, resumo_fechamento

from euler.dia_a_dia import diario_por_dia
from euler.formato import num
from euler.textos import AVISO_PROTOTIPO, ESTAGIOS_MODELO

SERIES_DASHBOARD = {
    "vazao_t_h": ("Vapor · vazão média", "t/h", ".1f"),
    "t_gases_c": ("Temperatura dos gases", "°C", ".0f"),
    "o2_seco_pct": ("O₂ nos gases · base seca", "%", ".1f"),
    "recebido_t": ("Combustível recebido · não é consumo", "t/dia", ".1f"),
}


def _periodo_pacote(pacote) -> str:
    diario = pacote.dados("diario") if pacote is not None else None
    if diario is None or diario.empty:
        return "Sem período carregado"
    instantes = diario.get("instante_observado", pd.Series(dtype="datetime64[ns]")).dropna()
    if instantes.empty:
        return "Sem período carregado"
    return f"{instantes.min():%d/%m/%Y} a {instantes.max():%d/%m/%Y}"


def _contexto(pacote, persistido=None, fechamento=None, planta_selecionada=None) -> dict[str, str]:
    """Contexto visível, sem confundir autenticação com conexão de sensores."""
    auth = st.session_state.get("_euler_auth_context") or {}
    memberships = auth.get("memberships") or []
    org_atual = arm.organizacao_atual()
    org = (memberships[0].get("organizations") or {}) if memberships else {}
    persistencia = st.session_state.get("persistencia") or {}
    diario = pacote.dados("diario") if pacote is not None else None

    equipamento = "Não identificado"
    periodo = _periodo_pacote(pacote)
    if (
        diario is not None
        and not diario.empty
        and "caldeira_id" in diario
        and diario["caldeira_id"].notna().any()
    ):
        equipamento = str(diario["caldeira_id"].dropna().iloc[0])
    if persistido is not None:
        equipamento = persistido.equipamento["nome"]
        if fechamento is not None:
            inicio = pd.Timestamp(fechamento["inicio"])
            fim = pd.Timestamp(fechamento["fim"])
            periodo = f"{inicio:%d/%m/%Y} a {fim:%d/%m/%Y}"
    return {
        "organizacao": str(
            (org_atual or {}).get("nome") or org.get("name") or "Sem organização vinculada"
        ),
        "planta": str(
            persistido.planta["nome"]
            if persistido is not None
            else (
                planta_selecionada["nome"]
                if planta_selecionada is not None
                else persistencia.get("planta_nome") or "Nenhuma planta selecionada"
            )
        ),
        "equipamento": equipamento,
        "periodo": periodo,
        "origem": (
            persistido.origem
            if persistido is not None
            else (
                "Sem dados persistidos" if planta_selecionada is not None else estado.rotulo_dados()
            )
        ),
    }


def _cabecalho_dashboard(contexto: dict[str, str]) -> None:
    with st.container(key="euler-abertura"):
        st.html('<div class="euler-sobrelinha">Visão operacional · EULER 3.0</div>')
        # Mantém a marca como título sem competir visualmente com o nome da tela.
        st.title("EULER", anchor=False)
        st.html('<div class="euler-dashboard-title">Dashboard</div>')
        st.caption("Contexto, registros disponíveis e o próximo passo — sem números presumidos.")
        itens = "".join(
            f"<span>{escape(rotulo)}<strong>{escape(contexto[chave])}</strong></span>"
            for chave, rotulo in (
                ("organizacao", "Organização"),
                ("planta", "Planta"),
                ("equipamento", "Equipamento"),
                ("periodo", "Período"),
                ("origem", "Origem"),
            )
        )
        st.html(f'<div class="euler-contexto" aria-label="Contexto atual">{itens}</div>')


def _indicadores(investigacao: dict | None, fechamento: dict | None = None) -> None:
    custo = None
    consumo = None
    proxima = None
    resumo = resumo_fechamento(fechamento)
    if resumo:
        custo_atual = resumo["custo_brl_t_vapor"]
        diferenca = resumo["desvio_brl_t_vapor"]
        consumo_atual = resumo["consumo_especifico_t_t"]
        proxima = resumo["proxima_verificacao"]
        detalhe_custo = (
            "Fechamento vigente · custo do combustível consumido dividido pelo vapor "
            f"do período · política {resumo['politica_custo'] or 'não informada'}."
        )
        detalhe_diferenca = (
            "Desvio ainda não explicado por tonelada de vapor; não é economia nem pagamento."
            if diferenca is not None
            else "Desvio indisponível no fechamento selecionado."
        )
        detalhe_consumo = (
            "Fechamento vigente · combustível consumido por tonelada de vapor (t/t)."
            if consumo_atual is not None
            else "Consumo específico indisponível no fechamento selecionado."
        )
    elif investigacao:
        mudou = investigacao.get("o_que_mudou") or {}
        custo = mudou.get("custo_vapor")
        consumo = mudou.get("consumo_especifico") or {}
        proxima = (investigacao.get("proxima_verificacao") or {}).get("acao")
        custo_atual = custo.get("comparacao") if custo else None
        diferenca = custo.get("delta") if custo else None
        consumo_atual = consumo.get("comparacao") if consumo else None
        detalhe_custo = (
            "Período de comparação da investigação · R$/t de vapor."
            if custo_atual is not None
            else "Dados insuficientes para calcular custo por tonelada de vapor."
        )
        detalhe_diferenca = (
            "Comparação menos referência · R$/t de vapor."
            if diferenca is not None
            else "Diferença indisponível sem períodos e custos comparáveis."
        )
        detalhe_consumo = (
            "Período de comparação · combustível por tonelada de vapor."
            if consumo_atual is not None
            else "Dados insuficientes para calcular o consumo específico."
        )
    else:
        custo_atual = diferenca = consumo_atual = None
        detalhe_custo = "Dados insuficientes para calcular custo por tonelada de vapor."
        detalhe_diferenca = "Diferença indisponível sem períodos e custos comparáveis."
        detalhe_consumo = "Dados insuficientes para calcular o consumo específico."

    with st.container(key="dashboard-kpis"):
        colunas = st.columns(5)
        with colunas[0]:
            cartao_indicador(
                "custo",
                "Custo energético",
                None if custo_atual is None else f"R$ {num(custo_atual, 2)} / t vapor",
                detalhe=detalhe_custo,
                estado="neutro" if custo_atual is not None else "indisponivel",
            )
        with colunas[1]:
            cartao_indicador(
                "esperado",
                "Custo esperado",
                None,
                detalhe="Não apurado: a referência histórica não é tratada como expectativa.",
                estado="indisponivel",
            )
        with colunas[2]:
            cartao_indicador(
                "diferenca",
                "Diferença",
                None
                if diferenca is None
                else f"{'+' if diferenca > 0 else ''}R$ {num(diferenca, 2)} / t vapor",
                detalhe=detalhe_diferenca,
                estado="atencao" if diferenca is not None and diferenca > 0 else "neutro",
            )
        with colunas[3]:
            cartao_indicador(
                "consumo",
                "Consumo",
                None if consumo_atual is None else f"{num(consumo_atual, 3)} t/t",
                detalhe=detalhe_consumo,
                estado="neutro" if consumo_atual is not None else "indisponivel",
            )
        with colunas[4]:
            cartao_indicador(
                "verificacao",
                "Próxima verificação",
                "Definida" if proxima else None,
                detalhe=proxima
                or "Execute uma investigação válida para definir a próxima verificação.",
                estado="atencao" if proxima else "indisponivel",
            )


def _grafico_historico(pacote, *, periodo=None, origem=None) -> None:
    with cartao("historico-principal"):
        st.markdown("### Histórico operacional")
        if pacote is None:
            chip_status("Sem dados", "indisponivel")
            st.caption("Importe registros para visualizar uma série histórica.")
            return
        diario = diario_por_dia(pacote)
        if periodo is not None:
            diario = filtrar_periodo(diario, periodo["inicio"], periodo["fim"])
        disponiveis = [c for c in SERIES_DASHBOARD if c in diario and diario[c].notna().any()]
        if not disponiveis:
            chip_status("Dados insuficientes", "indisponivel")
            st.caption("Nenhuma série diária válida está disponível para este conjunto de dados.")
            return
        campo = st.selectbox(
            "Indicador do gráfico",
            disponiveis,
            format_func=lambda c: SERIES_DASHBOARD[c][0],
            key="dashboard-serie",
        )
        titulo, unidade, formato = SERIES_DASHBOARD[campo]
        dados = diario[["dia", campo]].rename(columns={campo: "valor"})
        grafico = (
            alt.Chart(dados)
            .mark_line(
                color="#31D877",
                point={"filled": True, "size": 42},
                invalid="break-paths-show-domains",
            )
            .encode(
                x=alt.X("dia:T", title="Dia", axis=alt.Axis(format="%d/%m")),
                y=alt.Y("valor:Q", title=unidade, scale=alt.Scale(zero=False)),
                tooltip=[
                    alt.Tooltip("dia:T", title="Dia", format="%d/%m/%Y"),
                    alt.Tooltip("valor:Q", title=f"{titulo} ({unidade})", format=formato),
                ],
            )
            .properties(height=300)
        )
        st.altair_chart(grafico, width="stretch")
        fonte = (
            f"registros persistidos da planta · origem {origem}"
            if origem
            else "registros importados nesta sessão"
        )
        st.caption(
            f"Fonte: {fonte}. Unidade: {unidade}. Lacunas permanecem interrompidas; "
            "combustível recebido representa compras, não consumo."
        )


def _situacao_equipamento(pacote, persistido=None) -> None:
    with cartao("situacao-equipamento"):
        st.markdown("### Situação dos equipamentos")
        diario = pacote.dados("diario") if pacote is not None else None
        if diario is None or diario.empty:
            chip_status("Medições indisponíveis", "indisponivel")
            st.metric("Última leitura registrada", "—")
            st.caption("Sem medições suficientes para atribuir estado operacional.")
            return
        instantes = diario["instante_observado"].dropna()
        ultima = f"{instantes.max():%d/%m/%Y %H:%M}" if not instantes.empty else "—"
        avisos = [a for a in pacote.avisos if a.gravidade in {"erro", "atencao"}]
        chip_status("Registros disponíveis", "atencao" if avisos else "neutro")
        st.metric("Última leitura registrada", ultima)
        origem = (
            f"{persistido.cobertura.get('importacoes', 0)} importação(ões) persistida(s)"
            if persistido is not None
            else f"{len(diario)} leitura(s) normalizada(s)"
        )
        st.caption(
            f"{origem} · {len(diario)} leitura(s) · {len(avisos)} aviso(s) de erro/atenção. "
            "Disponibilidade de registros não significa conexão com sensores nem estado normal."
        )
        st.page_link("paginas/limites.py", label="Ver qualidade e limites", icon=":material/rule:")


def _acoes_rapidas() -> None:
    with cartao("acoes-rapidas"):
        st.markdown("### Ações rápidas")
        st.page_link("paginas/acompanhamento.py", label="Nova importação", icon=":material/upload:")
        st.page_link(
            "paginas/investigacao.py",
            label="Abrir investigação",
            icon=":material/troubleshoot:",
        )
        st.page_link(
            "paginas/fechamentos.py",
            label="Revisar fechamento",
            icon=":material/event_available:",
        )
        if st.button(
            "Explorar demonstração",
            type="primary",
            icon=":material/play_circle:",
            key="ato1",
        ):
            estado.usar_caso_demo(completo=True)
            st.switch_page("paginas/saude.py")


def _central_investigacoes(investigacao: dict | None) -> None:
    with cartao("central-investigacoes"):
        st.markdown("### Central de investigações")
        if not investigacao:
            chip_status("Nenhuma investigação atual", "indisponivel")
            st.caption(
                "Compare períodos válidos para registrar evidências, hipóteses e a próxima verificação."
            )
            st.page_link(
                "paginas/investigacao.py",
                label="Iniciar investigação",
                icon=":material/arrow_forward:",
            )
            return
        conclusao = investigacao.get("conclusao") or {}
        proxima = investigacao.get("proxima_verificacao") or {}
        chip_status(
            "Conclusão com limitações" if conclusao.get("abstencao") else "Investigação disponível",
            "atencao" if conclusao.get("abstencao") else "neutro",
        )
        st.markdown(conclusao.get("texto") or "Investigação registrada sem resumo textual.")
        if proxima.get("acao"):
            st.info(f"**Próxima verificação:** {proxima['acao']}")
        st.page_link(
            "paginas/investigacao.py", label="Ver evidências e limitações", icon=":material/search:"
        )


def _fechamento_e_importacao(
    persistido=None, fechamento=None, *, selecao_persistida: bool = False
) -> None:
    a, b = st.columns(2)
    with a, cartao("fechamento-resumo"):
        st.markdown("### Fechamento mensal")
        if fechamento is None:
            chip_status("Nenhum vigente no contexto", "indisponivel")
            st.caption("Sem fechamento vigente para o equipamento e período selecionados.")
        else:
            chip_status("Versão vigente selecionada", "neutro")
            st.caption(
                f"Fechamento #{fechamento['id']} · revisão de dados "
                f"{fechamento['revisao_dados']} · valores preservados no histórico."
            )
        st.page_link(
            "paginas/fechamentos.py", label="Abrir fechamentos", icon=":material/arrow_forward:"
        )
    with b, cartao("ultima-importacao"):
        st.markdown("### Última importação")
        arquivos = st.session_state.get("arquivos") or ()
        if persistido is not None and persistido.importacoes:
            ultima = persistido.importacoes[0]
            chip_status("Histórico persistido", "neutro")
            st.metric("Importações do equipamento", len(persistido.importacoes))
            st.caption(
                f"Última importação: {pd.Timestamp(ultima['recebido_em']):%d/%m/%Y %H:%M} UTC · "
                f"revisão {ultima['revisao']} · por {ultima['autor']}."
            )
        elif selecao_persistida:
            chip_status("Nenhuma no contexto", "indisponivel")
            st.caption("Nenhuma importação está disponível para o equipamento selecionado.")
        elif not arquivos:
            chip_status("Nenhuma nesta sessão", "indisponivel")
            st.caption("Nenhum arquivo está carregado nesta sessão.")
        else:
            chip_status(
                "Demonstração sintética" if estado.dados_sinteticos() else "Dados enviados",
                "atencao" if estado.dados_sinteticos() else "neutro",
            )
            st.metric("Arquivos carregados", len(arquivos))
            st.caption(estado.rotulo_dados())
        st.page_link(
            "paginas/plantas.py", label="Ver origem e histórico", icon=":material/database:"
        )


def _seletor_persistido():
    """Seleciona tenant/planta/equipamento e lê dados salvos sem misturar contextos."""
    organizacoes = arm.organizacoes_autorizadas()
    if len(organizacoes) > 1:
        nomes = {org["id"]: org["nome"] for org in organizacoes}
        st.selectbox(
            "Organização",
            list(nomes),
            format_func=nomes.get,
            key=arm.ORGANIZACAO_SELECIONADA,
        )
    arm.sincronizar_organizacao()
    repo = arm.repositorio()
    plantas = {planta["id"]: planta for planta in repo.listar_plantas()}
    if not plantas:
        st.session_state.pop("dashboard_contexto_persistido", None)
        if st.session_state.get("arquivos"):
            st.info(
                "Nenhuma planta persistida nesta organização. O dashboard exibe somente "
                "os dados identificados desta sessão; salve-os para reabrir depois."
            )
        else:
            st.info("Nenhuma planta persistida nesta organização. O dashboard permanece sem dados.")
        return None, None, None

    with st.expander("Contexto de dados persistidos", expanded=True):
        planta_id = st.selectbox(
            "Planta autorizada",
            list(plantas),
            format_func=lambda valor: plantas[valor]["nome"],
            key="dashboard_planta",
        )
        planta = plantas[planta_id]
        armazem = repo.armazem(planta_id)
        try:
            equipamentos = {item["id"]: item for item in armazem.equipamentos()}
        finally:
            armazem.fechar()
        versoes = repo.listar_importacoes(planta_id)
        if not equipamentos:
            st.session_state["dashboard_contexto_persistido"] = {
                "planta_id": planta_id,
                "equipamento_id": None,
                "origem": "Sem dados persistidos",
            }
            st.info("Esta planta ainda não tem equipamento associado aos registros persistidos.")
            if versoes:
                _abrir_versao(repo, planta, versoes)
            return None, None, planta

        equipamento_id = st.selectbox(
            "Equipamento associado",
            list(equipamentos),
            format_func=lambda valor: equipamentos[valor]["nome"],
            key=f"dashboard_equipamento_{planta_id}",
        )
        persistido = carregar_dashboard(repo, planta_id, equipamento_id)
        st.session_state["dashboard_contexto_persistido"] = {
            "planta_id": planta_id,
            "equipamento_id": equipamento_id,
            "origem": persistido.origem,
        }
        fechamentos = {item["id"]: item for item in persistido.fechamentos}
        opcoes = list(reversed(fechamentos)) + ["serie_completa"]
        periodo_id = st.selectbox(
            "Período",
            opcoes,
            format_func=lambda valor: (
                "Série persistida completa"
                if valor == "serie_completa"
                else (
                    f"Fechamento vigente #{valor} · "
                    f"{pd.Timestamp(fechamentos[valor]['inicio']):%d/%m/%Y} a "
                    f"{pd.Timestamp(fechamentos[valor]['fim']):%d/%m/%Y}"
                )
            ),
            key=f"dashboard_periodo_{planta_id}_{equipamento_id}",
        )
        fechamento = None if periodo_id == "serie_completa" else fechamentos[periodo_id]
        st.caption(
            f"Origem: {persistido.origem} · {len(persistido.importacoes)} importação(ões) "
            "persistida(s) · leitura isolada desta planta e deste equipamento."
        )
        if persistido.importacoes:
            with st.expander("Histórico de importações"):
                st.dataframe(
                    [
                        {
                            "Revisão": item["revisao"],
                            "Recebida em": item["recebido_em"],
                            "Responsável": item["autor"],
                            "Registros novos": item["resumo"].get("novas", 0),
                            "Conflitos": item["resumo"].get("conflitos_pendentes", 0),
                        }
                        for item in persistido.importacoes
                    ],
                    hide_index=True,
                    width="stretch",
                )
        if versoes:
            _abrir_versao(repo, planta, versoes)
        return persistido, fechamento, planta


def _abrir_versao(repo, planta, versoes) -> None:
    indice = st.selectbox(
        "Versão arquivada para abrir na sessão",
        range(len(versoes)),
        format_func=lambda i: (
            f"{versoes[i]['criado_em']} · {versoes[i]['rotulo']} · {versoes[i]['id'][:8]}"
        ),
        key=f"dashboard_versao_{planta['id']}_{len(versoes)}",
    )
    if st.button("Abrir versão persistida", key=f"dashboard_abrir_{planta['id']}"):
        arm.abrir_importacao(planta, versoes[indice]["id"])
        st.rerun()


persistido, fechamento, planta_selecionada = _seletor_persistido()
selecao_persistida = planta_selecionada is not None
pacote = (
    persistido.pacote
    if selecao_persistida and persistido is not None
    else (None if selecao_persistida else estado.pacote())
)
investigacao, _ = (
    estado.investigacao_atual()
    if pacote is not None and not selecao_persistida
    else (None, "nenhuma")
)
_cabecalho_dashboard(_contexto(pacote, persistido, fechamento, planta_selecionada))

secao("Indicadores")
_indicadores(investigacao, fechamento)

principal, lateral = st.columns([2.15, 1])
with principal:
    _grafico_historico(
        pacote,
        periodo=None
        if fechamento is None
        else {"inicio": fechamento["inicio"], "fim": fechamento["fim"]},
        origem=persistido.origem if persistido is not None else None,
    )
with lateral:
    painel_intelligence_desativado()
    _situacao_equipamento(pacote, persistido)

execucao, atalhos = st.columns([1.45, 1])
with execucao:
    _central_investigacoes(investigacao)
with atalhos:
    _acoes_rapidas()

_fechamento_e_importacao(persistido, fechamento, selecao_persistida=selecao_persistida)

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
    if st.button("Ver demonstração com dados incompletos", key="ato2"):
        estado.usar_caso_demo(completo=False)
        st.switch_page("paginas/saude.py")
    for titulo, texto in ESTAGIOS_MODELO:
        st.markdown(f"**{titulo}**")
        st.caption(texto)
    st.caption(
        "A EULER investiga e recomenda verificações. Não comanda nem avalia a segurança da caldeira."
    )
