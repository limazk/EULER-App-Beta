"""Tela Dados e limites: o que dá e o que não dá para concluir, e por quê (T11)."""

import estado
import pandas as pd
import streamlit as st

from euler.capacidades import avaliar
from euler.direto import balanco_direto
from euler.formato import num, pct
from euler.investigacao import indireto_periodo
from euler.periodos import periodos_entre_estoques, resumir_periodo
from euler.vapor import P_ATM_NIVEL_DO_MAR_BAR

st.title("Dados e limites")
st.markdown(
    "O que dá e o que não dá para concluir com os dados enviados, **e por quê**. "
    "Quando falta um dado, a análise fica bloqueada: a EULER não completa nada com "
    "porcentagens inventadas."
)

ICONE = {
    "habilitada": ":material/check_circle:",
    "parcial": ":material/contrast:",
    "bloqueada": ":material/block:",
}
ROTULO = {"habilitada": "Dá para concluir", "parcial": "Dá, com limites", "bloqueada": "Bloqueada"}


def mostrar(pacote) -> None:
    caps = avaliar(pacote)
    contagem = {s: sum(c.situacao == s for c in caps) for s in ROTULO}
    m1, m2, m3 = st.columns(3)
    m1.metric("Análises liberadas", contagem["habilitada"])
    m2.metric("Com limites", contagem["parcial"])
    m3.metric("Bloqueadas", contagem["bloqueada"])

    periodos = periodos_entre_estoques(pacote)
    if periodos:
        st.caption(
            f"{len(periodos)} período(s) entre medições de estoque, de "
            f"{periodos[0][0]:%d/%m/%Y} a {periodos[-1][1]:%d/%m/%Y}."
        )

    for c in caps:
        with st.container(border=True):
            cabeca, situacao = st.columns([4, 1])
            cabeca.markdown(f"**{c.nome}**  \n{c.pergunta}")
            situacao.markdown(f"{ICONE[c.situacao]} {ROTULO[c.situacao]}")
            if c.motivos:
                st.markdown("**Por quê:**\n" + "\n".join(f"- {m}" for m in c.motivos))
            if c.o_que_fazer:
                st.markdown("**Para liberar:**\n" + "\n".join(f"- {o}" for o in c.o_que_fazer))


def _com_incerteza(valor: float, incerteza: float | None, fmt, orcamento=None) -> str:
    """Valor ± U; sem incerteza completa, diz isso (nunca mostra ± 0, auditoria A3)."""
    if incerteza is not None:
        return f"{fmt(valor)} ± {fmt(incerteza)}"
    if orcamento is not None and orcamento.faltam:
        return f"{fmt(valor)} (incerteza incompleta)"
    return fmt(valor)


def _faixa_patio(cenarios: dict[str, float] | None) -> str:
    """Limites da eficiência pelos cenários do pátio (D38)."""
    if not cenarios or "minimo" not in cenarios or "maximo" not in cenarios:
        return "—"
    return f"{pct(cenarios['minimo'])} a {pct(cenarios['maximo'])}"


def por_periodo(pacote) -> None:
    periodos = periodos_entre_estoques(pacote)
    if not periodos:
        return
    st.markdown("### Período a período")
    st.caption(
        "Cada linha vai de uma medição de estoque à seguinte. ✕ = não dá para concluir "
        'naquele período; o motivo está na última coluna. "Incerteza incompleta": falta '
        "cadastrar a incerteza de algum instrumento usado no cálculo (ver Faixa de incerteza "
        "da eficiência, acima). A eficiência direta supõe que o "
        "combustível queimado tem a qualidade do recebido no período; a coluna seguinte mostra "
        "os limites possíveis conforme o uso do pátio (quanto maior o estoque perto do "
        "consumido, mais larga a faixa). São cenários de contabilidade do pátio, não intervalo "
        "de confiança nem desempenho validado: um limite acima de 100% menos a perda nos gases "
        "calculada para o mesmo período (mesma fronteira e base PCI) é incompatível com ela e "
        "só mostra quanto o pátio pode pesar no resultado. Os limites não são cortados."
    )
    p_gases = pacote.p_atm_bar or P_ATM_NIVEL_DO_MAR_BAR
    linhas = []
    for inicio, fim in periodos:
        r = resumir_periodo(pacote, inicio, fim)
        b = balanco_direto(r)
        ind = indireto_periodo(r, p_gases)
        bloqueios = [x.motivo for x in b.bloqueios] + (
            [ind.bloqueio.motivo] if ind.bloqueio else []
        )
        linhas.append(
            {
                "Período": f"{inicio:%d/%m} a {fim:%d/%m}",
                "Vapor (t)": "✕" if r.vapor_t is None else num(r.vapor_t.valor, 0),
                "Combustível (t)": "✕"
                if r.combustivel_kg is None
                else num(r.combustivel_kg.valor / 1000, 0),
                "Eficiência direta": "✕"
                if b.eficiencia is None
                else _com_incerteza(
                    b.eficiencia.valor, b.eficiencia.incerteza, pct, b.eficiencia.orcamento
                ),
                "Estoque / consumido": "—"
                if r.fracao_estoque is None
                else pct(r.fracao_estoque, 0),
                "Eficiência conforme o pátio": _faixa_patio(b.eficiencia_cenarios),
                "Perda nos gases": "✕"
                if ind.resultado is None
                else f"{num(ind.resultado.perda_pct, 1)}% do PCI",
                "Por que não dá": " ".join(dict.fromkeys(bloqueios)) or "—",
            }
        )
    # tabela simples: quebra o texto e mostra o motivo inteiro
    st.table(pd.DataFrame(linhas).set_index("Período"))


pacote = estado.exigir_pacote()
if pacote is not None:
    mostrar(pacote)
    por_periodo(pacote)
