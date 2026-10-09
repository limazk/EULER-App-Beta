"""Composição somente-leitura do dashboard a partir do banco persistido da planta."""

from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd

from euler.fechamento import fechamentos_vigentes

ORIGENS = {
    "sintetico": "sintético",
    "publico": "público",
    "cliente_autorizado": "cliente autorizado",
    "nao_classificado": "não classificado",
}


@dataclass(frozen=True)
class DashboardPersistido:
    planta: dict
    equipamento: dict
    pacote: object | None
    importacoes: tuple[dict, ...]
    fechamentos: tuple[dict, ...]
    cobertura: dict
    origem: str


def carregar_dashboard(repo, planta_id: str, equipamento_id: str) -> DashboardPersistido:
    """Lê um único equipamento de uma única planta pertencente ao repositório autorizado."""
    plantas = {planta["id"]: planta for planta in repo.listar_plantas()}
    if planta_id not in plantas:
        raise ValueError("Planta selecionada não pertence à organização atual.")
    armazem = repo.armazem(planta_id)
    try:
        equipamentos = {item["id"]: item for item in armazem.equipamentos()}
        if equipamento_id not in equipamentos:
            raise ValueError("Equipamento selecionado não pertence à planta atual.")
        arquivos = armazem.arquivos(equipamento_id)
        pacote = armazem.pacote(equipamento_id) if arquivos else None
        return DashboardPersistido(
            planta=plantas[planta_id],
            equipamento=equipamentos[equipamento_id],
            pacote=pacote,
            importacoes=tuple(armazem.importacoes(equipamento_id)),
            fechamentos=tuple(fechamentos_vigentes(armazem, equipamento_id)),
            cobertura=armazem.cobertura(equipamento_id),
            origem=ORIGENS.get(plantas[planta_id].get("classe"), "não informada"),
        )
    finally:
        armazem.fechar()


def _finito(valor) -> float | None:
    if isinstance(valor, bool) or not isinstance(valor, int | float) or not math.isfinite(valor):
        return None
    return float(valor)


def _quociente(numerador, denominador) -> float | None:
    numerador = _finito(numerador)
    denominador = _finito(denominador)
    if numerador is None or denominador is None or denominador <= 0:
        return None
    return numerador / denominador


def resumo_fechamento(fechamento: dict | None) -> dict | None:
    """Extrai KPIs preservados; não recalcula o fechamento nem cria custo esperado."""
    if fechamento is None:
        return None
    resultado = fechamento.get("resultado") or {}
    nucleo = resultado.get("nucleo") or {}
    conta = nucleo.get("conta_do_periodo") or {}
    explicacao = nucleo.get("explicacao_conta") or {}
    entradas = explicacao.get("entradas") or {}
    desvio = explicacao.get("desvio") or {}
    consumo = nucleo.get("consumo_especifico") or {}
    proxima = nucleo.get("proxima_verificacao") or {}
    vapor_t = entradas.get("vapor_t")
    return {
        "id": fechamento.get("id"),
        "periodo": {"inicio": fechamento.get("inicio"), "fim": fechamento.get("fim")},
        "origem": resultado.get("origem_dados"),
        "politica_custo": conta.get("politica_custo"),
        "consumo_t": _finito(conta.get("consumido_t")),
        "recebido_t": _finito(conta.get("recebido_t")),
        "consumo_especifico_t_t": _finito(consumo.get("periodo_t_t")),
        "custo_brl_t_vapor": _quociente(conta.get("custo_atribuido_brl"), vapor_t),
        "custo_esperado_brl_t_vapor": None,
        "desvio_brl_t_vapor": _quociente(desvio.get("custo_brl"), vapor_t),
        "desvio_estabelecido": desvio.get("estado") in {"acima", "abaixo"},
        "proxima_verificacao": proxima.get("acao"),
    }


def filtrar_periodo(diario: pd.DataFrame, inicio, fim) -> pd.DataFrame:
    """Recorta dias inclusivamente, sem preencher lacunas ou alterar valores."""
    if diario.empty or inicio is None or fim is None:
        return diario.copy()
    dias = pd.to_datetime(diario["dia"], errors="coerce", utc=True)
    limite_inicial = pd.Timestamp(inicio)
    limite_final = pd.Timestamp(fim)
    limite_inicial = (
        limite_inicial.tz_localize("UTC")
        if limite_inicial.tzinfo is None
        else limite_inicial.tz_convert("UTC")
    )
    limite_final = (
        limite_final.tz_localize("UTC")
        if limite_final.tzinfo is None
        else limite_final.tz_convert("UTC")
    )
    return diario.loc[dias.between(limite_inicial, limite_final, inclusive="both")].copy()
