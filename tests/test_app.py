"""Testes de fumaça do app: cada tela abre sem erro e mostra o rodapé de segurança."""

import ast
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from euler.textos import RODAPE_SEGURANCA

APP = Path(__file__).resolve().parents[1] / "app"
PAGINAS = sorted(p.name for p in (APP / "paginas").glob("*.py"))


def abrir(pagina: str | None = None) -> AppTest:
    at = AppTest.from_file(str(APP / "main.py"), default_timeout=30).run()
    if pagina:
        at.switch_page(f"paginas/{pagina}").run()
    return at


def test_tela_inicial_abre_com_rodape():
    at = abrir()
    assert not at.exception
    assert any(t.value == "EULER" for t in at.title)
    assert any(c.value == RODAPE_SEGURANCA for c in at.caption)


@pytest.mark.parametrize("pagina", PAGINAS)
def test_toda_pagina_abre_sem_erro_e_com_rodape(pagina):
    at = abrir(pagina)
    assert not at.exception, at.exception
    assert any(c.value == RODAPE_SEGURANCA for c in at.caption)


def test_calculadora_mostra_caso_de_referencia_g01():
    at = abrir("calculadora.py")
    valores = {m.label: m.value for m in at.metric}
    assert valores["Perda nos gases"] == "11,77 % do PCI"
    assert valores["Razão de ar λ"] == "1,611"
    assert valores["PCI úmido"] == "10,12 MJ/kg"
    assert any("Simulação" in w.value for w in at.warning)


def test_calculadora_bloqueia_com_motivo():
    at = abrir("calculadora.py")
    # gases a 60 °C com combustível a 70% de umidade: abaixo do orvalho (≈71 °C)
    at.slider[0].set_value(60)
    at.slider[2].set_value(70).run()
    assert not at.metric
    assert any("bloqueado" in e.value for e in at.error)


def test_nenhuma_tela_usa_st_stop_que_esconderia_o_rodape():
    for arquivo in [*(APP / "paginas").glob("*.py"), APP / "estado.py", APP / "main.py"]:
        arvore = ast.parse(arquivo.read_text(encoding="utf-8"))
        chamadas = [
            n
            for n in ast.walk(arvore)
            if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute)
            and n.func.attr == "stop"
        ]
        assert not chamadas, arquivo.name


def clicar(at: AppTest, inicio_do_rotulo: str) -> AppTest:
    next(b for b in at.button if b.label.startswith(inicio_do_rotulo)).click().run()
    return at


def test_importar_exemplo_com_problemas_mostra_avisos():
    at = clicar(abrir("importar.py"), "Exemplo com problemas")
    assert not at.exception
    valores = {m.label: m.value for m in at.metric}
    assert valores["Tabelas importadas"] == "5"
    assert int(valores["Avisos de atenção"]) >= 15
    assert any(c.value == RODAPE_SEGURANCA for c in at.caption)


def abrir_com_demo(pagina: str) -> AppTest:
    at = clicar(abrir("importar.py"), "Caso de demonstração")
    at.switch_page(f"paginas/{pagina}").run()
    return at


def test_extrato_com_caso_de_demonstracao():
    at = abrir_com_demo("extrato.py")
    assert not at.exception, at.exception
    assert any("mais barato por tonelada nem sempre" in m.value for m in at.markdown)
    assert any(i.value.startswith("F3 tem o menor preço por tonelada") for i in at.info)
    assert any(c.value == RODAPE_SEGURANCA for c in at.caption)


def test_extrato_sem_dados_orienta_a_importar():
    at = abrir("extrato.py")
    assert not at.exception
    assert any("Nenhum dado importado" in i.value for i in at.info)


def test_dados_e_limites_com_demo_bloqueia_so_a_faixa_de_incerteza():
    at = abrir_com_demo("limites.py")
    assert not at.exception, at.exception
    valores = {m.label: m.value for m in at.metric}
    # auditoria A3: o demo não cadastra todos os instrumentos usados na eficiência
    assert valores["Bloqueadas"] == "1"


def test_dados_e_limites_com_modelos_mostra_bloqueios():
    at = clicar(abrir("importar.py"), "Modelos")
    at.switch_page("paginas/limites.py").run()
    assert not at.exception
    assert int({m.label: m.value for m in at.metric}["Bloqueadas"]) > 0
    assert any("Por quê" in m.value for m in at.markdown)


def test_investigacao_com_demo_mostra_o_que_falta_para_concluir():
    at = abrir_com_demo("investigacao.py")
    assert not at.exception, at.exception
    # Auditoria A3: sem a incerteza do método de umidade, a EULER se abstém e diz o que cadastrar
    assert any(w.value.startswith("Não dá para concluir") for w in at.warning)
    assert any("Mais calor saindo pela chaminé" in m.value for m in at.markdown)
    assert any("Cadastrar em instrumentos.csv" in i.value for i in at.info)
    assert any(c.value == RODAPE_SEGURANCA for c in at.caption)


def test_investigacao_semana_sem_vapor_abstem():
    at = abrir_com_demo("investigacao.py")
    at.select_slider[1].set_value((6, 6)).run()  # semana 7: medidor de vapor fora
    assert not at.exception, at.exception
    assert any(w.value.startswith("Não dá para concluir") for w in at.warning)


def test_relatorio_sem_investigacao_orienta():
    at = abrir("relatorio.py")
    assert not at.exception
    assert any("Investigação" in i.value for i in at.info)


def test_relatorio_depois_da_investigacao_gera_html():
    at = abrir_com_demo("investigacao.py")
    at.switch_page("paginas/relatorio.py").run()
    clicar(at, "Gerar relatório")
    assert not at.exception, at.exception
    assert any(c.value == RODAPE_SEGURANCA for c in at.caption)


def test_investigacao_mostra_fator_que_mudou_no_sentido_contrario():
    """Explicações concorrentes (matriz V-E1) na tela real: o fator oposto aparece no bloco
    2 com o rótulo próprio, junto da frase de fechamento (antes ele sumia da tela)."""
    from construtor_caso import Periodo, montar
    from test_validacao_combustivel_incerteza import _referencia_lab

    perda = 100 * _referencia_lab()(230, 8, 0.36)[0]
    pacote, _ = montar([Periodo(11.773, umidade=0.40), Periodo(perda, t_gases_c=230, umidade=0.36)])
    at = abrir()
    at.session_state["arquivos"] = tuple(
        sorted((f"{nome}.csv", dados) for nome, dados in pacote._arquivos_teste.items())
    )
    at.session_state["rotulo_dados"] = "caso de teste: explicações concorrentes"
    at.session_state["altitude_m"] = 0.0
    at.switch_page("paginas/investigacao.py").run()
    assert not at.exception, at.exception
    assert any("Mudou no sentido contrário" in m.value for m in at.markdown)
    assert any("fecham dentro da incerteza" in c.value for c in at.caption)
