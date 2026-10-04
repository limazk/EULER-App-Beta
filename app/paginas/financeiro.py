"""Painel financeiro: explicação da conta de combustível (D89) e compras registradas."""

from html import escape

import estado
import pandas as pd
import streamlit as st
from componentes import cabecalho, md
from financeiro import nao_negativo

from euler.capacidades import avaliar
from euler.formato import num
from euler.investigacao import investigar
from euler.periodos import periodos_entre_estoques


def dinheiro(v):
    return "Não calculado" if v is None else f"R$ {num(v, 2)}"


@st.cache_data(show_spinner="Preparando o resumo financeiro…", max_entries=32)
def analisar(assinatura, ref, comp, _pacote):
    return investigar(_pacote, ref, comp)


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
            "Combustível consumido",
            dinheiro_sinal(c["consumido"]["custo_brl"]),
            f"{toneladas(c['consumido']['combustivel_t'])} queimadas no período, ao preço médio "
            "dos recebimentos.",
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
            f"Desvio ainda não explicado · {rotulo.lower()}",
            dinheiro_sinal(d["custo_brl"]),
            f"{toneladas(d['combustivel_t'])} ({num(d['pct_do_esperado'], 1)}% do esperado)"
            + (
                f". Faixa das medições: {dinheiro_sinal(faixa[0])} a {dinheiro_sinal(faixa[1])}."
                if faixa
                else ". Faixa não determinada."
            ),
            classe,
        )
    with st.container(border=True):
        st.markdown("**Parcela evitável: não apurada**")
        motivo = c["evitavel"]["motivo"].removeprefix("Parcela evitável não apurada: ")
        st.caption(motivo[:1].upper() + motivo[1:])
        if c["evitavel"]["verificacao"]:
            st.markdown(md(f"**Próxima verificação:** {c['evitavel']['verificacao']}"))
            st.caption(j["proxima_verificacao"]["porque"])

    st.markdown("### Por que a conta mudou em relação à referência")
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


def mostrar(pacote):
    j, _ = estado.investigacao_atual()
    if j is None:
        caps = {c.id: c for c in avaliar(pacote)}
        periodos = periodos_entre_estoques(pacote)
        if caps["comparacao"].habilitada and len(periodos) >= 2:
            n = len(periodos)
            meio = max(1, n // 2)
            escolha = st.session_state.get("periodos_escolhidos")
            if escolha and escolha["assinatura"] == estado.assinatura():
                a, b = escolha["ref"], escolha["comp"]
            else:
                a, b = (0, meio - 1), (meio, min(n - 1, meio + 1))
            if max(*a, *b) < n and (a[1] < b[0] or b[1] < a[0]):
                ref = (periodos[a[0]][0], periodos[a[1]][1])
                comp = (periodos[b[0]][0], periodos[b[1]][1])
                j = analisar(estado.assinatura(), ref, comp, pacote)
                estado.guardar_investigacao(j)

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

    combustivel = pacote.dados("combustivel")
    if combustivel is not None:
        receb = combustivel[combustivel["tipo"] == "recebimento"].copy()
        if not receb.empty:
            receb["valor_valido"] = receb["preco_brl"].map(nao_negativo)
            validos = receb.dropna(subset=["valor_valido"])
            total = float(validos["valor_valido"].sum()) if len(validos) else None
            st.markdown("### Compras registradas")
            st.caption(
                f"Todos os recebimentos carregados: {receb['data'].min():%d/%m/%Y} "
                f"a {receb['data'].max():%d/%m/%Y}. "
                "Este período pode ser diferente da comparação acima."
            )
            cartao(
                "Valor dos recebimentos"
                if len(validos) == len(receb)
                else "Valor parcial dos recebimentos",
                dinheiro(total),
                f"{len(validos)} de {len(receb)} recebimentos com preço. "
                "Compra não equivale a consumo nem a pagamento confirmado.",
            )
            if len(validos):
                grupos = (
                    validos.assign(fornecedor=validos["fornecedor_id"].fillna("Sem identificação"))
                    .groupby("fornecedor")["valor_valido"]
                    .sum()
                    .sort_values(ascending=False)
                )
                st.bar_chart(
                    pd.DataFrame({"Compras (R$)": grupos}),
                    horizontal=True,
                    color="#7f9ab4",
                    height=190,
                )
            st.page_link(
                "paginas/extrato.py",
                label="Comparar fornecedores por custo da energia",
                icon=":material/receipt_long:",
            )


cabecalho(
    "Financeiro", "Quanto o consumo pesa no caixa — e o que vale investigar.", "Visão econômica"
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
pacote = estado.exigir_pacote()
if pacote is not None:
    mostrar(pacote)
