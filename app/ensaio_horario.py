"""Ensaio exploratório EPA: registros horários reais, sem inventar regime estável.

Rota separada do balanço estacionário: energia reportada em PCS / vapor
reportado. Modelo estatístico condicionado à carga, sem diagnóstico causal.
Não importa GJ como toneladas no baseline físico de combustível.
"""

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

from euler.deteccao import comparar
from euler.economia import valorizar_energia
from euler.tipos import Grandeza

DADOS = Path(__file__).resolve().parents[1] / "validation/public/ensaio_horario"
GJ_MMBTU = 1.05505585262
T_MIL_LB = 0.45359237


def preparar(bruto: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Uma instalação/unidade; horas completas medidas, positivas e sem duplicatas.

    Nenhuma interpolação: cada registro EPA já é agregado de uma hora.
    Não usar trapézios nem integrar lacunas entre médias horárias.
    """
    chaves = ["Facility ID", "Unit ID", "Date", "Hour"]
    if bruto.duplicated(chaves).any():
        raise ValueError("Registros horários duplicados: análise bloqueada.")
    if len(bruto[["Facility ID", "Unit ID"]].drop_duplicates()) != 1:
        raise ValueError("Analise uma unidade por vez, sem misturar fronteiras.")
    d = bruto.copy()
    colunas = ["Operating Time", "Heat Input (mmBtu)", "Steam Load (1000 lb/hr)"]
    for c in colunas:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    finitos = np.isfinite(d[colunas]).all(axis=1)
    completos = d["Operating Time"].eq(1)
    medidos = d["Heat Input Measure Indicator"].eq("Measured")
    positivos = d["Heat Input (mmBtu)"].gt(0) & d["Steam Load (1000 lb/hr)"].gt(0)
    validos = finitos & completos & medidos & positivos
    resumo = {"recebidos": len(d), "usados": int(validos.sum()), "excluidos": int((~validos).sum())}
    d = d.loc[validos].copy()
    datas = pd.to_datetime(d.Date, format="%Y-%m-%d", errors="raise")
    d["mes"] = datas.dt.strftime("%Y-%m")
    d["vapor_t"] = d["Steam Load (1000 lb/hr)"] * T_MIL_LB
    d["energia_gj"] = d["Heat Input (mmBtu)"] * GJ_MMBTU
    return d.sort_values(["Date", "Hour"]), resumo


def _ajuste(ref: pd.DataFrame) -> tuple[float, float, float]:
    x, y = ref.vapor_t.to_numpy(), ref.energia_gj.to_numpy()
    if len(x) < 3 or np.var(x) <= 0:
        raise ValueError("Referência insuficiente para comparar cargas.")
    b = float(np.sum((x - x.mean()) * (y - y.mean())) / np.sum((x - x.mean()) ** 2))
    a = float(y.mean() - b * x.mean())
    r2 = float(1 - np.sum((y - a - b * x) ** 2) / np.sum((y - y.mean()) ** 2))
    return a, b, r2


def _faixas(ref: pd.DataFrame, comp: pd.DataFrame, largura: int) -> dict:
    """Conferência por faixas: mínimo 10 horas na referência, sem extrapolar.

    Método de sensibilidade descritivo; não equivale a pareamento causal.
    """
    a = (
        ref.assign(faixa=np.floor(ref.vapor_t / largura))
        .groupby("faixa")
        .agg(vapor=("vapor_t", "sum"), energia=("energia_gj", "sum"), n=("vapor_t", "size"))
    )
    a = a[a.n >= 10]
    a["intensidade"] = a.energia / a.vapor
    c = comp.assign(faixa=np.floor(comp.vapor_t / largura)).join(a.intensidade, on="faixa")
    c = c.dropna(subset=["intensidade"])
    previsto = c.vapor_t * c.intensidade
    delta = float((c.energia_gj - previsto).sum()) if len(c) else None
    return {
        "largura_t_h": largura,
        "horas": len(c),
        "delta_gj": delta,
        "delta_pct": None if not len(c) else 100 * delta / float(previsto.sum()),
    }


def executar() -> dict:
    fonte = json.loads((DADOS / "fontes.json").read_text(encoding="utf-8"))
    caminho = DADOS / "ingredion_2023q1.csv"
    if hashlib.sha256(caminho.read_bytes()).hexdigest() != fonte["recorte_sha256"]:
        raise ValueError("O recorte público mudou: confira sua origem antes de executar.")
    bruto = pd.read_csv(caminho, dtype={"Unit ID": str})
    saida = {"fonte": fonte, "unidades": {}}
    for unidade, original in bruto.groupby("Unit ID"):
        d, qualidade = preparar(original)
        ref = d[d.mes == "2023-01"]
        a, b, r2 = _ajuste(ref)
        meses = []
        for mes in ["2023-02", "2023-03"]:
            todas = d[d.mes == mes]
            c = todas[todas.vapor_t.between(ref.vapor_t.min(), ref.vapor_t.max())].copy()
            c["previsto_gj"] = a + b * c.vapor_t
            if c.empty or (c.previsto_gj <= 0).any():
                raise ValueError("Sem previsão positiva na faixa observada da referência.")
            c["delta_gj"] = c.energia_gj - c.previsto_gj
            vapor = float(c.vapor_t.sum())
            esperado, observado = float(c.previsto_gj.sum()), float(c.energia_gj.sum())
            motor = comparar(
                "Energia por vapor na mesma distribuição de carga",
                "GJ/t",
                Grandeza(esperado / vapor, "GJ/t", "estimado"),
                Grandeza(observado / vapor, "GJ/t", "estimado"),
            )
            delta = motor.delta * vapor
            preco_mcf = fonte["precos_usd_mcf"][mes]
            preco_gj = preco_mcf / (fonte["calor_mmbtu_mcf"] * GJ_MMBTU)
            dias = c.groupby("Date").delta_gj.sum()
            intensidade_ref = float(ref.energia_gj.sum() / ref.vapor_t.sum())
            intensidade_mes = float(todas.energia_gj.sum() / todas.vapor_t.sum())
            diario = (
                c.groupby("Date")
                .agg(
                    vapor_t=("vapor_t", "sum"),
                    energia_gj=("energia_gj", "sum"),
                    previsto_gj=("previsto_gj", "sum"),
                    horas=("Hour", "size"),
                )
                .reset_index()
            )
            diario["observado_gj_t"] = diario.energia_gj / diario.vapor_t
            diario["referencia_gj_t"] = diario.previsto_gj / diario.vapor_t
            meses.append(
                {
                    "mes": mes,
                    "horas_validas": len(todas),
                    "horas_comparaveis": len(c),
                    "horas_fora_faixa": len(todas) - len(c),
                    "vapor_t": vapor,
                    "energia_observada_gj": observado,
                    "energia_referencia_gj": esperado,
                    "delta_gj": delta,
                    "delta_pct": 100 * delta / esperado,
                    "intensidade_sem_ajuste_ref": intensidade_ref,
                    "intensidade_sem_ajuste_mes": intensidade_mes,
                    "variacao_sem_ajuste_pct": 100 * (intensidade_mes / intensidade_ref - 1),
                    "preco_usd_mcf": preco_mcf,
                    "preco_usd_gj": preco_gj,
                    "valor_referencia_usd": valorizar_energia(delta, preco_gj),
                    "comparacao_motor": asdict(motor),
                    "dias_comparaveis": len(dias),
                    "dias_delta_positivo": int((dias > 0).sum()),
                    "economia_comprovada_usd": None,
                    "causa_comprovada": False,
                    "sensibilidade": [_faixas(ref, c, largura) for largura in [5, 10]],
                    "diario": diario.to_dict(orient="records"),
                }
            )
        saida["unidades"][unidade] = {
            "qualidade": qualidade,
            "horas_referencia": len(ref),
            "carga_min_t_h": float(ref.vapor_t.min()),
            "carga_max_t_h": float(ref.vapor_t.max()),
            "intercepto_gj_h": a,
            "inclinacao_gj_t": b,
            "r2_referencia": r2,
            "comparacoes": meses,
        }
    return saida
