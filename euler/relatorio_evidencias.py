"""Relatório legível derivado do mesmo diagnóstico que alimenta a interface."""

from euler.evidencias import ROTULOS
from euler.formato import num


def casas(valor) -> int:
    """Casas decimais da observação: 3 para valores pequenos (ex.: 0,321 t/t), 2 nos demais.

    Mantém a mesma precisão das outras telas (antes 0,321 t/t aparecia como 0,32)."""
    return 3 if isinstance(valor, (int, float)) and abs(valor) < 10 else 2


def texto_valor(e: dict) -> str:
    """Valorização do desvio, ou "não estimado" com o motivo (ausente nunca vira zero)."""
    v = e.get("desvio_estimado")
    if v is None:
        motivo = e.get("motivo_sem_valor")
        return "não estimado" + (f". {motivo}" if motivo else "")
    return f"{num(v)} {e.get('moeda', '')}".strip()


def texto_diagnostico(d: dict) -> str:
    """Unidades, premissas, limitações e identificação preservadas no texto."""
    o, e = d["observacao"], d["economia"]
    linhas = [
        f"## Diagnóstico EULER · {d['equipamento']} · {d['periodo']}",
        d["conclusao"],
        "Causa confirmada: NÃO.",
        f"Identificação: {d['analise_id']}",
        f"SHA-256 do resultado: {d['resultado_sha256']}",
        d["escopo_classificacao"],
        "### Dimensões da evidência",
    ]
    for k, v in d["dimensoes"].items():
        linhas.append(f"- {ROTULOS[k]}: {v['nivel']}. " + " ".join(v["motivos"]))
    linhas += [
        "### Observação e baseline",
        (
            f"Referência: {num(o.get('referencia'), casas(o.get('referencia')))} {o['unidade']}; "
            f"observado: {num(o.get('comparacao'), casas(o.get('comparacao')))} {o['unidade']}; "
            f"diferença: {num(o.get('variacao'), casas(o.get('variacao')))} {o['unidade']}."
        ),
        "Origem, modelo, parâmetros e resultados detalhados: exportação JSON do mesmo ID.",
        "### Hipóteses (nenhuma causa confirmada)",
    ]
    for h in d.get("hipoteses", []):
        linhas.append(
            f"- {h.get('titulo', h['id'])}: {h.get('estado_interpretacao', h.get('status'))}. "
            + " ".join(str(x) for x in h.get("evidencias", []))
        )
    linhas.append("### Próximas verificações")
    for v in d.get("proximas_medicoes", []):
        linhas.append(f"{v['ordem']}. {v['acao']} Motivo: {v['porque']}")
    linhas += [
        "Ordem qualitativa por dependências diagnósticas; não é valor da informação calculado.",
        "### Impacto econômico",
        f"Desvio estimado: {texto_valor(e)}",
        f"Preço: {num(e.get('preco'), 6)} {e.get('unidade_preco', '')}; período: {e.get('periodo')}.",
        f"Origem do preço: {e.get('origem_preco') or 'não documentada'}.",
        "Oportunidade recuperável: não apurada. Economia verificada: não apurada.",
    ]
    linhas += [f"- {p}" for p in e.get("premissas", [])]
    linhas += ["### Limitações"] + [f"- {p}" for p in d.get("limitacoes", [])]
    return "\n\n".join(linhas)
