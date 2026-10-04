"""Snapshots locais imutáveis; um SQLite por planta, fora do código-fonte.

Não altera nem normaliza os arquivos. A aplicação continua usando seus leitores.
Deduplicação considera bytes, nomes, altitude, origem sintética e revisão anterior;
reenviar o conteúdo da revisão anterior retorna essa revisão, sem alterar autoria.
SHA-256 detecta corrupção acidental, não autentica autores ou impede adulteração.
SQLite local não implementa autenticação, criptografia nem um serviço multiusuário.
"""

from __future__ import annotations

import base64
import hashlib
import json
import math
import os
import re
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

VERSAO = 1
MAX_ARQUIVOS_BYTES = 50 * 1024 * 1024
MAX_BACKUP_BYTES = 128 * 1024 * 1024
_REPO = Path(__file__).resolve().parents[1]
_ESQUEMA = """
CREATE TABLE planta (id TEXT PRIMARY KEY, nome TEXT NOT NULL, criado_em TEXT NOT NULL);
CREATE TABLE importacoes (
 id TEXT PRIMARY KEY, criado_em TEXT NOT NULL, rotulo TEXT NOT NULL,
 autor TEXT NOT NULL, motivo TEXT NOT NULL, anterior_id TEXT REFERENCES importacoes(id),
 altitude REAL, sinteticos INTEGER NOT NULL CHECK(sinteticos IN (0,1)),
 sha256 TEXT NOT NULL, dedup_chave TEXT NOT NULL UNIQUE, metadados_sha256 TEXT NOT NULL
);
CREATE TABLE arquivos (
 importacao_id TEXT NOT NULL REFERENCES importacoes(id), nome TEXT NOT NULL,
 conteudo BLOB NOT NULL, sha256 TEXT NOT NULL, PRIMARY KEY(importacao_id, nome)
);
CREATE TABLE analises (
 id TEXT PRIMARY KEY, importacao_id TEXT NOT NULL REFERENCES importacoes(id),
 criado_em TEXT NOT NULL, assinatura TEXT NOT NULL, resultado TEXT NOT NULL,
 sha256 TEXT NOT NULL, UNIQUE(importacao_id, assinatura, sha256)
);
PRAGMA user_version=1;
"""


def _json(valor):
    return json.dumps(
        valor, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    )


def _hash(valor: bytes) -> str:
    return hashlib.sha256(valor).hexdigest()


def _assinatura(valor) -> str:
    return _hash(_json(valor).encode("utf-8"))


def _id(valor: str) -> str:
    if not isinstance(valor, str) or str(UUID(valor)) != valor:
        raise ValueError("Identificador de registro inválido.")
    return valor


def _texto(valor, campo, limite=2000):
    if not isinstance(valor, str) or not valor.strip() or len(valor) > limite or "\x00" in valor:
        raise ValueError(f"Informe {campo} válido (até {limite} caracteres).")
    return valor.strip()


def _agora():
    return datetime.now(UTC).isoformat()


def _data(valor):
    if not isinstance(valor, str) or datetime.fromisoformat(valor).tzinfo is None:
        raise ValueError("Data do registro inválida: informe fuso horário.")
    return valor


def _arquivos(arquivos):
    if not isinstance(arquivos, dict) or not 1 <= len(arquivos) <= 20:
        raise ValueError("A importação deve conter entre 1 e 20 arquivos.")
    for nome, conteudo in arquivos.items():
        if (
            not isinstance(nome, str)
            or not 1 <= len(nome) <= 255
            or not nome.strip()
            or nome in {".", ".."}
            or re.search(r'[<>:"/\\|?*\x00-\x1f]', nome)
        ):
            raise ValueError("Nome de arquivo inválido.")
        if not isinstance(conteudo, bytes):
            # Contrato público usa ValueError para rejeições de entrada recuperáveis na UI.
            raise ValueError("Arquivos devem ser fornecidos como bytes originais.")  # noqa: TRY004
    if sum(map(len, arquivos.values())) > MAX_ARQUIVOS_BYTES:
        raise ValueError("Importação excede o limite de 50 MiB.")


def _conteudo_sha(arquivos, altitude, sinteticos):
    _arquivos(arquivos)
    if altitude is not None and (
        isinstance(altitude, bool)
        or not isinstance(altitude, int | float)
        or not math.isfinite(altitude)
    ):
        raise ValueError("Altitude deve ser finita ou ausente.")
    if type(sinteticos) is not bool:
        raise ValueError("A origem sintética deve ser explícita.")
    return _assinatura(
        {
            "arquivos": {k: _hash(v) for k, v in arquivos.items()},
            "altitude": float(altitude) if altitude is not None else None,
            "sinteticos": sinteticos,
        }
    )


def _meta_sha(meta):
    return _assinatura({k: v for k, v in meta.items() if k != "metadados_sha256"})


def _analise_sha(importacao_id, assinatura, resultado):
    return _assinatura(
        {"importacao_id": importacao_id, "assinatura": assinatura, "resultado": resultado}
    )


class Repositorio:
    """Repositório transacional local. Nenhum arquivo de cliente fica no Git."""

    def __init__(self, raiz: Path | None = None):
        padrao = (
            Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local" / "share"))
            / "EULER"
            / "dados"
        )
        self.raiz = Path(raiz or os.environ.get("EULER_DADOS_DIR") or padrao).expanduser().resolve()
        if self.raiz.is_relative_to(_REPO):
            raise ValueError("Escolha uma pasta de dados fora do repositório da EULER.")
        self.raiz.mkdir(parents=True, exist_ok=True)

    def _caminho(self, planta_id):
        caminho = self.raiz / f"{_id(planta_id)}.sqlite"
        if caminho.is_symlink() or caminho.resolve().parent != self.raiz:
            raise ValueError("Caminho da planta inválido.")
        return caminho

    @contextmanager
    def _conectar(self, planta_id, *, escrita=False):
        caminho = self._caminho(planta_id)
        if not caminho.is_file():
            raise ValueError("Planta não encontrada.")
        con = sqlite3.connect(caminho.as_uri() + "?mode=rw", uri=True, timeout=30)
        con.row_factory = sqlite3.Row
        try:
            con.execute("PRAGMA foreign_keys=ON")
            if con.execute("PRAGMA user_version").fetchone()[0] != VERSAO:
                raise ValueError("Versão do banco não suportada; não foi alterado.")
            con.execute("BEGIN IMMEDIATE" if escrita else "BEGIN")
            if con.execute("SELECT id FROM planta").fetchone()[0] != planta_id:
                raise ValueError("Identidade da planta não corresponde ao arquivo.")
            yield con
            con.commit()
        except BaseException:
            con.rollback()
            raise
        finally:
            con.close()

    def _criar(self, nome, preencher=None):
        planta = {
            "id": str(uuid4()),
            "nome": _texto(nome, "nome da planta", 200),
            "criado_em": _agora(),
        }
        caminho = self._caminho(planta["id"])
        temporario = caminho.with_suffix(".pending")
        con = sqlite3.connect(temporario, timeout=30)
        try:
            con.execute("PRAGMA foreign_keys=ON")
            con.executescript(_ESQUEMA)
            with con:
                con.execute("INSERT INTO planta VALUES (?,?,?)", tuple(planta.values()))
                if preencher:
                    preencher(con)
            con.close()
            os.replace(temporario, caminho)
        except BaseException:
            con.close()
            temporario.unlink(missing_ok=True)
            raise
        return planta

    def criar_planta(self, nome: str) -> dict:
        return self._criar(nome)

    def listar_plantas(self) -> list[dict]:
        plantas = []
        for caminho in self.raiz.glob("*.sqlite"):
            with self._conectar(caminho.stem) as con:
                plantas.append(dict(con.execute("SELECT * FROM planta").fetchone()))
        return sorted(plantas, key=lambda p: p["nome"].casefold())

    @staticmethod
    def _ler_importacao(con, importacao_id):
        row = con.execute("SELECT * FROM importacoes WHERE id=?", (_id(importacao_id),)).fetchone()
        if row is None:
            raise ValueError("Importação não encontrada nesta planta.")
        meta = dict(row)
        if _meta_sha(meta) != meta["metadados_sha256"]:
            raise ValueError("Falha de integridade dos metadados da importação.")
        arquivos = {}
        for arq in con.execute("SELECT * FROM arquivos WHERE importacao_id=?", (importacao_id,)):
            if _hash(arq["conteudo"]) != arq["sha256"]:
                raise ValueError("Falha de integridade do arquivo original.")
            arquivos[arq["nome"]] = arq["conteudo"]
        if _conteudo_sha(arquivos, meta["altitude"], bool(meta["sinteticos"])) != meta["sha256"]:
            raise ValueError("Falha de integridade do conjunto de arquivos.")
        return {**meta, "sinteticos": bool(meta["sinteticos"]), "arquivos": arquivos}

    def salvar_importacao(
        self,
        planta_id,
        arquivos: dict[str, bytes],
        *,
        altitude: float | None,
        rotulo: str,
        sinteticos: bool,
        autor: str,
        motivo: str,
        anterior_id: str | None = None,
    ) -> dict:
        sha = _conteudo_sha(arquivos, altitude, sinteticos)
        rotulo, autor, motivo = (
            _texto(rotulo, "rótulo", 200),
            _texto(autor, "autor", 200),
            _texto(motivo, "motivo"),
        )
        chave = _assinatura([sha, _id(anterior_id) if anterior_id else None])
        with self._conectar(planta_id, escrita=True) as con:
            if anterior_id:
                anterior = self._ler_importacao(con, anterior_id)
                if anterior["sha256"] == sha:
                    return {k: v for k, v in {**anterior, "dedup": True}.items() if k != "arquivos"}
            repetida = con.execute(
                "SELECT id FROM importacoes WHERE dedup_chave=?", (chave,)
            ).fetchone()
            if repetida:
                meta = self._ler_importacao(con, repetida[0])
                return {k: v for k, v in {**meta, "dedup": True}.items() if k != "arquivos"}
            meta = {
                "id": str(uuid4()),
                "criado_em": _agora(),
                "rotulo": rotulo,
                "autor": autor,
                "motivo": motivo,
                "anterior_id": anterior_id,
                "altitude": float(altitude) if altitude is not None else None,
                "sinteticos": int(sinteticos),
                "sha256": sha,
                "dedup_chave": chave,
            }
            meta["metadados_sha256"] = _meta_sha(meta)
            self._inserir_importacao(con, meta, arquivos)
        return {**meta, "sinteticos": sinteticos, "dedup": False}

    @staticmethod
    def _inserir_importacao(con, meta, arquivos):
        colunas = "id,criado_em,rotulo,autor,motivo,anterior_id,altitude,sinteticos,sha256,dedup_chave,metadados_sha256"
        con.execute(
            f"INSERT INTO importacoes ({colunas}) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            tuple(meta[c] for c in colunas.split(",")),
        )
        con.executemany(
            "INSERT INTO arquivos VALUES (?,?,?,?)",
            [(meta["id"], k, v, _hash(v)) for k, v in arquivos.items()],
        )

    def carregar_importacao(self, planta_id, importacao_id) -> dict:
        with self._conectar(planta_id) as con:
            return self._ler_importacao(con, importacao_id)

    def listar_importacoes(self, planta_id) -> list[dict]:
        with self._conectar(planta_id) as con:
            registros = [
                dict(r)
                for r in con.execute(
                    "SELECT * FROM importacoes ORDER BY criado_em DESC, rowid DESC"
                )
            ]
            for meta in registros:
                if _meta_sha(meta) != meta["metadados_sha256"]:
                    raise ValueError("Falha de integridade do histórico de importações.")
            return registros

    def salvar_analise(self, planta_id, importacao_id, *, assinatura: str, resultado: dict) -> str:
        assinatura = _texto(assinatura, "assinatura", 500)
        if not isinstance(resultado, dict):
            raise ValueError("Resultado deve ser um objeto JSON.")  # noqa: TRY004
        try:
            serializado = _json(resultado)
        except (TypeError, OverflowError, RecursionError) as exc:
            raise ValueError("Resultado deve conter apenas valores JSON finitos.") from exc
        if len(serializado.encode()) > MAX_ARQUIVOS_BYTES:
            raise ValueError("Análise excede o limite de tamanho.")
        sha = _analise_sha(importacao_id, assinatura, resultado)
        with self._conectar(planta_id, escrita=True) as con:
            self._ler_importacao(con, importacao_id)
            anterior = con.execute(
                "SELECT id FROM analises WHERE importacao_id=? AND assinatura=? AND sha256=?",
                (importacao_id, assinatura, sha),
            ).fetchone()
            if anterior:
                return anterior[0]
            registro_id = str(uuid4())
            con.execute(
                "INSERT INTO analises VALUES (?,?,?,?,?,?)",
                (registro_id, importacao_id, _agora(), assinatura, serializado, sha),
            )
            return registro_id

    @staticmethod
    def _ler_analises(con, importacao_id):
        registros = []
        for row in con.execute(
            "SELECT * FROM analises WHERE importacao_id=? ORDER BY criado_em DESC, rowid DESC",
            (importacao_id,),
        ):
            r = dict(row)
            resultado = json.loads(r["resultado"])
            if _analise_sha(r["importacao_id"], r["assinatura"], resultado) != r["sha256"]:
                raise ValueError("Falha de integridade da análise salva.")
            r["resultado"] = resultado
            registros.append(r)
        return registros

    def listar_analises(self, planta_id, importacao_id) -> list[dict]:
        with self._conectar(planta_id) as con:
            self._ler_importacao(con, importacao_id)
            return self._ler_analises(con, importacao_id)

    def exportar_backup(self, planta_id) -> bytes:
        """Exporta snapshot consistente, sem SQL executável; contém dados sensíveis."""
        with self._conectar(planta_id) as con:
            conteudo = {
                "versao": VERSAO,
                "planta": dict(con.execute("SELECT * FROM planta").fetchone()),
                "importacoes": [],
                "analises": [],
            }
            for row in con.execute("SELECT id FROM importacoes ORDER BY rowid"):
                imp = self._ler_importacao(con, row[0])
                imp["sinteticos"] = int(imp["sinteticos"])
                imp["arquivos"] = {
                    k: base64.b64encode(v).decode("ascii") for k, v in imp["arquivos"].items()
                }
                conteudo["importacoes"].append(imp)
                conteudo["analises"].extend(self._ler_analises(con, row[0]))
            backup = _json({"conteudo": conteudo, "sha256": _assinatura(conteudo)}).encode()
            if len(backup) > MAX_BACKUP_BYTES:
                raise ValueError("Backup excede 128 MiB; exportação não disponível nesta versão.")
            return backup

    def restaurar_backup(self, backup: bytes) -> dict:
        """Restaura em nova planta; valida tudo antes de publicar o banco."""
        if not isinstance(backup, bytes) or len(backup) > MAX_BACKUP_BYTES:
            raise ValueError("Backup inválido ou maior que 128 MiB.")
        try:
            envelope = json.loads(backup)
            conteudo = envelope["conteudo"]
            if _assinatura(conteudo) != envelope["sha256"]:
                raise ValueError("Falha de integridade do backup.")
            if conteudo["versao"] != VERSAO:
                raise ValueError("Versão do backup não suportada.")
            _id(conteudo["planta"]["id"])
            _data(conteudo["planta"]["criado_em"])
            nome = _texto(conteudo["planta"]["nome"], "nome da planta", 200)
            importacoes = self._validar_backup(conteudo)
        except (KeyError, TypeError, AttributeError, OverflowError, RecursionError) as exc:
            raise ValueError("Estrutura do backup inválida.") from exc

        def preencher(con):
            for meta, arquivos in importacoes:
                self._inserir_importacao(con, meta, arquivos)
            for a in conteudo["analises"]:
                con.execute(
                    "INSERT INTO analises VALUES (?,?,?,?,?,?)",
                    (
                        a["id"],
                        a["importacao_id"],
                        a["criado_em"],
                        a["assinatura"],
                        _json(a["resultado"]),
                        a["sha256"],
                    ),
                )

        return self._criar(nome, preencher)

    @staticmethod
    def _validar_backup(conteudo):
        vistos, resultado = set(), []
        if not isinstance(conteudo["importacoes"], list) or not isinstance(
            conteudo["analises"], list
        ):
            raise ValueError("Listas de registros inválidas no backup.")  # noqa: TRY004
        for registro in conteudo["importacoes"]:
            meta = {k: v for k, v in registro.items() if k != "arquivos"}
            if set(meta) != {
                "id",
                "criado_em",
                "rotulo",
                "autor",
                "motivo",
                "anterior_id",
                "altitude",
                "sinteticos",
                "sha256",
                "dedup_chave",
                "metadados_sha256",
            }:
                raise ValueError("Campos da importação incompatíveis com a versão do backup.")
            ident = _id(meta["id"])
            _data(meta["criado_em"])
            for campo, limite in (("rotulo", 200), ("autor", 200), ("motivo", 2000)):
                if _texto(meta[campo], campo, limite) != meta[campo]:
                    raise ValueError("Metadado não canônico no backup.")
            if ident in vistos or (
                meta["anterior_id"] is not None and meta["anterior_id"] not in vistos
            ):
                raise ValueError("Histórico inválido ou fora de ordem no backup.")
            if type(meta["sinteticos"]) is not int or meta["sinteticos"] not in (0, 1):
                raise ValueError("Origem dos dados inválida no backup.")
            arquivos = {
                k: base64.b64decode(v, validate=True) for k, v in registro["arquivos"].items()
            }
            sha = _conteudo_sha(arquivos, meta["altitude"], bool(meta["sinteticos"]))
            if (
                sha != meta["sha256"]
                or _meta_sha(meta) != meta["metadados_sha256"]
                or _assinatura([sha, meta["anterior_id"]]) != meta["dedup_chave"]
            ):
                raise ValueError("Falha de integridade de importação no backup.")
            vistos.add(ident)
            resultado.append((meta, arquivos))
        analises_ids = set()
        for a in conteudo["analises"]:
            ident = _id(a["id"])
            _data(a["criado_em"])
            _texto(a["assinatura"], "assinatura", 500)
            if (
                ident in analises_ids
                or a["importacao_id"] not in vistos
                or not isinstance(a["resultado"], dict)
            ):
                raise ValueError("Análise sem origem ou duplicada no backup.")
            if _analise_sha(a["importacao_id"], a["assinatura"], a["resultado"]) != a["sha256"]:
                raise ValueError("Falha de integridade da análise no backup.")
            analises_ids.add(ident)
        return resultado
