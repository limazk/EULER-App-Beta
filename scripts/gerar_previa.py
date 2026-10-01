"""Gera a prévia interativa do app EULER (uma página HTML que abre sem o Streamlit).

A página mostra as telas com o visual do app e os resultados **calculados pelo motor** para o
caso de demonstração sintético: nada é recalculado nem inventado no navegador. A
investigação é calculada para as combinações de períodos que a prévia oferece (referência
começando em 03/08 e comparação depois dela).

Uso:
    python scripts/gerar_previa.py                 # demo/previa/index.html
    python scripts/gerar_previa.py saida.html

A página é o conteúdo do corpo (sem <html>/<head>), pronta para publicar como Artifact;
para abrir direto no navegador, ela também funciona assim.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "app"))

import pandas as pd
from formatacao import (
    SERIES,
    STATUS,
    diferenca,
    linhas_por_periodo,
    partes_do_selo,
    valor_formatado,
)
from graficos import CORES

from euler.capacidades import avaliar
from euler.combustivel import (
    extrato_por_fornecedor,
    extrato_semanal,
    frase_tonelada_vs_energia,
)
from euler.formato import num, pct, plural
from euler.investigacao import SUFIXO_CADASTRAR, investigar
from euler.io import importar_pasta
from euler.io.esquemas import TABELAS
from euler.periodos import periodos_entre_estoques
from euler.relatorio import gerar_html
from euler.textos import (
    AVISO_PROTOTIPO,
    ESTAGIOS_MODELO,
    FRASE_PRODUTO,
    PERGUNTA_CENTRAL,
    RODAPE_SEGURANCA,
)
from euler.vapor import p_atm_por_altitude_bar

MODELO = RAIZ / "scripts" / "previa_modelo.html"
ALTITUDE_DEMO_M = 1000.0
REF_FIM_MAX = 3  # a referência termina entre a semana 1 e a 4


def _versao() -> str:
    saida = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], cwd=RAIZ, capture_output=True, text=True,
        check=False,
    )  # fmt: skip
    return saida.stdout.strip() or "desconhecida"


def _importacao(pacote) -> dict:
    avisos = pacote.tabela_avisos()
    contagem = avisos["Gravidade"].value_counts()
    tabelas = []
    for nome, tabela in TABELAS.items():
        imp = pacote.importacoes.get(nome)
        if imp is None:
            situacao, n = "não enviada", "—"
        elif imp.bloqueada:
            situacao, n = "bloqueada (ver erros)", str(len(imp.original))
        else:
            situacao, n = "importada", str(len(imp.dados))
        tabelas.append([tabela.titulo, tabela.arquivo, n, situacao])
    linhas = avisos.astype({"Linha": "string"}).fillna({"Linha": "—"})
    return {
        "contagem": {g: int(contagem.get(g, 0)) for g in ("Erro", "Atenção", "Informação")},
        "n_tabelas": len(pacote.importacoes),
        "tabelas": tabelas,
        "avisos": [[r.Gravidade, r.Tabela, str(r.Linha), r.Aviso] for r in linhas.itertuples()],
    }


def _capacidades(pacote) -> list[dict]:
    return [
        {
            "nome": c.nome,
            "pergunta": c.pergunta,
            "situacao": c.situacao,
            "motivos": list(c.motivos),
            "o_que_fazer": list(c.o_que_fazer),
        }
        for c in avaliar(pacote)
    ]


def _series(pacote) -> dict:
    diario = pacote.dados("diario")
    saida = {}
    for coluna, (botao, titulo, unidade, formato) in SERIES.items():
        if coluna not in diario or not diario[coluna].notna().any():
            continue
        d = diario.dropna(subset=[coluna, "instante_observado"])
        d = d[d["regime"].fillna("estavel") != "parada"]
        dias = d.groupby(d["instante_observado"].dt.tz_localize(None).dt.normalize())[coluna].mean()
        saida[coluna] = {
            "botao": botao,
            "titulo": f"{titulo} ({unidade}, média do dia)",
            "unidade": unidade,
            "casas": int(formato[1]),
            "pontos": [[f"{dia:%Y-%m-%d}", round(float(v), 3)] for dia, v in dias.items()],
        }
    return saida


def _extrato(pacote) -> dict:
    combustivel, amostras = pacote.dados("combustivel"), pacote.dados("amostras")
    extrato = extrato_por_fornecedor(combustivel, amostras)
    lotes, forn = extrato.lotes, extrato.fornecedores
    determinados = lotes[lotes["situacao"] == "determinada"]
    com_custo = determinados.dropna(subset=["brl_gj"])
    fornecedores = sorted(combustivel["fornecedor_id"].dropna().unique())
    semanal = extrato_semanal(lotes)
    alertas = extrato.alertas_umidade
    resumo_alertas = []
    for f, g in alertas.groupby("fornecedor_id"):
        acima = int((g["alerta_direcao"] == "acima").sum())
        abaixo = len(g) - acima
        partes = [f"{acima} acima" if acima else "", f"{abaixo} abaixo" if abaixo else ""]
        resumo_alertas.append([f, f"{' e '.join(x for x in partes if x)} da faixa"])
    nao_det = extrato.lotes_nao_determinados
    datas = combustivel[combustivel["tipo"] == "recebimento"]["data"]
    return {
        "periodo": f"{datas.min():%d/%m/%Y} a {datas.max():%d/%m/%Y}",
        "frase": frase_tonelada_vs_energia(forn),
        "metricas": [
            [
                "Energia entregue (lotes determinados)",
                f"{num(determinados['energia_gj'].sum(), 0)} GJ",
            ],
            [
                "Custo médio da energia",
                f"R$ {num(com_custo['preco_brl'].sum() / com_custo['energia_gj'].sum())}/GJ",
            ],
            ["Lotes com energia determinada", f"{len(determinados)} de {len(lotes)}"],
        ],
        "cores": {f: CORES[i] for i, f in enumerate(fornecedores[: len(CORES)])},
        "barras": [
            {
                "f": r.fornecedor_id,
                "t": float(r.brl_t),
                "gj": float(r.brl_gj),
                "rt": f"R$ {num(r.brl_t)}/t",
                "rgj": f"R$ {num(r.brl_gj)}/GJ",
            }
            for r in forn.dropna(subset=["brl_t", "brl_gj"]).itertuples()
        ],
        "tabela": [
            [
                f"{r.posicao_energia}º" if pd.notna(r.posicao_energia) else "—",
                r.fornecedor_id,
                str(r.lotes),
                num(r.massa_t, 1),
                num(r.brl_t),
                pct(r.umidade_media),
                f"{pct(r.umidade_referencia)} → {pct(r.umidade_recente)}",
                num(r.energia_gj, 0),
                num(r.brl_gj),
                str(r.alertas_umidade),
            ]
            for r in forn.itertuples()
        ],
        "semanal": [
            [
                r.fornecedor_id,
                f"{r.semana:%Y-%m-%d}",
                round(float(r.umidade_media), 4),
                int(r.lotes),
            ]
            for r in semanal.itertuples()
        ],
        "n_alertas": len(alertas),
        "alertas": resumo_alertas,
        "nao_determinados": [
            [
                f"{r.data:%d/%m/%Y %H:%M}",
                r.fornecedor_id,
                r.lote_id,
                num(r.massa_kg / 1000 if pd.notna(r.massa_kg) else None, 1),
                r.motivo,
            ]
            for r in nao_det.itertuples()
        ],
    }


def _hipotese(h: dict) -> dict:
    rotulo, cor, _ = STATUS[h["status"]]
    efeito = h["efeito"]["consumo_pct"]
    return {
        "status": h["status"],
        "rotulo": rotulo,
        "cor": cor,
        "titulo": h["titulo"],
        "porque": h["porque"],
        "efeito": (
            f"Efeito estimado no consumo: {'+' if efeito >= 0 else ''}{num(efeito, 1)}%"
            if efeito is not None and h["status"] in ("sustentada", "possivel")
            else ""
        ),
        "verificacao": h["verificacao"],
    }


def _investigacao(j: dict) -> dict:
    """O que a tela Investigação mostra para uma comparação (mesmas regras da tela)."""
    om = j["o_que_mudou"]
    consumo = om.get("consumo_especifico")
    if consumo and consumo["variacao"] is not None and consumo["referencia"]:
        variacao = 100 * consumo["variacao"] / consumo["referencia"]
        kpi_consumo = {
            "valor": f"{num(consumo['comparacao'], 3)} t/t",
            "delta": f"{'+' if variacao >= 0 else ''}{num(variacao, 1)}% sobre "
            f"{num(consumo['referencia'], 3)} t/t",
            "sobe": variacao >= 0,
            "selo": partes_do_selo(consumo),
        }
    else:
        kpi_consumo = None
    valor = j["valor_em_jogo"]
    if valor:
        incerteza = (
            f"Incerteza: ± R$ {num(valor['incerteza_brl'], 0)}. "
            if valor["incerteza_brl"] is not None
            else ""
        )
        kpi_valor = {
            "valor": f"R$ {num(valor['valor_brl'], 0)}",
            "legenda": incerteza + valor["base"],
        }
    else:
        kpi_valor = {"valor": None, "legenda": j["valor_em_jogo_motivo"]}
    hips = j["hipoteses"]
    contagem = {s: sum(h["status"] == s for h in hips) for s in STATUS}
    partes = [
        plural(contagem["possivel"] + contagem["nao_avaliavel"], "em aberto", "em aberto"),
        plural(contagem["descartada"], "descartada", "descartadas"),
    ]
    if contagem["oposta"]:
        partes.append(plural(contagem["oposta"], "no sentido contrário", "no sentido contrário"))
    indicadores = [
        {
            "nome": c["nome"][0].upper() + c["nome"][1:],
            "ref": valor_formatado(c["referencia"], c["unidade"]),
            "comp": valor_formatado(c["comparacao"], c["unidade"]),
            "dif": diferenca(c),
            "selo": partes_do_selo(c),
        }
        for c in om["indicadores"]
        if not (c["referencia"] is None and c["comparacao"] is None)
    ]
    fechamento = om.get("fechamento") or {}
    falta = j["o_que_falta"]
    return {
        "rotulo_ref": j["periodos"]["referencia"]["rotulo"],
        "rotulo_comp": j["periodos"]["comparacao"]["rotulo"],
        "conclusao": j["conclusao"],
        "proxima": j["proxima_verificacao"],
        "kpi_consumo": kpi_consumo,
        "kpi_valor": kpi_valor,
        "kpi_expl": {
            "n": contagem["sustentada"],
            "legenda": " · ".join(partes) + ". Compatível não é causa comprovada.",
        },
        "frase": om["frase"],
        "custo": om["custo_vapor"]["frase"] if om["custo_vapor"] else None,
        "indicadores": indicadores,
        "sustentadas": [_hipotese(h) for h in hips if h["status"] == "sustentada"],
        "opostas": [_hipotese(h) for h in hips if h["status"] == "oposta"],
        "abertas": [_hipotese(h) for h in hips if h["status"] in ("possivel", "nao_avaliavel")],
        "descartadas": [_hipotese(h) for h in hips if h["status"] == "descartada"],
        "fechamento": [x for x in (fechamento.get("frase"), fechamento.get("frase_com_condicionais")) if x],
        "falta_cadastrar": [f.removesuffix(SUFIXO_CADASTRAR) for f in falta if f.endswith(SUFIXO_CADASTRAR)],
        "falta_outros": [f for f in falta if not f.endswith(SUFIXO_CADASTRAR)],
        "independencia": j["independencia"]["nota"] + " (E12)",
        "relatorio": gerar_html(j),
    }  # fmt: skip


def dados_da_previa() -> dict:
    pacote = importar_pasta(
        RAIZ / "demo" / "caso_demo", p_atm_bar=p_atm_por_altitude_bar(ALTITUDE_DEMO_M)
    )
    periodos = periodos_entre_estoques(pacote)
    n = len(periodos)
    combos = {}
    for r in range(REF_FIM_MAX + 1):
        for a in range(r + 1, n):
            for b in range(a, n):
                ref = (periodos[0][0], periodos[r][1])
                comp = (periodos[a][0], periodos[b][1])
                combos[f"{r}|{a}-{b}"] = _investigacao(investigar(pacote, ref, comp))
                print(f"  comparação {r}|{a}-{b}", flush=True)
    avisos = pacote.tabela_avisos()
    atencao = avisos[avisos["Gravidade"].isin(["Erro", "Atenção"])]
    return {
        "versao": _versao(),
        "rotulo_dados": "caso de demonstração (caldeira sintética de 20 t/h, 8 semanas)",
        "textos": {
            "frase": FRASE_PRODUTO,
            "pergunta": PERGUNTA_CENTRAL,
            "aviso": AVISO_PROTOTIPO,
            "rodape": RODAPE_SEGURANCA,
            "estagios": [list(e) for e in ESTAGIOS_MODELO],
        },
        "periodos": [
            {
                "ini": f"{a:%d/%m}",
                "fim": f"{b:%d/%m}",
                "ini_iso": f"{a:%Y-%m-%dT%H:%M}",
                "fim_iso": f"{b:%Y-%m-%dT%H:%M}",
                "dias": round((b - a).total_seconds() / 86400),
            }
            for a, b in periodos
        ],
        "importacao": _importacao(pacote),
        "qualidade": [f"{r.Tabela}: {r.Aviso}" for r in atencao.itertuples()],
        "capacidades": _capacidades(pacote),
        "por_periodo": linhas_por_periodo(pacote),
        "series": _series(pacote),
        "extrato": _extrato(pacote),
        "combos": combos,
        "padrao": [3, 4, 5],
    }


def gerar(destino: Path) -> Path:
    dados = dados_da_previa()
    texto = json.dumps(dados, ensure_ascii=False, separators=(",", ":"))
    texto = texto.replace("</", "<\\/")  # o JSON vai dentro de <script>
    html = MODELO.read_text(encoding="utf-8").replace("/*DADOS*/{}", texto)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(html, encoding="utf-8")
    return destino


if __name__ == "__main__":
    saida = Path(sys.argv[1]) if len(sys.argv) > 1 else RAIZ / "demo" / "previa" / "index.html"
    print(gerar(saida))
