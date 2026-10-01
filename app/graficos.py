"""Gráficos do app (Altair), seguindo a paleta categórica validada e números em pt-BR.

Cor segue a entidade (fornecedor), nunca a posição: o mesmo fornecedor tem sempre a
mesma cor, mesmo quando o período muda. Até 3 fornecedores a paleta é segura para
daltonismo em qualquer par; acima disso, as tabelas ao lado continuam como apoio.
"""

from __future__ import annotations

import altair as alt
import pandas as pd

CORES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
TINTA_SECUNDARIA = "#52514e"
GRADE = "#e6e5e1"
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
        grafico.configure(locale=LOCALE_PT_BR)
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
        .configure_title(fontSize=14, anchor="start", color="#0b0b0b")
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
    pontos = base.mark_point(size=64, filled=True, stroke="white", strokeWidth=2).encode(
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
