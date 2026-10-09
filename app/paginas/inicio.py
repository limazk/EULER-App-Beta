"""Dashboard EULER 3.0: contexto, dados sustentados e próximos passos."""

from html import escape

import altair as alt
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

from euler.dia_a_dia import diario_por_dia
from euler.formato import num
from euler.textos import AVISO_PROTOTIPO, ESTAGIOS_MODELO

SERIES_DASHBOARD = {
    "vazao_t_h": ("Vapor · vazão média", "t/h", ".1f"),
    "t_gases_c": ("Temperatura dos gases", "°C", ".0f"),
    "o2_seco_pct": ("O₂ nos gases · base seca", "%", ".1f"),
    "recebido_t": ("Combustível recebido · não é consumo", "t/dia", ".1f"),
}


def _contexto(pacote) -> dict[str, str]:
    """Contexto visível, sem confundir autenticação com conexão de sensores."""
    auth = st.session_state.get("_euler_auth_context") or {}
    memberships = auth.get("memberships") or []
    org = (memberships[0].get("organizations") or {}) if memberships else {}
    persistencia = st.session_state.get("persistencia") or {}
    diario = pacote.dados("diario") if pacote is not None else None

    equipamento = "Não identificado"
    periodo = "Sem período carregado"
    if diario is not None and not diario.empty:
        if "caldeira_id" in diario and diario["caldeira_id"].notna().any():
            equipamento = str(diario["caldeira_id"].dropna().iloc[0])
        instantes = diario.get("instante_observado", pd.Series(dtype="datetime64[ns]"))
        instantes = instantes.dropna()
        if not instantes.empty:
            periodo = f"{instantes.min():%d/%m/%Y} a {instantes.max():%d/%m/%Y}"
    return {
        "organizacao": str(org.get("name") or "Sem organização vinculada"),
        "planta": str(persistencia.get("planta_nome") or "Nenhuma planta selecionada"),
        "equipamento": equipamento,
        "periodo": periodo,
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
            )
        )
        st.html(f'<div class="euler-contexto" aria-label="Contexto atual">{itens}</div>')


def _indicadores(investigacao: dict | None) -> None:
    custo = None
    consumo = None
    proxima = None
    if investigacao:
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


def _grafico_historico(pacote) -> None:
    with cartao("historico-principal"):
        st.markdown("### Histórico operacional")
        if pacote is None:
            chip_status("Sem dados", "indisponivel")
            st.caption("Importe registros para visualizar uma série histórica.")
            return
        diario = diario_por_dia(pacote)
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
        st.caption(
            "Fonte: registros importados nesta sessão. Lacunas permanecem interrompidas; "
            "combustível recebido representa compras, não consumo."
        )


def _situacao_equipamento(pacote) -> None:
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
        st.caption(
            f"{len(diario)} leitura(s) normalizada(s) · {len(avisos)} aviso(s) de erro/atenção. "
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


def _fechamento_e_importacao() -> None:
    a, b = st.columns(2)
    with a, cartao("fechamento-resumo"):
        st.markdown("### Fechamento mensal")
        chip_status("Consultar situação", "neutro")
        st.caption(
            "O dashboard não presume cobertura ou aprovação. Consulte a versão vigente e o histórico."
        )
        st.page_link(
            "paginas/fechamentos.py", label="Abrir fechamentos", icon=":material/arrow_forward:"
        )
    with b, cartao("ultima-importacao"):
        st.markdown("### Última importação")
        arquivos = st.session_state.get("arquivos") or ()
        if not arquivos:
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


pacote = estado.pacote()
investigacao, _ = estado.investigacao_atual() if pacote is not None else (None, "nenhuma")
_cabecalho_dashboard(_contexto(pacote))

secao("Indicadores")
_indicadores(investigacao)

principal, lateral = st.columns([2.15, 1])
with principal:
    _grafico_historico(pacote)
with lateral:
    painel_intelligence_desativado()
    _situacao_equipamento(pacote)

execucao, atalhos = st.columns([1.45, 1])
with execucao:
    _central_investigacoes(investigacao)
with atalhos:
    _acoes_rapidas()

_fechamento_e_importacao()

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
