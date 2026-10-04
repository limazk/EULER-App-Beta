"""Persistência real: reinício, isolamento, revisões e restauração íntegra."""

import hashlib
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from euler.persistencia import Repositorio


def salvar(repo, planta, conteudo=b"a,b\n1,2\n", **alteracoes):
    opcoes = {
        "altitude": 1000.0,
        "rotulo": "Outubro",
        "sinteticos": True,
        "autor": "Operador",
        "motivo": "Importação inicial",
    }
    opcoes.update(alteracoes)
    return repo.salvar_importacao(planta["id"], {"diario": conteudo}, **opcoes)


def test_reinicio_dedup_e_isolamento(tmp_path):
    repo = Repositorio(tmp_path)
    a, b = repo.criar_planta("A"), repo.criar_planta("B")
    primeira = salvar(repo, a)
    outra = salvar(repo, a, autor="Outra pessoa")
    assert primeira["id"] == outra["id"] and outra["dedup"]
    reenviada = salvar(repo, a, anterior_id=primeira["id"], motivo="Reenvio")
    assert reenviada["id"] == primeira["id"] and reenviada["dedup"]
    novo = Repositorio(tmp_path)
    assert len(novo.listar_plantas()) == 2
    assert novo.carregar_importacao(a["id"], primeira["id"])["autor"] == "Operador"
    assert novo.listar_importacoes(b["id"]) == []
    with pytest.raises(ValueError):
        novo.carregar_importacao(b["id"], primeira["id"])


def test_correcao_preserva_original_e_analise(tmp_path):
    repo = Repositorio(tmp_path)
    planta = repo.criar_planta("Caldeira")
    v1 = salvar(repo, planta)
    v2 = salvar(repo, planta, b"a,b\n1,3\n", anterior_id=v1["id"], motivo="Corrigir leitura")
    assert v1["id"] != v2["id"]
    assert repo.carregar_importacao(planta["id"], v1["id"])["arquivos"]["diario"] == b"a,b\n1,2\n"
    assert repo.listar_importacoes(planta["id"])[0]["anterior_id"] == v1["id"]
    repo.salvar_analise(planta["id"], v1["id"], assinatura="motor/v1", resultado={"valor": None})
    registros = Repositorio(tmp_path).listar_analises(planta["id"], v1["id"])
    assert registros[0]["resultado"] == {"valor": None}
    with pytest.raises(ValueError):
        repo.salvar_analise(
            planta["id"], v2["id"], assinatura="motor/v1", resultado={"v": float("nan")}
        )
    assert repo.listar_analises(planta["id"], v2["id"]) == []


def test_backup_restaura_nova_planta_sem_sobrescrever(tmp_path):
    repo = Repositorio(tmp_path)
    planta = repo.criar_planta("Original")
    v1 = salvar(repo, planta)
    v2 = salvar(repo, planta, b"corrigido", anterior_id=v1["id"], motivo="Correção")
    repo.salvar_analise(planta["id"], v2["id"], assinatura="abc", resultado={"ok": True})
    backup = repo.exportar_backup(planta["id"])
    restaurada = repo.restaurar_backup(backup)
    assert restaurada["id"] != planta["id"]
    assert repo.carregar_importacao(restaurada["id"], v2["id"])["anterior_id"] == v1["id"]
    assert repo.listar_analises(restaurada["id"], v2["id"])[0]["resultado"] == {"ok": True}
    corrompido = json.loads(backup)
    corrompido["conteudo"]["planta"]["nome"] = "Alterado"
    with pytest.raises(ValueError, match="integridade"):
        repo.restaurar_backup(json.dumps(corrompido).encode())
    assert len(repo.listar_plantas()) == 2


def test_validacoes_e_rollback(tmp_path):
    repo = Repositorio(tmp_path)
    planta = repo.criar_planta("Teste")
    with pytest.raises(ValueError):
        repo.listar_importacoes("../fora")
    with pytest.raises(ValueError):
        salvar(repo, planta, altitude=float("inf"))
    with pytest.raises(ValueError):
        salvar(repo, planta, autor="")
    with pytest.raises(ValueError):
        salvar(repo, planta, anterior_id=repo.criar_planta("Outra")["id"])
    assert repo.listar_importacoes(planta["id"]) == []
    with pytest.raises(ValueError):
        Repositorio(Path(__file__).resolve().parents[1] / "dados-clientes")


def test_integridade_e_concorrencia(tmp_path):
    repo = Repositorio(tmp_path)
    planta = repo.criar_planta("Concorrente")
    with ThreadPoolExecutor(max_workers=4) as pool:
        registros = list(pool.map(lambda _: salvar(repo, planta), range(8)))
    assert len({r["id"] for r in registros}) == 1
    with sqlite3.connect(tmp_path / f"{planta['id']}.sqlite") as con:
        con.execute("UPDATE arquivos SET conteudo = ?", (b"adulterado",))
    with pytest.raises(ValueError, match="integridade"):
        repo.carregar_importacao(planta["id"], registros[0]["id"])
    with pytest.raises(ValueError, match="integridade"):
        repo.exportar_backup(planta["id"])


def test_transacao_nao_deixa_importacao_parcial(tmp_path, monkeypatch):
    repo = Repositorio(tmp_path)
    planta = repo.criar_planta("Rollback")
    inserir = repo._inserir_importacao

    def falhar(con, meta, arquivos):
        inserir(con, meta, arquivos)
        raise OSError("Disco indisponível")

    monkeypatch.setattr(repo, "_inserir_importacao", falhar)
    with pytest.raises(OSError):
        salvar(repo, planta)
    assert repo.listar_importacoes(planta["id"]) == []
    with sqlite3.connect(tmp_path / f"{planta['id']}.sqlite") as con:
        assert con.execute("SELECT COUNT(*) FROM arquivos").fetchone()[0] == 0


def test_assinatura_analise_adulterada_e_versao_futura(tmp_path):
    repo = Repositorio(tmp_path)
    planta = repo.criar_planta("Integridade")
    imp = salvar(repo, planta)
    repo.salvar_analise(planta["id"], imp["id"], assinatura="motor1", resultado={"ok": True})
    caminho = tmp_path / f"{planta['id']}.sqlite"
    with sqlite3.connect(caminho) as con:
        con.execute("UPDATE analises SET assinatura='motor2'")
    with pytest.raises(ValueError, match="integridade"):
        repo.listar_analises(planta["id"], imp["id"])
    with sqlite3.connect(caminho) as con:
        con.execute("PRAGMA user_version=999")
    with pytest.raises(ValueError, match="Versão"):
        repo.listar_importacoes(planta["id"])


def test_configuracao_explicita_por_ambiente(tmp_path, monkeypatch):
    monkeypatch.setenv("EULER_DADOS_DIR", str(tmp_path / "fora-do-repo"))
    assert Repositorio().raiz == (tmp_path / "fora-do-repo").resolve()


def test_restauracao_falha_sem_deixar_nova_planta(tmp_path, monkeypatch):
    repo = Repositorio(tmp_path)
    planta = repo.criar_planta("Original")
    salvar(repo, planta)
    backup = repo.exportar_backup(planta["id"])
    inserir = repo._inserir_importacao

    def falhar(con, meta, arquivos):
        inserir(con, meta, arquivos)
        raise OSError("Falha durante restauração")

    monkeypatch.setattr(repo, "_inserir_importacao", falhar)
    with pytest.raises(OSError):
        repo.restaurar_backup(backup)
    assert len(repo.listar_plantas()) == 1
    assert list(tmp_path.glob("*.pending")) == []


def test_nome_original_com_acentos_e_espacos(tmp_path):
    repo = Repositorio(tmp_path)
    planta = repo.criar_planta("Fábrica A")
    arquivos = {"Medição da caldeira — outubro.csv": b"exato\r\n"}
    imp = repo.salvar_importacao(
        planta["id"],
        arquivos,
        altitude=None,
        rotulo="Mês",
        sinteticos=False,
        autor="João",
        motivo="Arquivo original",
    )
    restaurada = repo.restaurar_backup(repo.exportar_backup(planta["id"]))
    assert repo.carregar_importacao(restaurada["id"], imp["id"])["arquivos"] == arquivos


@pytest.mark.parametrize("malformado", [1, [], ["erro"], None])
def test_backup_registro_malformado_rejeitado(tmp_path, malformado):
    repo = Repositorio(tmp_path)
    planta = repo.criar_planta("Backup")
    salvar(repo, planta)
    envelope = json.loads(repo.exportar_backup(planta["id"]))
    envelope["conteudo"]["importacoes"] = [malformado]
    canonico = json.dumps(
        envelope["conteudo"],
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()
    envelope["sha256"] = hashlib.sha256(canonico).hexdigest()
    with pytest.raises(ValueError):
        repo.restaurar_backup(json.dumps(envelope).encode())
    assert len(repo.listar_plantas()) == 1
