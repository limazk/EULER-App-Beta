"""Tela Investigação: o consumo mudou? O que os dados sustentam? O que verificar? (T13)."""

import json

import estado
import graficos
import pandas as pd
import streamlit as st
from componentes import md

from euler.capacidades import avaliar
from euler.formato import num, pct
from euler.investigacao import investigar
from euler.periodos import periodos_entre_estoques
from euler.relatorio import mudou_detectavel
from euler.textos import PERGUNTA_CENTRAL

st.title("Investigação")
st.markdown(f"> {PERGUNTA_CENTRAL}")

STATUS = {
    "sustentada": ("Compatível com os dados (não comprovada)", ":material/check_circle:"),
    "oposta": ("Mudou no sentido contrário (compensou parte)", ":material/swap_vert:"),
    "possivel": ("Continua possível", ":material/help:"),
    "descartada": ("Descartada pelos dados", ":material/cancel:"),
    "nao_avaliavel": ("Não dá para avaliar", ":material/block:"),
}


def _rotulo_periodo(p) -> str:
    return f"{p[0]:%d/%m} a {p[1]:%d/%m}"


def _escolher_periodos(periodos):
    n = len(periodos)
    rotulos = [_rotulo_periodo(p) for p in periodos]
    ref_fim = max(1, n // 2)
    comp_fim = min(n, ref_fim + 2)
    c1, c2 = st.columns(2)
    ref = c1.select_slider(
        "Período de referência (como era)",
        options=list(range(n)),
        value=(0, ref_fim - 1),
        format_func=lambda i: rotulos[i],
    )
    comp = c2.select_slider(
        "Período de comparação (como ficou)",
        options=list(range(n)),
        value=(min(ref_fim, n - 1), comp_fim - 1),
        format_func=lambda i: rotulos[i],
    )
    return (periodos[ref[0]][0], periodos[ref[1]][1]), (periodos[comp[0]][0], periodos[comp[1]][1])


def _grafico_temperatura(pacote, ref, comp) -> None:
    diario = pacote.dados("diario")
    if diario is None or not diario["t_gases_c"].notna().any():
        return
    d = diario.dropna(subset=["t_gases_c", "instante_observado"])
    d = d[d["regime"].fillna("estavel") != "parada"]
    dias = d.groupby(d["instante_observado"].dt.tz_localize(None).dt.normalize())[
        "t_gases_c"
    ].mean()
    df = pd.DataFrame({"dia": dias.index, "valor": dias.values.astype(float)})
    st.altair_chart(
        graficos.serie_diaria_com_periodos(
            df,
            "Temperatura dos gases na chaminé (°C, média do dia)",
            ".0f",
            [(ref[0], ref[1], "Referência"), (comp[0], comp[1], "Comparação")],
        ),
        width="stretch",
    )


def _hipoteses(lista, titulo_vazio: str) -> None:
    if not lista:
        st.caption(titulo_vazio)
    for h in lista:
        rotulo, icone = STATUS[h["status"]]
        with st.container(border=True):
            st.markdown(f"{icone} **{h['titulo']}** · {rotulo}")
            st.markdown(md(h["porque"]))
            efeito = h["efeito"]["consumo_pct"]
            if efeito is not None and h["status"] in ("sustentada", "possivel"):
                st.caption(
                    f"Efeito estimado no consumo: {'+' if efeito >= 0 else ''}{num(efeito, 1)}%"
                )
            st.caption(f"Como verificar: {h['verificacao']}")


def _indicadores(j) -> None:
    linhas = []
    for c in j["o_que_mudou"]["indicadores"]:
        if c["referencia"] is None and c["comparacao"] is None:
            continue
        if c["unidade"] == "fração":
            f = pct
        else:

            def f(v, u=c["unidade"]):
                casas = 3 if u == "MJ/kg" else 1
                return "—" if v is None else f"{num(v, casas)} {u}"

        linhas.append(
            {
                "Indicador": c["nome"][0].upper() + c["nome"][1:],
                "Referência": f(c["referencia"]),
                "Comparação": f(c["comparacao"]),
                "Mudou de forma detectável?": mudou_detectavel(c),
            }
        )
    # tabela simples: quebra o texto (a coluna da detecção tem frases longas)
    st.table(pd.DataFrame(linhas).set_index("Indicador"))


def mostrar(pacote) -> None:
    caps = {c.id: c for c in avaliar(pacote)}
    if not caps["comparacao"].habilitada:
        st.warning("**Investigação bloqueada.** " + " ".join(caps["comparacao"].motivos))
        st.markdown("Para liberar: " + " ".join(caps["comparacao"].o_que_fazer))
        return
    periodos = periodos_entre_estoques(pacote)
    ref, comp = _escolher_periodos(periodos)
    if not (ref[1] <= comp[0] or comp[1] <= ref[0]):
        st.warning("Os dois períodos se sobrepõem. Escolha períodos separados.")
        return

    j = investigar(pacote, ref, comp)
    st.session_state["investigacao"] = j

    conclusao = j["conclusao"]
    if conclusao["abstencao"]:
        st.warning(md(conclusao["texto"]), icon=":material/pan_tool:")
    else:
        st.success(md(conclusao["texto"]), icon=":material/fact_check:")

    st.markdown("### 1. O que mudou")
    st.markdown(f"**{md(j['o_que_mudou']['frase'])}**")
    if j["o_que_mudou"]["custo_vapor"]:
        st.markdown(md(j["o_que_mudou"]["custo_vapor"]["frase"]))
    _grafico_temperatura(pacote, ref, comp)
    _indicadores(j)
    valor = j["valor_em_jogo"]
    if valor:
        st.metric(
            "Valor em jogo no período de comparação (estimado)",
            md(f"R$ {num(valor['valor_brl'], 0)}"),
        )
        incerteza = (
            f"Incerteza: ± R$ {num(valor['incerteza_brl'], 0)}. "
            if valor["incerteza_brl"] is not None
            else ""
        )
        st.caption(md(incerteza + valor["base"]))
    else:
        st.caption(md(j["valor_em_jogo_motivo"]))

    hips = j["hipoteses"]
    st.markdown("### 2. O que os dados sustentam")
    _hipoteses(
        [h for h in hips if h["status"] == "sustentada"],
        "Nenhuma explicação é sustentada pelos dados.",
    )
    opostas = [h for h in hips if h["status"] == "oposta"]
    if opostas:
        _hipoteses(opostas, "")
    fechamento = j["o_que_mudou"].get("fechamento")
    if fechamento:
        st.caption(md(fechamento["frase"]))
        if fechamento.get("frase_com_condicionais"):
            st.caption(md(fechamento["frase_com_condicionais"]))
    st.caption(
        '"Compatível com os dados" não é causa comprovada: cada explicação precisa da '
        "verificação indicada."
    )
    descartadas = [h for h in hips if h["status"] == "descartada"]
    if descartadas:
        with st.expander(f"O que foi descartado e por quê ({len(descartadas)})"):
            _hipoteses(descartadas, "")

    st.markdown("### 3. Explicações que continuam possíveis")
    _hipoteses(
        [h for h in hips if h["status"] in ("possivel", "nao_avaliavel")],
        "Nenhuma outra explicação continua em aberto.",
    )

    st.markdown("### 4. O que falta saber")
    if j["o_que_falta"]:
        st.markdown("\n".join(f"- {md(f)}" for f in j["o_que_falta"]))
    else:
        st.caption("Nada essencial faltando para esta comparação.")
    st.caption(md(j["independencia"]["nota"]) + " (E12)")

    st.markdown("### 5. Próxima verificação")
    prox = j["proxima_verificacao"]
    st.info(f"**{md(prox['acao'])}**  \n{md(prox['porque'])}", icon=":material/search:")

    st.page_link(
        "paginas/relatorio.py",
        label="Gerar o relatório desta comparação",
        icon=":material/description:",
    )

    with st.expander("Dados técnicos da investigação (JSON)"):
        texto = json.dumps(j, ensure_ascii=False, indent=2)
        st.download_button(
            "Baixar o JSON", texto, file_name="investigacao_euler.json", mime="application/json"
        )
        st.json(j, expanded=False)


pacote = estado.exigir_pacote()
if pacote is not None:
    mostrar(pacote)
