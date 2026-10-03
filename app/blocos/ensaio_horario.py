"""Ensaio real: resultado executivo, orientação de investigação e trilha auditável."""

import json

import pandas as pd
import streamlit as st
from ensaio_horario import DADOS, executar
from parecer_ensaio import INVESTIGACOES, parecer, relatorio_texto

from euler.formato import num


def _resumo(u, p):
    meses = u["comparacoes"]
    st.metric("Valor estimado do desvio", f"US$ {num(p['valor_usd'])}", border=True)
    st.caption(
        "Estimativa a preço de referência regional do gás · somente horas comparáveis. "
        "Não é prejuízo confirmado nem economia garantida. Combustível efetivo e contrato "
        "da planta ainda precisam ser confirmados."
    )
    a, b = st.columns(2)
    for col, m, nome in zip((a, b), meses, ("Fevereiro", "Março"), strict=True):
        col.metric(nome, f"{num(m['delta_pct'])}%", border=True)
    st.caption(
        "Diferença de energia frente à referência, ajustada à produção de vapor. Janeiro = referência."
    )
    st.markdown(
        f"**{num(p['energia_gj'])} GJ de diferença energética** nas {num(p['horas'], 0)} horas comparadas."
    )
    st.markdown("**O resultado ao longo dos dias**")
    diario = pd.DataFrame([d for m in meses for d in m["diario"]])
    diario["Dia"] = pd.to_datetime(diario["Date"])
    diario["Diferença (%)"] = 100 * (diario.energia_gj / diario.previsto_gj - 1)
    st.bar_chart(
        diario.set_index("Dia")[["Diferença (%)"]],
        x_label="Dia",
        y_label="Diferença de energia (%)",
        height=230,
    )
    st.caption(
        "Acima de zero: mais energia que a referência para aquela produção. "
        "Abaixo: menos energia. Cada dia pode ter quantidade diferente de horas comparáveis; "
        "dias sem essas horas não são preenchidos."
    )
    with st.container(border=True):
        st.markdown("**O que já sabemos — e o que continua em aberto**")
        st.markdown(
            "**Calculado:** diferença de consumo ajustada à carga e seu valor a preço declarado.\n\n"
            "**Em aberto:** se há perda térmica, qual é a causa e quanto seria recuperável. "
            "As incertezas dos instrumentos ainda não foram informadas."
        )
    st.markdown("**Cobertura da comparação**")
    for m, nome in zip(meses, ("Fevereiro", "Março"), strict=True):
        st.progress(
            m["horas_comparaveis"] / m["horas_validas"],
            text=f"{nome}: {m['horas_comparaveis']} de {m['horas_validas']} horas válidas comparadas",
        )
    st.caption(
        f"{p['fora_faixa']} horas válidas ficaram fora da faixa de carga de janeiro e foram excluídas. "
        "Os resultados não cobrem essas horas nem devem ser extrapolados para o ano."
    )


def _operador(p):
    st.markdown("### O que fazer com este resultado")
    if p["status"] == "investigar":
        st.info(
            "**Verificação indicada.** Encaminhar o desvio ao responsável técnico e conferir "
            "os registros abaixo antes de decidir uma intervenção."
        )
    else:
        st.info(
            "**Acompanhar e conferir a comparação.** Este resultado não sustenta uma "
            "intervenção por aumento persistente de consumo."
        )
    st.caption(
        "Orientação de investigação para este caso histórico; não é um alarme ao vivo. "
        "Não altera setpoints nem substitui os procedimentos de segurança da planta."
    )
    for i, v in enumerate(p["verificacoes"], 1):
        with st.container(border=True):
            st.markdown(f"**{i}. {v['onde']}**")
            st.write(v["conferir"])
            st.caption(v["para_que"])
    with st.expander("Se o desvio persistir: onde aprofundar a investigação"):
        st.write(
            "Estas são frentes possíveis, sem causa atribuída ou ordem de prioridade entre elas. "
            "O responsável técnico escolhe a próxima verificação conforme os registros disponíveis."
        )
        for v in INVESTIGACOES:
            st.markdown(f"**{v['onde']}**")
            st.write(v["dados"])
            st.caption(v["resposta"])
        st.link_button(
            "Referência técnica · sistemas de vapor / DOE",
            "https://www.energy.gov/cmei/ito/steam-systems",
        )
    st.markdown("**Quando uma intervenção poderá ser indicada?**")
    st.write(
        "Quando as verificações sustentarem uma causa e uma avaliação técnica justificar "
        "a ação. Depois, comparar antes e depois sob condições equivalentes para medir "
        "a economia efetiva. Este ensaio ainda não chegou a essa etapa."
    )


def _evidencias(r, u, p):
    f = r["fonte"]
    st.markdown("### Um resultado que pode ser conferido")
    st.markdown(
        "**Origem:** registros horários públicos EPA/CAMPD, preservados pela PUDL. "
        "Recorte de 8.034 registros com vapor informado, em quatro caldeiras.\n\n"
        "**Integridade:** o arquivo é conferido por uma verificação de integridade a cada execução. "
        "Isso verifica se o recorte mudou; não certifica os instrumentos da planta.\n\n"
        "**Comparação:** referência ajustada em janeiro; fevereiro e março somente na faixa "
        "de produção já observada. Dados ausentes, substituídos e horas parciais não são completados.\n\n"
        "**Conferência numérica:** ajuste recalculado por método independente e conta financeira "
        "verificada nos testes. Isso verifica a implementação; não substitui validação de campo."
    )
    if p["sensibilidade_consistente"]:
        st.info(
            "O aumento também aparece usando faixas de produção de 5 e 10 t/h. "
            "É uma conferência de consistência; não é intervalo de confiança nem prova de causa."
        )
    st.markdown("**Como o dinheiro foi calculado**")
    st.write("Diferença de energia × preço por unidade de energia = valor estimado do desvio.")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Mês": m["mes"],
                    "Diferença (GJ)": num(m["delta_gj"]),
                    "Preço (US$/GJ)": num(m["preco_usd_gj"], 4),
                    "Valor (US$)": num(m["valor_referencia_usd"]),
                }
                for m in u["comparacoes"]
            ]
        ),
        hide_index=True,
        width="stretch",
    )
    st.caption(
        "O mesmo preço valoriza observado e referência em cada mês. A conta usa precisão "
        "completa; casas decimais não representam a precisão do gasto real da empresa."
    )
    st.write(
        "Preço médio industrial do gás em Illinois: US\\$ 8,02 por mil pés cúbicos em fevereiro "
        "e US\\$ 6,54 em março de 2023. Poder calorífico regional anual: 1,040 MMBtu por mil "
        "pés cúbicos. Uma MMBtu equivale a 1,05505585262 GJ."
    )
    st.warning(
        "A B10 registra carvão secundário no cadastro EPA, sem participação horária disponível. "
        "A valorização integral como gás é condicional. Não temos a fatura nem o contrato da planta."
    )
    st.caption(
        "Janeiro não é uma operação certificada como ideal. Hora completa não garante regime estável. "
        "Faltam condições da água/vapor, eventos e incertezas. A B10 foi destacada após examinar "
        "as quatro unidades: estudo retrospectivo, sem validação prospectiva ou endosso da empresa."
    )
    for nome, chave in (
        ("Registros originais · EPA/PUDL", "url"),
        ("Preço publicado · EIA", "preco_fonte"),
        ("Poder calorífico · EIA", "calor_fonte"),
    ):
        st.link_button(nome, f[chave])
    with st.expander("Detalhes técnicos · método, cobertura e integridade"):
        st.write(
            f"Referência: {u['horas_referencia']} horas; {num(u['carga_min_t_h'])} "
            f"a {num(u['carga_max_t_h'])} t/h. Energia em PCS."
        )
        st.latex(r"E_{ref}(V)=a+bV \qquad \Delta E=\sum_i(E_{obs,i}-E_{ref}(V_i))")
        st.caption(
            "E: energia por hora completa, em GJ; V: vapor por hora completa, em t. "
            "a e b ajustados somente em janeiro. Não é balanço térmico de eficiência."
        )
        st.dataframe(
            pd.DataFrame(
                [{"Mês": m["mes"], **s} for m in u["comparacoes"] for s in m["sensibilidade"]]
            ),
            hide_index=True,
        )
        st.code(f["recorte_sha256"], language=None)
        st.caption(
            "SHA-256 do recorte público; ausência de alteração do arquivo não comprova exatidão da medição."
        )
        st.download_button(
            "Baixar registros originais",
            (DADOS / "ingredion_2023q1.csv").read_bytes(),
            "ingredion_2023q1.csv",
            "text/csv",
        )


def renderizar():
    r = executar()
    st.subheader("Registros horários reais · do consumo à investigação")
    st.caption(
        "CASO PÚBLICO · Ingredion Argo, EUA · janeiro a março de 2023 · sem vínculo com a instalação"
    )
    unidade = st.selectbox("Caldeira do conjunto público", ["B10", "B08", "B07", "B06"])
    u = r["unidades"][unidade]
    p = parecer(u)
    with st.container(border=True):
        st.markdown(f"### {unidade} · {p['titulo']}")
        st.write(p["conclusao"])
    resultado, operador, evidencias = st.tabs(["Resultado", "O que verificar", "Fontes e cálculo"])
    with resultado:
        _resumo(u, p)
    with operador:
        _operador(p)
    with evidencias:
        _evidencias(r, u, p)
    st.download_button(
        "Baixar parecer com fontes",
        relatorio_texto(r, unidade),
        f"EULER_parecer_publico_{unidade}.md",
        "text/markdown",
    )
    with st.expander("Detalhes técnicos · exportar resultado da execução"):
        st.download_button(
            "Baixar resultado auditável",
            json.dumps(
                {"fonte": r["fonte"], "unidade": unidade, "resultado": u, "parecer": p},
                ensure_ascii=False,
                indent=2,
            ),
            f"EULER_ensaio_{unidade}.json",
            "application/json",
        )
    st.divider()
