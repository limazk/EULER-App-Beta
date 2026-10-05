"""Testes com dados reais publicados: o que foi conferido, com origem e limites explícitos.

Nenhum destes dados é de cliente. Cada caso roda no motor atual; medições ausentes continuam
ausentes. A tela começa pelo resumo do que foi testado e mostra um caso por aba.
"""

import estado
import pandas as pd
import streamlit as st
from blocos.ensaio_cervejaria import renderizar as renderizar_cervejaria
from blocos.ensaio_horario import renderizar as renderizar_ensaio_horario
from componentes import cabecalho
from ensaio_cervejaria import executar as executar_cervejaria
from ensaio_horario import executar as executar_horario
from ensaio_publico import DADOS, comparar_custo_publicado, executar
from resumo_publico import AVISO, linhas_resumo

from euler.economia import comparar_consumos
from euler.formato import num
from euler.tipos import Grandeza


@st.cache_data(show_spinner="Conferindo as fontes e executando o motor…")
def resultado():
    return executar()


@st.cache_data(show_spinner="Executando o ensaio horário…")
def resultado_horario():
    return executar_horario()


@st.cache_data(show_spinner="Conferindo os 660 dias da planta brasileira…")
def resultado_cervejaria():
    return executar_cervejaria()


def resumo(r: dict, h: dict, c: dict) -> None:
    """O que já foi testado com dados reais, num quadro só (números do próprio motor)."""
    st.markdown("### O que já foi testado com dados reais")
    st.dataframe(pd.DataFrame(linhas_resumo(r, h, c)), hide_index=True, width="stretch")
    st.caption(AVISO)


def biomassa_utfpr(r: dict) -> None:
    """Aumento de consumo publicado (Diniz, UTFPR, 2014)."""
    st.subheader("Consumo aumentou: teste real com biomassa")
    st.caption(
        "Diniz · UTFPR, 2014 · indústria de papel · comparação de médias entre seca e chuva."
    )
    fonte_aumento = r["caso_aumento"]["fonte"]
    st.markdown(
        "**Este é um caso de aumento publicado, sem inverter os períodos.** "
        "Os valores abaixo entram no motor de comparação e valorização da EULER. "
        "Você pode executar novamente ou editar as entradas para um cenário separado."
    )
    with st.form("ensaio_aumento"):
        a, b = st.columns(2)
        ref = a.number_input(
            "Consumo na seca (t biomassa/t vapor)",
            min_value=0.0001,
            value=0.30,
            step=0.01,
            format="%.4f",
        )
        comp = b.number_input(
            "Consumo na chuva (t biomassa/t vapor)",
            min_value=0.0001,
            value=0.35,
            step=0.01,
            format="%.4f",
        )
        prod = a.number_input("Vapor produzido (t/dia)", min_value=0.01, value=1200.0)
        preco = b.number_input("Preço histórico (US$/t biomassa)", min_value=0.0, value=26.53)
        st.form_submit_button("Executar comparação na EULER", type="primary")
    publicado = (ref, comp, prod, preco) == (0.30, 0.35, 1200.0, 26.53)
    aumento = comparar_consumos(
        Grandeza(ref, "t/t", "estimado"), Grandeza(comp, "t/t", "estimado"), prod, preco, "USD"
    )
    if not publicado:
        st.warning(
            "Cenário editado por você. Os resultados abaixo não reproduzem mais as entradas publicadas."
        )
    else:
        st.caption(
            "Entradas publicadas preservadas. O cálculo é executado ao abrir e a cada envio do formulário."
        )
    a, b, c = st.columns(3)
    a.metric("Variação de consumo", f"{num(aumento['aumento_pct'])}%", border=True)
    b.metric(
        "Diferença de biomassa", f"{num(aumento['combustivel_adicional_t'])} t/dia", border=True
    )
    c.metric("Diferença valorizada", f"US$ {num(aumento['diferenca_valorizada'])}/dia", border=True)
    st.caption(
        "Valores com sinal: positivo = aumento; negativo = redução. Não há conversão cambial."
    )
    st.markdown(
        f"Combustível para a mesma produção: **{num(aumento['combustivel_referencia_t'])} → "
        f"{num(aumento['combustivel_comparacao_t'])} t/dia**. "
        f"Custo calculado: **US\\$ {num(aumento['custo_referencia'])} → "
        f"US\\$ {num(aumento['custo_comparacao'])}/dia**."
    )
    if publicado:
        st.success(
            "Conferência independente: (0,35 − 0,30) × 1.200 × 26,53 = US\\$ 1.591,80/dia. "
            "O motor reproduz essa conta. O texto publicado dá US\\$ 1.591/dia pela diferença "
            "de custos sem casas decimais: a divergência é de US\\$ 0,80/dia (0,05%)."
        )
    st.info(
        "O número acima é uma diferença aritmética a preço constante. Sem incertezas dos "
        "instrumentos, a mudança não é confirmada metrologicamente. A fonte associa o aumento "
        "à chuva/umidade, mas este recorte não permite à EULER separar umidade, carga e outras causas. "
        "Não é economia garantida."
    )
    with st.expander("Rastreabilidade, limites e próxima verificação"):
        st.markdown(
            "- O preço é histórico em dólares. A unidade por tonelada é inferida da aritmética "
            "da fonte, que não escreve o denominador na frase do preço.\n"
            "- São médias publicadas, sem séries brutas. Não criamos estoques, horários ou leituras.\n"
            "- Esta rota testa comparação de consumo e valorização E13; não executa balanço "
            "térmico completo, atribuição de causa ou comprovação de recuperação.\n"
            "- Próxima verificação: conferir massa/medidor de vapor, incertezas, carga e "
            "condições do vapor; medir a umidade dos lotes efetivamente queimados nos dois períodos. "
            "Esses registros permitem avaliar a hipótese de umidade antes de recomendar investimento."
        )
        st.json(aumento, expanded=False)
        st.link_button("Fonte do aumento · UTFPR, página 33 do PDF", fonte_aumento["pdf_url"])


def custo_unisanta(r: dict) -> None:
    """Custo do combustível por tonelada de vapor (Unisanta, 2015)."""
    st.subheader("Quanto isso representa em dinheiro?")
    st.caption(
        "Caso brasileiro publicado pela Unisanta (2015) · médias de 2010 e 2011 · gás natural. "
        "Este caso já fazia parte da pesquisa da EULER e agora pode ser conferido aqui."
    )
    f = r["caso_financeiro"]
    st.markdown(
        "A publicação adota **R\\$ 1,10/kg** nos dois períodos. Assim, conseguimos comparar "
        "o custo de combustível por tonelada de vapor, sem buscar um preço de outro mercado. "
        "É um preço histórico da publicação, não uma cotação atual ou uma fatura auditada."
    )
    a, b, c = st.columns(3)
    a.metric("Antes · combustível por t de vapor", f"R$ {num(f['antes_brl_t'])}", border=True)
    b.metric("Depois · combustível por t de vapor", f"R$ {num(f['depois_brl_t'])}", border=True)
    c.metric("Redução calculada por t de vapor", f"{num(f['reducao_pct'])}%", border=True)
    st.success(
        f"Diferença de R\\$ {num(f['diferenca_brl_t'])} por tonelada de vapor. "
        "É uma redução calculada a partir das médias publicadas; não é economia gerada pela EULER."
    )
    with st.expander("Ver a conta e o que ela permite concluir"):
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Período": "2010",
                        "Combustível (kg/h)": 7562,
                        "Vapor (t/h)": 119.39,
                        "Consumo (kg/t vapor)": num(f["antes_kg_t"]),
                        "Combustível (R$/h)": num(f["antes_brl_h"]),
                    },
                    {
                        "Período": "2011",
                        "Combustível (kg/h)": 7458,
                        "Vapor (t/h)": 123.85,
                        "Consumo (kg/t vapor)": num(f["depois_kg_t"]),
                        "Combustível (R$/h)": num(f["depois_brl_h"]),
                    },
                ]
            ),
            hide_index=True,
            width="stretch",
        )
        st.markdown(
            f"**Diferença bruta:** R\\$ {num(f['reducao_bruta_brl_h'])}/h, mas a produção aumentou.\n\n"
            f"**À mesma produção de 123,85 t/h:** a diferença seria R\\$ "
            f"{num(f['diferenca_normalizada_brl_h'])}/h se a intensidade anterior permanecesse constante. "
            "É uma projeção linear para comparação; não é dinheiro recuperado nem referência ajustada por carga.\n\n"
            "**Conta:** combustível (kg/h) ÷ vapor (t/h) × preço (R\\$/kg). "
            "Não inclui água, eletricidade, manutenção ou demais custos do vapor."
        )
        st.info(
            "Há uma intervenção relatada (retirada de pré-aquecedor ar/vapor), mas também mudou "
            "o combustível de partida. Sem registros brutos e incertezas, não isolamos a contribuição "
            "de cada mudança. A comparação do motor mantém a detectabilidade inconclusiva. "
            "Não anualizamos médias sem conhecer as horas efetivas."
        )
        st.caption(
            "Auditoria financeira de médias, separada do balanço completo. A publicação calcula outro "
            "custo por uma equação de entalpia; os números aqui usam somente massa e preço. "
            "Totais anuais inconsistentes da fonte não foram usados."
        )
        st.link_button("Consultar dissertação · tabelas 6, 7, 14 e 15", f["fonte"]["url"])
    with st.expander("Como a comparação muda com outro preço?"):
        p = st.number_input(
            "Preço para cenário (R$/kg)",
            min_value=0.0,
            value=1.10,
            step=0.10,
            key="preco_cenario_publico",
        )
        s = comparar_custo_publicado(p)
        st.metric("Diferença no cenário · por t de vapor", f"R$ {num(s['diferenca_brl_t'])}")
        st.caption(
            "Cenário escolhido por você, aplicado às mesmas médias históricas. "
            "Não substitui o preço publicado nem representa o gasto de uma empresa atual."
        )


def tres_cargas(r: dict) -> None:
    """Cálculos térmicos em três cargas (Ohijeagbon e colaboradores, 2026)."""
    st.subheader("Caldeira a carvão em três condições de carga")
    st.caption(
        "Médias operacionais publicadas por Ohijeagbon e colaboradores (2026), "
        "caldeira subcrítica a carvão. Não são três dias nem um histórico antes/depois."
    )
    st.warning(
        "Cálculos térmicos condicionais: a fonte informa pressão estática em MPa sem explicitar "
        "se é absoluta ou manométrica. A conferência abaixo interpreta os valores como absolutos. "
        "Não há preços nem incerteza instrumental documentados."
    )
    a, b, c = st.columns(3)
    a.metric("Estados de água e vapor conferidos", "15", border=True)
    b.metric(
        "Maior diferença entre bibliotecas",
        f"{num(max(abs(e['delta_heos_pct']) for e in r['estados']), 3)}%",
        border=True,
    )
    c.metric("Economia comprovada", "Não apurada", border=True)
    st.caption(
        "Comparação numérica: EULER/IAPWS-IF97 versus CoolProp/HEOS (IAPWS-95). "
        "A concordância verifica a implementação para estes pontos; não certifica os sensores da planta."
    )
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Carga publicada": f"{num(c['carga_pct'])}%",
                    "Vapor (t/h)": num(c["vapor_t_h"], 2),
                    "Combustível por vapor (kg/t)": num(c["consumo_kg_t"], 2),
                    "Potência transferida ao vapor (MW)*": num(c["potencia_vapor_mw"], 2),
                }
                for c in r["cargas"]
            ]
        ),
        hide_index=True,
        width="stretch",
    )
    st.caption(
        "*Estimativa a partir das médias publicadas de vazão e das entalpias calculadas pela EULER; "
        "depende da interpretação da pressão e da fronteira água de alimentação → vapor superaquecido."
    )
    st.info(
        "O consumo específico varia de 126,74 a 128,04 kg/t entre cargas diferentes. "
        "A EULER devolve a diferença, mas não confirma uma mudança detectável sem incerteza. "
        "Essa variação não demonstra desperdício nem justifica uma intervenção."
    )
    with st.expander("Conferir cálculos, referências e divergências"):
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Carga (%)": e["carga_pct"],
                        "Ponto": e["ponto"],
                        "EULER (kJ/kg)": e["h_euler_kj_kg"],
                        "Fonte (kJ/kg)": e["h_fonte_kj_kg"],
                        "HEOS (kJ/kg)": e["h_heos_kj_kg"],
                        "Diferença EULER/fonte (%)": e["delta_fonte_pct"],
                        "Célula da fonte": e["celula_h"],
                    }
                    for e in r["estados"]
                ]
            ),
            hide_index=True,
            width="stretch",
        )
        st.markdown(
            "**Pontos a revisar na fonte:** divergência de até 0,99% em entalpias; "
            "oxigênio do combustível escrito como 7,9% e fração 0,078; DOI diferente no manual; "
            "pressões crescentes ao longo do economizador. Preservamos esses dados sem corrigir "
            "silenciosamente. O poder calorífico publicado é PCS, não PCI: não foi usado como PCI."
        )
        st.caption(
            "A massa de combustível consta em uma linha com rótulo ambíguo de mistura carvão/ar; a tabela lista o ar separadamente. A razão kg/t depende dessa interpretação."
        )
        st.link_button("Consultar a fonte e o manual", r["fonte_subcritica"]["url"])
        st.download_button(
            "Baixar a planilha original",
            (DADOS / "Boiler_Operational_Dataset_Tables_REVISED.xlsx").read_bytes(),
            "caldeira_subcritica_original.xlsx",
        )


def serie_zhejiang(r: dict) -> None:
    """Importação de uma série real por minuto (Zhejiang, 2022)."""
    st.subheader("Série de uma caldeira em uma indústria química")
    z = r["zhejiang"]
    st.markdown(
        f"**{num(z['linhas'], 0)} registros originais**, de 27/03 a 01/04/2022, Zhejiang, China. "
        "Usamos o arquivo com as lacunas preservadas, sem preenchimento por modelo."
    )
    a, b, c = st.columns(3)
    a.metric("Menor temperatura do vapor", f"{num(z['temperatura_min_c'])} °C", border=True)
    b.metric("Maior temperatura do vapor", f"{num(z['temperatura_max_c'])} °C", border=True)
    c.metric("Registros prontos para importar", num(r["importacao"]["linhas"], 0), border=True)
    st.markdown(
        "**A importação real passou:** 7.200 leituras observadas, uma por minuto, com os valores "
        "de temperatura preservados. O recorte seleciona uma em cada 12 linhas; não cria médias nem preenche lacunas. "
        "O fuso +08:00 foi inferido da localização e está declarado no arquivo."
    )
    st.caption(
        "Neste pacote, pressão e vazão não foram mapeadas por falta de confirmação suficiente das unidades/base. "
        "Sem combustível, preço, água de entrada e pressão confirmada, eficiência e perdas financeiras ficam bloqueadas."
    )
    with st.container(border=True):
        st.markdown("**Experimente no aplicativo**")
        st.caption(
            "Substitui os dados ativos desta sessão pelo recorte público. Depois, veja os avisos em Dados e limites."
        )
        if st.button(
            "Carregar registros reais de Zhejiang", key="carregar_zhejiang", type="primary"
        ):
            estado.importar_novos({"diario.csv": (DADOS / "diario.csv").read_bytes()}, None)
            st.session_state["rotulo_dados"] = (
                "Zhejiang · registros públicos reais · temperatura do vapor"
            )
            st.success(
                "Registros públicos carregados. Abra Dados e limites para conferir o resultado."
            )
        st.page_link("paginas/limites.py", label="Ver Dados e limites", icon=":material/rule:")
        st.download_button(
            "Baixar CSV pronto para importar",
            (DADOS / "diario.csv").read_bytes(),
            "diario.csv",
            "text/csv",
        )
    with st.expander("O que este ensaio comprova — e o que falta"):
        st.markdown(
            "- **Verificado:** origem pública rastreável, importação, preservação das temperaturas, "
            "cálculos termodinâmicos condicionais e bloqueios por insuficiência de dados.\n"
            "- **Ainda não demonstrado:** causa de perda, economia recuperável, custo por fornecedor "
            "e desempenho completo em uma planta brasileira a biomassa.\n"
            "- **Próxima evidência necessária:** histórico sincronizado de combustível, vapor, "
            "condições da água/vapor, qualidade do combustível, preços e eventos, com unidades e incertezas."
        )
        st.caption(
            "Na série inteira, 7.037 leituras (8,14%) estão fora de 530–545 °C, faixa dos autores. "
            "O artigo cita 8,6%; a diferença está registrada. Essa classificação não é um diagnóstico da EULER."
        )
        st.link_button("Fonte original de Zhejiang · CC0", z["url"])
        st.link_button("Ler artigo da série", "https://doi.org/10.1038/s41597-025-05096-4")


cabecalho(
    "Testes com dados públicos",
    "Dados reais publicados por empresas, governos e universidades, executados no motor atual. "
    "Medições ausentes continuam ausentes.",
    "Dados reais testados",
)
r = resultado()
cervejaria = resultado_cervejaria()
resumo(r, resultado_horario(), cervejaria)
abas = st.tabs(
    [
        "Planta brasileira · RS",
        "Caldeiras EPA · EUA",
        "Biomassa · UTFPR",
        "Custo do vapor · Unisanta",
        "Três cargas · carvão",
        "Série · Zhejiang",
    ],
    key="publicos_aba",
)
with abas[0]:
    renderizar_cervejaria(cervejaria)
with abas[1]:
    renderizar_ensaio_horario()
with abas[2]:
    biomassa_utfpr(r)
with abas[3]:
    custo_unisanta(r)
with abas[4]:
    tres_cargas(r)
with abas[5]:
    serie_zhejiang(r)
