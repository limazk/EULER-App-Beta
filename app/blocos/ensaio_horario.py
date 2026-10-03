"""Visual executivo do ensaio horário real, separado dos dados ativos."""

import pandas as pd
import streamlit as st
from ensaio_horario import DADOS, executar

from euler.formato import num


def renderizar():
    r = executar()
    st.subheader("Registros horários reais: indústria de ingredientes alimentícios")
    st.caption("Ingredion · Argo, Illinois · EPA/PUDL · janeiro a março de 2023")
    st.markdown(
        "**Agora a EULER parte das leituras horárias, sem receber médias de consumo prontas.** "
        "Janeiro é a referência. Comparamos fevereiro e março somente nas cargas já observadas. "
        "Este ensaio é exploratório: compara energia e vapor; não fecha o balanço térmico."
    )
    unidade = st.selectbox("Caldeira do conjunto público", ["B10", "B08", "B07", "B06"])
    u = r["unidades"][unidade]
    meses = u["comparacoes"]
    a, b = st.columns(2)
    a.metric("Fevereiro: diferença por carga", f"{num(meses[0]['delta_pct'])}%", border=True)
    b.metric("Março: diferença por carga", f"{num(meses[1]['delta_pct'])}%", border=True)
    st.metric(
        "Diferença valorizada · 2 meses",
        f"US$ {num(sum(m['valor_referencia_usd'] for m in meses))}",
        border=True,
    )
    st.caption(
        "Valor a preço de referência regional do gás, condicionado a esse combustível; "
        "não é a fatura da empresa, prejuízo comprovado ou economia recuperável. "
        "Sinal negativo indica consumo abaixo da referência."
    )
    if unidade == "B10":
        st.info(
            "A B10 ficou acima da referência nos dois meses. O sinal também aparece ao comparar "
            "faixas de produção semelhantes. É motivo para investigar; ainda não identifica a causa. "
            "As demais caldeiras estão disponíveis no seletor para conferir o conjunto completo."
        )
    diario = pd.DataFrame([d for m in meses for d in m["diario"]])
    diario = diario.rename(
        columns={"observado_gj_t": "Observado", "referencia_gj_t": "Referência por carga"}
    )
    diario["Date"] = pd.to_datetime(diario["Date"])
    st.scatter_chart(
        diario.set_index("Date")[["Observado", "Referência por carga"]],
        x_label="Dia · somente horas comparáveis",
        y_label="GJ de combustível/t de vapor",
    )
    st.caption(
        f"{sum(m['horas_comparaveis'] for m in meses):,} horas comparadas; "
        f"{sum(m['horas_fora_faixa'] for m in meses):,} horas válidas fora da faixa foram excluídas. "
        f"Referência: {u['horas_referencia']} horas, de {num(u['carga_min_t_h'])} a "
        f"{num(u['carga_max_t_h'])} t de vapor/h. Ausências não foram preenchidas."
    )
    with st.expander("Conferir o teste, o dinheiro e as próximas verificações"):
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Mês": m["mes"],
                        "Horas comparáveis": m["horas_comparaveis"],
                        "Sem ajuste por carga (%)": m["variacao_sem_ajuste_pct"],
                        "Com ajuste por carga (%)": m["delta_pct"],
                        "Diferença (GJ)": m["delta_gj"],
                        "Valor de referência (US$)": m["valor_referencia_usd"],
                    }
                    for m in meses
                ]
            ),
            hide_index=True,
            width="stretch",
        )
        st.markdown(
            "**Preço:** média industrial de Illinois, US\\$ 8,02 por mil pés cúbicos em fevereiro "
            "e US\\$ 6,54 em março. Conversão pela média regional de 2023: 1,040 MMBtu por mil "
            "pés cúbicos. Dentro de cada mês, observado e referência usam o mesmo preço.\n\n"
            "**Conferência:** regressão calculada novamente por método independente; "
            "sensibilidade com faixas de 5 e 10 t/h, pelo menos 10 horas de referência por faixa. "
            "Cada método pode usar horas diferentes.\n\n"
            "**Próxima verificação na planta:** conferir medidores de vapor e combustível; "
            "comparar pressão/temperatura do vapor e da água; verificar partidas, mudanças "
            "de combustível e registros de manutenção. Com isso, avaliar se o desvio permanece "
            "antes de investigar combustão, purga ou troca térmica. Nenhum ajuste operacional é prescrito."
        )
        st.dataframe(
            pd.DataFrame(
                [{"Mês": m["mes"], **s} for m in meses for s in m["sensibilidade"]]
            ).rename(
                columns={
                    "largura_t_h": "Faixa de produção (t/h)",
                    "horas": "Horas comparáveis",
                    "delta_gj": "Diferença (GJ)",
                    "delta_pct": "Diferença (%)",
                }
            ),
            hide_index=True,
        )
        st.warning(
            "Não há incertezas instrumentais, estado do vapor nem eventos operacionais suficientes "
            "para confirmar perda térmica ou causa. O campo de combustível secundário da B10 "
            "ainda registra carvão: a divisão por combustível não está nesta série. "
            "A valorização como gás é condicional. B10 foi destacada após triagem das quatro "
            "unidades; este não é um teste prospectivo nem estima taxa de acerto comercial."
        )
        st.link_button("Fonte dos registros EPA/PUDL", r["fonte"]["url"])
        st.link_button("Preço industrial publicado pela EIA", r["fonte"]["preco_fonte"])
        st.link_button("Poder calorífico regional publicado pela EIA", r["fonte"]["calor_fonte"])
        st.download_button(
            "Baixar registros originais do recorte",
            (DADOS / "ingredion_2023q1.csv").read_bytes(),
            "ingredion_2023q1.csv",
        )
    st.divider()
