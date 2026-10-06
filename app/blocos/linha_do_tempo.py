"""Linha do tempo financeira dos fechamentos (D103): só apresenta `euler.linha_do_tempo`.

Gráfico do desvio de cada fechamento com a faixa de incerteza, as ações registradas como
marcas verticais, a tabela com os mesmos valores e a leitura da série. Nenhum número novo:
"por tonelada de vapor" é o mesmo desvio dividido pelo vapor medido no período.
"""

import altair as alt
import pandas as pd
import streamlit as st
from acompanhamento_ui import brl, data
from componentes import md
from graficos import TINTA_SECUNDARIA, _configurar

from euler.formato import num
from euler.linha_do_tempo import linha_do_tempo

# Estado do desvio: cor só como apoio; o nome do estado está na dica e na tabela.
ESTADO = {
    "acima": ("Acima do esperado", "#efbd80"),
    "abaixo": ("Abaixo do esperado", "#9cb5ca"),
    "nao_estabelecido": ("Dentro da incerteza", "#a3a3a3"),
    "sem_faixa": ("Sem faixa de incerteza", "#a3a3a3"),
    None: ("Conta indisponível", "#a3a3a3"),
}
MODOS = {
    "Total do período (R$)": ("desvio_brl", "faixa_brl", "R$ no período"),
    "Por tonelada de vapor (R$/t)": (
        "desvio_por_t_vapor_brl",
        "faixa_por_t_vapor_brl",
        "R$ por t de vapor",
    ),
}


def _rs(v) -> str:
    return "—" if v is None else ("−" if v < 0 else "") + f"R$ {num(abs(v), 2)}"


def _faixa(f, fmt=brl) -> str:
    return "—" if not f else f"{fmt(f[0])} a {fmt(f[1])}"


def _sem_fuso(x) -> pd.Timestamp:
    t = pd.Timestamp(x)
    return t.tz_localize(None) if t.tzinfo else t


def _rotulo(p: dict) -> str:
    return f"#{p['fechamento_id']} · {data(p['inicio'])} a {data(p['fim'])}"


def tabela(ps: list[dict]) -> pd.DataFrame:
    """Uma linha por fechamento, com os valores já calculados (texto pronto para a tela)."""
    return pd.DataFrame(
        [
            {
                "Fechamento": _rotulo(p),
                "Dias": num(p["dias"], 0),
                "Vapor": "—" if p["vapor_t"] is None else f"{num(p['vapor_t'], 0)} t",
                "Consumo": "—"
                if p["consumo_t_t"] is None
                else f"{num(p['consumo_t_t'] * 1000, 1)} kg/t",
                "Custo": brl(p["custo_brl"]),
                "Custo por t de vapor": _rs(p["custo_por_t_vapor_brl"]),
                "Custo por dia": brl(p["custo_por_dia_brl"]),
                "Desvio": brl(p["desvio_brl"]),
                "Faixa do desvio": _faixa(p["faixa_brl"]),
                "Situação": ESTADO[p["estado"]][0],
                "Qualidade da conta": p["qualidade"],
                "Ações no período": "; ".join(x["descricao"] for x in p["acoes"]) or "—",
            }
            for p in ps
        ]
    )


def dados_grafico(ps: list[dict], campo: str, campo_faixa: str) -> pd.DataFrame:
    """Só fechamentos com o valor escolhido; os demais ficam fora do gráfico (sem zero)."""
    linhas = []
    for p in ps:
        v = p[campo]
        if v is None:
            continue
        ini, fim = _sem_fuso(p["inicio"]), _sem_fuso(p["fim"])
        f = p[campo_faixa]
        fmt = brl if campo == "desvio_brl" else _rs
        rotulo, cor = ESTADO[p["estado"]]
        linhas.append(
            {
                "inicio": ini,
                "fim": fim,
                "meio": ini + (fim - ini) / 2,
                "valor": float(v),
                "baixo": None if not f else float(f[0]),
                "alto": None if not f else float(f[1]),
                "fechamento": _rotulo(p),
                "desvio": fmt(v),
                "faixa": _faixa(f, fmt),
                "situacao": rotulo,
                "qualidade": p["qualidade"],
                "cor": cor,
            }
        )
    return pd.DataFrame(linhas)


def grafico(ps: list[dict], campo: str, campo_faixa: str, titulo: str) -> bool:
    df = dados_grafico(ps, campo, campo_faixa)
    if df.empty:
        return False
    df = df.astype({"baixo": float, "alto": float})
    acoes = _acoes(ps)
    datas = [df.inicio.min(), df.fim.max(), *([] if acoes.empty else acoes.data)]
    x = alt.X(
        "inicio:T",
        title=None,
        scale=alt.Scale(domain=[min(datas), max(datas)]),
        axis=alt.Axis(format="%d/%m", tickCount=6, grid=False, labelOverlap=True),
    )
    y = alt.Y("valor:Q", title=titulo, axis=alt.Axis(tickCount=4, format=",.0f"))
    dicas = [
        alt.Tooltip("fechamento:N", title="Fechamento"),
        alt.Tooltip("desvio:N", title="Desvio"),
        alt.Tooltip("faixa:N", title="Faixa"),
        alt.Tooltip("situacao:N", title="Situação"),
        alt.Tooltip("qualidade:N", title="Qualidade da conta"),
    ]
    base = alt.Chart(df)
    camadas = [
        alt.Chart(pd.DataFrame({"valor": [0.0]}))
        .mark_rule(color=TINTA_SECUNDARIA, strokeWidth=1)
        .encode(y="valor:Q"),
        base.mark_rule(color="#d5dce2", strokeWidth=1.5).encode(
            x="meio:T", y="baixo:Q", y2="alto:Q", tooltip=dicas
        ),
        base.mark_rule(strokeWidth=3).encode(
            x=x, x2="fim:T", y=y, color=alt.Color("cor:N", scale=None, legend=None), tooltip=dicas
        ),
        base.mark_point(filled=True, size=60, opacity=1).encode(
            x=alt.X("meio:T", title=None),
            y=y,
            color=alt.Color("cor:N", scale=None, legend=None),
            tooltip=dicas,
        ),
    ]
    if not acoes.empty:
        camadas.append(
            alt.Chart(acoes)
            .mark_rule(color=TINTA_SECUNDARIA, strokeDash=[4, 4], strokeWidth=1.5)
            .encode(
                x="data:T",
                tooltip=[
                    alt.Tooltip("rotulo:N", title="Ação registrada"),
                    alt.Tooltip("avaliacao:N", title="Avaliação"),
                ],
            )
        )
    st.altair_chart(_configurar(alt.layer(*camadas).properties(height=240)), width="stretch")
    return True


def _acoes(ps: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "data": _sem_fuso(x["data"]),
                "rotulo": f"{data(x['data'])} · {x['descricao']}",
                "avaliacao": x["avaliacao"] or "Ainda não avaliada",
            }
            for p in ps
            for x in p["acoes"]
        ]
    )


def renderizar(a, equip_id: str) -> None:
    """Seção completa: leitura da série, gráfico do desvio e tabela dos fechamentos."""
    lt = linha_do_tempo(a, equip_id)
    ps = lt["periodos"]
    st.markdown("### Linha do tempo dos fechamentos")
    st.caption(
        "Cada fechamento gravado, em ordem: o desvio apareceu agora, está se repetindo ou "
        "mudou depois de uma ação? Valores preservados de cada fechamento."
    )
    st.markdown(md("\n".join(f"- {frase}" for frase in lt["leitura"])))
    if not ps:
        return
    modo = st.radio(
        "Mostrar o desvio",
        list(MODOS),
        horizontal=True,
        key=f"lt_modo_{equip_id}",
        help="Períodos com duração ou produção diferentes se comparam melhor por tonelada "
        "de vapor.",
    )
    campo, campo_faixa, titulo = MODOS[modo]
    if grafico(ps, campo, campo_faixa, titulo):
        fora = [p for p in ps if p[campo] is None]
        st.caption(
            "Cada segmento é o desvio de um fechamento (custo consumido − esperado); a barra "
            "vertical é a faixa de incerteza. Âmbar: acima do esperado além da incerteza; azul: "
            "abaixo; cinza: dentro da incerteza ou sem faixa. Linhas tracejadas: ações "
            "registradas. Os mesmos valores estão na tabela abaixo."
            + (
                f" {len(fora)} fechamento(s) sem esse valor ficam fora do gráfico, sem zero."
                if fora
                else ""
            )
        )
    else:
        st.info("Nenhum fechamento tem esse valor calculado. Veja os motivos na tabela abaixo.")
    with st.expander("Tabela dos fechamentos", expanded=len(ps) <= 3):
        st.dataframe(tabela(ps), hide_index=True, width="stretch")
        st.caption(
            "Qualidade da conta: completa (preço e faixa), preço incompleto, sem faixa ou "
            "conta indisponível. Custo atribuído ao consumo não é pagamento confirmado."
        )
