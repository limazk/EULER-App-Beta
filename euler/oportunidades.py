"""Oportunidades: qual hipótese vale verificar primeiro (D90).

Camada transparente sobre a investigação existente. Não cria nota, pesos nem "valor da
informação" em reais. Para cada hipótese do motor reúne: impacto potencial associado ao
desvio (com faixa), força da evidência (rubrica ordinal), a próxima verificação (com a
complexidade de uma regra de triagem proposta), a relação com as demais oportunidades
(sobreposição) e onde a oportunidade está na cadeia até a economia verificada.

Prioridade de investigação não é prioridade de intervenção. A intervenção só pode ser
avaliada com causa sustentada por verificação registrada, o que esta versão ainda não
tem: o campo existe e fica indisponível, com o motivo.

Vocabulário (não são sinônimos): desvio monetizado (explicação da conta, E16); impacto
potencial associado (efeito de uma hipótese em reais, aqui); parcela evitável, economia
estimada e economia verificada (ainda não apuradas).
"""

from datetime import datetime
from math import exp, isfinite

VERSAO = "oportunidades/0.1"

# Regra de triagem PROPOSTA (D90), pendente de revisão por engenharia: complexidade da
# verificação que o motor escreve para cada hipótese. Só se aplica quando a ação do motor
# começa com `acao`; se o motor escreveu outra ação (ex.: pontos de gases diferentes), a
# complexidade fica "não classificada" em vez de herdar uma classificação de outra ação.
VERIFICACOES = {
    "temperatura_gases": {
        "acao": "Comparar a leitura do termopar da chaminé",
        "complexidade": "baixa",
        "exige_parada": False,
        "recurso": "termômetro de referência portátil no mesmo ponto",
        "distingue": "erro do termopar × mudança real da temperatura na chaminé",
        "etapa_seguinte": (
            "Só a segunda etapa (inspeção das superfícies de troca) exige parada programada."
        ),
    },
    "excesso_ar": {
        "acao": "Conferir a calibração do analisador de O₂",
        "complexidade": "baixa",
        "exige_parada": False,
        "recurso": "analisador portátil de O₂ no mesmo ponto",
        "distingue": "erro do analisador × excesso de ar na combustão × entrada de ar falso",
        "etapa_seguinte": None,
    },
    "umidade_combustivel": {
        "acao": "Conferir a amostragem de umidade dos lotes",
        "complexidade": "baixa",
        "exige_parada": False,
        "recurso": "laboratório (estufa) e amostras do pátio",
        "distingue": "erro de amostragem × combustível realmente mais úmido",
        "etapa_seguinte": None,
    },
    "condicao_vapor": {
        "acao": "Conferir as leituras de pressão do vapor",
        "complexidade": "baixa",
        "exige_parada": False,
        "recurso": "instrumentos já instalados",
        "distingue": "erro de leitura × mudança real no vapor entregue",
        "etapa_seguinte": None,
    },
    "perdas_nao_medidas": {
        "acao": "Registrar as purgas",
        "complexidade": "media",
        "exige_parada": False,
        "recurso": "registro de purgas, massa purgada, CO nos gases e ronda de vazamentos",
        "distingue": "purga × casco × vazamentos × combustão incompleta (hoje misturados)",
        "etapa_seguinte": None,
    },
}

# Natureza e grupo de sobreposição de cada hipótese (D90). Mesmo grupo = pode ser parte da
# mesma perda; os impactos não devem ser somados.
NATUREZA = {
    "temperatura_gases": ("eficiencia_caldeira", "perda_nos_gases"),
    "excesso_ar": ("eficiencia_caldeira", "perda_nos_gases"),
    "perdas_nao_medidas": ("eficiencia_caldeira", "perdas_alem_da_chamine"),
    "umidade_combustivel": ("qualidade_combustivel", "qualidade_combustivel"),
    "condicao_vapor": ("servico_vapor", "servico_vapor"),
}
ROTULO_NATUREZA = {
    "eficiencia_caldeira": "Eficiência da caldeira",
    "qualidade_combustivel": "Qualidade e compra do combustível",
    "servico_vapor": "Vapor entregue (não é perda)",
}
NOTA_GRUPO = {
    "perda_nos_gases": (
        "Temperatura dos gases e O₂ atuam sobre a mesma perda nos gases; os efeitos são "
        "calculados um fator por vez (interações desprezadas). Não somar sem ressalva."
    ),
    "perdas_alem_da_chamine": (
        "Resíduo entre o balanço direto e a perda nos gases: mistura purga, casco, vazamentos e "
        "combustão incompleta, que os registros atuais não separam."
    ),
    "qualidade_combustivel": (
        "Fator distinto (energia por tonelada de combustível); parte do efeito aparece também "
        "na perda nos gases pela umidade, já incluída no próprio efeito."
    ),
    "servico_vapor": "Mudança no vapor entregue (pressão e água), não perda da caldeira.",
}

# Mesma regra da dimensão "evidência física" do diagnóstico (D86): compatível = MODERADA;
# FORTE exigiria verificação registrada, que ainda não existe.
EVIDENCIA = {
    "sustentada": (
        "MODERADA",
        (
            "Mudança detectável, relevante e compatível com o consumo pelo modelo físico; "
            "causa não confirmada."
        ),
    ),
    "possivel": ("FRACA", "Compatível, mas a mudança ou o seu efeito ainda não está confirmado."),
    "descartada": ("INSUFICIENTE", "Enfraquecida nestes dados."),
    "oposta": ("INSUFICIENTE", "Mudou no sentido contrário: compensou parte da mudança."),
    "nao_avaliavel": ("INSUFICIENTE", "Não dá para avaliar com os dados atuais."),
}

PRIORIDADES = ("alta", "media", "baixa", "sem_base", "fora")
ROTULO_PRIORIDADE = {
    "alta": "Prioridade alta para investigação",
    "media": "Investigar",
    "baixa": "Não priorizar agora",
    "sem_base": "Dados insuficientes para uma prioridade defensável",
    "fora": "Fora das oportunidades",
}

REGRAS = {
    "objetivos": [
        "Efeito de cada hipótese no consumo: modelo físico do motor, um fator por vez.",
        "Detectabilidade: mudança maior que U = 2u da diferença (erros independentes).",
        "Relevância: efeito acima da fração D29 da menor mudança de consumo detectável.",
        "Situação da hipótese (compatível, possível, enfraquecida, não avaliável): motor.",
        "Desvio monetizado e preço dos recebimentos: explicação da conta (E16).",
    ],
    "propostos": [
        "Força da evidência por situação da hipótese (mesma regra da evidência física, D86).",
        "Complexidade e necessidade de parada de cada verificação (catálogo de triagem).",
        (
            "Prioridade alta: hipótese compatível ou possível, relevante e com verificação de "
            "complexidade baixa; investigar: as demais compatíveis ou possíveis."
        ),
        (
            "Ordem: primeiro a próxima verificação do motor; depois a prioridade; depois o maior "
            "impacto em reais. Não há nota nem pesos."
        ),
        "Grupos de sobreposição (mesma perda nos gases; resíduo além da chaminé).",
        "Faixa do impacto só pela incerteza da mudança do indicador (k = 2).",
    ],
}

CADEIA = (
    ("dados", "Dados importados", True),
    ("desvio", "Desvio e conta explicada", True),
    ("oportunidades", "Oportunidades e hipóteses", True),
    ("investigacao", "Próxima verificação", True),
    ("causa", "Causa sustentada por verificação registrada", False),
    ("intervencao", "Intervenção, custo e payback", False),
    ("pos", "Comparação depois da intervenção", False),
    ("economia", "Economia verificada", False),
    ("persistencia", "Acompanhamento da persistência", False),
)


def _f(x) -> float | None:
    return float(x) if isinstance(x, (int, float)) and isfinite(x) else None


def _dias(periodo: dict) -> float | None:
    try:
        ini = datetime.fromisoformat(periodo["inicio"])
        fim = datetime.fromisoformat(periodo["fim"])
    except (KeyError, TypeError, ValueError):
        return None
    d = (fim - ini).total_seconds() / 86400
    return d if d > 0 else None


def _base(j: dict) -> dict:
    """Base para converter efeitos em toneladas e reais: a mesma da explicação da conta."""
    conta = j.get("explicacao_conta") or {}
    comp = (j.get("periodos") or {}).get("comparacao") or {}
    dias = _dias(comp)
    if not conta.get("disponivel"):
        return {
            "e0_t": None,
            "preco": None,
            "dias": dias,
            "parcelas": {},
            "motivo": conta.get("motivo")
            or "Consumo esperado não calculado: impacto não pode ser convertido em toneladas.",
        }
    vapor = _f((comp.get("vapor_t") or {}).get("valor"))
    k = _f(conta["esperado"].get("consumo_referencia_t_t"))
    preco = _f(conta["consumido"].get("preco_brl_t"))
    return {
        "e0_t": None if vapor is None or k is None else k * vapor,
        "preco": preco,
        "dias": dias,
        "parcelas": (conta.get("variacao") or {}).get("combustivel_t") or {},
        "motivo": None
        if preco is not None
        else "Impacto financeiro ainda não pode ser monetizado: sem preço dos recebimentos.",
    }


PARCELA_DA_CONTA = {"umidade_combustivel": "qualidade", "condicao_vapor": "condicao_vapor"}


def _impacto(h: dict, base: dict) -> dict:
    """Impacto potencial associado ao desvio: combustível (t) e reais no período analisado."""
    ef = h.get("efeito") or {}
    e, u = _f(ef.get("consumo_pct")), _f(ef.get("consumo_pct_incerteza_k2"))
    vazio = {
        "combustivel_t": None,
        "faixa_t": None,
        "custo_brl": None,
        "faixa_brl": None,
        "cenarios_patio_brl": None,
        "custo_dia_brl": None,
        "efeito_consumo_pct": e,
        "incerteza_efeito_pct_k2": u,
    }
    if e is None:
        return {**vazio, "motivo": "Efeito no consumo não calculado para esta hipótese."}
    if base["e0_t"] is None:
        return {**vazio, "motivo": base["motivo"]}
    fator = exp(e / 100) - 1
    parcela = _f(base["parcelas"].get(PARCELA_DA_CONTA.get(h["id"], "")))
    # mesma base da explicação da conta, para o mesmo efeito não ter dois valores em telas
    # diferentes; nas demais hipóteses, consumo esperado ao consumo por t da referência
    base_t = parcela / fator if parcela is not None and fator else base["e0_t"]
    t = base_t * fator
    faixa_t = None if u is None else sorted(base_t * (exp((e + s * u) / 100) - 1) for s in (-1, 1))
    patio = [x for x in (ef.get("consumo_pct_faixa_patio") or []) if _f(x) is not None]
    cen_t = sorted({base_t * (exp(x / 100) - 1) for x in patio}) if patio else None
    if cen_t and max(cen_t) - min(cen_t) < 1e-9:
        cen_t = None
    p = base["preco"]

    def brl(x):
        return None if x is None or p is None else x * p

    return {
        "combustivel_t": t,
        "faixa_t": faixa_t,
        "custo_brl": brl(t),
        "faixa_brl": None if faixa_t is None or p is None else [x * p for x in faixa_t],
        "cenarios_patio_brl": None if cen_t is None or p is None else [x * p for x in cen_t],
        "custo_dia_brl": None if p is None or not base["dias"] else t * p / base["dias"],
        "efeito_consumo_pct": e,
        "incerteza_efeito_pct_k2": u,
        "motivo": base["motivo"],
    }


def _verificacao(h: dict, separa: set[str]) -> dict:
    cat = VERIFICACOES.get(h["id"])
    acao = h.get("verificacao") or ""
    classificada = cat is not None and acao.startswith(cat["acao"])
    return {
        "acao": acao,
        "informacao": h.get("medicoes", []),
        "complexidade": cat["complexidade"] if classificada else None,
        "exige_parada": cat["exige_parada"] if classificada else None,
        "recurso": cat["recurso"] if classificada else None,
        "distingue": cat["distingue"] if classificada else None,
        "etapa_seguinte": cat["etapa_seguinte"] if classificada else None,
        "proxima_do_motor": h["id"] in separa,
        "origem_complexidade": "regra de triagem proposta (D90)"
        if classificada
        else "não classificada: ação diferente das previstas no catálogo",
    }


def _prioridade(h: dict, natureza: str, imp: dict, verif: dict) -> tuple[str, list[str]]:
    """Regra proposta (D90), categórica e sem pesos."""
    status = h.get("status")
    if natureza == "servico_vapor":
        return "fora", [NOTA_GRUPO["servico_vapor"]]
    if status == "nao_avaliavel":
        return "sem_base", ["O motor não consegue avaliar esta hipótese com os dados atuais."]
    if status in ("descartada", "oposta"):
        return "baixa", [EVIDENCIA[status][1]]
    e = imp["efeito_consumo_pct"]
    if e is not None and e <= 0:
        return "baixa", ["O efeito estimado reduz o consumo: não é perda a investigar agora."]
    motivos = [EVIDENCIA.get(status, ("", "Situação da hipótese não reconhecida."))[1]]
    relevante = (h.get("avaliacao") or {}).get("relevante")
    motivos.append(
        "Efeito relevante pelo critério D29."
        if relevante is True
        else "Relevância do efeito não estabelecida pelo critério D29."
    )
    if verif["complexidade"] is not None:
        motivos.append(
            f"Verificação de complexidade {verif['complexidade'].replace('media', 'média')}"
            + (", sem parada" if verif["exige_parada"] is False else "")
            + " (regra proposta)."
        )
    else:
        motivos.append("Complexidade da verificação não classificada.")
    if relevante is True and verif["complexidade"] == "baixa":
        return "alta", motivos
    return "media", motivos


def _oportunidade(h: dict, base: dict, separa: set[str]) -> dict:
    natureza, grupo = NATUREZA.get(h["id"], ("eficiencia_caldeira", h["id"]))
    imp = _impacto(h, base)
    verif = _verificacao(h, separa)
    prioridade, motivos = _prioridade(h, natureza, imp, verif)
    if verif["proxima_do_motor"] and prioridade in ("alta", "media"):
        motivos.append("É a próxima verificação indicada pelo motor da investigação.")
    nivel, motivo_ev = EVIDENCIA.get(h.get("status"), ("INSUFICIENTE", "Situação desconhecida."))
    return {
        "id": h["id"],
        "titulo": h.get("titulo", h["id"]),
        "natureza": natureza,
        "natureza_rotulo": ROTULO_NATUREZA.get(natureza, natureza),
        "grupo": grupo,
        "situacao_motor": h.get("status"),
        "evidencia": {"nivel": nivel, "motivo": motivo_ev, "fontes": h.get("evidencia")},
        "impacto": imp,
        "verificacao": verif,
        "prioridade": prioridade,
        "prioridade_rotulo": ROTULO_PRIORIDADE[prioridade],
        "porque": motivos,
        "intervencao": {
            "disponivel": False,
            "motivo": "ainda não avaliada, porque a causa não está confirmada.",
            "investimento_brl": None,
            "economia_anual_estimada_brl": None,
            "payback_anos": None,
        },
    }


def _chave(o: dict) -> tuple:
    """Ordem documentada (D90): próxima verificação do motor; prioridade; maior impacto em
    reais (ou em toneladas, sem preço); id. Impacto ausente vai depois, nunca vira zero."""
    imp = o["impacto"]
    v = imp["custo_brl"] if imp["custo_brl"] is not None else imp["combustivel_t"]
    em_investigacao = o["prioridade"] in ("alta", "media")
    return (
        0 if o["verificacao"]["proxima_do_motor"] and em_investigacao else 1,
        PRIORIDADES.index(o["prioridade"]),
        (0, -v) if v is not None else (1, 0.0),
        o["id"],
    )


def _sobreposicao(ops: list[dict], j: dict) -> list[str]:
    ativos = [o for o in ops if o["prioridade"] in ("alta", "media")]
    avisos = []
    grupos: dict[str, list[dict]] = {}
    for o in ativos:
        grupos.setdefault(o["grupo"], []).append(o)
    for g, lista in grupos.items():
        if len(lista) > 1 or g == "perdas_alem_da_chamine":
            avisos.append(NOTA_GRUPO.get(g, "Oportunidades do mesmo grupo podem se sobrepor."))
    if len(ativos) > 1:
        fech = (j.get("o_que_mudou") or {}).get("fechamento") or {}
        avisos.append(
            "Não some os impactos: cada efeito é calculado com um fator por vez."
            + (f" {fech['frase']}" if fech.get("frase") else "")
        )
    return avisos


def _resumo(j: dict, ops: list[dict], base: dict) -> dict:
    ativos = [o for o in ops if o["prioridade"] in ("alta", "media")]
    vj = j.get("valor_em_jogo")
    dias = base["dias"]
    if not ativos:
        sem_base = any(o["prioridade"] == "sem_base" for o in ops)
        frase = (
            "Dados insuficientes para estabelecer uma prioridade defensável."
            if sem_base
            else "Nenhuma oportunidade em investigação nestes períodos."
        )
    else:
        frase = f"{len(ativos)} {'oportunidade' if len(ativos) == 1 else 'oportunidades'} em investigação."
    associado = {
        "custo_brl": None if vj is None else vj.get("valor_brl"),
        "incerteza_brl": None if vj is None else vj.get("incerteza_brl"),
        "dias": dias,
        "base": (
            "Valor em jogo da investigação: aumento de consumo por tonelada de vapor confirmado "
            "pelas incertezas, ao preço médio dos recebimentos. Total medido, não soma das "
            "oportunidades."
            if vj
            else (j.get("valor_em_jogo_motivo") or "Valor em jogo não estimado.")
        ),
    }
    primeira = ativos[0] if ativos else None
    return {
        "frase": frase,
        "em_investigacao": len(ativos),
        "associado": associado,
        "primeira": None
        if primeira is None
        else {
            "id": primeira["id"],
            "titulo": primeira["titulo"],
            "acao": primeira["verificacao"]["acao"],
        },
    }


def priorizar(j: dict) -> dict:
    """Prioridade de investigação a partir do JSON da investigação (D90).

    Entrada: resultado de `investigar` (hipóteses, próxima verificação, explicação da conta,
    valor em jogo, fechamento, períodos). Saída: oportunidades ordenadas, resumo, avisos de
    sobreposição, regras (objetivas × propostas) e a cadeia até a economia verificada.
    Determinística: mesma entrada, mesma ordem.
    """
    separa = set((j.get("proxima_verificacao") or {}).get("separa") or [])
    base = _base(j)
    ops = sorted((_oportunidade(h, base, separa) for h in j.get("hipoteses", [])), key=_chave)
    for i, o in enumerate(ops, 1):
        o["ordem"] = i
    return {
        "versao": VERSAO,
        "resumo": _resumo(j, ops, base),
        "oportunidades": ops,
        "sobreposicao": _sobreposicao(ops, j),
        "intervencao": {
            "disponivel": False,
            "motivo": (
                "Prioridade de intervenção indisponível: nenhuma causa está sustentada por "
                "verificação registrada, e a EULER ainda não registra verificações nem "
                "intervenções. Quando existir, usará investimento, custos adicionais, parada, "
                "economia anual estimada e payback simples (investimento ÷ economia anual), "
                "sempre como estimativa, não economia verificada."
            ),
        },
        "cadeia": [{"id": a, "etapa": b, "disponivel": c} for a, b, c in CADEIA],
        "regras": REGRAS,
    }


def projetar_ano(
    valor_periodo: float | None, dias_periodo: float | None, dias_operacao_ano: float | None
) -> float | None:
    """Projeção linear com dias de operação por ano INFORMADOS pela fábrica: valor ÷ dias do
    período × dias por ano. Supõe o mesmo regime, carga e preço do período analisado; é
    premissa do usuário, não estimativa da EULER. Ausente em qualquer entrada: None."""
    v, d, a = _f(valor_periodo), _f(dias_periodo), _f(dias_operacao_ano)
    if v is None or d is None or a is None or d <= 0:
        return None
    if not 0 < a <= 366:
        raise ValueError("Dias de operação por ano: entre 1 e 366.")
    return v / d * a
