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
    # o botão leva direto a "Dados e limites", com tudo liberado
    assert {m.label: m.value for m in at.metric}.get("Bloqueadas") == "0"
    assert _rodape_ok(at)

    at.switch_page("paginas/investigacao.py").run()
    assert not at.exception, at.exception
    # Fase R (D44): "Os dados sustentam" virou "Explicações compatíveis com os dados"
    assert any("Explicações compatíveis" in s.value for s in at.success)
    assert _rodape_ok(at)

    at.switch_page("paginas/extrato.py").run()
    assert not at.exception, at.exception
    assert any(i.value.startswith("F3 tem o menor preço") for i in at.info)

    at.switch_page("paginas/relatorio.py").run()
    next(b for b in at.button if b.label == "Gerar relatório").click().run()
    assert not at.exception, at.exception
    assert _rodape_ok(at)

    assert time.perf_counter() - inicio < 60
