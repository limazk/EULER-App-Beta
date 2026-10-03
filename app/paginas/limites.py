"""Tela Dados e limites: o que dá e o que não dá para concluir, e por quê (T11)."""

import estado
import pandas as pd
import streamlit as st
from componentes import cabecalho, cartao, proximo_passo
from formatacao import COLUNAS_RESUMO, SITUACAO_PERIODO, linhas_por_periodo

from euler.capacidades import avaliar
from euler.direto import balanco_direto
from euler.fluxos import balanco_por_vazoes, fluxo_entalpia_vapor
from euler.formato import num, plural
from euler.periodos import periodos_entre_estoques, resumir_periodo
from euler.planta import mapear_planta
from euler.tipos import AnaliseBloqueada

cabecalho(
    "Dados e limites",
    "A EULER começa perguntando **o que esta planta tem?** e monta as rotas físicas "
    "compatíveis com os sinais disponíveis. Quando uma rota não fecha, procura outra forma "
    "fisicamente válida; o que continuar ausente não vira zero nem hipótese escondida.",
    "Passo 3 de 6",
)

ICONE = {
    "habilitada": ":material/check_circle:",
    "parcial": ":material/contrast:",
    "bloqueada": ":material/block:",
}
ROTULO = {"habilitada": "Dá para concluir", "parcial": "Dá, com limites", "bloqueada": "Bloqueada"}


def qualidade(pacote) -> None:
    """Resumo dos avisos de qualidade (a lista completa fica em Importar dados)."""
    avisos = pacote.tabela_avisos()
    n = avisos["Gravidade"].value_counts()
    with cartao("qualidade"):
        st.markdown(
            ":material/fact_check: **Qualidade dos registros:** "
            f"{plural(int(n.get('Erro', 0)), 'erro', 'erros')} · "
            f"{plural(int(n.get('Atenção', 0)), 'aviso de atenção', 'avisos de atenção')} · "
            f"{plural(int(n.get('Informação', 0)), 'informação', 'informações')}. "
            "Nada foi corrigido nem preenchido em silêncio."
        )
        atencao = avisos[avisos["Gravidade"].isin(["Erro", "Atenção"])]
        if len(atencao):
            st.markdown(
                "\n".join(f"- {linha.Tabela}: {linha.Aviso}" for linha in atencao.itertuples())
            )
        st.page_link(
            "paginas/importar.py",
            label="Ver todos os avisos em Importar dados",
            icon=":material/list_alt:",
        )


def _capacidade_completa(c) -> None:
    """Análise bloqueada ou com limites: mostra por quê e o que fazer para liberar."""
    with cartao(f"cap-{c.id}"):
        cabeca, situacao = st.columns([4, 1])
        cabeca.markdown(f"**{c.nome}**  \n{c.pergunta}")
        cor = "red" if c.situacao == "bloqueada" else "orange"
        situacao.markdown(f":{cor}-badge[{ICONE[c.situacao]} {ROTULO[c.situacao]}]")
        if c.motivos:
            st.markdown("**Por quê:**\n" + "\n".join(f"- {m}" for m in c.motivos))
        if c.o_que_fazer:
            st.markdown("**Para liberar:**\n" + "\n".join(f"- {o}" for o in c.o_que_fazer))


def mapa_adaptativo(pacote) -> None:
    """Mostra primeiro o que já é possível fazer com a instrumentação existente."""
    perfil = mapear_planta(pacote)
    st.markdown("### O que esta planta tem?")
    st.caption(
        "O motor escolhe rotas por pergunta física. 'Disponível' quer dizer que os ingredientes "
        "mínimos existem; cada cálculo ainda confere cobertura, simultaneidade e coerência física."
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Sinais reconhecidos", len(perfil.sinais), border=True)
    m2.metric("Rotas com sinais presentes", len(perfil.disponiveis), border=True)
    m3.metric(
        "Rotas parciais",
        sum(r.situacao == "parcial" for r in perfil.rotas),
        border=True,
    )
    m4.metric("Tags ainda sem mapa", len(perfil.nao_mapeados), border=True)

    disponiveis = [r for r in perfil.rotas if r.situacao == "disponivel"]
    if disponiveis:
        with cartao("rotas-adaptativas"):
            st.markdown("**Caminhos candidatos — ainda sujeitos à validação dos dados:**")
            for rota in disponiveis:
                st.markdown(
                    f"- **{rota.nome}** · rota: *{rota.alternativa}*  \n"
                    f"  {rota.pergunta}  \n"
                    f"  :gray[Usando: {', '.join(rota.usando) or 'dados observados'}]"
                )

    diario = pacote.dados("diario")
    if diario is not None and perfil.rota("entalpia_vapor").situacao == "disponivel":
        try:
            fluxo = fluxo_entalpia_vapor(diario)
            st.markdown("#### Física já extraída do lado do vapor")
            a, b, c = st.columns(3)
            a.metric(
                "Fluxo médio de entalpia do vapor", f"{num(fluxo.media_mw, 1)} MW", border=True
            )
            b.metric("Leituras válidas", fluxo.n, border=True)
            c.metric("Cobertura de leituras", f"{100 * fluxo.cobertura_leituras:.0f}%", border=True)
            st.caption(fluxo.nota)
            if fluxo.hipoteses:
                st.caption("Hipóteses: " + "; ".join(fluxo.hipoteses) + ".")
        except AnaliseBloqueada as erro:
            st.info(f"O lado do vapor está parcialmente observável: {erro.motivo}")

    rota_eta = perfil.rota("eficiencia_direta")
    if (
        diario is not None
        and rota_eta.situacao == "disponivel"
        and rota_eta.alternativa.startswith("historiador")
    ):
        try:
            b = balanco_por_vazoes(diario)
            st.markdown("#### Balanço disponível pelo historiador")
            e1, e2, e3 = st.columns(3)
            e1.metric(
                "Conversão combustível → vapor (estimativa)",
                f"{100 * b.eficiencia:.1f}%",
                border=True,
            )
            e2.metric("Cobertura comum", f"{100 * b.cobertura:.0f}%", border=True)
            e3.metric("Intervalos usados", b.intervalos_usados, border=True)
            st.caption(b.nota)
            if b.intervalos_pulados:
                st.caption(
                    f"{b.intervalos_pulados} intervalo(s) excluído(s) por lacuna, condição "
                    "inválida ou mudança de estado. " + "; ".join(b.motivos_exclusao)
                )
            if b.eficiencia > 1:
                st.warning(
                    "Resultado acima de 100%: conferir base calorífica, fronteira e medições."
                )
            if b.hipoteses:
                st.caption("Hipóteses: " + "; ".join(b.hipoteses) + ".")
        except AnaliseBloqueada as erro:
            st.info(f"A rota por vazões existe, mas este recorte ainda não fecha: {erro.motivo}")

    if perfil.nao_mapeados:
        with st.expander("Tags encontradas que a EULER ainda não sabe interpretar"):
            st.write(", ".join(perfil.nao_mapeados))
            st.caption(
                "Essas colunas continuam preservadas no arquivo original. A EULER não atribui "
                "unidade ou significado físico sem um mapa explícito."
            )

    parciais = [r for r in perfil.rotas if r.situacao == "parcial"]
    if parciais:
        with st.expander("O menor dado adicional que abre novas rotas"):
            for rota in parciais:
                st.markdown(
                    f"**{rota.nome}** · melhor rota atual: *{rota.alternativa}*  \n"
                    f"Já temos: {', '.join(rota.usando) or '—'}  \n"
                    f"Falta: {', '.join(rota.faltam) or '—'}"
                )
                if rota.nota:
                    st.caption(rota.nota)


def mostrar(pacote) -> None:
    mapa_adaptativo(pacote)
    st.markdown("### Verificações do fluxo estruturado atual")
    caps = avaliar(pacote)
    contagem = {s: sum(c.situacao == s for c in caps) for s in ROTULO}
    m1, m2, m3 = st.columns(3)
    m1.metric("Análises liberadas", contagem["habilitada"], border=True)
    m2.metric("Com limites", contagem["parcial"], border=True)
    m3.metric("Bloqueadas", contagem["bloqueada"], border=True)
    qualidade(pacote)

    atencao = [c for c in caps if c.situacao != "habilitada"]
    if atencao:
        st.markdown("### Precisa de dados para concluir")
        for c in atencao:
            _capacidade_completa(c)

    liberadas = [c for c in caps if c.situacao == "habilitada"]
    if liberadas:
        st.markdown("### Liberadas com estes dados")
        with cartao("liberadas"):
            metade = (len(liberadas) + 1) // 2
            for coluna, grupo in zip(
                st.columns(2, gap="large"), (liberadas[:metade], liberadas[metade:]), strict=True
            ):
                coluna.markdown(
                    "\n\n".join(
                        f":green[{ICONE['habilitada']}] **{c.nome}**  \n:gray[{c.pergunta}]"
                        for c in grupo
                    )
                )

    with st.expander("Detalhes técnicos: equações e decisões de cada análise"):
        st.markdown(
            "Itens E (equações) de `docs/fisica/fisica_para_revisao.md` e propostas D de "
            "`docs/gestao/decisoes.md`, todos em revisão.\n\n"
            + "\n".join(f"- {c.nome}: {c.referencia}" for c in caps if c.referencia)
        )

    periodos = periodos_entre_estoques(pacote)
    if periodos:
        st.caption(
            f"{plural(len(periodos), 'período', 'períodos')} entre medições de estoque, de "
            f"{periodos[0][0]:%d/%m/%Y} a {periodos[-1][1]:%d/%m/%Y}."
        )


@st.cache_data(show_spinner="Calculando período a período…", max_entries=16)
def _linhas_por_periodo(assinatura: str, _pacote) -> list[dict]:
    """Guardada pela assinatura dos dados (arquivos + altitude): voltar a esta tela não
    recalcula as semanas."""
    return linhas_por_periodo(_pacote)


def por_periodo(pacote) -> None:
    periodos = periodos_entre_estoques(pacote)
    if not periodos:
        return
    st.markdown("### Período a período")
    st.caption(
        "Cada linha vai de uma medição de estoque à seguinte. **Com limites**: falta a "
        "incerteza de algum instrumento ou a perda nos gases; **Não dá para concluir**: falta a "
        "eficiência ou o consumo. O motivo de cada um está em “Ver detalhes de cada período”."
    )
    linhas = _linhas_por_periodo(estado.assinatura(), pacote)
    resumo = pd.DataFrame(linhas)[list(COLUNAS_RESUMO)]
    resumo["Situação"] = resumo["Situação"].map(
        lambda s: f":{SITUACAO_PERIODO.get(s, 'gray')}-badge[{s}]"
    )
    st.table(resumo, hide_index=True, border="horizontal")
    with st.expander("Ver detalhes de cada período"):
        detalhes = pd.DataFrame(linhas).drop(columns=["Eficiência", "Situação"])
        # tabela simples: quebra o texto e mostra o motivo inteiro
        st.table(detalhes, hide_index=True, border="horizontal")
        st.markdown(
            "**Como ler as colunas de eficiência.** A **eficiência direta** supõe que o "
            "combustível queimado tem a qualidade do recebido no período. A coluna "
            "**Eficiência conforme o pátio** mostra os limites possíveis conforme o uso do pátio "
            "(quanto maior o estoque perto do consumido, mais larga a faixa). São cenários de "
            "contabilidade do pátio, não intervalo de confiança nem desempenho validado: um "
            "limite acima de 100% menos a perda nos gases calculada para o mesmo período (mesma "
            "fronteira e base PCI) é incompatível com ela e só mostra quanto o pátio pode pesar "
            "no resultado. Os limites não são cortados."
        )


@st.cache_data(show_spinner="Conferindo as análises complementares…", max_entries=32)
def _detalhes_fisicos(assinatura: str, inicio, fim, _pacote) -> dict:
    """Organiza resultados e bloqueios do motor; não calcula indicadores na tela."""
    r = resumir_periodo(_pacote, inicio, fim)
    b = balanco_direto(r)
    purga = getattr(b, "energia_purga_gj", None)
    return {
        "regimes": getattr(r, "regimes_presentes", ()),
        "apto_carga": getattr(r, "apto_baseline_carga", False),
        "regime_gases": r.bloqueios.get("regime_indireto"),
        "purga_gj": None if purga is None else purga.valor,
        "purga_pct": getattr(b, "perda_purga_pct_pci", None),
        "bloqueio_purga": r.bloqueios.get("purga"),
        "ua": getattr(r, "ua_economizador_mw_k", None),
        "q": getattr(r, "q_economizador_mw", None),
        "bloqueio_ua": r.bloqueios.get("ua_economizador"),
    }


def novas_analises(pacote) -> None:
    periodos = periodos_entre_estoques(pacote)
    if not periodos:
        return
    with st.expander("Novas análises físicas · em revisão"):
        st.markdown(
            "**Regime de operação, energia da purga e transferência no economizador.** "
            "Cada resultado depende das medições do período. Um campo sem dados permanece "
            "sem resultado; não é tratado como zero."
        )
        indice = st.selectbox(
            "Período destas análises",
            range(len(periodos)),
            format_func=lambda i: f"{periodos[i][0]:%d/%m/%Y} a {periodos[i][1]:%d/%m/%Y}",
            key="periodo_novas_analises",
        )
        d = _detalhes_fisicos(estado.assinatura(), *periodos[indice], pacote)
        rotulos = {
            "estavel": "estável",
            "transitorio": "transitório",
            "partida": "partida",
            "parada": "parada",
            "nao_informado": "não informado",
        }
        regimes = ", ".join(rotulos.get(x, x.replace("_", " ")) for x in d["regimes"])
        st.markdown(f"**Regime registrado:** {regimes or 'não informado'}.")
        st.caption(
            "Regime elegível para a referência por carga; os demais pré-requisitos "
            "são verificados na Saúde da caldeira."
            if d["apto_carga"]
            else "Este período não é elegível para a referência por carga: ela exige "
            "regime explicitamente estável em todo o período."
        )
        if d["regime_gases"] is not None:
            st.warning(d["regime_gases"].motivo)
        purga, economizador = st.columns(2, gap="large")
        with purga:
            st.markdown("#### Energia da purga")
            if d["purga_gj"] is None:
                bloqueio = d["bloqueio_purga"]
                st.info(
                    bloqueio.motivo
                    if bloqueio is not None
                    else "Não calculável: faltam massa purgada, pressão própria do ponto "
                    "de purga ou condições da água com cobertura válida do período."
                )
            else:
                st.metric("Energia bruta · estimada", f"{num(d['purga_gj'], 3)} GJ")
                if d["purga_pct"] is not None:
                    st.caption(f"Equivale a {num(d['purga_pct'], 2)}% da energia do combustível.")
            st.caption(
                "Número e duração das purgas não determinam sua massa. A estimativa "
                "supõe líquido saturado na pressão informada e não desconta recuperação "
                "de calor. Sua incerteza ainda não foi quantificada."
            )
        with economizador:
            st.markdown("#### Transferência no economizador")
            if d["ua"] is None:
                bloqueio = d["bloqueio_ua"]
                st.info(
                    bloqueio.motivo
                    if bloqueio is not None
                    else "Não calculável: são necessárias vazão e pressão da água, "
                    "temperaturas de entrada e saída da água e dos gases, com medições "
                    "simultâneas completas e regime estável."
                )
            else:
                st.metric("UA aparente · estimado", f"{num(d['ua'], 4)} MW/K")
                if d["q"] is not None:
                    st.caption(f"Calor transferido estimado: {num(d['q'], 3)} MW.")
            st.caption(
                "O UA aparente descreve a transferência de calor, usando uma aproximação "
                "de contracorrente equivalente. Precisa ser interpretado junto com carga "
                "e condições do equipamento; não comprova incrustação ou sujeira. "
                "Sua incerteza ainda não foi quantificada."
            )


pacote = estado.exigir_pacote()
if pacote is not None:
    mostrar(pacote)
    por_periodo(pacote)
    novas_analises(pacote)
    proximo_passo("paginas/investigacao.py", "4. Investigação")
