"""Auditoria retrospectiva do mesmo ensaio EPA; protocolo em docs/fisica.

As faixas por reamostragem não são incerteza instrumental nem prova causal.
Nenhuma escolha de modelo é feita para maximizar o sinal ou o valor financeiro.
"""

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from ensaio_horario import DADOS, _ajuste, executar, preparar

ROOT = Path(__file__).resolve().parents[1]
SEMENTE = 20261003
ARQUIVOS_METODO = [
    "app/robustez_ensaio.py",
    "app/ensaio_horario.py",
    "euler/deteccao.py",
    "euler/economia.py",
    "validation/public/ensaio_horario/fontes.json",
    "docs/fisica/protocolo_robustez_ensaio_publico.md",
    "scripts/auditar_ensaio_publico.py",
    "tests/test_robustez_ensaio.py",
]


def assinaturas() -> dict:
    """SHA-256 do texto UTF-8 com quebras LF: estável entre checkouts Windows/Linux.

    O CSV público permanece conferido por seus bytes originais, sem normalização.
    """
    return {
        p: hashlib.sha256((ROOT / p).read_text(encoding="utf-8").encode("utf-8")).hexdigest()
        for p in ARQUIVOS_METODO
    }


def _resumo(comp: pd.DataFrame, previsto: np.ndarray) -> dict:
    if comp.empty or not np.isfinite(previsto).all() or np.any(previsto <= 0):
        return {"horas": len(comp), "delta_pct": None, "delta_gj": None}
    delta = float(np.sum(comp.energia_gj.to_numpy() - previsto))
    return {"horas": len(comp), "delta_gj": delta, "delta_pct": 100 * delta / float(sum(previsto))}


def comparar_modelos(ref: pd.DataFrame, comp: pd.DataFrame) -> dict:
    """Linear, quadrático e faixas nas mesmas horas, restritas ao suporte de janeiro."""
    c = comp[comp.vapor_t.between(ref.vapor_t.min(), ref.vapor_t.max())].copy()
    for largura in (5, 10):
        grupos = ref.assign(faixa=np.floor(ref.vapor_t / largura)).groupby("faixa")
        tab = grupos.agg(n=("vapor_t", "size"), v=("vapor_t", "sum"), e=("energia_gj", "sum"))
        tab = tab[tab.n >= 10]
        c[f"faixa_{largura}"] = np.floor(c.vapor_t / largura).map(tab.e / tab.v)
    c = c.dropna(subset=["faixa_5", "faixa_10"])
    a, b, _ = _ajuste(ref)
    # Centragem para evitar mau condicionamento das potências de carga.
    centro = float(ref.vapor_t.mean())
    x = ref.vapor_t.to_numpy() - centro
    beta = np.linalg.lstsq(
        np.column_stack([np.ones(len(x)), x, x * x]), ref.energia_gj, rcond=None
    )[0]
    z = c.vapor_t.to_numpy() - centro
    previsoes = {
        "linear": (a + b * c.vapor_t).to_numpy(),
        "quadratico": beta[0] + beta[1] * z + beta[2] * z * z,
        "faixas_5_t_h": (c.vapor_t * c.faixa_5).to_numpy(),
        "faixas_10_t_h": (c.vapor_t * c.faixa_10).to_numpy(),
    }
    return {
        "horas_comuns": len(c),
        "horas_excluidas": len(comp) - len(c),
        "metodos": [{"metodo": k, **_resumo(c, v)} for k, v in previsoes.items()],
    }


def avaliar_temporal(ref: pd.DataFrame) -> list[dict]:
    """Dois testes cronológicos em janeiro; carga observada no treino, sem vazamento."""
    saida = []
    for fim, inicio, ultimo in (("14", "15", "21"), ("21", "22", "31")):
        treino = ref[ref.Date <= f"2023-01-{fim}"]
        teste = ref[ref.Date.between(f"2023-01-{inicio}", f"2023-01-{ultimo}")]
        c = teste[teste.vapor_t.between(treino.vapor_t.min(), treino.vapor_t.max())]
        try:
            a, b, _ = _ajuste(treino)
            pred = (a + b * c.vapor_t).to_numpy()
            motivo = None
        except ValueError:
            c = c.iloc[:0]
            pred = np.array([])
            motivo = "Referência insuficiente neste trecho; não foi substituída por outro período."
        base = _resumo(c, pred)
        saida.append(
            {
                "treino_fim": f"2023-01-{fim}",
                "teste_inicio": f"2023-01-{inicio}",
                "teste_fim": f"2023-01-{ultimo}",
                "horas_treino": len(treino),
                "horas_teste": len(teste),
                "horas_comparaveis": len(c),
                "vies_pct": base["delta_pct"],
                "motivo": motivo,
                "erro_absoluto_medio_gj_h": None
                if c.empty
                else float(np.mean(abs(c.energia_gj - pred))),
            }
        )
    return saida


def _referencias(ref: pd.DataFrame, comp: pd.DataFrame) -> dict:
    refs = {
        "janeiro_completo": ref,
        "janeiro_01_15": ref[ref.Date <= "2023-01-15"],
        "janeiro_16_31": ref[ref.Date >= "2023-01-16"],
    }
    if any(len(r) < 3 or r.vapor_t.var() <= 0 for r in refs.values()):
        return {
            "horas_comuns": 0,
            "metodos": [],
            "motivo": "Uma metade de janeiro não permite ajuste; comparação bloqueada.",
        }
    minimo = max(r.vapor_t.min() for r in refs.values())
    maximo = min(r.vapor_t.max() for r in refs.values())
    c = comp[comp.vapor_t.between(minimo, maximo)]
    metodos = []
    for nome, r in refs.items():
        a, b, _ = _ajuste(r)
        metodos.append({"referencia": nome, **_resumo(c, (a + b * c.vapor_t).to_numpy())})
    return {"horas_comuns": len(c), "metodos": metodos}


def blocos_moveis(n: int, tamanho: int, repeticoes: int, rng) -> np.ndarray:
    """Índices de blocos contíguos não circulares; preserva n dias por repetição."""
    if not 1 <= tamanho <= n or repeticoes < 1:
        raise ValueError("Tamanho de bloco ou número de repetições inválido.")
    inicios = rng.integers(0, n - tamanho + 1, size=(repeticoes, int(np.ceil(n / tamanho))))
    return (inicios[:, :, None] + np.arange(tamanho)).reshape(repeticoes, -1)[:, :n]


def _estatisticas_diarias(d: pd.DataFrame, mes: str) -> np.ndarray:
    """Somas suficientes para OLS. Zero de contribuição não é dado imputado."""
    x = d.assign(n=1, xx=d.vapor_t**2, xy=d.vapor_t * d.energia_gj)
    cols = ["n", "vapor_t", "energia_gj", "xx", "xy"]
    dias = pd.date_range(mes + "-01", periods=pd.Period(mes).days_in_month).strftime("%Y-%m-%d")
    return x.groupby("Date")[cols].sum().reindex(dias, fill_value=0).to_numpy(float)


def _reamostrar(ref, comp, mes, repeticoes, rng) -> list[dict]:
    r, c = _estatisticas_diarias(ref, "2023-01"), _estatisticas_diarias(comp, mes)
    saida = []
    for tamanho in (1, 3, 7):
        sr = r[blocos_moveis(len(r), tamanho, repeticoes, rng)].sum(axis=1)
        sc = c[blocos_moveis(len(c), tamanho, repeticoes, rng)].sum(axis=1)
        n, sx, sy, sxx, sxy = sr.T
        with np.errstate(divide="ignore", invalid="ignore"):
            b = (sxy - sx * sy / n) / (sxx - sx * sx / n)
            a = (sy - b * sx) / n
            esperado = a * sc[:, 0] + b * sc[:, 1]
            pct = 100 * (sc[:, 2] - esperado) / esperado
        valido = np.isfinite(pct) & (esperado > 0) & (sc[:, 0] > 0) & (n > 2)
        quantis = np.quantile(pct[valido], [0.025, 0.975]) if valido.any() else [None, None]
        saida.append(
            {
                "bloco_dias": tamanho,
                "validas": int(valido.sum()),
                "invalidas": int((~valido).sum()),
                "quantil_025_pct": None if quantis[0] is None else float(quantis[0]),
                "quantil_975_pct": None if quantis[1] is None else float(quantis[1]),
            }
        )
    return saida


def _diagnostico(ref: pd.DataFrame) -> dict:
    a, b, r2 = _ajuste(ref)
    d = ref.copy()
    d["residuo"] = d.energia_gj - a - b * d.vapor_t
    # Pares separados por exatamente 1/24 h; não comprimir a linha do tempo.
    # Para 24 h, não se exige observação em todas as horas intermediárias.
    d["instante"] = pd.to_datetime(d.Date) + pd.to_timedelta(d.Hour, unit="h")
    s = d.set_index("instante").residuo
    corrs = {}
    for lag in (1, 24):
        pares = pd.concat(
            [s.rename("atual"), s.shift(freq=pd.Timedelta(hours=lag)).rename("anterior")], axis=1
        ).dropna()
        valor = pares.atual.corr(pares.anterior) if len(pares) > 2 else float("nan")
        corrs[str(lag)] = {
            "pares": len(pares),
            "correlacao": float(valor) if np.isfinite(valor) else None,
        }
    return {"r2": r2, "autocorrelacao_residuos": corrs, "validacao_temporal": avaliar_temporal(ref)}


def auditar(repeticoes: int = 2000) -> tuple[dict, pd.DataFrame]:
    """Reexecuta dados reais, reconcilia linha a linha e publica todos os resultados."""
    motor = executar()  # Inclui verificação SHA-256 e bloqueio de duplicatas.
    bruto = pd.read_csv(DADOS / "ingredion_2023q1.csv", dtype={"Unit ID": str})
    trilha = bruto.copy()
    trilha["mes"] = trilha.Date.str[:7]
    trilha["decisao"] = "excluido_qualidade"
    trilha["motivo"] = ""
    colunas = ["Operating Time", "Heat Input (mmBtu)", "Steam Load (1000 lb/hr)"]
    numericos = bruto[colunas].apply(pd.to_numeric, errors="coerce")
    regras = [
        (~np.isfinite(numericos).all(axis=1), "Dado numérico ausente ou não finito; "),
        (~numericos["Operating Time"].eq(1), "Hora de operação incompleta; "),
        (~bruto["Heat Input Measure Indicator"].eq("Measured"), "Energia sem indicador Measured; "),
        (
            numericos["Heat Input (mmBtu)"].le(0) | numericos["Steam Load (1000 lb/hr)"].le(0),
            "Energia ou vapor não positivo; ",
        ),
    ]
    for mascara, motivo in regras:
        trilha.loc[mascara, "motivo"] += motivo
    for coluna in ("previsto_gj", "delta_gj", "preco_usd_gj", "valor_condicional_usd"):
        trilha[coluna] = np.nan
    saida = {
        "protocolo": "robustez-v1",
        "semente": SEMENTE,
        "repeticoes": repeticoes,
        "fonte_sha256": motor["fonte"]["recorte_sha256"],
        "assinaturas": assinaturas(),
        "versoes": {"numpy": np.__version__, "pandas": pd.__version__},
        "natureza": "sensibilidade retrospectiva; não é inferência causal ou metrológica",
        "unidades": {},
    }
    for unidade, original in bruto.groupby("Unit ID", sort=True):
        d, qualidade = preparar(original)
        ref = d[d.mes == "2023-01"]
        a, b, _ = _ajuste(ref)
        trilha.loc[d.index, "decisao"] = "fora_faixa"
        trilha.loc[d.index, "motivo"] = "Carga fora do intervalo observado em janeiro."
        trilha.loc[ref.index, "decisao"] = "referencia"
        trilha.loc[ref.index, "motivo"] = "Hora usada no ajuste de janeiro."
        trilha.loc[d.index, "energia_gj"] = d.energia_gj
        trilha.loc[d.index, "vapor_t"] = d.vapor_t
        meses = []
        for m in motor["unidades"][unidade]["comparacoes"]:
            todas = d[d.mes == m["mes"]]
            c = todas[todas.vapor_t.between(ref.vapor_t.min(), ref.vapor_t.max())].copy()
            c["previsto"] = a + b * c.vapor_t
            c["delta"] = c.energia_gj - c.previsto
            trilha.loc[c.index, "decisao"] = "comparavel"
            trilha.loc[c.index, "motivo"] = "Hora válida dentro da faixa de carga de janeiro."
            for nome, val in (
                ("previsto_gj", c.previsto),
                ("delta_gj", c.delta),
                ("preco_usd_gj", m["preco_usd_gj"]),
                ("valor_condicional_usd", c.delta * m["preco_usd_gj"]),
            ):
                trilha.loc[c.index, nome] = val
            if not np.isclose(c.delta.sum(), m["delta_gj"], rtol=0, atol=1e-6):
                raise ValueError("Auditoria não reconcilia com o motor.")
            dias = c.groupby("Date").agg(delta=("delta", "sum"), previsto=("previsto", "sum"))
            sem_dia = 100 * (c.delta.sum() - dias.delta) / (c.previsto.sum() - dias.previsto)
            meses.append(
                {
                    "mes": m["mes"],
                    "delta_original_pct": m["delta_pct"],
                    "delta_original_gj": m["delta_gj"],
                    "valor_condicional_usd": m["valor_referencia_usd"],
                    "horas_comparaveis": len(c),
                    "horas_validas": len(todas),
                    "modelos": comparar_modelos(ref, todas),
                    "referencias": _referencias(ref, todas),
                    "retirada_de_um_dia_pct": {
                        "min": float(sem_dia.min()),
                        "max": float(sem_dia.max()),
                    },
                    "reamostragem": _reamostrar(
                        ref, c, m["mes"], repeticoes, np.random.default_rng(SEMENTE)
                    ),
                    "reducao_energia_reportada_para_zerar_pct": 100
                    * float(c.delta.sum() / c.energia_gj.sum()),
                    "causa_comprovada": False,
                    "economia_recuperavel_usd": None,
                }
            )
        saida["unidades"][unidade] = {
            "qualidade": qualidade,
            "diagnostico": _diagnostico(ref),
            "meses": meses,
        }
    return saida, trilha


def carregar_auditoria() -> dict | None:
    """Só apresenta artefato local se entradas e método ainda forem os auditados."""
    arquivo = DADOS / "auditoria_robustez.json"
    if not arquivo.exists():
        return None
    try:
        r = json.loads(arquivo.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    dado_hash = hashlib.sha256((DADOS / "ingredion_2023q1.csv").read_bytes()).hexdigest()
    if r.get("assinaturas") != assinaturas() or r.get("fonte_sha256") != dado_hash:
        return None
    return r
