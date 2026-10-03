"""Painel financeiro: compras, consumo valorizado e cenário de recuperação."""

from html import escape

import estado
import pandas as pd
import streamlit as st
from componentes import cabecalho, md
from financeiro import nao_negativo, resumo_financeiro, simular_recuperacao

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

    if j:
        r = resumo_financeiro(j)
        valor = r["diferenca_brl"]
        c1, c2 = st.columns([1, 1])
        with c1:
            cartao(
                "Combustível consumido · estimativa",
                dinheiro(r["consumido_brl"]),
                "Consumo do período valorizado ao preço médio dos recebimentos.",
                "fin-total",
            )
        with c2:
            cartao(
                "Acima da referência · estimativa",
                dinheiro(valor),
                "Diferença de consumo em reais. Parcela recuperável ainda não determinada.",
                "fin-alert",
            )
        if valor is None:
            st.info(j["valor_em_jogo_motivo"])
        else:
            v = j["valor_em_jogo"]
            st.caption(
                f"{num(v['combustivel_extra_t'], 1)} t de combustível acima da referência. "
                + (
                    f"Incerteza do valor: ± {dinheiro(v['incerteza_brl'])}. "
                    if v["incerteza_brl"] is not None
                    else "Incerteza financeira incompleta. "
                )
                + "Causa e recuperação precisam de verificação."
            )
        left, right = st.columns([1.15, 1])
        with left, st.container(border=True):
            st.markdown("#### Para produzir a mesma quantidade")
            if r["referencia_brl"] is not None and r["consumido_brl"] > 0:
                for label, value, color in [
                    ("Ao consumo da referência", r["referencia_brl"], "#7f9ab4"),
                    ("Ao consumo observado", r["consumido_brl"], "#f4ba79"),
                ]:
                    width = 100 * value / r["consumido_brl"]
                    st.html(
                        f'<div class="fin-bar-label"><span>{label}</span>'
                        f'<b>{dinheiro(value)}</b></div><div class="fin-track">'
                        f'<div style="width:{width}%;background:{color}"></div></div>'
                    )
                st.caption(
                    "Mesmo volume de vapor e mesmo preço do combustível. "
                    "Comparação descritiva; não isola carga, qualidade ou outras causas."
                )
            else:
                st.caption(
                    "A comparação em reais aparece quando há dados suficientes "
                    "e aumento de consumo detectável."
                )
            custo = j["o_que_mudou"].get("custo_vapor")
            if custo:
                st.markdown(
                    md(
                        f"**Combustível por tonelada de vapor:** "
                        f"{dinheiro(custo['referencia'])} → {dinheiro(custo['comparacao'])}"
                    )
                )
                st.caption("Estimativa em R$/t de vapor; não inclui os demais custos da operação.")
        with right, st.container(border=True):
            st.markdown("#### E se recuperarmos parte dessa diferença?")
            if valor is not None and valor > 0:
                st.caption("SIMULAÇÃO · escolha sua hipótese; não é uma previsão da EULER.")
                percentual = st.slider(
                    "Parcela da diferença que seria recuperada",
                    0,
                    100,
                    0,
                    step=5,
                    format="%d%%",
                    key=f"fin_recuperacao_{estado.assinatura()}_{p['comparacao']['inicio']}_"
                    f"{p['comparacao']['fim']}_{p['referencia']['inicio']}_{p['referencia']['fim']}",
                )
                resultado = simular_recuperacao(valor, percentual)
                cartao(
                    "Economia no cenário · mesmo período",
                    dinheiro(resultado),
                    f"Se {percentual}% da diferença for recuperada, mantendo produção e preço.",
                    "fin-scenario",
                )
            else:
                st.caption(
                    "O simulador fica disponível quando o motor determina "
                    "uma diferença positiva em reais."
                )
            st.markdown("**Economia comprovada: ainda não apurada.**")
            st.caption("Depende de intervenção registrada e comparação posterior equivalente.")

        with st.container(border=True):
            st.markdown("#### Próxima verificação para avançar")
            st.write(j["proxima_verificacao"]["acao"])
            st.caption(j["proxima_verificacao"]["porque"])
        with st.expander("De onde vêm os valores"):
            st.write(
                "Consumo valorizado = toneladas consumidas × preço médio dos recebimentos. "
                "Esse preço é uma aproximação do custo do combustível queimado, "
                "não uma apuração contábil dos estoques. A diferença vem do motor "
                "de investigação; não somamos possíveis causas nem projetamos um ano."
            )
            if j["valor_em_jogo"]:
                st.write(j["valor_em_jogo"]["base"])
            st.caption(
                "A incerteza exibida vem do motor e não inclui incerteza do preço. "
                "Custos de intervenção não estão descontados do cenário."
            )
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
.fin-scenario {background:#20312c;border-color:#3c6254;min-height:0}
.fin-scenario .fin-value {color:#9be5c2;font-size:2rem}
.fin-bar-label {display:flex;justify-content:space-between;gap:14px;font-size:.86rem;
 color:#d2d7dc;margin:17px 0 9px;flex-wrap:wrap}
.fin-track {background:#33383b;border-radius:6px;height:21px;overflow:hidden}
.fin-track div {height:100%;border-radius:6px}
@media(max-width:640px){.fin-card{padding:20px;min-height:0}.fin-value{font-size:2rem}}
</style>""")
pacote = estado.exigir_pacote()
if pacote is not None:
    mostrar(pacote)
