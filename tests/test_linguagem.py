"""Linguagem de fábrica (D64): nenhuma tela nem relatório cita nome de arquivo, nome de
variável ou código de equação/decisão fora de "Detalhes técnicos".

O teste percorre a árvore de cada tela (com os dois atos do demo, o exemplo com problemas,
os modelos e sem dados) e os relatórios do demo, e procura os três padrões no texto que o
usuário vê. Conteúdo dentro de um expansor cujo título começa com "Detalhes técnicos" fica
de fora: é lá que esses nomes podem aparecer.
"""

from __future__ import annotations

import re
from contextlib import suppress
from html.parser import HTMLParser
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest
from streamlit.testing.v1.element_tree import Block, Expander

from euler.investigacao import investigar
from euler.io import importar_pasta
from euler.periodos import periodos_entre_estoques
from euler.relatorio import gerar_html
from euler.vapor import p_atm_por_altitude_bar

RAIZ = Path(__file__).resolve().parents[1]
APP = RAIZ / "app" / "main.py"
TECNICO = "Detalhes técnicos"

PROIBIDOS = {
    "nome de arquivo": re.compile(r"\b[\w-]+\.(?:csv|xlsx|md|py|json)\b"),
    "nome de variável": re.compile(r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b"),
    "código de equação ou decisão": re.compile(r"\b[EDMQT]\d{1,2}\b"),
}
ICONE = re.compile(r":material/[a-z0-9_]+:")
"""Ícones do Streamlit (`:material/check_circle:`) viram desenho na tela, não texto."""


def _texto(valor) -> list[str]:
    if isinstance(valor, str):
        return [valor]
    if isinstance(valor, pd.DataFrame):
        return [str(c) for c in valor.columns] + [str(v) for v in valor.to_numpy().ravel()]
    if isinstance(valor, (list, tuple)):
        return [str(v) for v in valor]
    return []


def textos_visiveis(no) -> list[str]:
    """Textos de um nó da tela e dos filhos, sem o que está em "Detalhes técnicos"."""
    if isinstance(no, Expander) and str(no.label).startswith(TECNICO):
        return []
    saida = []
    # num seletor, o usuário vê as opções já formatadas; o valor é o código interno
    atributos = ("label", "options") if hasattr(no, "options") else ("label", "value")
    for atributo in atributos:
        # elementos sem o atributo, ou cujo valor depende de estado que não existe aqui
        with suppress(AttributeError, KeyError, IndexError, TypeError, ValueError):
            saida += _texto(getattr(no, atributo, None))
    if isinstance(no, Block):
        for filho in no.children.values():
            saida += textos_visiveis(filho)
    return saida


def violacoes(textos: list[str]) -> list[str]:
    achados = []
    for texto in textos:
        texto = ICONE.sub("", texto)
        for nome, padrao in PROIBIDOS.items():
            for m in padrao.finditer(texto):
                achados.append(f"{nome}: {m.group(0)!r} em {texto[:90]!r}")
    return sorted(set(achados))


def _tela(at: AppTest) -> list[str]:
    return textos_visiveis(at.main) + textos_visiveis(at.sidebar)


def _abrir(botao: str | None, paginas: list[str]) -> list[str]:
    at = AppTest.from_file(str(APP), default_timeout=60).run()
    textos = _tela(at)
    if botao:
        at.switch_page("paginas/importar.py").run()
        next(b for b in at.button if b.label.startswith(botao)).click().run()
        textos += _tela(at)
    for pagina in paginas:
        at.switch_page(f"paginas/{pagina}").run()
        assert not at.exception, at.exception
        textos += _tela(at)
        if pagina == "relatorio.py":
            gerar = [b for b in at.button if b.label == "Gerar relatório"]
            if gerar:
                gerar[0].click().run()
                textos += _tela(at)
    return textos


TODAS = [
    "inicio.py", "importar.py", "limites.py", "investigacao.py", "extrato.py",
    "investigacao.py", "relatorio.py", "calculadora.py",
]  # fmt: skip


@pytest.mark.parametrize(
    "botao",
    [None, "Ato 1", "Ato 2", "Exemplo com problemas", "Modelos"],
    ids=["sem dados", "ato 1", "ato 2", "exemplo com problemas", "modelos"],
)
def test_telas_falam_a_lingua_da_fabrica(botao):
    assert violacoes(_abrir(botao, TODAS)) == []


class _SoTexto(HTMLParser):
    def __init__(self):
        super().__init__()
        self.partes: list[str] = []
        self._pular = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("style", "script"):
            self._pular += 1

    def handle_endtag(self, tag):
        if tag in ("style", "script"):
            self._pular -= 1

    def handle_data(self, data):
        if not self._pular:
            self.partes.append(data)


@pytest.mark.parametrize("pasta", ["caso_demo_completo", "caso_demo"])
def test_relatorios_falam_a_lingua_da_fabrica(pasta):
    p = importar_pasta(RAIZ / "demo" / pasta, p_atm_bar=p_atm_por_altitude_bar(1000))
    s = periodos_entre_estoques(p)
    textos = []
    for ref, comp in [((0, 3), (4, 5)), ((0, 3), (6, 6)), ((0, 3), (7, 7)), ((4, 5), (7, 7))]:
        j = investigar(p, (s[ref[0]][0], s[ref[1]][1]), (s[comp[0]][0], s[comp[1]][1]))
        leitor = _SoTexto()
        leitor.feed(gerar_html(j))
        textos += leitor.partes
    assert violacoes(textos) == []


def test_o_detector_acha_os_tres_tipos():
    assert violacoes(["Envie diario.csv", "'umidade_bu_frac' = 38", "Cálculo (E11)"]) == [
        "código de equação ou decisão: 'E11' em 'Cálculo (E11)'",
        "nome de arquivo: 'diario.csv' em 'Envie diario.csv'",
        "nome de variável: 'umidade_bu_frac' em \"'umidade_bu_frac' = 38\"",
    ]
    assert violacoes(["O₂ nos gases; F3 tem o menor preço; R$ 20,05/GJ"]) == []
    assert violacoes([":green[:material/check_circle:] **Qualidade**"]) == []
