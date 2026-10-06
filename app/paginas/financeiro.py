"""Painel financeiro: explicação da conta de combustível (D89) e compras registradas."""

from html import escape

import estado
import pandas as pd
import streamlit as st
from componentes import cabecalho, incerteza_explicada, md
from financeiro import movimentacao_periodo, resumo_compras, resumo_variacao

from euler.formato import num


def dinheiro(v):
    return "Não calculado" if v is None else f"R$ {num(v, 2)}"


def cartao(rotulo, valor, legenda, classe=""):
    st.html(
        f'<div class="fin-card {classe}"><div class="fin-label">{escape(rotulo)}</div>'
        f'<div class="fin-value">{escape(valor)}</div><p>{escape(legenda)}</p></div>'
    )


ESTADOS = {
    "acima": ("Acima do esperado", "fin-alert"),
    "abaixo": ("Abaixo do esperado", "fin-total"),
    "nao_estabelecido": ("Não ficou bem estabelecido", ""),
    "sem_faixa": ("Faixa não determinada", ""),
}


def dinheiro_sinal(v):
    return "—" if v is None else ("−" if v < 0 else "") + f"R$ {num(abs(v), 0)}"


def toneladas(v):
    return "—" if v is None else ("−" if v < 0 else "") + f"{num(abs(v), 1)} t"


def ponte_da_conta(c):
    """Resumo da decomposição reconciliada; sem nova atribuição física."""
    r = resumo_variacao(c)
    st.markdown("### Por que o custo mudou")
    if not r["disponivel"]:
        st.info(r["motivo"])
        return
    st.caption(
        md(
            f"Custo atribuído ao consumo: {dinheiro(r['custo_referencia_brl'])} na referência → "
            f"{dinheiro(r['custo_brl'])} no período. Variação: {dinheiro_sinal(r['variacao_brl'])}. "
            "Compare também a duração dos períodos acima."
        )
    )
    for coluna, parcela in zip(st.columns(3), r["grupos"]):
        coluna.metric(parcela["titulo"], dinheiro_sinal(parcela["custo_brl"]), border=True)
    st.caption(
        "As três parcelas fecham a variação total. São uma decomposição sob as premissas "
        "da referência; o residual não demonstra, sozinho, desperdício ou perda de eficiência."
    )
    if r["nao_separados"]:
        st.caption("Ainda misturados ao residual: " + "; ".join(r["nao_separados"]) + ".")


def explicar(j):
    """Explicação da conta (D89): o motor já calculou; a tela só apresenta."""
    c = j["explicacao_conta"]
    d, e = c["desvio"], c["esperado"]
    dias = {
        k: (pd.Timestamp(x["fim"]) - pd.Timestamp(x["inicio"])).total_seconds() / 86400
        for k, x in j["periodos"].items()
    }
    rotulo, classe = ESTADOS[d["estado"]]
    st.markdown(md(f"#### {d['frase']}"))
    c1, c2, c3 = st.columns(3)
    with c1:
        cartao(
            "Custo atribuído ao consumo",
            dinheiro_sinal(c["consumido"]["custo_brl"]),
            f"{toneladas(c['consumido']['combustivel_t'])} queimadas no período, ao preço médio "
            "dos recebimentos com preço e massa válidos.",
            "fin-total",
        )
    with c2:
        cartao(
            "Esperado nas mesmas condições",
            dinheiro_sinal(e["custo_brl"]),
            f"{toneladas(e['combustivel_t'])}: consumo por tonelada de vapor da referência, "
            "ajustado por: " + ", ".join(e["ajustado_por"]) + ".",
        )
    with c3:
        faixa = d["faixa_brl"]
        cartao(
            f"Desvio monetizado · {rotulo.lower()}",
            dinheiro_sinal(d["custo_brl"]),
            f"{toneladas(d['combustivel_t'])} ({num(d['pct_do_esperado'], 1)}% do esperado)"
            + (
                f". Faixa das medições: {dinheiro_sinal(faixa[0])} a {dinheiro_sinal(faixa[1])}."
                if faixa
                else ". Faixa não determinada."
            ),
            classe,
        )
    preco = c["consumido"]["preco_brl_t"]
    st.caption(
        f"Preço do combustível: {dinheiro(preco)}/t · média ponderada dos recebimentos com preço e massa válidos. "
        "Custo atribuído não é pagamento confirmado."
        if preco is not None
        else "Preço do combustível não informado no período: informe o valor total e a massa "
        "dos recebimentos para expressar a diferença em reais."
    )
    with st.expander("Entender a faixa de incerteza"):
        incerteza_explicada(d.get("incerteza"))
    with st.container(border=True):
        potencial, verificada = st.columns(2)
        with potencial:
            st.markdown("**Oportunidade fundamentada**")
            st.markdown("Parcela evitável: não apurada")
            st.caption(
                "Depende de confirmar um mecanismo corrigível e uma referência justificável."
            )
        with verificada:
            st.markdown("**Economia verificada**")
            st.markdown("Não avaliada nesta comparação")
            st.caption(
                "Consulte avaliações pós-intervenção em Ações. Uma queda de consumo isolada não comprova economia."
            )
        if c["evitavel"]["verificacao"]:
            st.markdown(md(f"**Próxima verificação:** {c['evitavel']['verificacao']}"))
            st.caption(j["proxima_verificacao"]["porque"])
        st.page_link(
            "paginas/oportunidades.py",
            label="Ver as oportunidades em ordem de prioridade",
            icon=":material/flag:",
        )

    ponte_da_conta(c)

    with st.expander("Por que a conta mudou · composição e premissas"):
        v = c["variacao"]
        if v["disponivel"]:
            st.caption(
                md(
                    f"Conta da referência ({num(dias['referencia'], 0)} dias) "
                    f"{dinheiro_sinal(v['custo_referencia_brl'])} → conta do período "
                    f"({num(dias['comparacao'], 0)} dias) {dinheiro_sinal(v['custo_brl'])}: variação "
                    f"de {dinheiro_sinal(v['variacao_brl'])}. As parcelas somam exatamente a variação."
                )
            )
        else:
            st.caption(v["motivo"])
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Parcela": x["titulo"],
                        "Pergunta": x["pergunta"],
                        "Combustível": toneladas(x["combustivel_t"])
                        if x["separado"] or x["id"] == "preco"
                        else "no desvio",
                        "Valor": dinheiro_sinal(x["custo_brl"])
                        if x["custo_brl"] is not None
                        else ("no desvio" if not x["separado"] else "—"),
                    }
                    for x in v["componentes"]
                ]
            ),
            hide_index=True,
            width="stretch",
        )
        vj = j.get("valor_em_jogo")
        if vj and v["disponivel"]:
            b = {x["id"]: x["custo_brl"] for x in v["componentes"]}
            st.caption(
                md(
                    f"Na Investigação, o valor em jogo é {dinheiro_sinal(vj['valor_brl'])}: consumo "
                    "acima da referência para o mesmo vapor. Aqui ele se divide em condição do vapor "
                    f"({dinheiro_sinal(b['condicao_vapor'])}), qualidade do combustível "
                    f"({dinheiro_sinal(b['qualidade'])}) e desvio não explicado "
                    f"({dinheiro_sinal(b['nao_explicado'])})."
                )
            )
        with st.expander("Premissas, faixas e cenários"):
            for x in v["componentes"]:
                st.markdown(md(f"**{x['titulo']}:** {x['base']}"))
            for x in e["nao_ajustado"]:
                st.write(x)
            if d["cenarios_preco_brl"]:
                a, b = d["cenarios_preco_brl"]
                st.markdown(
                    md(
                        "Cenários de preço (menor e maior preço por tonelada dos lotes do período): "
                        f"desvio de {dinheiro_sinal(a)} a {dinheiro_sinal(b)}."
                    )
                )
            if d["cenarios_qualidade_brl"]:
                a, b = d["cenarios_qualidade_brl"]
                st.markdown(
                    md(
                        "Cenários do pátio (combustível queimado = recebido ou o mais antigo do "
                        f"estoque): desvio de {dinheiro_sinal(a)} a {dinheiro_sinal(b)}."
                    )
                )
            for x in c["premissas"]:
                st.caption(md(x))
            st.caption(
                "Economia comprovada: ainda não apurada. Depende de intervenção registrada e "
                "comparação posterior com a referência ajustada."
            )


def compras_e_estoque(pacote, j):
    """Compras da comparação e conta física; histórico fora do período fica recolhido."""
    combustivel = pacote.dados("combustivel")
    if combustivel is None:
        st.info("Importe os recebimentos para acompanhar compras e custo do combustível.")
        return
    if j:
        p = j["periodos"]["comparacao"]
        c = j.get("explicacao_conta") or {}
        cp = movimentacao_periodo(
            pacote,
            p["inicio"],
            p["fim"],
            preco_brl_t=(c.get("consumido") or {}).get("preco_brl_t"),
        )
        r = cp["compras"]
        st.markdown("### Compras e estoque no período")
        st.caption(
            "Mesmas datas da comparação acima. Recebimentos após o início e até o fim do período."
        )
        compra, recebido, pagamento = st.columns(3)
        parcial = r["sem_preco"] > 0 and r["valor_conhecido_brl"] is not None
        compra.metric(
            "Valor conhecido dos recebimentos" if parcial else "Valor dos recebimentos",
            dinheiro(r["valor_conhecido_brl"])
            if r["valor_conhecido_brl"] is not None
            else "Não informado",
            border=True,
        )
        recebido.metric("Combustível recebido", toneladas(r["recebido_t"]), border=True)
        pagamento.metric("Pagamento confirmado", "Não informado", border=True)
        st.caption(
            f"{r['lotes']} recebimentos · {r['sem_preco']} sem preço válido · {r['sem_massa']} sem massa válida. Compra não é consumo; valor de nota não é pagamento."
        )
        if r["massas_estimadas"]:
            st.caption(
                f"{r['massas_estimadas']} recebimentos com massa estimada a partir do volume e da densidade informados."
            )
        if parcial:
            st.warning(
                "Valor parcial: falta preço em parte dos recebimentos. O subtotal conhecido não representa a compra total."
            )
        if not r["lotes"]:
            st.info(
                "Nenhum recebimento registrado neste período. Isso não comprova ausência de compras na operação."
            )
        if cp["variacao_estoque_t"] is not None:
            diferenca = cp["variacao_estoque_t"]
            st.caption(
                "O estoque "
                + (
                    f"aumentou {toneladas(diferenca)}"
                    if diferenca > 0
                    else f"diminuiu {toneladas(abs(diferenca))}"
                    if diferenca < 0
                    else "permaneceu no mesmo nível"
                )
                + ". Por isso, recebimento e consumo devem ser lidos separadamente."
            )
        with st.expander("Conferir a conta do estoque"):
            st.markdown(
                "**Estoque inicial + recebimentos − estoque final = combustível consumido**"
            )
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "Registro": "Estoque inicial",
                            "Massa": toneladas(cp["estoque_inicial_t"]),
                        },
                        {"Registro": "Recebimentos", "Massa": toneladas(cp["recebido_t"])},
                        {"Registro": "Estoque final", "Massa": toneladas(cp["estoque_final_t"])},
                        {"Registro": "Consumo calculado", "Massa": toneladas(cp["consumido_t"])},
                    ]
                ),
                hide_index=True,
                width="stretch",
            )
            if cp["motivo_consumo"]:
                st.info(cp["motivo_consumo"])
            st.caption(
                "Estoque em reais não apurado nesta comparação. Consulte Fechamentos da planta para a política de custo cadastrada e seu histórico."
            )
    with st.expander("Todos os recebimentos carregados", expanded=j is None):
        r = resumo_compras(combustivel)
        st.caption(
            "Histórico completo carregado; pode incluir datas fora da comparação. Não somar este valor ao período acima."
        )
        cartao(
            "Compras registradas" if not r["sem_preco"] else "Valor parcial dos recebimentos",
            dinheiro(r["valor_conhecido_brl"]),
            f"{r['lotes']} recebimentos · {r['sem_preco']} sem preço válido. Compra não equivale a consumo nem a pagamento confirmado.",
        )
        grupos = [x for x in r["fornecedores"] if x["valor_brl"] is not None]
        if grupos:
            valores = (
                pd.DataFrame(
                    {
                        "Fornecedor": [
                            x["fornecedor"] + (" · parcial" if x["parcial"] else "") for x in grupos
                        ],
                        "Compras (R$)": [x["valor_brl"] for x in grupos],
                    }
                )
                .set_index("Fornecedor")
                .sort_values("Compras (R$)", ascending=False)
            )
            st.bar_chart(valores, horizontal=True, color="#7f9ab4", height=190)
        st.page_link(
            "paginas/extrato.py",
            label="Comparar fornecedores por custo da energia",
            icon=":material/receipt_long:",
        )


def mostrar(pacote):
    j = estado.investigacao_ou_padrao(pacote)

    if j:
        p = j["periodos"]
        datas = {k: (pd.Timestamp(v["inicio"]), pd.Timestamp(v["fim"])) for k, v in p.items()}
        dias = (datas["comparacao"][1] - datas["comparacao"][0]).total_seconds() / 86400
        st.caption(
            f"Período analisado: {datas['comparacao'][0]:%d/%m/%Y} a "
            f"{datas['comparacao'][1]:%d/%m/%Y} ({num(dias, 1)} dias) · "
            f"Referência: {datas['referencia'][0]:%d/%m/%Y} a {datas['referencia'][1]:%d/%m/%Y}"
        )
    st.page_link(
        "paginas/investigacao.py",
        label="Escolher períodos e ver investigação",
        icon=":material/tune:",
    )

    if j and (j.get("explicacao_conta") or {}).get("disponivel"):
        explicar(j)
    elif j:
        st.info((j.get("explicacao_conta") or {}).get("motivo") or j["o_que_mudou"]["frase"])
    else:
        st.info(
            "O consumo ainda não pode ser comparado em reais. "
            "Você já pode consultar as compras registradas abaixo."
        )

    compras_e_estoque(pacote, j)


cabecalho(
    "Financeiro",
    "Entenda a conta do combustível e o que merece verificação.",
    "Analisar um período",
)
st.html("""<style>
.fin-card {border:1px solid #3c4145;border-radius:16px;padding:24px 26px;
 background:#25292c;margin:3px 0 12px;min-height:165px;box-sizing:border-box}
.fin-label {font-size:.8rem;letter-spacing:.045em;color:#b7c2cb;font-weight:600}
.fin-value {font-size:clamp(1.6rem,3vw,2.7rem);font-weight:650;letter-spacing:-.04em;
 color:#f3f6f8;line-height:1.3;margin:14px 0;overflow-wrap:anywhere}
.fin-card p {font-size:.85rem;line-height:1.5;color:#b5bfc5;margin:0;max-width:48ch}
.fin-total {background:linear-gradient(130deg,#283944,#20272c);border-color:#45545f}
.fin-alert {background:linear-gradient(130deg,#3b3023,#292725);border-color:#705431}
.fin-alert .fin-value {color:#ffd39b}
@media(max-width:640px){.fin-card{padding:20px;min-height:0}.fin-value{font-size:2rem}}
</style>""")
origem = st.radio(
    "Origem da análise",
    ["Dados desta sessão", "Fechamentos da planta"],
    horizontal=True,
    key="fin_origem",
)
if origem == "Fechamentos da planta":
    from blocos.financeiro_planta import mostrar as mostrar_planta

    mostrar_planta()
else:
    pacote = estado.exigir_pacote()
    if pacote is not None:
        mostrar(pacote)
