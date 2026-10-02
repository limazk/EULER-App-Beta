"""Tela Saúde da caldeira: consumo por tonelada de vapor período a período (D65).

Logo depois de carregar os dados: o consumo de cada período entre medições de estoque, os
eventos registrados e um selo (mudou, estável ou não dá para dizer). Os números vêm de
`euler.saude`, que usa as mesmas contas da Investigação; a tela só arruma.
"""

import estado
import graficos
import pandas as pd
import streamlit as st
from componentes import cabecalho, cartao, proximo_passo
from formatacao import (
    COR_SAUDE,
    SELO_SAUDE,
    SITUACAO_SAUDE,
    texto_consumo,
    variacao_referencia,
)

from euler.formato import num
from euler.saude import avaliar_saude

cabecalho(
    "Saúde da caldeira",
    "Quanto combustível a caldeira gastou para cada tonelada de vapor, período a período, com "
    "os eventos registrados. Se o consumo mudou, um clique leva direto à investigação.",
    "Passo 2 de 6",
)


@st.cache_data(show_spinner="Calculando o consumo período a período…", max_entries=16)
def _saude(assinatura: str, _pacote):
    """Guardada pela assinatura dos dados: voltar a esta tela não recalcula."""
    return avaliar_saude(_pacote)


def _sem_fuso(t: pd.Timestamp) -> pd.Timestamp:
    return t.tz_localize(None)


def _icone_selo(s) -> str:
    if s.selo != "mudou":
        return ":material/check_circle:" if s.selo == "estavel" else ":material/help:"
    sobe = s.comparacao_mudanca is not None and (s.comparacao_mudanca.delta or 0) > 0
    return ":material/trending_up:" if sobe else ":material/trending_down:"


def investigar(s) -> None:
    """Leva os períodos da mudança para a Investigação, já escolhidos."""
    st.session_state["periodos_escolhidos"] = {
        "assinatura": estado.assinatura(),
        "ref": s.referencia,
        "comp": s.mudanca,
    }
    # os controles da Investigação usam esta escolha como valor inicial
    for chave in ("periodo_ref", "periodo_comp"):
        st.session_state.pop(chave, None)
    st.switch_page("paginas/investigacao.py")


def _numeros(s) -> None:
    if s.consumo_referencia is None:
        return
    p = s.periodos
    a, b = s.referencia
    c1, c2 = st.columns(2)
    c1.metric(
        f"Referência · {p[a].inicio:%d/%m} a {p[b].fim:%d/%m}",
        f"{num(s.consumo_referencia.valor, 3)} t/t",
        border=True,
    )
    if s.mudanca is not None and s.comparacao_mudanca is not None:
        cmp = s.comparacao_mudanca
        a, b = s.mudanca
        c2.metric(
            f"Mudança · {p[a].inicio:%d/%m} a {p[b].fim:%d/%m}",
            f"{num(cmp.comparacao, 3)} t/t",
            f"{100 * cmp.delta / cmp.referencia:+.1f}%".replace(".", ","),
            delta_color="inverse",
            border=True,
        )


def _grafico(s) -> None:
    linhas = []
    for p in s.periodos:
        u = None if p.consumo is None else p.consumo.incerteza
        valor = None if p.consumo is None else p.consumo.valor
        linhas.append(
            {
                "inicio": _sem_fuso(p.inicio),
                "fim": _sem_fuso(p.fim),
                "meio": _sem_fuso(p.inicio + (p.fim - p.inicio) / 2),
                "valor": valor,
                "baixo": None if u is None else valor - u,
                "alto": None if u is None else valor + u,
                "periodo": f"{p.inicio:%d/%m} a {p.fim:%d/%m}",
                "texto": texto_consumo(p),
                "situacao": SITUACAO_SAUDE[p.estado],
            }
        )
    df = pd.DataFrame(linhas).astype({"valor": float, "baixo": float, "alto": float})
    if df["valor"].isna().all():
        st.info("Nenhum período tem o consumo calculado; os motivos estão na tabela abaixo.")
        return
    faixas = []
    if s.referencia is not None:
        a, b = s.referencia
        faixas.append((df["inicio"][a], df["fim"][b], "Referência", graficos.FAIXA_REFERENCIA))
    if s.mudanca is not None:
        a, b = s.mudanca
        faixas.append((df["inicio"][a], df["fim"][b], "Mudança", graficos.FAIXA_COMPARACAO))
    eventos = pd.DataFrame(
        [
            {
                "instante": _sem_fuso(e["instante"]),
                "dia": f"{e['instante']:%d/%m}",
                "n": str(i),
                "tipo": e["tipo"],
                "descricao": e["descricao"],
            }
            for i, e in enumerate(s.eventos, start=1)
        ],
        columns=["instante", "dia", "n", "tipo", "descricao"],
    )
    # eventos do mesmo dia ficam no mesmo lugar do eixo: um rótulo só ("3 · 4")
    eventos["numero"] = eventos.groupby("dia")["n"].transform(" · ".join)
    referencia = None if s.consumo_referencia is None else s.consumo_referencia.valor
    st.altair_chart(graficos.consumo_por_periodo(df, faixas, eventos, referencia), width="stretch")
    st.caption(
        "Traço azul: consumo médio de cada período (combustível queimado ÷ vapor produzido), "
        "origem **estimado** a partir das medições; traço vertical: incerteza (k = 2). Linha "
        "pontilhada: a referência. Linhas tracejadas numeradas: eventos registrados. Período "
        "sem traço: não dá para calcular (motivo na tabela)."
    )


def _eventos(s) -> None:
    if not s.eventos:
        st.caption("Nenhum evento registrado (limpeza, manutenção, troca de fornecedor…).")
        return
    st.markdown(
        "\n".join(
            f"{i}. **{e['instante']:%d/%m %H:%M}** · {e['tipo']}: {e['descricao']}"
            for i, e in enumerate(s.eventos, start=1)
        )
    )


def _tabela(s) -> None:
    linhas = [
        {
            "Período": f"{p.inicio:%d/%m} a {p.fim:%d/%m}",
            "Consumo (t/t)": texto_consumo(p),
            "Em relação à referência": variacao_referencia(p),
            "Situação": (
                f":{COR_SAUDE.get(p.estado, 'gray')}-badge[{SITUACAO_SAUDE[p.estado]}]"
                + ("" if p.consumo is not None or not p.motivo else f" {p.motivo}")
            ),
        }
        for p in s.periodos
    ]
    st.table(pd.DataFrame(linhas), hide_index=True, border="horizontal")


def _comparacao_por_carga(s) -> None:
    """Exibe a referência por carga já calculada pelo motor, sem alterar o selo."""
    with st.expander("Comparação por carga · análise complementar"):
        st.markdown(
            "**A produção de vapor ajuda a explicar a mudança de consumo?** Esta camada "
            "compara o combustível com uma referência ajustada à produção de vapor. "
            "O resultado é complementar: o selo acima continua usando a comparação "
            "com a incerteza das medições."
        )
        modelo = getattr(s, "baseline_carga", None)
        if modelo is None:
            st.info(
                "Não há uma referência por carga calculável com estes dados. O ajuste "
                "exige pelo menos três períodos de referência explicitamente estáveis, "
                "com consumo de combustível e vapor válidos e mais de uma carga observada."
            )
            return
        st.caption(
            f"Referência estimada com {modelo.n} períodos. Faixa observada: "
            f"{num(modelo.carga_min_t_h, 2)} a {num(modelo.carga_max_t_h, 2)} t/h de vapor. "
            "O motor não usa essa relação fora da faixa observada."
        )
        residuos = getattr(s, "residuos_carga", {})
        linhas = []
        for p in s.periodos:
            if p.estado == "referencia":
                continue
            valor = residuos.get(p.indice)
            linhas.append(
                {
                    "Período": f"{p.inicio:%d/%m} a {p.fim:%d/%m}",
                    "Desvio normalizado · estimado": (
                        "Não calculável" if valor is None else num(valor, 2)
                    ),
                }
            )
        if linhas:
            st.table(pd.DataFrame(linhas), hide_index=True, border="horizontal")
        st.caption(
            "O desvio é expresso em desvios-padrão de previsão, sem unidade: positivo "
            "significa consumo acima da referência por carga; negativo, abaixo. "
            "Não é probabilidade nem prova de uma causa. Sem regime estável, dados "
            "válidos, carga dentro da faixa ou dispersão estimável, o valor não é calculado. "
            "Esta camada ainda não inclui as incertezas instrumentais separadamente "
            "e está em revisão física."
        )


def mostrar(pacote) -> None:
    s = _saude(estado.assinatura(), pacote)
    cor, rotulo = SELO_SAUDE[s.selo]
    with cartao("saude-selo"):
        st.markdown(f"#### :{cor}-badge[{_icone_selo(s)} {rotulo}]")
        st.markdown(f"**{s.frase}**")
        _numeros(s)
        if s.mudanca is not None:
            if st.button(
                "Investigar esta mudança",
                type="primary",
                icon=":material/troubleshoot:",
                key="investigar_mudanca",
            ):
                investigar(s)
        else:
            st.page_link(
                "paginas/investigacao.py",
                label="Escolher os períodos na Investigação",
                icon=":material/troubleshoot:",
            )
    if s.periodos:
        _grafico(s)
        st.markdown("#### Eventos registrados")
        _eventos(s)
        st.markdown("#### Período a período")
        _tabela(s)
        _comparacao_por_carga(s)
    st.caption(
        "Mudou = a diferença para a referência é maior que a incerteza das medições; estável = "
        "fica dentro dela; não dá para dizer = falta o consumo do período ou a incerteza. "
        "Referência: a primeira metade dos períodos (a mesma escolha inicial da Investigação). "
        "O selo diz se o consumo mudou, não por quê: a causa é o que a investigação examina."
    )


pacote = estado.exigir_pacote()
if pacote is not None:
    mostrar(pacote)
    proximo_passo("paginas/limites.py", "3. Dados e limites")
