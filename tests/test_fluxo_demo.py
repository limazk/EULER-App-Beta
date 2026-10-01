"""Fluxo completo do caso de demonstração (T15 + T18), como um usuário faria.

Aceite do T15: fluxo completo em menos de 5 minutos, sem ajuda. Aqui medimos o tempo
de processamento do app (o tempo humano de leitura fica no roteiro do vídeo).
"""

import time
from pathlib import Path

from streamlit.testing.v1 import AppTest

from euler.textos import RODAPE_SEGURANCA

APP = Path(__file__).resolve().parents[1] / "app" / "main.py"


def _rodape_ok(at: AppTest) -> bool:
    return any(c.value == RODAPE_SEGURANCA for c in at.caption)


def test_fluxo_completo_do_caso_de_demonstracao():
    inicio = time.perf_counter()
    at = AppTest.from_file(str(APP), default_timeout=60).run()
    next(b for b in at.button if b.label.startswith("Começar com o caso")).click().run()
    assert not at.exception, at.exception
    # o botão leva direto a "Dados e limites"; só a faixa de incerteza da eficiência fica
    # bloqueada (o demo não cadastra todos os instrumentos; auditoria A3)
    assert {m.label: m.value for m in at.metric}.get("Bloqueadas") == "1"
    assert _rodape_ok(at)

    at.switch_page("paginas/investigacao.py").run()
    assert not at.exception, at.exception
    # auditoria A3: abstenção com o que cadastrar (antes: "Explicações compatíveis")
    assert any(w.value.startswith("Não dá para concluir") for w in at.warning)
    assert _rodape_ok(at)

    at.switch_page("paginas/extrato.py").run()
    assert not at.exception, at.exception
    assert any(i.value.startswith("F3 tem o menor preço") for i in at.info)

    at.switch_page("paginas/relatorio.py").run()
    next(b for b in at.button if b.label == "Gerar relatório").click().run()
    assert not at.exception, at.exception
    assert _rodape_ok(at)

    assert time.perf_counter() - inicio < 60
