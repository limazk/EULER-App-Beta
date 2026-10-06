"""Apresentação financeira do resultado existente, sem novas hipóteses físicas.

A explicação da conta (custo consumido, esperado, desvio) vem do motor (`euler.conta`,
D89). Não há simulador de percentual de recuperação: a parcela evitável depende de
verificar um mecanismo específico.
"""

from math import isclose, isfinite

import pandas as pd


def nao_negativo(valor):
    """Número finito >= 0; ausente/inválido permanece None."""
    if valor is None:
        return None
    try:
        valor = float(valor)
    except (TypeError, ValueError):
        return None
    return valor if isfinite(valor) and valor >= 0 else None


def resumo_variacao(conta: dict) -> dict:
    """Agrupa parcelas E16 já calculadas, em BRL, sem atribuir novas causas.

    Preço + produção/ajustes disponíveis + residual = variação do custo. A ordem e
    as hipóteses são as do motor; parcelas não separadas permanecem no residual.
    Uma inconsistência de reconciliação bloqueia a ponte, em vez de corrigir valores.
    """
    v = conta.get("variacao") or {}
    vazio = {"disponivel": False, "grupos": [], "nao_separados": [], "fechamento_brl": None}
    if not conta.get("disponivel") or not v.get("disponivel"):
        return {**vazio, "motivo": v.get("motivo") or conta.get("motivo") or "Conta indisponível."}
    componentes = v["componentes"]
    por_id = {x["id"]: x for x in componentes}
    ajustes = [por_id[k] for k in ("producao", "condicao_vapor", "qualidade")]
    grupos = [
        {
            "id": "preco",
            "titulo": "Preço do combustível",
            "custo_brl": por_id["preco"]["custo_brl"],
        },
        {
            "id": "producao_ajustes",
            "titulo": "Produção e ajustes disponíveis",
            "custo_brl": sum(
                x["custo_brl"] for x in ajustes if x["separado"] and x["custo_brl"] is not None
            ),
        },
        {
            "id": "nao_explicado",
            "titulo": "Ainda não explicado",
            "custo_brl": por_id["nao_explicado"]["custo_brl"],
        },
    ]
    valores = [x["custo_brl"] for x in grupos]
    total = v["variacao_brl"]
    if any(x is None or not isfinite(x) for x in valores) or not isclose(
        sum(valores), total, rel_tol=1e-10, abs_tol=1e-6
    ):
        return {
            **vazio,
            "motivo": "Não foi possível reconciliar a composição com a variação total. Revise o resultado antes de interpretá-lo.",
        }
    return {
        "disponivel": True,
        "motivo": None,
        "grupos": grupos,
        "nao_separados": [x["titulo"] for x in componentes if not x["separado"]],
        "custo_referencia_brl": v["custo_referencia_brl"],
        "custo_brl": v["custo_brl"],
        "variacao_brl": total,
        "fechamento_brl": total - sum(valores),
    }


def resumo_compras(combustivel, inicio=None, fim=None) -> dict:
    """Recebimentos registrados: massas em t e valores em BRL, sem inferir pagamento.

    Usa a mesma fronteira do motor E9: inicio < data <= fim. Soma parcial é rotulada
    separadamente; massa ou preço ausente impede total/média correspondente. Sem
    linhas, não afirma gasto zero. O DataFrame original permanece intacto.
    """
    receb = (
        pd.DataFrame()
        if combustivel is None
        else combustivel[combustivel["tipo"] == "recebimento"].copy()
    )
    if len(receb) and inicio is not None:
        receb = receb[receb["data"] > pd.Timestamp(inicio)]
    if len(receb) and fim is not None:
        receb = receb[receb["data"] <= pd.Timestamp(fim)]
    n = len(receb)
    valores = receb["preco_brl"].map(nao_negativo) if n else pd.Series(dtype=float)
    coluna_massa = "massa_kg_calc" if "massa_kg_calc" in receb else "massa_kg"
    massas = receb[coluna_massa].map(nao_negativo) if n else pd.Series(dtype=float)
    n_precos, n_massas = int(valores.notna().sum()), int(massas.notna().sum())
    valor = float(valores.sum()) if n_precos else None
    massa = float(massas.sum()) / 1000 if n_massas else None
    valor_total = valor if n and n_precos == n else None
    massa_total = massa if n and n_massas == n else None
    grupos = []
    if n_precos:
        receb["valor_valido"] = valores
        for fornecedor, linhas in receb.groupby(receb["fornecedor_id"].fillna("Sem identificação")):
            conhecidos = linhas["valor_valido"].dropna()
            grupos.append(
                {
                    "fornecedor": str(fornecedor),
                    "valor_brl": float(conhecidos.sum()) if len(conhecidos) else None,
                    "parcial": len(conhecidos) != len(linhas),
                }
            )
    return {
        "lotes": n,
        "sem_preco": n - n_precos,
        "sem_massa": n - n_massas,
        "massas_estimadas": int((receb["massa_origem"] == "estimado").sum())
        if n and "massa_origem" in receb
        else 0,
        "valor_conhecido_brl": valor,
        "valor_total_brl": valor_total,
        "massa_conhecida_t": massa,
        "recebido_t": massa_total,
        "preco_medio_brl_t": valor_total / massa_total
        if valor_total is not None and massa_total is not None and massa_total > 0
        else None,
        "pagamento_brl": None,
        "fornecedores": grupos,
    }


def movimentacao_periodo(pacote, inicio, fim, preco_brl_t=None) -> dict:
    """Conta E9 existente + cobertura das compras; não valoriza estoque sem política.

    O consumo e seus bloqueios vêm de euler.fechamento. Nesta vista da sessão, o
    preço é a média dos recebimentos usada pela investigação. Ausências de massa
    são mantidas no resumo, mesmo quando uma soma pandas retornaria um subtotal.
    """
    from euler.fechamento import conta_do_periodo

    conta = conta_do_periodo(
        pacote,
        inicio,
        fim,
        {"politica": "recebimentos_do_periodo", "preco_brl_t": nao_negativo(preco_brl_t)},
    )
    compras = resumo_compras(pacote.dados("combustivel"), inicio, fim)
    return {
        **conta,
        "recebido_t": compras["recebido_t"],
        "valor_notas_brl": compras["valor_total_brl"],
        "compras": compras,
        "variacao_estoque_t": None
        if conta["estoque_inicial_t"] is None or conta["estoque_final_t"] is None
        else conta["estoque_final_t"] - conta["estoque_inicial_t"],
    }
