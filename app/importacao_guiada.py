"""Adaptação explícita de CSV/Excel ao contrato; não calcula grandezas físicas.

Originais permanecem byte a byte em anexos .bin. O manifesto registra hashes,
aba, colunas, unidades e constantes informadas. O leitor e o banco existentes
recebem os CSVs adaptados; não se cria outro caminho de normalização científica.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from zipfile import BadZipFile

import pandas as pd

from euler.io.esquemas import TABELAS
from euler.io.leitura import ALIASES_COLUNAS, _numero, ler_csv


@dataclass
class FonteGuiada:
    chave: str
    arquivo: str
    aba: str | None
    bruto: pd.DataFrame
    virgula_decimal: bool


def assinatura_envio(arquivos: dict[str, bytes], decisoes: dict) -> str:
    """Identidade do conteúdo e das decisões; trocar arquivo de mesmo nome invalida prévia."""
    entrada = {
        "arquivos": {n: hashlib.sha256(b).hexdigest() for n, b in sorted(arquivos.items())},
        "decisoes": decisoes,
    }
    return hashlib.sha256(json.dumps(entrada, sort_keys=True).encode()).hexdigest()


def _normal(nome: str) -> str:
    texto = "".join(c for c in unicodedata.normalize("NFKD", nome) if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", texto.lower()).strip()


def _validar_cabecalho(colunas: list[str], nome: str) -> None:
    if len(set(colunas)) != len(colunas):
        raise ValueError(f"{nome}: há nomes de colunas repetidos. Diferencie os cabeçalhos.")
    if any(not c for c in colunas) or "linha" in colunas:
        raise ValueError(
            f"{nome}: preencha todos os cabeçalhos; 'linha' é reservado à rastreabilidade."
        )


def ler_fontes(arquivos: dict[str, bytes]) -> list[FonteGuiada]:
    """Lê qualquer nome de arquivo/aba, texto intacto; cabeçalho deve estar na primeira linha."""
    fontes = []
    for nome, conteudo in arquivos.items():
        if nome.lower().endswith(".csv"):
            try:
                texto = conteudo.decode("utf-8-sig")
            except UnicodeDecodeError:
                texto = conteudo.decode("cp1252")
            primeira = texto.split("\n", 1)[0]
            sep = ";" if primeira.count(";") > primeira.count(",") else ","
            cab = next(csv.reader(io.StringIO(texto), delimiter=sep), [])
            _validar_cabecalho([c.strip() for c in cab], nome)
            df, virgula, avisos = ler_csv(conteudo, nome)
            if any(a.tipo in {"colunas_a_mais", "arquivo_vazio"} for a in avisos):
                raise ValueError(f"{nome}: confira o separador e o número de colunas do arquivo.")
            fontes.append(FonteGuiada(nome, nome, None, df, virgula))
        elif nome.lower().endswith(".xlsx"):
            try:
                abas = pd.read_excel(
                    io.BytesIO(conteudo),
                    sheet_name=None,
                    header=None,
                    dtype=str,
                    keep_default_na=False,
                )
            except (ValueError, BadZipFile, OSError) as exc:
                raise ValueError(
                    f"{nome}: não foi possível ler o Excel. Confira o formato .xlsx."
                ) from exc
            for aba, bruto in abas.items():
                if bruto.empty:
                    continue
                cab = bruto.iloc[0].fillna("").astype(str).str.strip().tolist()
                _validar_cabecalho(cab, f"{nome} · {aba}")
                df = bruto.iloc[1:].copy().fillna("").astype(str)
                df.columns = cab
                df.insert(0, "linha", df.index + 1)
                df = df[df[cab].apply(lambda r: any(v.strip() for v in r), axis=1)]
                fontes.append(
                    FonteGuiada(f"{nome}::{aba}", nome, aba, df.reset_index(drop=True), False)
                )
    if not fontes:
        raise ValueError(
            "Nenhuma tabela encontrada. Envie CSV ou Excel com cabeçalho na primeira linha."
        )
    return fontes


def sugerir_mapeamento(colunas: list[str], tabela: str, salvo: dict | None = None) -> dict:
    """Sugere somente nome exato, rótulo exato ou alias explícito; nada de fuzzy matching."""
    contrato = TABELAS[tabela]
    nomes = {c.nome for c in contrato.colunas}
    candidatos: dict[str, set[str]] = {}
    for col in contrato.colunas:
        for rotulo in (col.nome, col.rotulo):
            candidatos.setdefault(_normal(rotulo), set()).add(col.nome)
    for alias, alvo in ALIASES_COLUNAS.items():
        if alvo in nomes:
            candidatos.setdefault(_normal(alias), set()).add(alvo)
    mapa = {}
    for coluna in colunas:
        if salvo and salvo.get(coluna) in nomes:
            mapa[coluna] = salvo[coluna]
        elif coluna in nomes:
            mapa[coluna] = coluna
        elif len(opcoes := candidatos.get(_normal(coluna), set())) == 1:
            mapa[coluna] = next(iter(opcoes))
    return mapa


def sugerir_tabela(fonte: FonteGuiada) -> str | None:
    """Nome conhecido ou cobertura inequívoca das colunas obrigatórias."""
    nome = (fonte.aba or Path(fonte.arquivo).stem).strip().lower()
    if nome in TABELAS:
        return nome
    candidatos = []
    colunas = [c for c in fonte.bruto if c != "linha"]
    for nome, tabela in TABELAS.items():
        mapa = sugerir_mapeamento(colunas, nome)
        obrigatorias = {c.nome for c in tabela.colunas if c.obrigatoria}
        if obrigatorias <= set(mapa.values()):
            candidatos.append((len(mapa), nome))
    candidatos.sort(reverse=True)
    if candidatos and (len(candidatos) == 1 or candidatos[0][0] > candidatos[1][0]):
        return candidatos[0][1]
    return None


def unidades_permitidas(col) -> dict[str, tuple[float, float]]:
    """Conversões dimensionais exatas (destino = origem × fator + offset).

    Não converte preço unitário em total, volume em massa ou pressão absoluta
    em manométrica: essas operações requerem informação física adicional.
    """
    opcoes = {col.unidade: (1.0, 0.0)}
    extras = {
        "kg": {"t": (1000.0, 0.0)},
        "kg (como recebido, úmido)": {"kg": (1.0, 0.0), "t": (1000.0, 0.0)},
        "t/h": {"kg/h": (0.001, 0.0)},
        "kg/h": {"t/h": (1000.0, 0.0)},
        "t (acumulado)": {"kg (acumulado)": (0.001, 0.0)},
        "°C": {"K": (1.0, -273.15)},
        "bar manométrico": {"kPa manométrico": (0.01, 0.0)},
        "fração, base úmida": {"%, base úmida": (0.01, 0.0)},
        "fração, base seca": {"%, base seca": (0.01, 0.0)},
        "% em base seca": {"fração em base seca": (100.0, 0.0)},
    }
    opcoes.update(extras.get(col.unidade, {}))
    return opcoes


def preparar_lote(arquivos: dict[str, bytes], decisoes: dict) -> dict[str, bytes]:
    """Produz CSVs do contrato e trilha auditável. Ausentes continuam vazios.

    Cada tabela recebe uma única fonte; não escolhe entre fontes sobrepostas.
    Constantes são declarações do usuário, apenas em colunas não existentes.
    """
    saida: dict[str, bytes] = {}
    adaptacoes = []
    for fonte in ler_fontes(arquivos):
        escolha = decisoes.get(fonte.chave, {})
        tabela = escolha.get("tabela")
        if not tabela:
            continue
        contrato = TABELAS[tabela]
        destino = contrato.arquivo
        if destino in saida:
            raise ValueError(
                "Duas fontes apontam para a mesma tabela. Envie um conjunto por tabela."
            )
        mapa = escolha.get("mapeamento", {})
        unidades = escolha.get("unidades", {})
        constantes = escolha.get("constantes", {})
        if len(set(mapa.values())) != len(mapa):
            raise ValueError("Duas colunas apontam para a mesma coluna EULER. Escolha apenas uma.")
        df = pd.DataFrame(index=fonte.bruto.index)
        ids = [c for c in fonte.bruto if _normal(c) in {"caldeira id", "boiler id", "caldeira"}]
        if "caldeira_id" in {c.nome for c in contrato.colunas}:
            for coluna_id in ids:
                if mapa.get(coluna_id) != "caldeira_id":
                    raise ValueError(
                        "Preserve a coluna de identificação da caldeira do arquivo; ela não pode ser ignorada ou substituída."
                    )
        # Origem existente é vinculante, mesmo se o usuário tentar ignorá-la.
        origens = [c for c in fonte.bruto if _normal(c) in {"origem dado", "origem do dado"}]
        for c in origens:
            if mapa.get(c) not in (None, "origem_dado"):
                raise ValueError("A coluna de origem não pode ser usada como outra grandeza.")
            if "origem_dado" in mapa.values() and mapa.get(c) != "origem_dado":
                raise ValueError("Mais de uma coluna de origem. Confira a declaração original.")
            existentes = {v.strip() for v in fonte.bruto[c] if v.strip()}
            if constantes.get("origem_dado") and existentes - {constantes["origem_dado"]}:
                raise ValueError("A origem declarada não pode substituir a origem do arquivo.")
            df["origem_dado"] = fonte.bruto[c]
        for origem, alvo in mapa.items():
            if origem not in fonte.bruto or alvo not in {c.nome for c in contrato.colunas}:
                raise ValueError("Mapeamento contém coluna inexistente.")
            col = contrato.coluna(alvo)
            valores = fonte.bruto[origem].copy()
            if col.tipo == "numero":
                unidade = unidades.get(origem)
                if unidade not in unidades_permitidas(col):
                    raise ValueError(
                        f"Confirme a unidade de {origem}; unidade ausente ou incompatível."
                    )
                fator, offset = unidades_permitidas(col)[unidade]

                def converter(v, virgula=fonte.virgula_decimal, f=fator, o=offset, nome=origem):
                    if not v.strip() or v.strip().lower() in {
                        "-",
                        "--",
                        "nan",
                        "na",
                        "n/a",
                        "s/d",
                        "sd",
                        "null",
                        "none",
                    }:
                        return ""
                    try:
                        numero = _numero(v, virgula)[0]
                        resultado = numero * f + o
                        if not math.isfinite(resultado):
                            raise ValueError(v)
                        return str(resultado)
                    except (ValueError, TypeError, OverflowError) as exc:
                        raise ValueError(
                            f"{nome}: não foi possível converter '{v}'. Confira a unidade e o valor."
                        ) from exc

                valores = valores.map(converter)
            df[alvo] = valores
        for campo, valor in constantes.items():
            if campo not in {"origem_dado", "caldeira_id", "tipo"}:
                raise ValueError("Constante não permitida; informe medições na planilha.")
            if campo not in df and valor:
                df[campo] = valor
        faltam = [c.rotulo for c in contrato.colunas if c.obrigatoria and c.nome not in df]
        if faltam:
            raise ValueError(
                f"{contrato.titulo}: associe as colunas obrigatórias: {', '.join(faltam)}."
            )
        saida[destino] = df.to_csv(index=False, lineterminator="\n").encode("utf-8")
        adaptacoes.append(
            {
                "fonte": fonte.chave,
                "arquivo": fonte.arquivo,
                "aba": fonte.aba,
                "tabela": tabela,
                "mapeamento": mapa,
                "unidades": unidades,
                "constantes": constantes,
                "linhas_originais": fonte.bruto["linha"].tolist(),
                "colunas_nao_usadas": [c for c in fonte.bruto if c != "linha" and c not in mapa],
                "sha256_adaptado": hashlib.sha256(saida[destino]).hexdigest(),
            }
        )
    if not adaptacoes:
        raise ValueError("Selecione ao menos uma tabela para analisar.")
    originais = []
    for i, (nome, conteudo) in enumerate(arquivos.items(), 1):
        guardado = f"original_{i:02d}.bin"
        saida[guardado] = conteudo
        originais.append(
            {
                "nome": nome,
                "arquivo_guardado": guardado,
                "tipo": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                if nome.lower().endswith(".xlsx")
                else "text/csv",
                "sha256": hashlib.sha256(conteudo).hexdigest(),
            }
        )
    saida["euler_importacao.json"] = json.dumps(
        {"versao": 1, "originais": originais, "adaptacoes": adaptacoes},
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
    ).encode("utf-8")
    return saida


def guia_importacao(arquivos, *, chave, salvo=None, origem=None, caldeira=None):
    """Formulário compartilhado; retorna lote adaptado e perfil somente após confirmação."""
    import streamlit as st

    fontes = ler_fontes(arquivos)
    identidade = assinatura_envio(arquivos, {})[:12]
    base = f"{chave}_{identidade}"
    decisoes, perfil = {}, {}
    st.markdown("**Confira como a EULER vai ler sua planilha**")
    st.caption("Sugestões precisam da sua confirmação. Valores vazios continuam ausentes.")
    for i, fonte in enumerate(fontes):
        prefixo = f"{base}_{i}"
        with st.expander(f"{fonte.chave} · {len(fonte.bruto)} registros", expanded=True):
            tabelas = ["", *TABELAS]
            sugestao = sugerir_tabela(fonte) or ""
            tabela = st.selectbox(
                "Que registros esta tabela contém?",
                tabelas,
                index=tabelas.index(sugestao),
                format_func=lambda t: (
                    TABELAS[t].titulo if t else "Selecionar / não usar esta tabela"
                ),
                key=f"{prefixo}_tabela",
            )
            if not tabela:
                continue
            contrato = TABELAS[tabela]
            colunas = [c for c in fonte.bruto if c != "linha"]
            sugestoes = sugerir_mapeamento(colunas, tabela, salvo)
            mapa, unidades = {}, {}
            reconhecidas = len(sugestoes)
            st.caption(
                f"{reconhecidas} de {len(colunas)} colunas reconhecidas. "
                "Confira as associações antes de confirmar."
            )
            with st.expander(
                "Conferir ou ajustar colunas e unidades",
                expanded=any(
                    c not in sugestoes or (c != sugestoes[c] and c not in ALIASES_COLUNAS)
                    for c in colunas
                ),
            ):
                for j, coluna in enumerate(colunas):
                    c1, c2 = st.columns([2, 1])
                    opcoes = ["", *[c.nome for c in contrato.colunas]]
                    alvo = c1.selectbox(
                        f"{coluna} →",
                        opcoes,
                        index=opcoes.index(sugestoes.get(coluna, "")),
                        format_func=lambda n, t=contrato: (
                            t.coluna(n).rotulo_inicial if n else "Não usar"
                        ),
                        key=f"{prefixo}_{tabela}_{j}_col",
                        help="Associe pela grandeza; não confunda total de vapor com vazão, ou preço total com preço por tonelada.",
                    )
                    if not alvo:
                        continue
                    mapa[coluna] = alvo
                    col = contrato.coluna(alvo)
                    if col.tipo == "numero":
                        opcoes_u = ["", *unidades_permitidas(col)]
                        explicita = coluna == alvo or ALIASES_COLUNAS.get(coluna) == alvo
                        unidade = c2.selectbox(
                            "Unidade no arquivo",
                            opcoes_u,
                            index=1 if explicita else 0,
                            format_func=lambda u: u or "Confirmar unidade",
                            key=f"{prefixo}_{tabela}_{j}_{alvo}_unit",
                            help=col.descricao,
                        )
                        unidades[coluna] = unidade
                        if unidade and unidade != col.unidade:
                            c2.caption(f"Será convertida para {col.unidade}.")
            constantes = {}
            if (
                "caldeira_id" in {c.nome for c in contrato.colunas}
                and "caldeira_id" not in mapa.values()
            ):
                constantes["caldeira_id"] = st.text_input(
                    "Código da caldeira (aplica-se a todas as linhas desta tabela)",
                    value=caldeira or "",
                    key=f"{prefixo}_caldeira",
                ).strip()
            tem_origem = any(_normal(c) in {"origem dado", "origem do dado"} for c in colunas)
            if (
                "origem_dado" in {c.nome for c in contrato.colunas}
                and "origem_dado" not in mapa.values()
                and not tem_origem
            ):
                origens = ["", "real", "publico", "sintetico"]
                constantes["origem_dado"] = st.selectbox(
                    "Origem de todos os registros desta tabela",
                    origens,
                    index=origens.index(origem) if origem in origens else 0,
                    format_func=lambda o: {
                        "": "Informar origem",
                        "real": "Empresa · uso autorizado",
                        "publico": "Dados públicos",
                        "sintetico": "Demonstração sintética",
                    }[o],
                    key=f"{prefixo}_origem",
                )
            if tabela == "combustivel" and "tipo" not in mapa.values():
                constantes["tipo"] = st.selectbox(
                    "O que todas as linhas representam?",
                    ["", "recebimento", "estoque"],
                    format_func=lambda t: t or "Informe ou associe uma coluna com o tipo",
                    key=f"{prefixo}_tipo",
                )
            decisoes[fonte.chave] = {
                "tabela": tabela,
                "mapeamento": mapa,
                "unidades": unidades,
                "constantes": constantes,
            }
            perfil.update(mapa)
            with st.expander("Ver primeiras linhas do arquivo original"):
                st.dataframe(fonte.bruto.head(8), hide_index=True, width="stretch")
    identidade_decisoes = assinatura_envio(arquivos, decisoes)[:12]
    confirmado = st.checkbox(
        "Conferi as colunas, as unidades e a origem dos registros selecionados",
        key=f"{base}_{identidade_decisoes}_confirmado",
    )
    st.caption(
        "O envio preserva os arquivos originais e um registro das adaptações. Nenhum arquivo é enviado ao GitHub."
    )
    if not confirmado:
        return None, perfil
    return preparar_lote(arquivos, decisoes), perfil
