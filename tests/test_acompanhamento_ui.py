"""Um fluxo de dados acumulados deve usar o mesmo banco que guarda os originais."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

from euler.persistencia import Repositorio

APP = Path(__file__).resolve().parents[1] / "app"


def test_tela_confirma_versao_no_mesmo_banco_e_reabre_serie(tmp_path, monkeypatch):
    raiz = tmp_path / "dados"
    monkeypatch.setenv("EULER_DADOS_DIR", str(raiz))
    repo = Repositorio(raiz)
    planta = repo.criar_planta("Acompanhamento sintético", classe="sintetico")
    demo = APP.parent / "demo" / "caso_demo_completo"
    arquivos = {p.name: p.read_bytes() for p in demo.glob("*.csv")}
    v = repo.salvar_importacao(
        planta["id"],
        arquivos,
        altitude=1000,
        sinteticos=True,
        rotulo="Caso completo",
        autor="Teste",
        motivo="Integração",
    )
    at = AppTest.from_file(str(APP / "main.py"), default_timeout=60).run()
    at.switch_page("paginas/acompanhamento.py").run()
    assert not at.exception, at.exception

    def clicar(rotulo):
        next(b for b in at.button if b.label == rotulo).click().run()
        assert not at.exception, at.exception

    at.text_input(key="equip_id").set_value("CALD-01")
    # Código do equipamento do caso distribuído, extraído do próprio diário.
    import csv
    import io

    codigo = next(csv.DictReader(io.StringIO(arquivos["diario.csv"].decode("utf-8-sig"))))[
        "caldeira_id"
    ]
    at.text_input(key="equip_caldeira_id").set_value(codigo)
    at.text_input(key="equip_nome").set_value("Caldeira sintética")
    at.number_input(key="equip_altitude").set_value(1000.0)
    clicar("Cadastrar equipamento")
    at.text_input(key="acomp_autor").set_value("Teste de integração").run()
    clicar("Preparar prévia")
    clicar("Confirmar registros novos")
    a = repo.armazem(planta["id"])
    try:
        assert a.registros("CALD-01", "diario")
        assert a.importacoes("CALD-01")
        assert a.con.execute("SELECT count(*) FROM arquivos").fetchone()[0] == len(arquivos)
    finally:
        a.fechar()
    clicar("Analisar série acumulada")
    assert at.session_state["persistencia"]["planta_id"] == planta["id"]
    assert at.session_state["dados_sinteticos"] is True
    assert dict(at.session_state["arquivos"])["diario.csv"]
    assert repo.carregar_importacao(planta["id"], v["id"])["arquivos"] == arquivos
