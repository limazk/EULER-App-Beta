"""Referência versionada, política de custo e fechamento recorrente (D93).

O fechamento responde, para um período entre medições de estoque:
quanto combustível foi consumido e quanto custou; quanto seria esperado nas condições do
período; que diferença permanece depois dos ajustes possíveis; o que mudou desde o
fechamento anterior; o que precisa ser investigado; e quais ações anteriores tiveram
resultado. Reutiliza o motor existente (`investigar`, explicação da conta E16,
oportunidades D90); não cria cálculo físico novo.

Reprodutibilidade: o núcleo do fechamento (dados + referência + política) tem um hash.
`reproduzir` reconstrói os dados na revisão gravada e recalcula o núcleo; o contexto
(investigações e ações conhecidas naquele momento) é guardado à parte.
"""

from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path

import pandas as pd

from euler.armazem import (
    POLITICAS_CUSTO,
    Armazem,
    ErroArmazem,
    agora_iso,
    jdump,
    sha,
)
from euler.conta import explicar_conta
from euler.formato import num
from euler.investigacao import investigar
from euler.periodos import _cenarios, _lotes_todos, periodos_entre_estoques, vapor_e_combustivel
from euler.vapor import p_atm_por_altitude_bar

TIPOS_REFERENCIA = {
    "inicial": "Primeira referência do equipamento.",
    "estrutural": "Mudança estrutural documentada (equipamento, combustível, intervenção).",
    "correcao_de_dados": "Os dados da referência anterior foram corrigidos.",
}


@lru_cache(maxsize=1)
def versao_codigo() -> str:
    """Impressão digital do código de cálculo (euler/*.py): muda quando o método muda."""
    h = hashlib.sha256()
    for arq in sorted((Path(__file__).parent).rglob("*.py")):
        h.update(arq.name.encode())
        h.update(arq.read_bytes())
    return h.hexdigest()[:12]


def _ts(x) -> pd.Timestamp:
    return pd.Timestamp(x)


def p_atm(a: Armazem, equip_id: str) -> float | None:
    alt = a.equipamento(equip_id)["config"].get("altitude_m")
    return None if alt is None else p_atm_por_altitude_bar(float(alt))


# ---------------------------------------------------------------- referência versionada


def referencias(a: Armazem, equip_id: str) -> list[dict]:
    return [
        {**dict(r), "dados": json.loads(r["dados"] or "{}")}
        for r in a.con.execute(
            "SELECT * FROM referencia WHERE equipamento_id=? ORDER BY versao", (equip_id,)
        )
    ]


def referencia(a: Armazem, referencia_id: int) -> dict:
    r = a.con.execute("SELECT * FROM referencia WHERE id=?", (referencia_id,)).fetchone()
    if r is None:
        raise ErroArmazem("Referência não encontrada.")
    return {**dict(r), "dados": json.loads(r["dados"] or "{}")}


def referencia_vigente(a: Armazem, equip_id: str) -> dict | None:
    refs = referencias(a, equip_id)
    return refs[-1] if refs else None


def _resumo_referencia(pacote, inicio, fim) -> dict:
    r = vapor_e_combustivel(pacote, inicio, fim)
    if r.vapor_t is None or r.combustivel_kg is None:
        motivos = " ".join(b.motivo for b in r.bloqueios.values())
        raise ErroArmazem(f"O período não serve de referência: {motivos}")
    comb, vapor = r.combustivel_kg.valor / 1000, r.vapor_t.valor
    return {"combustivel_t": comb, "vapor_t": vapor, "consumo_t_t": comb / vapor}


def criar_referencia(
    a: Armazem,
    equip_id: str,
    inicio,
    fim,
    tipo: str,
    motivo: str,
    autor: str,
    intervencao_id: int | None = None,
    confirmar_absorcao: bool = False,
) -> dict:
    """Nova versão da referência. Versões anteriores nunca mudam.

    Proteção (D93): se o novo período consome mais por tonelada de vapor que a referência
    vigente, de forma detectável, a nova referência "absorveria" essa piora. Isso só é
    aceito como mudança estrutural com confirmação explícita, e fica registrado em todas
    as versões seguintes. Correção de dados nunca pode absorver piora.
    """
    if tipo not in TIPOS_REFERENCIA:
        raise ErroArmazem("Tipo de referência desconhecido.")
    if not (motivo or "").strip() or not (autor or "").strip():
        raise ErroArmazem("Uma referência exige motivo e autor.")
    inicio, fim = _ts(inicio), _ts(fim)
    pacote = a.pacote(equip_id, p_atm_bar=p_atm(a, equip_id))
    limites = {p for par in periodos_entre_estoques(pacote) for p in par}
    if inicio not in limites or fim not in limites or not inicio < fim:
        raise ErroArmazem(
            "Início e fim da referência precisam ser medições de estoque (período fechado)."
        )
    vigente = referencia_vigente(a, equip_id)
    if vigente is None and tipo != "inicial":
        raise ErroArmazem("A primeira referência do equipamento é do tipo 'inicial'.")
    if vigente is not None and tipo == "inicial":
        raise ErroArmazem("Já existe referência: use 'estrutural' ou 'correcao_de_dados'.")
    dados = _resumo_referencia(pacote, inicio, fim)
    if vigente is not None:
        ini_v, fim_v = _ts(vigente["inicio"]), _ts(vigente["fim"])
        if not (fim_v <= inicio or fim <= ini_v):
            dados["absorve_piora_pct"] = None
            dados["comparacao_com_anterior"] = "Períodos sobrepostos: comparação direta não feita."
        else:
            j = investigar(pacote, (ini_v, fim_v), (inicio, fim))
            c = j["o_que_mudou"]["consumo_especifico"]
            variacao = None if not c.get("variacao") else 100 * c["variacao"] / c["referencia"]
            dados["variacao_vs_anterior_pct"] = variacao
            dados["detectabilidade_vs_anterior"] = c.get("detectabilidade")
            piora = c.get("detectabilidade") == "sim" and (c.get("variacao") or 0) > 0
            dados["absorve_piora_pct"] = variacao if piora else None
            if piora and (tipo != "estrutural" or not confirmar_absorcao):
                raise ErroArmazem(
                    f"O novo período consome {num(variacao, 1)}% a mais por tonelada de vapor "
                    "que a referência vigente, de forma detectável. Adotá-lo esconderia essa "
                    "piora. Só é aceito como mudança estrutural documentada e confirmada."
                )
    with a._transacao() as cur:
        rev = a._nova_revisao(cur)
        versao = (vigente or {}).get("versao", 0) + 1
        cur.execute(
            "INSERT INTO referencia (equipamento_id, versao, inicio, fim, tipo, motivo, autor, "
            "criada_em, revisao, intervencao_id, dados) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                equip_id,
                versao,
                inicio.isoformat(),
                fim.isoformat(),
                tipo,
                motivo,
                autor,
                agora_iso(),
                rev,
                intervencao_id,
                jdump(dados),
            ),
        )
        a._evento(cur, equip_id, "referencia", versao, "criada", autor, {"tipo": tipo, **dados})
    return referencia_vigente(a, equip_id)


# ---------------------------------------------------------------- tabela de preços


def registrar_preco(
    a: Armazem,
    equip_id: str,
    combustivel: str,
    preco_brl_t: float,
    valido_de,
    origem: str,
    autor: str,
    valido_ate=None,
    fornecedor: str | None = None,
    custo_adicional_brl_t: float | None = None,
    custo_adicional_desc: str | None = None,
    moeda: str = "BRL",
    unidade: str = "t",
) -> int:
    """Preço vigente por período (contrato, nota, cotação). Só BRL por tonelada; nada é
    convertido em silêncio. Custos adicionais (frete etc.) ficam separados e declarados."""
    if moeda != "BRL" or unidade != "t":
        raise ErroArmazem("Esta versão só aceita preço em BRL por tonelada.")
    if not (preco_brl_t >= 0) or (custo_adicional_brl_t is not None and custo_adicional_brl_t < 0):
        raise ErroArmazem("Preço e custo adicional não podem ser negativos.")
    if custo_adicional_brl_t and not (custo_adicional_desc or "").strip():
        raise ErroArmazem("Descreva o custo adicional (ex.: frete).")
    de = _ts(valido_de)
    ate = None if valido_ate is None else _ts(valido_ate)
    if ate is not None and ate <= de:
        raise ErroArmazem("O fim da validade precisa ser depois do início.")
    with a._transacao() as cur:
        a._nova_revisao(cur)
        cur.execute(
            "INSERT INTO preco (equipamento_id, combustivel, fornecedor, preco_brl_t, moeda, "
            "unidade, valido_de, valido_ate, custo_adicional_brl_t, custo_adicional_desc, origem,"
            " criado_em, autor) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                equip_id,
                combustivel,
                fornecedor,
                float(preco_brl_t),
                moeda,
                unidade,
                de.isoformat(),
                None if ate is None else ate.isoformat(),
                custo_adicional_brl_t,
                custo_adicional_desc,
                origem,
                agora_iso(),
                autor,
            ),
        )
        pid = cur.lastrowid
        a._evento(cur, equip_id, "preco", pid, "registrado", autor, {"preco_brl_t": preco_brl_t})
    return pid


def precos(a: Armazem, equip_id: str) -> list[dict]:
    return [
        dict(r)
        for r in a.con.execute(
            "SELECT * FROM preco WHERE equipamento_id=? AND anulado_motivo IS NULL ORDER BY valido_de",
            (equip_id,),
        )
    ]


def preco_do_periodo(a: Armazem, equip_id: str, pacote, inicio, fim, politica: str) -> dict:
    """Preço atribuído ao combustível consumido no período, pela política declarada.

    Nunca troca de política em silêncio: se a política escolhida não tem dado suficiente,
    o preço fica ausente com o motivo.
    """
    if politica not in POLITICAS_CUSTO:
        raise ErroArmazem("Política de custo desconhecida.")
    inicio, fim = _ts(inicio), _ts(fim)
    base = {"politica": politica, "descricao": POLITICAS_CUSTO[politica], "moeda": "BRL"}
    lotes = _lotes_todos(pacote)
    no_periodo = lotes[(lotes["data"] > inicio) & (lotes["data"] <= fim)] if len(lotes) else lotes
    if politica == "recebimentos_do_periodo":
        com_preco = no_periodo.dropna(subset=["preco_brl"]) if len(no_periodo) else no_periodo
        if not len(com_preco):
            return {
                **base,
                "preco_brl_t": None,
                "motivo": "Nenhum lote com preço recebido no período.",
            }
        sem = len(no_periodo) - len(com_preco)
        return {
            **base,
            "preco_brl_t": float(
                com_preco["preco_brl"].sum() / (com_preco["massa_kg"].sum() / 1000)
            ),
            "lotes": len(com_preco),
            "lotes_sem_preco": sem,
            "custo_adicional_brl_t": None,
            "motivo": None
            if not sem
            else f"{sem} lote(s) do período sem preço ficaram fora da média.",
        }
    if politica == "fifo":
        r = vapor_e_combustivel(pacote, inicio, fim)
        cen = _cenarios(lotes, "preco_brl_t", r, None) if len(lotes) else None
        if cen is None or cen.fifo is None:
            motivo = (cen.fifo_indisponivel if cen else None) or (
                "estoques ou lotes insuficientes para seguir o combustível do pátio"
            )
            return {**base, "preco_brl_t": None, "motivo": f"FIFO indisponível: {motivo}."}
        return {
            **base,
            "preco_brl_t": float(cen.fifo),
            "custo_adicional_brl_t": None,
            "motivo": None,
        }
    vigentes = [
        p
        for p in precos(a, equip_id)
        if _ts(p["valido_de"]) <= inicio
        and (p["valido_ate"] is None or _ts(p["valido_ate"]) >= fim)
    ]
    if not vigentes:
        return {
            **base,
            "preco_brl_t": None,
            "motivo": "Nenhum preço da tabela cobre todo o período.",
        }
    if len(vigentes) > 1:
        return {
            **base,
            "preco_brl_t": None,
            "motivo": (
                "Mais de um preço vigente no período (combustíveis ou fornecedores diferentes): "
                "a tabela exige uma regra de rateio ainda não definida."
            ),
        }
    p = vigentes[0]
    adicional = p["custo_adicional_brl_t"] or 0.0
    return {
        **base,
        "preco_brl_t": p["preco_brl_t"] + adicional,
        "preco_base_brl_t": p["preco_brl_t"],
        "custo_adicional_brl_t": p["custo_adicional_brl_t"],
        "custo_adicional_desc": p["custo_adicional_desc"],
        "origem": p["origem"],
        "combustivel": p["combustivel"],
        "motivo": None,
    }


# ---------------------------------------------------------------- conta do período


def conta_do_periodo(pacote, inicio, fim, preco: dict) -> dict:
    """Compra/recebimento, estoque, consumo e custo atribuído: grandezas diferentes (D93).

    Recebido = lotes que chegaram no período (notas). Consumido = estoque inicial +
    recebido − estoque final (E9). Custo atribuído = consumido × preço da política.
    Despesa ou pagamento do período não fazem parte dos dados da EULER.
    """
    inicio, fim = _ts(inicio), _ts(fim)
    r = vapor_e_combustivel(pacote, inicio, fim)
    lotes = _lotes_todos(pacote)
    rec = lotes[(lotes["data"] > inicio) & (lotes["data"] <= fim)] if len(lotes) else lotes
    recebido_t = float(rec["massa_kg"].sum()) / 1000 if len(rec) else 0.0
    com_valor = rec.dropna(subset=["preco_brl"]) if len(rec) else rec
    consumido_t = None if r.combustivel_kg is None else r.combustivel_kg.valor / 1000
    p = preco.get("preco_brl_t")
    return {
        "recebido_t": recebido_t,
        "recebido_lotes": len(rec),
        "valor_notas_brl": float(com_valor["preco_brl"].sum()) if len(com_valor) else None,
        "lotes_sem_valor": len(rec) - len(com_valor),
        "estoque_inicial_t": None if r.estoque_inicial_kg is None else r.estoque_inicial_kg / 1000,
        "estoque_final_t": None if r.estoque_final_kg is None else r.estoque_final_kg / 1000,
        "consumido_t": consumido_t,
        "custo_atribuido_brl": None if consumido_t is None or p is None else consumido_t * p,
        "politica_custo": preco["politica"],
        "despesa_ou_pagamento": None,
        "nota_pagamento": (
            "Despesa contábil e pagamento do período não estão nos dados da EULER: compra não "
            "é consumo, e o custo atribuído ao consumo não é o que saiu do caixa."
        ),
        "motivo_consumo": None
        if consumido_t is not None
        else " ".join(b.motivo for b in r.bloqueios.values()),
    }


# ---------------------------------------------------------------- fechamento


def fechamentos(a: Armazem, equip_id: str) -> list[dict]:
    return [
        {**dict(r), "resultado": json.loads(r["resultado"])}
        for r in a.con.execute(
            "SELECT * FROM fechamento WHERE equipamento_id=? ORDER BY id", (equip_id,)
        )
    ]


def fechamento(a: Armazem, fechamento_id: int) -> dict:
    r = a.con.execute("SELECT * FROM fechamento WHERE id=?", (fechamento_id,)).fetchone()
    if r is None:
        raise ErroArmazem("Fechamento não encontrado.")
    return {**dict(r), "resultado": json.loads(r["resultado"])}


def validade_periodos(pacote, periodos) -> list[dict]:
    """Cada período entre estoques com vapor e combustível conhecidos, ou o motivo."""
    saida = []
    for ini, fim in periodos:
        r = vapor_e_combustivel(pacote, ini, fim)
        valido = r.vapor_t is not None and r.combustivel_kg is not None
        saida.append(
            {
                "inicio": ini,
                "fim": fim,
                "valido": valido,
                "motivo": None if valido else " ".join(b.motivo for b in r.bloqueios.values()),
            }
        )
    return saida


def sequencia_valida(itens: list[dict]) -> list[dict]:
    """Períodos válidos consecutivos a partir do primeiro (para no primeiro inválido)."""
    saida = []
    for x in itens:
        if not x["valido"]:
            break
        saida.append(x)
    return saida


def periodos_pendentes(a: Armazem, equip_id: str) -> list[dict]:
    """Períodos completos entre estoques depois do último fechamento e da referência, com
    a indicação de quais têm vapor e combustível conhecidos."""
    pacote = a.pacote(equip_id, p_atm_bar=p_atm(a, equip_id))
    ref = referencia_vigente(a, equip_id)
    anteriores = fechamentos(a, equip_id)
    corte = max(
        [_ts(f["fim"]) for f in anteriores] + ([_ts(ref["fim"])] if ref else []),
        default=None,
    )
    pend = [p for p in periodos_entre_estoques(pacote) if corte is None or p[0] >= corte]
    return validade_periodos(pacote, pend)


def _nucleo(a, equip_id, pacote, ref, inicio, fim, politica) -> dict:
    """Parte reproduzível: depende só dos dados, da referência, da política e do código."""
    j = investigar(pacote, (_ts(ref["inicio"]), _ts(ref["fim"])), (inicio, fim))
    preco_ref = preco_do_periodo(a, equip_id, pacote, ref["inicio"], ref["fim"], politica)
    preco = preco_do_periodo(a, equip_id, pacote, inicio, fim, politica)
    entradas = (j.get("explicacao_conta") or {}).get("entradas")
    if entradas:
        conta = explicar_conta(
            **{
                **entradas,
                "preco_ref_brl_t": preco_ref.get("preco_brl_t"),
                "preco_brl_t": preco.get("preco_brl_t"),
                # cenários de preço por lote só fazem sentido na política de recebimentos
                "preco_min_brl_t": entradas.get("preco_min_brl_t")
                if politica == "recebimentos_do_periodo"
                else None,
                "preco_max_brl_t": entradas.get("preco_max_brl_t")
                if politica == "recebimentos_do_periodo"
                else None,
                "cenarios_qualidade_pct": tuple(entradas["cenarios_qualidade_pct"])
                if entradas.get("cenarios_qualidade_pct")
                else None,
            }
        )
    else:
        conta = j.get("explicacao_conta") or {"disponivel": False, "motivo": "Conta indisponível."}
    c = j["o_que_mudou"]["consumo_especifico"]
    comp = j["periodos"]["comparacao"]
    ops = j.get("oportunidades") or {}
    return {
        "periodo": {"inicio": inicio.isoformat(), "fim": fim.isoformat()},
        "referencia": {
            "id": ref["id"],
            "versao": ref["versao"],
            "inicio": ref["inicio"],
            "fim": ref["fim"],
            "tipo": ref["tipo"],
            "motivo": ref["motivo"],
            "absorve_piora_pct": ref["dados"].get("absorve_piora_pct"),
        },
        "politica_custo": preco,
        "politica_custo_referencia": preco_ref,
        "conta_do_periodo": conta_do_periodo(pacote, inicio, fim, preco),
        "consumo_especifico": {
            "referencia_t_t": c.get("referencia"),
            "periodo_t_t": c.get("comparacao"),
            "variacao_t_t": c.get("variacao"),
            "incerteza_variacao_t_t": c.get("incerteza_variacao"),
            "detectabilidade": c.get("detectabilidade"),
            "frase": j["o_que_mudou"]["frase"],
        },
        "custo_por_energia": {
            "periodo_brl_gj": comp.get("preco_brl_gj"),
            "motivo": None
            if comp.get("preco_brl_gj") is not None
            else "R$/GJ não calculado: falta umidade ou PCI medidos dos lotes (nada é presumido).",
        },
        "explicacao_conta": conta,
        "oportunidades": [
            {
                "id": o["id"],
                "titulo": o["titulo"],
                "prioridade": o["prioridade"],
                "evidencia": o["evidencia"]["nivel"],
                "impacto_brl": o["impacto"]["custo_brl"],
                "faixa_brl": o["impacto"]["faixa_brl"],
                "verificacao": o["verificacao"]["acao"],
                "complexidade": o["verificacao"]["complexidade"],
            }
            for o in ops.get("oportunidades", [])
        ],
        "sobreposicao": ops.get("sobreposicao", []),
        "proxima_verificacao": j["proxima_verificacao"],
        "evidencias": {
            k: v["nivel"]
            for k, v in (j.get("diagnostico_evidencias") or {}).get("dimensoes", {}).items()
        },
        "conclusao": j["conclusao"]["texto"],
    }


SITUACAO = {
    "acima": "Consumo acima da referência ajustada (estabelecido pelas medições).",
    "abaixo": "Consumo abaixo da referência ajustada (estabelecido pelas medições).",
    "nao_estabelecido": "Diferença dentro da incerteza: sem mudança de desempenho estabelecida.",
    "sem_faixa": "Sem incerteza declarada de todos os instrumentos: diferença não classificada.",
}


def _situacao(nucleo: dict) -> str | None:
    conta = nucleo["explicacao_conta"]
    return conta["desvio"]["estado"] if conta.get("disponivel") else None


def _comparar_com_anterior(nucleo: dict, anterior: dict | None) -> dict:
    if anterior is None:
        return {"existe": False, "frase": "Primeiro fechamento deste equipamento."}
    prev = anterior["resultado"]["nucleo"]
    if prev["referencia"]["id"] != nucleo["referencia"]["id"]:
        return {
            "existe": True,
            "fechamento_id": anterior["id"],
            "comparavel": False,
            "frase": (
                f"A referência mudou (v{prev['referencia']['versao']} → "
                f"v{nucleo['referencia']['versao']}): a comparação direta com o fechamento "
                "anterior não é feita."
            ),
        }
    e0, e1 = _situacao(prev), _situacao(nucleo)
    k0 = prev["consumo_especifico"]["periodo_t_t"]
    k1 = nucleo["consumo_especifico"]["periodo_t_t"]
    d0 = (prev["explicacao_conta"].get("desvio") or {}).get("pct_do_esperado")
    d1 = (nucleo["explicacao_conta"].get("desvio") or {}).get("pct_do_esperado")
    partes = []
    if e1 is None:
        partes.append(
            "Neste período a conta não pôde ser calculada: "
            + (nucleo["explicacao_conta"].get("motivo") or "dados insuficientes.")
        )
    elif e0 is None:
        partes.append(
            f"No fechamento anterior a conta não pôde ser calculada; agora: {SITUACAO[e1]}"
        )
    elif e0 != e1:
        partes.append(f"A situação mudou: {SITUACAO.get(e0, e0)} → {SITUACAO.get(e1, e1)}")
    else:
        partes.append(f"Situação mantida: {SITUACAO.get(e1, e1)}")
    if d0 is not None and d1 is not None:
        partes.append(
            f"Desvio não explicado: {num(d0, 1)}% → {num(d1, 1)}% do esperado "
            "(diferença entre fechamentos sem teste próprio de significância)."
        )
    return {
        "existe": True,
        "fechamento_id": anterior["id"],
        "comparavel": True,
        "situacao_anterior": e0,
        "situacao_atual": e1,
        "consumo_t_t": [k0, k1],
        "desvio_pct": [d0, d1],
        "frase": " ".join(partes),
    }


def produzir_fechamento(
    a: Armazem,
    equip_id: str,
    autor: str,
    inicio=None,
    fim=None,
) -> dict:
    """Fecha o período (padrão: todos os períodos completos ainda não fechados)."""
    ref = referencia_vigente(a, equip_id)
    if ref is None:
        raise ErroArmazem("Defina a referência do equipamento antes do primeiro fechamento.")
    if inicio is None or fim is None:
        pendentes = periodos_pendentes(a, equip_id)
        if not pendentes:
            raise ErroArmazem(
                "Sem período novo completo (entre medições de estoque) desde o último "
                "fechamento: o acompanhamento não tem dados novos para fechar."
            )
        # períodos válidos consecutivos; um período inválido no início é fechado sozinho,
        # para a lacuna ficar registrada com o motivo (nunca pulada em silêncio)
        validos = sequencia_valida(pendentes) or pendentes[:1]
        inicio, fim = validos[0]["inicio"], validos[-1]["fim"]
    inicio, fim = _ts(inicio), _ts(fim)
    revisao = a.revisao
    politica = a.equipamento(equip_id)["config"]["politica_custo"]
    pacote = a.pacote(equip_id, revisao=revisao, p_atm_bar=p_atm(a, equip_id))
    nucleo = _nucleo(a, equip_id, pacote, ref, inicio, fim, politica)
    anteriores = fechamentos(a, equip_id)
    from euler.acompanhamento import contexto_para_fechamento

    resultado = {
        "nucleo": nucleo,
        "nucleo_sha": sha(nucleo),
        "situacao": _situacao(nucleo),
        "situacao_frase": SITUACAO.get(_situacao(nucleo), "Conta indisponível neste período."),
        "comparacao_anterior": _comparar_com_anterior(
            nucleo, anteriores[-1] if anteriores else None
        ),
        "contexto": contexto_para_fechamento(a, equip_id, inicio, fim, nucleo),
        "cobertura": a.cobertura(equip_id),
    }
    with a._transacao() as cur:
        cur.execute(
            "INSERT INTO fechamento (equipamento_id, inicio, fim, referencia_id, revisao_dados, "
            "conjunto_sha, resultado, resultado_sha, versao_euler, criado_em, autor) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                equip_id,
                inicio.isoformat(),
                fim.isoformat(),
                ref["id"],
                revisao,
                a.conjunto_sha(equip_id, revisao),
                jdump(resultado),
                resultado["nucleo_sha"],
                versao_codigo(),
                agora_iso(),
                autor,
            ),
        )
        fid = cur.lastrowid
        a._evento(
            cur,
            equip_id,
            "fechamento",
            fid,
            "produzido",
            autor,
            {"situacao": resultado["situacao"]},
        )
    return fechamento(a, fid)


def reproduzir(a: Armazem, fechamento_id: int, referencia_id: int | None = None) -> dict:
    """Recalcula o núcleo com os dados da revisão gravada (e a mesma referência, ou outra
    versão escolhida). Compara o hash; se o código mudou, diz isso em vez de esconder."""
    f = fechamento(a, fechamento_id)
    ref = referencia(a, referencia_id or f["referencia_id"])
    pacote = a.pacote(
        f["equipamento_id"], revisao=f["revisao_dados"], p_atm_bar=p_atm(a, f["equipamento_id"])
    )
    politica = f["resultado"]["nucleo"]["politica_custo"]["politica"]
    nucleo = _nucleo(a, f["equipamento_id"], pacote, ref, _ts(f["inicio"]), _ts(f["fim"]), politica)
    novo_sha = sha(nucleo)
    mesma_ref = ref["id"] == f["referencia_id"]
    mesmo_codigo = versao_codigo() == f["versao_euler"]
    dados_ok = a.conjunto_sha(f["equipamento_id"], f["revisao_dados"]) == f["conjunto_sha"]
    return {
        "identico": mesma_ref and novo_sha == f["resultado_sha"],
        "mesma_referencia": mesma_ref,
        "mesmo_codigo": mesmo_codigo,
        "dados_identicos": dados_ok,
        "nucleo": nucleo,
        "frase": (
            "Resultado reproduzido de forma idêntica."
            if mesma_ref and novo_sha == f["resultado_sha"]
            else (
                f"Recalculado com a referência v{ref['versao']} (o original usou outra versão)."
                if not mesma_ref
                else (
                    "Resultado diferente: o código de cálculo mudou desde o fechamento."
                    if not mesmo_codigo
                    else "Resultado diferente com o mesmo código e os mesmos dados: verificar."
                )
            )
        ),
    }
