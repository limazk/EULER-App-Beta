"""Gráficos do app (Altair), seguindo a paleta categórica validada e números em pt-BR.

Cor segue a entidade (fornecedor), nunca a posição: o mesmo fornecedor tem sempre a
mesma cor, mesmo quando o período muda. Até 3 fornecedores a paleta é segura para
daltonismo em qualquer par; acima disso, as tabelas ao lado continuam como apoio.
"""

from __future__ import annotations

import altair as alt
import pandas as pd
from componentes import COR_COMPARACAO, COR_REFERENCIA

# Paleta categórica validada para fundo escuro (validador da paleta, superfície #212121:
# faixa de luminosidade, croma, separação para daltonismo e contraste ≥ 3:1).
CORES = ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300", "#9085e9", "#e66767"]
TINTA = "#ECECEC"
TINTA_SECUNDARIA = "#A3A3A3"
GRADE = "#333333"
SUPERFICIE = "#232323"
LOCALE_PT_BR = {
    "number": {"decimal": ",", "thousands": ".", "grouping": [3], "currency": ["R$ ", ""]},
    "time": {
        "dateTime": "%A, %e de %B de %Y. %X",
        "date": "%d/%m/%Y",
        "time": "%H:%M:%S",
        "periods": ["AM", "PM"],
        "days": ["domingo", "segunda", "terça", "quarta", "quinta", "sexta", "sábado"],
        "shortDays": ["dom", "seg", "ter", "qua", "qui", "sex", "sáb"],
        "months": [
            "janeiro", "fevereiro", "março", "abril", "maio", "junho",
            "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
        ],
        "shortMonths": [
            "jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez",
        ],
    },
}  # fmt: skip


def escala_cores(entidades: list[str]) -> alt.Scale:
    """Uma cor fixa por entidade, na ordem da paleta (sem repetir cores)."""
    dominio = sorted(entidades)[: len(CORES)]
    return alt.Scale(domain=dominio, range=CORES[: len(dominio)])


def _configurar(grafico: alt.Chart) -> alt.Chart:
    return (
        # fundo transparente: o gráfico fica sobre a cor do cartão ou da tela, sem caixa a mais
        grafico.configure(locale=LOCALE_PT_BR, background="transparent")
        .configure_view(stroke=None)
        .configure_axis(
            gridColor=GRADE,
            domainColor=GRADE,
            tickColor=GRADE,
            labelColor=TINTA_SECUNDARIA,
            titleColor=TINTA_SECUNDARIA,
            labelFontSize=12,
            titleFontSize=12,
            titleFontWeight="normal",
        )
        .configure_title(fontSize=14, anchor="start", color=TINTA)
        .configure_legend(labelColor=TINTA_SECUNDARIA, titleColor=TINTA_SECUNDARIA)
    )


def barras_por_fornecedor(
    df: pd.DataFrame, campo: str, titulo: str, rotulo: str, escala: alt.Scale
) -> alt.Chart:
    """Barras horizontais finas, ordenadas do menor para o maior (o mais barato no topo).

    df: colunas fornecedor_id, `campo` (número) e `rotulo` (texto já formatado).
    """
    # ordem explícita: com camadas (barra + texto) o Vega-Lite descarta a ordenação por campo
    ordem = list(df.sort_values(campo)["fornecedor_id"])
    base = alt.Chart(df, title=titulo).encode(
        y=alt.Y("fornecedor_id:N", sort=ordem, title=None),
        x=alt.X(
            f"{campo}:Q",
            title=None,
            axis=alt.Axis(labels=False, ticks=False, grid=False),
            scale=alt.Scale(domain=[0, float(df[campo].max()) * 1.3]),
        ),
        tooltip=[
            alt.Tooltip("fornecedor_id:N", title="Fornecedor"),
            alt.Tooltip(f"{rotulo}:N", title=titulo),
        ],
    )
    barras = base.mark_bar(size=22, cornerRadiusEnd=4).encode(
        color=alt.Color("fornecedor_id:N", scale=escala, legend=None)
    )
    textos = base.mark_text(align="left", dx=6, color=TINTA_SECUNDARIA, fontSize=13).encode(
        text=f"{rotulo}:N"
    )
    return _configurar((barras + textos).properties(height=40 * len(df) + 20))


def linhas_semanais(
    df: pd.DataFrame, campo: str, titulo: str, formato_eixo: str, escala: alt.Scale
) -> alt.Chart:
    """Linhas de 2 px por fornecedor ao longo das semanas, com rótulo direto no fim."""
    base = alt.Chart(df, title=titulo).encode(
        x=alt.X(
            "semana:T", title="Semana (início)", axis=alt.Axis(format="%d/%m", tickCount="week")
        ),
        y=alt.Y(
            f"{campo}:Q",
            title=None,
            axis=alt.Axis(format=formato_eixo),
            scale=alt.Scale(zero=False),
        ),
        color=alt.Color(
            "fornecedor_id:N", scale=escala, legend=alt.Legend(title="Fornecedor", orient="top")
        ),
    )
    linhas = base.mark_line(strokeWidth=2)
    pontos = base.mark_point(size=64, filled=True, stroke=SUPERFICIE, strokeWidth=2).encode(
        tooltip=[
            alt.Tooltip("fornecedor_id:N", title="Fornecedor"),
            alt.Tooltip("semana:T", title="Semana de", format="%d/%m/%Y"),
            alt.Tooltip(f"{campo}:Q", title=titulo, format=formato_eixo.replace("%", ".1%")),
            alt.Tooltip("lotes:Q", title="Lotes"),
        ]
    )
    ultimo = df.sort_values("semana").groupby("fornecedor_id").tail(1)
    rotulos = (
        alt.Chart(ultimo)
        .mark_text(align="left", dx=8, fontSize=12, color=TINTA_SECUNDARIA)
        .encode(x="semana:T", y=f"{campo}:Q", text="fornecedor_id:N")
    )
    return _configurar((linhas + pontos + rotulos).properties(height=300))


# mesmas cores da linha do tempo dos períodos (tela Investigação)
FAIXA_REFERENCIA = COR_REFERENCIA
FAIXA_COMPARACAO = COR_COMPARACAO


def consumo_por_periodo(
    df: pd.DataFrame,
    faixas: list[tuple[pd.Timestamp, pd.Timestamp, str, str]],
    eventos: pd.DataFrame,
    referencia: float | None,
) -> alt.Chart:
    """Consumo por tonelada de vapor de cada período, com incerteza, faixas e eventos.

    df: uma linha por período com `inicio`, `fim`, `meio` (datas sem fuso), `valor` (t/t ou
    NaN quando não há), `baixo`/`alto` (valor ∓ U, NaN sem incerteza) e textos `periodo`,
    `texto` e `situacao` para a dica. Cada período é um traço horizontal de 2 px do início ao
    fim (o consumo é a média do período), com a incerteza na vertical; período sem consumo
    fica vazio. faixas: (início, fim, rótulo, cor) — referência e mudança. eventos: `instante`,
    `numero` (rótulo curto, agrupado por dia), `tipo` e `descricao`. Uma série só: sem
    legenda, o título diz o que é.
    """
    com_valor = df.dropna(subset=["valor"])
    extremos = pd.concat([com_valor["valor"], com_valor["baixo"], com_valor["alto"]]).dropna()
    minimo, maximo = float(extremos.min()), float(extremos.max())
    amplitude = max(maximo - minimo, 0.01)
    eixo_y = alt.Y(
        "valor:Q",
        title=None,
        axis=alt.Axis(format=".3~f"),
        scale=alt.Scale(domain=[minimo - 0.25 * amplitude, maximo + 0.35 * amplitude]),
    )
    eixo_x = alt.X("inicio:T", title=None, axis=alt.Axis(format="%d/%m", tickCount="week"))
    camadas = []
    if faixas:
        bandas = pd.DataFrame(
            [{"inicio": a, "fim": b, "rotulo": r, "cor": c} for a, b, r, c in faixas]
        )
        camadas += [
            alt.Chart(bandas)
            .mark_rect(opacity=0.9)
            .encode(x=eixo_x, x2="fim:T", color=alt.Color("cor:N", scale=None, legend=None)),
            alt.Chart(bandas)
            .mark_text(
                align="left", baseline="top", dx=4, dy=4, color=TINTA_SECUNDARIA, fontSize=12
            )
            .encode(x="inicio:T", y=alt.value(0), text="rotulo:N"),
        ]
    if referencia is not None:
        camadas.append(
            alt.Chart(pd.DataFrame({"valor": [referencia]}))
            .mark_rule(strokeWidth=1, color=TINTA_SECUNDARIA, strokeDash=[2, 2])
            .encode(y=eixo_y)
        )
    if not eventos.empty:
        dica_evento = [
            alt.Tooltip("instante:T", title="Evento", format="%d/%m/%Y %H:%M"),
            alt.Tooltip("tipo:N", title="Tipo"),
            alt.Tooltip("descricao:N", title="O que foi feito"),
        ]
        camadas += [
            alt.Chart(eventos)
            .mark_rule(strokeWidth=1.5, color=TINTA_SECUNDARIA, strokeDash=[5, 3])
            .encode(x="instante:T", tooltip=dica_evento),
            # número no alto, à direita da linha (abaixo dos rótulos das faixas)
            alt.Chart(eventos.drop_duplicates("numero"))
            .mark_text(
                align="left",
                baseline="top",
                dx=4,
                dy=22,
                color=TINTA,
                fontSize=12,
                fontWeight="bold",
            )
            .encode(x="instante:T", y=alt.value(0), text="numero:N", tooltip=dica_evento),
        ]
    dica = [
        alt.Tooltip("periodo:N", title="Período"),
        alt.Tooltip("texto:N", title="Consumo (t/t)"),
        alt.Tooltip("situacao:N", title="Situação"),
    ]
    base = alt.Chart(com_valor)
    camadas += [
        base.mark_rule(strokeWidth=2, color=CORES[0]).encode(x=eixo_x, x2="fim:T", y=eixo_y),
        base.mark_rule(strokeWidth=1.5, color=CORES[0], opacity=0.8).encode(
            x="meio:T", y="baixo:Q", y2="alto:Q"
        ),
        base.mark_point(
            size=64, filled=True, color=CORES[0], stroke=SUPERFICIE, strokeWidth=2
        ).encode(x="meio:T", y=eixo_y, tooltip=dica),
    ]
    return _configurar(
        alt.layer(*camadas).properties(
            title="Combustível por tonelada de vapor (t/t), período a período", height=280
        )
    )


def serie_diaria_com_periodos(
    df: pd.DataFrame,
    titulo: str,
    formato: str,
    faixas: list[tuple[pd.Timestamp, pd.Timestamp, str]],
) -> alt.Chart:
    """Uma série diária (linha de 2 px) com os períodos comparados em faixas de fundo.

    df: colunas `dia` (data) e `valor`. faixas: (início, fim, rótulo) — referência e comparação.
    Uma única série: sem legenda, o título diz o que é.
    """
    cores = [FAIXA_REFERENCIA, FAIXA_COMPARACAO]
    minimo, maximo = float(df["valor"].min()), float(df["valor"].max())
    amplitude = max(maximo - minimo, 1.0)
    bandas = pd.DataFrame(
        [
            {
                "inicio": a.tz_localize(None),
                "fim": b.tz_localize(None),
                "rotulo": r,
                "cor": cores[i % 2],
            }
            for i, (a, b, r) in enumerate(faixas)
        ]
    )
    fundo = (
        alt.Chart(bandas)
        .mark_rect(opacity=0.9)
        .encode(x="inicio:T", x2="fim:T", color=alt.Color("cor:N", scale=None, legend=None))
    )
    rotulos = (
        alt.Chart(bandas)
        .mark_text(align="left", baseline="top", dx=4, dy=4, color=TINTA_SECUNDARIA, fontSize=12)
        .encode(x="inicio:T", y=alt.value(0), text="rotulo:N")
    )
    base = alt.Chart(df).encode(
        x=alt.X("dia:T", title=None, axis=alt.Axis(format="%d/%m", tickCount="week")),
        # folga acima dos dados para os rótulos das faixas não encostarem na linha
        y=alt.Y(
            "valor:Q",
            title=None,
            axis=alt.Axis(format=formato),
            scale=alt.Scale(domain=[minimo - 0.05 * amplitude, maximo + 0.3 * amplitude]),
        ),
    )
    linha = base.mark_line(strokeWidth=2, color=CORES[0])
    pontos = base.mark_point(size=30, filled=True, color=CORES[0]).encode(
        tooltip=[
            alt.Tooltip("dia:T", title="Dia", format="%d/%m/%Y"),
            alt.Tooltip("valor:Q", title=titulo, format=formato),
        ]
    )
    return _configurar((fundo + rotulos + linha + pontos).properties(title=titulo, height=260))
