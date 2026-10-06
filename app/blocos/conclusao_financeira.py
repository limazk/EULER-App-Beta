"""Quadro único da conclusão financeira (D101): a conta, a ponte e o que falta verificar.

Só apresenta `euler.conta.conclusao_financeira`; não calcula nem soma oportunidades.
"""

import streamlit as st
from componentes import md

from euler.formato import num


def _brl(v, sinal=False):
    if v is None:
        return "—"
    s = "−" if v < 0 else ("+" if sinal and v > 0 else "")
    return f"{s}R$\u00a0{num(abs(v), 0)}"


def _faixa(f):
    return "não determinada" if not f else f"{_brl(f[0])} a {_brl(f[1])}"


ESTADO = {
    "acima": "acima do esperado, além da incerteza",
    "abaixo": "abaixo do esperado, além da incerteza",
    "nao_estabelecido": "dentro da incerteza: não estabelecida",
    "sem_faixa": "sem faixa de incerteza",
}


def renderizar(q: dict, chave: str = "conclusao") -> None:
    """Desenha o quadro; `q` vem pronto do motor (mesmo objeto no relatório do fechamento)."""
    if not q.get("disponivel"):
        st.info(q.get("motivo") or "Conta indisponível.")
        return
    c, e, s = q["consumido"], q["esperado"], q["sem_explicacao"]
    with st.container(border=True, key=f"{chave}-quadro"):
        st.markdown("### Conclusão financeira")
        st.markdown(md(f"**{q['frase']}**"))
        preco = (
            f"{num(c['combustivel_t'], 1)} t × R$ {num(c['preco_brl_t'], 2)}/t"
            if c.get("preco_brl_t") is not None
            else f"{num(c['combustivel_t'], 1)} t"
        )
        st.markdown(
            md(
                "| A conta do período | Valor | Como foi obtido |\n|---|---:|---|\n"
                f"| Custo do combustível consumido | {_brl(c['custo_brl'])} | {preco} · consumo "
                "calculado pelos estoques e recebimentos |\n"
                f"| Esperado nas condições analisadas | {_brl(e['custo_brl'])} | referência ajustada "
                f"por {', '.join(e['ajustado_por'])} |\n"
                f"| **Diferença sem explicação** | **{_brl(s['custo_brl'], sinal=True)}** | "
                f"faixa das medições: {_faixa(s['faixa_brl'])} · {ESTADO[s['estado']]} |"
            )
        )
        p = q["ponte"]
        if p["disponivel"]:
            d = p.get("dias") or {}
            duracao = (
                f" ({num(d['referencia'], 0)} dias → {num(d['comparacao'], 0)} dias)"
                if d.get("referencia") and d.get("comparacao")
                else ""
            )
            linhas = "".join(
                f"| {g['titulo']}"
                + (f" · {g['nota']}" if g.get("nota") else "")
                + f" | {_brl(g['custo_brl'], sinal=True) if g['custo_brl'] is not None else 'não separado'} |\n"
                for g in p["grupos"]
            )
            st.markdown(
                md(
                    f"**Por que o custo mudou em relação à referência**{duracao}: "
                    f"{_brl(p['referencia_brl'])} → {_brl(p['periodo_brl'])}, variação de "
                    f"{_brl(p['variacao_brl'], sinal=True)}."
                )
            )
            st.markdown(md("| Parcela | Valor |\n|---|---:|\n" + linhas))
            st.caption(
                "As parcelas fecham a variação. Explicado quer dizer atribuído a um fator medido, "
                "não inevitável: a qualidade do combustível, por exemplo, pode ter parte evitável."
                + (
                    " Ainda dentro da diferença: " + "; ".join(p["nao_separados"]).lower() + "."
                    if p["nao_separados"]
                    else ""
                )
            )
        else:
            st.caption(md(f"Comparação com a referência: {p['motivo']}"))
        ev = q["evitavel"]
        st.markdown(md(f"**{ev['situacao']}.** O que falta verificar:"))
        itens = [md(x) for x in ev["antes"]]
        for x in ev["verificacoes"]:
            impacto = (
                f" · impacto associado {_brl(x['impacto_brl'])}"
                + (f" (faixa {_faixa(x['faixa_brl'])})" if x.get("faixa_brl") else "")
                if x.get("impacto_brl") is not None
                else ""
            )
            onde = f", {x['onde']}" if x.get("onde") else ""
            separa = f" Separa: {x['distingue']}." if x.get("distingue") else ""
            itens.append(md(f"**{x['titulo']}**{impacto}{onde}. {x['acao']}{separa}"))
        if itens:
            st.markdown("\n".join(f"{i}. {t}" for i, t in enumerate(itens, 1)))
        else:
            st.caption("Nenhuma verificação priorizada nesta comparação.")
        st.caption(ev["condicao"])
        st.caption(
            "Economia verificada: só depois de uma ação registrada e avaliada em Ações. "
            "A diferença acima não é economia nem prejuízo recuperável confirmado."
        )
