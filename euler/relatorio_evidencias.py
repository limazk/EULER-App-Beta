"""Relatório legível derivado do mesmo diagnóstico que alimenta a interface."""

from euler.evidencias import ROTULOS
from euler.formato import num


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
            f"Referência: {num(o.get('referencia'))} {o['unidade']}; "
            f"observado: {num(o.get('comparacao'))} {o['unidade']}; "
            f"diferença: {num(o.get('variacao'))} {o['unidade']}."
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
        f"Desvio estimado: {num(e.get('desvio_estimado'))} {e.get('moeda', '')}.",
        f"Preço: {num(e.get('preco'), 6)} {e.get('unidade_preco', '')}; período: {e.get('periodo')}.",
        f"Origem do preço: {e.get('origem_preco') or 'não documentada'}.",
        "Oportunidade recuperável: não apurada. Economia verificada: não apurada.",
    ]
    linhas += [f"- {p}" for p in e.get("premissas", [])]
    linhas += ["### Limitações"] + [f"- {p}" for p in d.get("limitacoes", [])]
    return "\n\n".join(linhas)
