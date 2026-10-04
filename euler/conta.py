"""Explicação da conta de combustível (D89, E16 em docs/fisica/fisica_para_revisao.md).

Separa "gastou mais" de "perdeu eficiência".

Responde, para o período analisado: quanto custou o combustível consumido, quanto seria
esperado nas condições analisadas e quanto da diferença continua sem explicação. Também
decompõe a variação da conta em relação à referência (produção, condição do vapor,
qualidade do combustível, preço e desvio não explicado).

Só usa números que o motor já calculou. Uma parcela só é separada quando há dado para
isso; senão fica misturada ao desvio, com o motivo (ausente nunca vira zero). Não
confirma causa, não estima parcela evitável e não aplica percentual de recuperação.
"""

from math import exp, isfinite

from euler.formato import num

PERGUNTAS = {
    "producao": "Quanto da variação era esperado para atender à demanda de vapor?",
    "condicao_vapor": "Cada tonelada de vapor exigiu mais ou menos energia?",
    "qualidade": "Foi preciso queimar mais massa porque cada tonelada entregou menos energia?",
    "preco": "Quanto veio da mudança de preço do combustível?",
    "nao_explicado": "Quanto permanece depois dos ajustes que os dados permitem?",
}
TITULOS = {
    "producao": "Produção de vapor",
    "condicao_vapor": "Condição do vapor e da água",
    "qualidade": "Qualidade do combustível",
    "preco": "Preço do combustível",
    "nao_explicado": "Desvio ainda não explicado",
}
NAO_MODELADO = (
    "Carga e regime de operação: não modelados nesta versão; seu efeito permanece no desvio."
)


def _f(x) -> float | None:
    return float(x) if isinstance(x, (int, float)) and isfinite(x) else None


def _nao_negativo(x) -> float | None:
    """Preço finito >= 0; negativo, NaN ou infinito fica ausente (nunca vira zero)."""
    x = _f(x)
    return x if x is not None and x >= 0 else None


def _brl(v: float | None) -> str:
    if v is None:
        return "—"
    return ("−" if v < 0 else "") + f"R$ {num(abs(v), 0)}"


def _t(v: float) -> str:
    return f"{num(abs(v), 1)} t"


def explicar_conta(
    *,
    combustivel_ref_t: float | None,
    vapor_ref_t: float | None,
    combustivel_t: float | None,
    vapor_t: float | None,
    preco_ref_brl_t: float | None,
    preco_brl_t: float | None,
    preco_min_brl_t: float | None = None,
    preco_max_brl_t: float | None = None,
    preco_ref_brl_gj: float | None = None,
    preco_brl_gj: float | None = None,
    horas_ref: float | None = None,
    horas: float | None = None,
    incerteza_consumo_t_t: float | None = None,
    efeito_condicao_vapor_pct: float | None = None,
    motivo_condicao_vapor: str = "energia por tonelada de vapor não calculada nos dois períodos",
    efeito_qualidade_pct: float | None = None,
    cenarios_qualidade_pct: tuple[float, float] | None = None,
    motivo_qualidade: str = "umidade e PCI medidos não disponíveis nos dois períodos",
    verificacao: str | None = None,
) -> dict:
    """Conta do período analisado (comparação) contra o esperado nas mesmas condições.

    Entradas: massas em t (combustível queimado E9, vapor do totalizador); preços em R$/t
    (média ponderada dos recebimentos do período; mínimo e máximo por lote); efeitos em
    pontos log % no consumo, como o motor os calcula (condição do vapor: razão da energia
    por kg de vapor; qualidade: razão do PCI úmido mais a perda nos gases pela umidade).
    `incerteza_consumo_t_t`: U (k = 2) da diferença de consumo específico com erros de
    instrumento independentes.

    Cadeia (hipótese: mesma eficiência da referência; D89):
      e0 = k_ref × vapor                    (produção, ao consumo por t da referência)
      e1 = e0 × exp(efeito condição / 100)  (se separado)
      e2 = e1 × exp(efeito qualidade / 100) (se separado) = consumo esperado ajustado
      desvio = combustível − e2             (alvo da investigação, não desperdício)
    Variação da conta: m·p − m_ref·p_ref = m_ref·(p − p_ref) + p·(m − m_ref), com
    m − m_ref = (e0 − m_ref) + (e1 − e0) + (e2 − e1) + desvio. A soma fecha exatamente; o
    desvio em reais é o "(observado − esperado ajustado) × preço" do período.

    Faixa do desvio: ± U × vapor, só das medições de consumo e vapor; não inclui a
    incerteza dos ajustes. Estado "acima"/"abaixo" só quando a faixa exclui zero em todos
    os cenários do pátio; senão "nao_estabelecido". Sem U: "sem_faixa".
    """
    # entradas guardadas no resultado: permitem recalcular com outra política de preço (D93)
    entradas = {k: list(v) if isinstance(v, tuple) else v for k, v in locals().items()}
    m_r, v_r = _f(combustivel_ref_t), _f(vapor_ref_t)
    m, v = _f(combustivel_t), _f(vapor_t)
    p_r, p = _nao_negativo(preco_ref_brl_t), _nao_negativo(preco_brl_t)
    if not all(x is not None and x > 0 for x in (m_r, v_r, m, v)):
        return {
            "disponivel": False,
            "motivo": (
                "Combustível queimado ou vapor não conhecidos nos dois períodos: o consumo "
                "esperado não pode ser calculado."
            ),
            "entradas": entradas,
        }
    k_r = m_r / v_r
    e0 = k_r * v
    ef_dh, ef_w = _f(efeito_condicao_vapor_pct), _f(efeito_qualidade_pct)
    e1 = e0 * exp(ef_dh / 100) if ef_dh is not None else e0
    e2 = e1 * exp(ef_w / 100) if ef_w is not None else e1
    desvio = m - e2

    def custo(t: float | None) -> float | None:
        return None if t is None or p is None else t * p

    ajustado = ["produção de vapor"]
    nao_ajustado = []
    if ef_dh is not None:
        ajustado.append("condição do vapor e da água")
    else:
        nao_ajustado.append(f"Condição do vapor: {motivo_condicao_vapor}; permanece no desvio.")
    if ef_w is not None:
        ajustado.append("qualidade do combustível medida")
    else:
        nao_ajustado.append(f"Qualidade do combustível: {motivo_qualidade}; permanece no desvio.")
    nao_ajustado.append(NAO_MODELADO)

    # cenários do pátio para a qualidade (recebido × FIFO): outros valores do desvio
    centros = [desvio]
    cen_q = None
    if ef_w is not None and cenarios_qualidade_pct:
        alt = {m - e1 * exp(x / 100) for x in cenarios_qualidade_pct if _f(x) is not None}
        if alt - {desvio}:  # só há cenário quando recebido e FIFO dão valores diferentes
            centros += sorted(alt)
            cen_q = None if p is None else sorted(custo(x) for x in alt)

    u = _f(incerteza_consumo_t_t)
    u_t = None if u is None else u * v
    faixa_t = None if u_t is None else (desvio - u_t, desvio + u_t)
    if u_t is None:
        estado = "sem_faixa"
    elif min(c - u_t for c in centros) > 0:
        estado = "acima"
    elif max(c + u_t for c in centros) < 0:
        estado = "abaixo"
    else:
        estado = "nao_estabelecido"

    p_min, p_max = _nao_negativo(preco_min_brl_t), _nao_negativo(preco_max_brl_t)
    cen_p = (
        sorted((desvio * p_min, desvio * p_max))
        if p_min is not None and p_max is not None and p_min != p_max
        else None
    )
    sentido = "acima" if desvio >= 0 else "abaixo"
    valor = custo(desvio)
    faixa_brl = None if faixa_t is None or p is None else [x * p for x in faixa_t]
    em_reais = (
        f", equivalente a {_brl(abs(valor))} ao preço médio dos recebimentos"
        if valor is not None
        else " (sem preço dos recebimentos no período, o valor em reais não foi estimado)"
    )
    faixa_txt = (
        f"de {_brl(faixa_brl[0])} a {_brl(faixa_brl[1])}"
        if faixa_brl
        else (f"de {_t(faixa_t[0])} a {_t(faixa_t[1])}" if faixa_t else "")
    )
    base = f"O consumo ficou {_t(desvio)} {sentido} da referência ajustada{em_reais}"
    if estado == "acima":
        frase = (
            f"{base}. A faixa das medições vai {faixa_txt}. Ainda não se sabe quanto dessa "
            "diferença pode ser evitado."
        )
    elif estado == "abaixo":
        frase = f"{base}. A faixa das medições vai {faixa_txt}: o consumo ficou abaixo do esperado."
    elif estado == "nao_estabelecido":
        conclusao = (
            "o custo adicional não ficou bem estabelecido."
            if desvio >= 0
            else "a diferença não ficou bem estabelecida."
        )
        frase = (
            f"{base}, mas a faixa das medições vai {faixa_txt} e inclui zero: {conclusao}"
            if faixa_t[0] <= 0 <= faixa_t[1]
            else (
                f"{base}. A faixa das medições vai {faixa_txt}, mas em um cenário do pátio "
                f"(combustível queimado diferente do recebido) a diferença pode ser zero: "
                f"{conclusao}"
            )
        )
    else:
        frase = (
            f"{base}, mas sem a incerteza declarada de todos os instrumentos não dá para "
            "saber se a diferença é maior que o erro de medição."
        )

    var = _variacao(m_r, m, e0, e1, e2, desvio, p_r, p, ef_dh, ef_w)
    var["componentes"] = _componentes(
        var,
        v_r,
        v,
        k_r,
        p_r,
        p,
        ef_dh,
        ef_w,
        motivo_condicao_vapor,
        motivo_qualidade,
        preco_ref_brl_gj,
        preco_brl_gj,
    )
    return {
        "disponivel": True,
        "motivo": None,
        "entradas": entradas,
        "moeda": "BRL",
        "consumido": {"combustivel_t": m, "preco_brl_t": p, "custo_brl": custo(m)},
        "esperado": {
            "combustivel_t": e2,
            "custo_brl": custo(e2),
            "consumo_referencia_t_t": k_r,
            "ajustado_por": ajustado,
            "nao_ajustado": nao_ajustado,
        },
        "desvio": {
            "combustivel_t": desvio,
            "custo_brl": valor,
            "pct_do_esperado": 100 * desvio / e2,
            "faixa_t": None if faixa_t is None else list(faixa_t),
            "faixa_brl": faixa_brl,
            "cenarios_qualidade_brl": cen_q,
            "cenarios_preco_brl": cen_p,
            "estado": estado,
            "frase": frase,
        },
        "evitavel": {
            "custo_brl": None,
            "motivo": (
                "Parcela evitável não apurada: depende de verificar um mecanismo específico e "
                "de uma condição de referência tecnicamente justificada. Nenhum percentual de "
                "recuperação é aplicado."
            ),
            "verificacao": verificacao,
        },
        "variacao": var,
        "premissas": _premissas(horas_ref, horas, preco_ref_brl_gj, preco_brl_gj, p),
    }


def _variacao(m_r, m, e0, e1, e2, desvio, p_r, p, ef_dh, ef_w) -> dict:
    t = {
        "producao": e0 - m_r,
        "condicao_vapor": e1 - e0 if ef_dh is not None else None,
        "qualidade": e2 - e1 if ef_w is not None else None,
        "nao_explicado": desvio,
    }
    if p is None or p_r is None:
        return {
            "disponivel": False,
            "motivo": (
                "Sem preço dos recebimentos "
                + ("nos dois períodos" if p is None and p_r is None else "num dos períodos")
                + ": a variação da conta não pode ser decomposta em reais."
            ),
            "combustivel_t": t,
        }
    brl = {k: None if x is None else x * p for k, x in t.items()}
    brl["preco"] = m_r * (p - p_r)
    return {
        "disponivel": True,
        "motivo": None,
        "custo_referencia_brl": m_r * p_r,
        "custo_brl": m * p,
        "variacao_brl": m * p - m_r * p_r,
        "combustivel_t": t,
        "brl": brl,
    }


def _componentes(var, v_r, v, k_r, p_r, p, ef_dh, ef_w, mot_dh, mot_w, pgj_r, pgj) -> list[dict]:
    t, brl = var["combustivel_t"], var.get("brl") or {}

    def linha(chave: str, base: str, separado: bool = True) -> dict:
        return {
            "id": chave,
            "titulo": TITULOS[chave],
            "pergunta": PERGUNTAS[chave],
            "separado": separado,
            "combustivel_t": t.get(chave),
            "custo_brl": brl.get(chave),
            "base": base,
        }

    preco_base = (
        f"R$ {num(p_r)}/t → R$ {num(p)}/t (média ponderada dos recebimentos), aplicada ao "
        "combustível da referência."
        if p is not None and p_r is not None
        else "Preço dos recebimentos ausente num dos períodos; parcela não separada."
    )
    if pgj_r is not None and pgj is not None:
        preco_base += (
            f" Por energia: R$ {num(pgj_r)}/GJ → R$ {num(pgj)}/GJ, base PCI úmido dos lotes."
        )
    return [
        linha(
            "producao",
            f"{num(v_r, 1)} t → {num(v, 1)} t de vapor, ao consumo da referência "
            f"({num(k_r, 3)} t de combustível por t de vapor).",
        ),
        linha(
            "condicao_vapor",
            f"Energia por tonelada de vapor: efeito de {num(ef_dh, 1)}% no consumo."
            if ef_dh is not None
            else f"Não separada: {mot_dh}. Permanece no desvio.",
            ef_dh is not None,
        ),
        linha(
            "qualidade",
            f"Umidade e PCI medidos: efeito de {num(ef_w, 1)}% no consumo (inclui a perda nos "
            "gases pela umidade)."
            if ef_w is not None
            else f"Não separada: {mot_w}. Permanece no desvio.",
            ef_w is not None,
        ),
        linha("preco", preco_base, p is not None and p_r is not None),
        linha(
            "nao_explicado",
            "Alvo da investigação; não é automaticamente desperdício recuperável. Inclui as "
            "parcelas não separadas, carga, regime e mecanismos de eficiência (gases, excesso "
            "de ar, purga).",
        ),
    ]


def _premissas(horas_ref, horas, pgj_r, pgj, p) -> list[str]:
    premissas = [
        (
            "Consumo esperado = consumo por tonelada de vapor da referência, ajustado só pelo que "
            "os dados permitem separar (hipótese: mesma eficiência da referência)."
        ),
        (
            "Preço = média ponderada dos recebimentos do período. Compra não é consumo: o "
            "combustível queimado pode ter sido comprado antes, a outro preço."
        ),
        "Frete e outros custos variáveis só entram se estiverem no preço informado de cada lote.",
        (
            "Custo do combustível consumido não é necessariamente caixa: contratos com mínimo de "
            "compra ou tarifa fixa não mudam com o consumo."
        ),
        (
            "A faixa vem das medições de consumo e vapor (k = 2); não inclui a incerteza dos "
            "ajustes nem do preço. Cenários de preço e do pátio são variações de premissa, não "
            "intervalos de confiança."
        ),
    ]
    h_r, h = _f(horas_ref), _f(horas)
    if h_r and h and abs(h_r - h) > 1:
        premissas.append(
            f"Períodos com durações diferentes ({num(h_r / 24, 1)} e {num(h / 24, 1)} dias): "
            "a parcela de produção inclui essa diferença."
        )
    if (pgj_r is None or pgj is None) and p is not None:
        premissas.append(
            "Custo por energia (R$/GJ) indisponível: com biomassa, R$/t pode confundir quando a "
            "umidade muda."
        )
    return premissas
