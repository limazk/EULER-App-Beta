"""As duas APIs compartilham armazenamento, originais e restauração integral."""

import json
import sqlite3

import pytest
from test_armazem import EQ, arquivos_caso

from euler.armazem import Armazem, ErroArmazem, abrir_planta, criar_planta, listar_plantas
from euler.persistencia import Repositorio


def test_duas_apis_mesmo_arquivo_backup_completo(tmp_path):
    repo = Repositorio(tmp_path)
    a = criar_planta("Unificada", "sintetico", raiz=tmp_path)
    a.criar_equipamento(EQ, "Caldeira")
    raw = arquivos_caso()
    lote = a.confirmar(a.previa(EQ, raw), autor="Ana")
    pid = a.info["planta_id"]
    assert len(repo.listar_plantas()) == len(listar_plantas(tmp_path)) == 1
    b = repo.armazem(pid)
    assert b.arquivo == a.arquivo
    b.fechar()
    assert repo.carregar_importacao(pid, lote["importacao_id"])["arquivos"] == raw
    assert a.exportar()["tabelas"]["arquivos"]
    json.dumps(a.exportar())  # BLOBs têm codificação explícita, não bytes soltos.
    restaurada = repo.restaurar_backup(repo.exportar_backup(pid))
    c = repo.armazem(restaurada["id"])
    assert c.info["classe"] == "sintetico"
    assert c.registros(EQ, "diario") == a.registros(EQ, "diario")
    assert c.importacoes(EQ) == a.importacoes(EQ)
    assert c.eventos() == a.eventos()
    assert repo.carregar_importacao(c.info["planta_id"], lote["importacao_id"])["arquivos"] == raw
    c.fechar()
    a.fechar()


def test_previa_nao_pode_ser_aplicada_em_outra_planta_ou_revisao(tmp_path):
    a = criar_planta("A", "sintetico", raiz=tmp_path)
    b = criar_planta("B", "sintetico", raiz=tmp_path)
    for p in (a, b):
        p.criar_equipamento(EQ, "Caldeira")
    preview = a.previa(EQ, arquivos_caso())
    with pytest.raises(ErroArmazem, match="planta"):
        b.confirmar(preview, autor="Ana")
    a.confirmar(preview, autor="Ana")
    with pytest.raises(ErroArmazem, match="prévia"):
        a.confirmar(preview, autor="Ana")
    a.fechar()
    b.fechar()


def test_versao_futura_nao_recebe_ddl_e_caminho_nao_escapa(tmp_path):
    arquivo = tmp_path / "futuro.sqlite"
    with sqlite3.connect(arquivo) as con:
        con.execute("PRAGMA user_version=999")
    before = arquivo.read_bytes()
    with pytest.raises(ValueError):
        Armazem(arquivo)
    assert arquivo.read_bytes() == before
    with pytest.raises(ValueError):
        abrir_planta("../escape", raiz=tmp_path)


@pytest.mark.parametrize("tipo", ["snapshot", "operacional"])
def test_migracao_v1_no_mesmo_arquivo_preserva_origem(tmp_path, tipo):
    import euler.armazem as arm
    import euler.persistencia as per

    pid = "legada"
    arquivo = tmp_path / f"{pid}.sqlite"
    with sqlite3.connect(arquivo) as con:
        if tipo == "snapshot":
            con.executescript(per._ESQUEMA)
            con.execute(
                "INSERT INTO planta VALUES (?,?,?)", (pid, "Legada", "2026-01-01T00:00:00+00:00")
            )
        else:
            con.executescript(arm.ESQUEMA)
            con.executemany(
                "INSERT INTO meta VALUES (?,?)",
                list(
                    {
                        "planta_id": pid,
                        "nome": "Legada",
                        "classe": "publico",
                        "autorizacao": "",
                        "revisao": "0",
                        "criada_em": "2026-01-01T00:00:00+00:00",
                    }.items()
                ),
            )
        con.execute("PRAGMA user_version=1")
    repo = Repositorio(tmp_path)
    planta = repo.listar_plantas()[0]
    assert planta["classe"] == ("publico" if tipo == "operacional" else "nao_classificado")
    assert arquivo.with_suffix(".sqlite.v1.bak").is_file()
    a = repo.armazem(pid)
    assert a.arquivo == arquivo
    assert a.con.execute("PRAGMA user_version").fetchone()[0] == 2
    a.fechar()


def test_origem_publica_nao_aceita_cliente_em_snapshot(tmp_path):
    repo = Repositorio(tmp_path)
    p = repo.criar_planta("Pública", classe="publico")
    arquivos = {k: v.replace(b"sintetico", b"real") for k, v in arquivos_caso().items()}
    with pytest.raises(ValueError, match="origem"):
        repo.salvar_importacao(
            p["id"],
            arquivos,
            altitude=None,
            rotulo="Lote",
            sinteticos=False,
            autor="Ana",
            motivo="Importar",
        )
    assert repo.listar_importacoes(p["id"]) == []


def test_correcao_nao_reclassifica_dado_nem_aceita_configuracao_invalida(tmp_path):
    a = criar_planta("A", "sintetico", raiz=tmp_path)
    a.criar_equipamento(EQ, "Caldeira")
    a.confirmar(a.previa(EQ, arquivos_caso()), autor="Ana")
    chave = next(iter(a._ativos(EQ, "diario")))
    rev = a.revisao
    with pytest.raises(ErroArmazem, match="Origem"):
        a.corrigir(EQ, "diario", chave, {"origem_dado": "real"}, "Correção", "Ana")
    with pytest.raises(ErroArmazem, match="Altitude"):
        a.configurar(EQ, {"altitude_m": float("nan")})
    with pytest.raises(ErroArmazem, match="inteiro positivo"):
        a.configurar(EQ, {"dias_para_desatualizado": 0})
    assert a.revisao == rev
    a.fechar()


def test_alias_das_duas_apis_usam_mesma_raiz(tmp_path, monkeypatch):
    import euler.armazem as arm
    import euler.persistencia as per

    monkeypatch.delenv("EULER_DADOS_DIR", raising=False)
    monkeypatch.setenv("EULER_DADOS", str(tmp_path / "comum"))
    assert arm.raiz_padrao() == per.raiz_padrao() == tmp_path / "comum"
    monkeypatch.setenv("EULER_DADOS_DIR", str(tmp_path / "prioritaria"))
    assert arm.raiz_padrao() == per.raiz_padrao() == tmp_path / "prioritaria"


def test_backup_preserva_entidades_operacionais_e_autorizacao(tmp_path):
    repo = Repositorio(tmp_path)
    p = repo.criar_planta("Cliente", classe="cliente_autorizado", autorizacao="Termo 01")
    a = repo.armazem(p["id"])
    a.criar_equipamento(EQ, "Caldeira")
    from euler.acompanhamento import registrar_intervencao
    from euler.fechamento import registrar_preco

    registrar_preco(a, EQ, "cavaco", 200, "2026-01-01", "Contrato 1", "Ana")
    registrar_intervencao(a, EQ, "2026-01-02", "calibracao", "Instrumento verificado", "Ana")
    a.salvar_perfil(EQ, "Supervisório", {"Temperatura": "t_gases_c"})
    original = {
        t: [tuple(r) for r in a.con.execute(f'SELECT * FROM "{t}"')]
        for t in ("preco", "intervencao", "perfil", "evento")
    }
    restaurada = repo.restaurar_backup(repo.exportar_backup(p["id"]))
    b = repo.armazem(restaurada["id"])
    assert b.info["autorizacao"] == "Termo 01"
    assert b.info["planta_id"] != a.info["planta_id"]
    for tabela, registros in original.items():
        assert [tuple(r) for r in b.con.execute(f'SELECT * FROM "{tabela}"')] == registros
    a.fechar()
    b.fechar()


def test_motivo_operacional_canonico_nao_invalida_restauracao(tmp_path):
    a = criar_planta("A", "sintetico", raiz=tmp_path)
    a.criar_equipamento(EQ, "Caldeira")
    a.confirmar(a.previa(EQ, arquivos_caso()), autor=" Ana ", motivo=" Importação ")
    repo = Repositorio(tmp_path)
    b = repo.restaurar_backup(repo.exportar_backup(a.info["planta_id"]))
    assert repo.listar_importacoes(b["id"])[0]["motivo"] == "Importação"
    a.fechar()


def test_planilha_nao_mistura_origem_publica_e_real(tmp_path):
    import io

    import pandas as pd

    buf = io.BytesIO()
    pd.DataFrame({"origem_dado": ["publico", "real"]}).to_excel(
        buf, index=False, sheet_name="diario"
    )
    repo = Repositorio(tmp_path)
    p = repo.criar_planta("P", classe="publico")
    with pytest.raises(ValueError, match="origem"):
        repo.salvar_importacao(
            p["id"],
            {"dados.xlsx": buf.getvalue()},
            altitude=None,
            rotulo="Importação",
            sinteticos=False,
            autor="Ana",
            motivo="Importação",
        )
