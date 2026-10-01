"""Tela Dados e limites: o que dá e o que não dá para concluir, e por quê (T11)."""

import estado
import pandas as pd
import streamlit as st
from componentes import cabecalho, cartao, proximo_passo

from euler.capacidades import avaliar
from euler.direto import balanco_direto
from euler.formato import num, pct, plural
from euler.investigacao import indireto_periodo
from euler.periodos import periodos_entre_estoques, resumir_periodo
from euler.vapor import P_ATM_NIVEL_DO_MAR_BAR

cabecalho(
    "Dados e limites",
    "O que dá e o que não dá para concluir com os dados enviados, **e por quê**. "
    "Quando falta um dado, a análise fica bloqueada: a EULER não completa nada com "
    "porcentagens inventadas.",
    "Passo 2 de 5",
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


def mostrar(pacote) -> None:
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

    periodos = periodos_entre_estoques(pacote)
    if periodos:
        st.caption(
            f"{plural(len(periodos), 'período', 'períodos')} entre medições de estoque, de "
            f"{periodos[0][0]:%d/%m/%Y} a {periodos[-1][1]:%d/%m/%Y}."
        )


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
        "cadastrar a incerteza de algum instrumento usado no cálculo (ver acima)."
    )
    with st.expander("Como ler as colunas de eficiência"):
        st.markdown(
            "A **eficiência direta** supõe que o combustível queimado tem a qualidade do "
            "recebido no período. A coluna **Eficiência conforme o pátio** mostra os limites "
            "possíveis conforme o uso do pátio (quanto maior o estoque perto do consumido, mais "
            "larga a faixa). São cenários de contabilidade do pátio, não intervalo de confiança "
            "nem desempenho validado: um limite acima de 100% menos a perda nos gases calculada "
            "para o mesmo período (mesma fronteira e base PCI) é incompatível com ela e só "
            "mostra quanto o pátio pode pesar no resultado. Os limites não são cortados."
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
    proximo_passo("paginas/investigacao.py", "3. Investigação")
