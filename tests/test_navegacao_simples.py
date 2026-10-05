"""A navegação simples não pode deixar telas ou links existentes inacessíveis."""

import ast
from pathlib import Path

from navegacao import COMPLEMENTARES, PRINCIPAIS, todas_as_paginas
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app"


def test_menu_curto_preserva_todas_as_rotas_sem_duplicar():
    paginas = todas_as_paginas()
    caminhos = [p[0] for p in paginas]
    assert len(PRINCIPAIS) <= 6
    assert len(caminhos) == len(set(caminhos))
    assert set(caminhos) == {f"paginas/{p.name}" for p in (APP / "paginas").glob("*.py")}
    assert any(
        p[0] == "paginas/dados_publicos.py" for grupo in COMPLEMENTARES.values() for p in grupo
    )


def test_links_entre_telas_continuam_registrados():
    rotas = {p[0] for p in todas_as_paginas()}
    for arquivo in APP.rglob("*.py"):
        for no in ast.walk(ast.parse(arquivo.read_text(encoding="utf-8"))):
            if (
                isinstance(no, ast.Call)
                and isinstance(no.func, ast.Attribute)
                and no.func.attr in {"page_link", "switch_page"}
                and no.args
                and isinstance(no.args[0], ast.Constant)
                and isinstance(no.args[0].value, str)
                and no.args[0].value.startswith("paginas/")
            ):
                assert no.args[0].value in rotas, (arquivo, no.args[0].value)


def test_inicio_tem_detalhes_recolhidos_e_acesso_aos_dados_reais(tmp_path, monkeypatch):
    monkeypatch.setenv("EULER_DADOS_DIR", str(tmp_path / "dados"))
    at = AppTest.from_file(str(APP / "main.py"), default_timeout=90).run()
    assert not at.exception, at.exception
    assert any(t.value == "EULER" for t in at.title)
    assert any(e.label == "Mais ferramentas" and not e.proto.expanded for e in at.sidebar.expander)
    assert any(
        e.label == "Sobre a demonstração e os limites" and not e.proto.expanded for e in at.expander
    )
    assert at.button(key="ato1")
    assert at.button(key="ato2")
    assert any("660 dias" in m.value for m in at.markdown)
