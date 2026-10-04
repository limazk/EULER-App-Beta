"""Diagnóstico da referência fornecida, sem ajustar modelos ou trocar períodos.

Rubrica de triagem EULER v1, não teste confirmatório. Limiares são revisáveis,
não universais. MAD apenas sinaliza potenciais outliers: nenhum é removido.
Origem do critério MAD: NIST/SEMATECH, EDA 1.3.5.17 (eda35h.htm).
"""

import numpy as np
import pandas as pd

from euler.evidencias import NIVEIS

PARAMETROS = {
    "n_minimo": 3,
    "n_triagem": 30,
    "invalidos_frac": 0.10,
    "vies_atencao_pct": 1.0,
    "vies_alto_pct": 3.0,
    "autocorrelacao_atencao": 0.5,
    "outlier_mad_z": 3.5,
}


def avaliar_referencia(
    *,
    observado,
    unidade,
    previsto=None,
    instantes=None,
    carga=None,
    carga_comparacao=None,
    unidade_carga=None,
    intervalo_horas=None,
    validacao_temporal=None,
    regimes=None,
) -> dict:
    """Arrays da referência, com unidade comum de energia/massa explicitada.

    Resíduo=observado−previsto. Métricas relativas à média absoluta observada.
    Carga em unidade separada; cobertura min/max não garante cobertura interna.
    Instantes opcionais; sem eles não se infere cronologia pela posição do array.
    Dados inválidos são contados e não preenchidos. Diagnósticos não alteram arrays.
    """
    if not isinstance(unidade, str) or not unidade.strip():
        raise ValueError("Informe a unidade dos valores observados e previstos.")
    y = np.asarray(observado, dtype=float)
    if y.ndim != 1:
        raise ValueError("Informe uma série unidimensional.")
    n, nivel, motivos, limites = len(y), 3, [], []

    def limitar(maximo, motivo):
        nonlocal nivel
        nivel = min(nivel, maximo)
        motivos.append(motivo)

    def vetor(v, nome):
        a = np.asarray(v, dtype=float)
        if a.shape != y.shape:
            raise ValueError(f"{nome}: comprimento diferente da referência.")
        return a

    valido = np.isfinite(y)
    if previsto is not None:
        p = vetor(previsto, "Previsto")
        valido &= np.isfinite(p)
        residuo = y - p
    else:
        residuo = None
        limitar(2, "Resíduos do modelo não disponíveis.")
    nv = int(valido.sum())
    m = {
        "unidade": unidade,
        "observacoes_recebidas": n,
        "observacoes_validas": nv,
        "observacoes_invalidas": n - nv,
        "dispersao_relativa_pct": None,
        "outliers_mad": None,
        "rmse_relativo_pct": None,
        "mudanca_residual_metades_pct": None,
        "autocorrelacao": None,
        "pares_autocorrelacao": 0,
        "cobertura_carga_frac": None,
        "carga_comparacao_ausente": None,
        "validacao_temporal": validacao_temporal,
    }
    if nv < 3:
        limitar(0, "Menos de três observações finitas; referência insuficiente.")
    elif nv < 30:
        limitar(1, "Poucas observações para os diagnósticos de triagem (menos de 30).")
    if n - nv:
        limitar(
            1 if (n - nv) / n > 0.1 else 2,
            "Dados ausentes ou inválidos na referência; exclusões contabilizadas.",
        )
    escala = float(np.mean(abs(y[valido]))) if nv else 0
    if nv > 1 and escala > 0:
        m["dispersao_relativa_pct"] = 100 * float(np.std(y[valido], ddof=1)) / escala
        r = residuo[valido] if residuo is not None else y[valido]
        mad = float(np.median(abs(r - np.median(r))))
        if mad > 0:
            m["outliers_mad"] = int((abs(0.6745 * (r - np.median(r)) / mad) > 3.5).sum())
            if m["outliers_mad"]:
                limitar(
                    2, "Potenciais outliers sinalizados por MAD; nenhum removido automaticamente."
                )
        else:
            limites.append("MAD nulo: outliers por esse método não avaliáveis.")
        if residuo is not None:
            m["rmse_relativo_pct"] = 100 * float(np.sqrt(np.mean(r**2))) / escala
    elif nv:
        limitar(0, "Escala observada nula; métricas relativas não avaliáveis.")
    if instantes is None:
        limitar(2, "Instantes ausentes; estabilidade temporal não verificada.")
    else:
        if len(instantes) != n:
            raise ValueError("Instantes: comprimento diferente da referência.")
        t = pd.DatetimeIndex(pd.to_datetime(instantes, errors="coerce"))
        if t.isna().any() or t.duplicated().any():
            limitar(1, "Instantes ausentes ou duplicados; estabilidade temporal não avaliável.")
        elif residuo is not None and nv >= 4 and escala > 0:
            s = pd.Series(residuo[valido], index=t[valido]).sort_index()
            meio = len(s) // 2
            drift = 100 * float(s.iloc[meio:].mean() - s.iloc[:meio].mean()) / escala
            m["mudanca_residual_metades_pct"] = drift
            if abs(drift) > 1:
                limitar(
                    1 if abs(drift) > 3 else 2,
                    "Mudança temporal entre as metades dos resíduos da referência.",
                )
            if intervalo_horas is not None:
                if not np.isfinite(intervalo_horas) or intervalo_horas <= 0:
                    raise ValueError("Intervalo temporal deve ser positivo e finito.")
                pares = pd.concat(
                    [s.rename("a"), s.shift(freq=pd.Timedelta(hours=intervalo_horas)).rename("b")],
                    axis=1,
                ).dropna()
                m["pares_autocorrelacao"] = len(pares)
                if len(pares) >= 3 and pares.a.std() > 0 and pares.b.std() > 0:
                    ac = float(pares.a.corr(pares.b))
                    m["autocorrelacao"] = ac
                    if abs(ac) > 0.5:
                        limitar(
                            2, "Dependência temporal dos resíduos; não supor horas independentes."
                        )
                else:
                    limitar(2, "Autocorrelação não avaliável nos pares temporais disponíveis.")
            else:
                limitar(2, "Intervalo para verificar autocorrelação não informado.")
    if carga is None or carga_comparacao is None:
        limitar(2, "Cobertura das condições de carga não avaliada.")
    else:
        if not unidade_carga:
            raise ValueError("Informe a unidade da carga.")
        x = vetor(carga, "Carga")
        xc = np.asarray(carga_comparacao, dtype=float)
        if xc.ndim != 1:
            raise ValueError("Carga de comparação deve ser unidimensional.")
        xr = x[valido & np.isfinite(x)]
        m["carga_comparacao_ausente"] = int((~np.isfinite(xc)).sum())
        m["carga_referencia_ausente"] = int((~np.isfinite(x)).sum())
        if len(xr) < 3 or not len(xc) or np.ptp(xr) == 0:
            limitar(0, "Carga insuficiente ou sem variação para avaliar suporte operacional.")
        else:
            dentro = np.isfinite(xc) & (xc >= min(xr)) & (xc <= max(xr))
            cobertura = float(dentro.mean())
            m["cobertura_carga_frac"] = cobertura
            m["unidade_carga"] = unidade_carga
            m["carga_min"] = float(min(xr))
            m["carga_max"] = float(max(xr))
            if dentro.sum() < 3:
                limitar(0, "Menos de três cargas de comparação no suporte da referência.")
            elif cobertura < 1:
                limitar(
                    1 if cobertura < 0.5 else 2,
                    "Cobertura de carga parcial; conclusões restritas ao suporte observado.",
                )
            if m["carga_referencia_ausente"]:
                limitar(2, "Carga ausente em parte da referência.")
    if not validacao_temporal:
        limitar(2, "Validação cronológica fora do ajuste não disponível.")
    else:
        for v in validacao_temporal:
            vies = v.get("vies_pct")
            if vies is None or not np.isfinite(vies) or v.get("horas_comparaveis", 0) < 3:
                limitar(2, "Trecho de validação temporal insuficiente; não substituído.")
            elif abs(vies) > 1:
                limitar(
                    1 if abs(vies) > 3 else 2,
                    "Viés na validação temporal da referência; processo ou modelo podem ter mudado.",
                )
    if regimes is None:
        limitar(
            2, "Regime operacional não informado; hora completa não certifica estacionariedade."
        )
    elif len(regimes) != n:
        raise ValueError("Regimes: comprimento diferente da referência.")
    elif any(r != "estavel" for r in regimes):
        limitar(1, "Há regimes transitórios ou não verificados na referência.")
    limites += [
        "Limiares de triagem EULER, sujeitos à revisão; não são significância estatística.",
        "Faixa min/max não garante suporte denso nem equivalência termodinâmica.",
        "Nenhuma referência foi trocada; dados não foram corrigidos nem imputados.",
    ]
    return {
        "versao": "referencia/1.0",
        "nivel": NIVEIS[nivel],
        "resumo": "Referência com estabilidade limitada. A interpretação do desvio deve ser feita com cautela."
        if nivel < 3
        else "Referência adequada nas verificações disponíveis; não certifica operação ideal.",
        "motivos": list(dict.fromkeys(motivos))
        or ["Diagnósticos disponíveis sem alertas pelos critérios de triagem."],
        "metricas": m,
        "parametros": PARAMETROS.copy(),
        "limitacoes": limites,
    }
