"""Planta brasileira real (MDL 1202): resposta, conferência dos registros, hipóteses e fontes."""

import json
from itertools import pairwise

import pandas as pd
import streamlit as st
from ensaio_cervejaria import DADOS, PERIODOS

from euler.formato import num


def _sinal(x: float, casas: int = 1) -> str:
    return f"{'+' if x >= 0 else '−'}{num(abs(x), casas)}"


def _resposta(r: dict) -> None:
    c = r["comparacao"]
    a, b = c["periodos"]
    cmp = c["comparacao"]
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("1º período", f"{num(a['consumo_t_t'], 4)} t/t", border=True)
    m2.metric("2º período", f"{num(b['consumo_t_t'], 4)} t/t", border=True)
    m3.metric("Diferença", f"{_sinal(c['variacao_pct'])}%", border=True)
    m4.metric(
        "Incerteza conhecida",
        f"±{num(cmp.incerteza_delta_correlacionada, 4)} t/t",
        border=True,
        help="Só a parte declarada (balança, 2%), com k = 2. O que falta não entra como zero.",
    )
    st.caption(
        "Consumo aparente = casca registrada ÷ vapor das duas caldeiras (t de casca por t de "
        "vapor). Mesmo trecho do calendário nos dois anos: 05/11 a 25/08. Origem: medido na "
        "planta e publicado; a razão é calculada pela EULER."
    )
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Período": f"{nome} · {pd.Timestamp(p['inicio']):%d/%m/%Y} a "
                    f"{pd.Timestamp(p['fim']):%d/%m/%Y}",
                    "Dias": p["dias"],
                    "Vapor (t)": num(p["vapor_t"], 0),
                    "Casca (t)": num(p["biomassa_t"], 0),
                    "Consumo aparente (t/t)": num(p["consumo_t_t"], 4),
                    "Vapor médio (t/dia)": num(p["carga_t_dia"], 0),
                    "Dias sem vapor registrado": p["dias_sem_vapor"],
                }
                for nome, p in zip(c["nomes"], c["periodos"], strict=True)
            ]
        ),
        hide_index=True,
        width="stretch",
    )
    m = pd.DataFrame(r["mensal"]["meses"])
    m["Mês"] = pd.to_datetime(m["mes"], format="%m/%Y")
    g1, g2 = st.columns(2)
    with g1:
        st.markdown("**Consumo aparente por mês (t de casca por t de vapor)**")
        st.line_chart(m.set_index("Mês")[["consumo_t_t"]], height=220, y_label="t/t")
    with g2:
        st.markdown("**Vapor médio por mês (t/dia)**")
        st.line_chart(m.set_index("Mês")[["carga_t_dia"]], height=220, y_label="t/dia")
    st.caption(
        "Mês a mês, a casca registrada inclui o que entrou ou saiu do estoque, que não foi "
        "publicado: as oscilações mensais não são da caldeira. Novembro de 2007 começa no dia 5 "
        "e agosto de 2009 termina no dia 25."
    )
    with st.container(border=True):
        st.markdown("**Outros cortes do mesmo registro**")
        s = r["sensibilidade"]
        linhas = []
        for grupo, nome in (
            ("metades", "Metades do registro"),
            ("epocas_balanca", "Entre calibrações da balança"),
            ("epocas_medidor_vapor", "Entre calibrações dos medidores de vapor"),
        ):
            for bloco in s[grupo]:
                linhas.append(
                    {
                        "Corte": nome,
                        "Trecho": bloco["rotulo"],
                        "Dias": bloco["dias"],
                        "Consumo aparente (t/t)": num(bloco["consumo_t_t"], 4),
                    }
                )
        st.dataframe(pd.DataFrame(linhas), hide_index=True, width="stretch")
        cai = all(
            b["consumo_t_t"] < a["consumo_t_t"] for grupo in s.values() for a, b in pairwise(grupo)
        )
        st.caption(
            "Em todos os cortes, cada trecho tem menos casca por tonelada de vapor que o anterior. "
            "A diferença não depende da escolha dos períodos; isso não mostra a causa."
            if cai
            else "Os cortes não seguem o mesmo sentido: a diferença depende do período escolhido."
        )
    st.markdown("**O que a EULER bloqueia neste caso**")
    for item in r["bloqueado"]:
        st.markdown(f"- {item}")


def _conferencia(r: dict) -> None:
    c = r["conferencia"]
    t, v = c["totais"], c["totais_verificados"]
    st.markdown("**Totais: soma da EULER × relatório de verificação publicado**")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Grandeza": nome,
                    "Soma da EULER (t)": num(t[k1], 3),
                    "Relatório (t)": num(v[k2], 0),
                }
                for nome, k1, k2 in (
                    ("Vapor das caldeiras a biomassa", "vapor_t", "vapor_t"),
                    ("Casca de arroz e de carvalho", "biomassa_t", "biomassa_t"),
                    (
                        "Óleo equivalente da caldeira reserva",
                        "oleo_equivalente_t",
                        "oleo_equivalente_t",
                    ),
                )
            ]
        ),
        hide_index=True,
        width="stretch",
    )
    if all(c["confere_com_verificacao"].values()):
        st.success(
            "As três somas reproduzem os totais do relatório de verificação, arredondados à "
            "tonelada. Isso confere a leitura da planilha, não os instrumentos da planta."
        )
    st.markdown(
        f"**Calendário:** {c['dias']} dias seguidos, de {c['inicio']} a {c['fim']}; "
        f"{c['dias_fora_do_calendario']} dias faltando e {c['datas_repetidas']} datas repetidas."
    )
    st.markdown(
        f"**Lacunas preservadas:** {c['dias_sem_vapor_registrado']} dias sem vapor registrado "
        f"nas duas caldeiras ({c['dias_sem_vapor_fim_de_semana']} em sábados ou domingos); "
        f"neles a casca registrada soma {num(c['casca_nos_dias_sem_vapor_t'], 0)} t. "
        "O padrão é de fábrica parada, mas a planilha não diz: os dias ficam sem vapor, não com "
        "zero."
    )
    with st.container(border=True):
        st.markdown("**O que a conferência encontrou**")
        st.markdown(
            f"- **Total diário em branco** em {', '.join(c['total_diario_em_branco'])}, embora as "
            f"duas caldeiras tenham registro. Somar só a coluna de total perde "
            f"{num(c['vapor_dos_totais_em_branco_t'], 2)} t; o total oficial só fecha somando as "
            "caldeiras.\n"
            + "".join(
                f"- **Energia em branco** na caldeira {n} em {data}, com vapor e entalpia "
                "registrados.\n"
                for n, data in c["energia_em_branco"]
            )
            + f"- **{len(c['acima_da_capacidade'])} registros acima da capacidade nominal** "
            f"({num(c['capacidade_t_h'], 0)} t/h por caldeira × horas de operação):"
        )
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Data": x["data"],
                        "Caldeira": x["caldeira"],
                        "Horas": num(x["horas"], 1),
                        "Vapor (t)": num(x["vapor_t"], 2),
                        "Média (t/h)": num(x["media_t_h"], 1),
                        "% da capacidade": num(x["pct_capacidade"], 0),
                    }
                    for x in c["acima_da_capacidade"]
                ]
            ),
            hide_index=True,
            width="stretch",
        )
        st.caption(
            "Nada foi corrigido. Quem tem o registro original (totalizador e livro de turno) "
            "confere se foi digitação, troca de caldeira ou leitura do medidor."
        )
    st.markdown("**A casca do dia não é a casca queimada no dia**")
    janelas = c["razao_vapor_biomassa"]
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Soma de": f"{dias} {'dia' if dias == 1 else 'dias'}",
                    "Vapor por t de casca · baixo (5%)": num(janelas[dias][0], 2),
                    "Mediana": num(janelas[dias][1], 2),
                    "Alto (95%)": num(janelas[dias][2], 2),
                }
                for dias in (1, 7, 30)
            ]
        ),
        hide_index=True,
        width="stretch",
    )
    st.caption(
        f"Em 90% dos dias, a razão fica entre {num(janelas[1][0], 1)} e {num(janelas[1][2], 1)} "
        "t de vapor por t de casca: uma dispersão dessas vem de entrega ou estoque, não da "
        f"queima. Somando 30 dias, ela cai para {num(janelas[30][0], 1)} a "
        f"{num(janelas[30][2], 1)}. Os documentos divergem sobre a origem da coluna (volume no "
        "galpão × densidade, no PDD; notas fiscais e balança, na verificação). Por isso a "
        "EULER usa só somas longas e chama a razão de consumo aparente."
    )
    e = r["entalpia"]
    st.markdown("**Física: entalpia do vapor**")
    st.markdown(
        f"A planilha usa a entalpia do vapor saturado de uma tabela própria. Em "
        f"{num(e['dias_caldeira'], 0)} dias-caldeira, ela difere da IF97 da EULER entre "
        f"{num(e['tabela']['min_pct'], 3)}% e {num(e['tabela']['max_pct'], 3)}%, com a pressão "
        "referida a 1 kgf/cm² absoluto, como na tabela da planilha (ao nível do mar: "
        f"{num(e['nivel_do_mar']['min_pct'], 3)}% a {num(e['nivel_do_mar']['max_pct'], 3)}%)."
    )
    st.caption(
        "A planilha conta a energia do vapor desde 0 °C. A energia útil desconta a água de "
        "alimentação, cuja temperatura não foi publicada: a cada 10 °C de água, a energia útil "
        f"fica cerca de {num(e['pct_por_10c_de_agua'], 1)}% abaixo da energia da planilha. "
        "Por isso a eficiência fica bloqueada."
    )


def _hipoteses(r: dict) -> None:
    st.markdown("### Explicações que continuam possíveis")
    st.caption("Nenhuma é causa atribuída. Cada uma vem com a verificação que a separa das outras.")
    for i, h in enumerate(r["hipoteses"], 1):
        with st.container(border=True):
            st.markdown(f"**{i}. {h['titulo']}**")
            st.write(h["o_que_os_registros_mostram"])
            st.caption(f"Verificação: {h['verificacao']}")
    c = r["comparacao"]
    st.info(
        "**Próxima medição que mais separa as explicações:** o estoque de casca do galpão nas "
        "datas de corte. Com ele, a EULER calcula a casca queimada em cada período e a "
        "diferença deixa de depender de entrega e estoque."
    )
    st.caption(
        "Para comparação, o exemplo de projeto do fabricante no PDD indica "
        f"{num(c['projeto_vapor_por_biomassa'], 2)} t de vapor por t de casca, com casca a 12% de "
        f"umidade. Os registros dão {num(c['periodos'][0]['vapor_por_biomassa'], 2)} no 1º "
        f"período e {num(c['periodos'][1]['vapor_por_biomassa'], 2)} no 2º. É contexto, não "
        "referência: o exemplo não é ensaio destas caldeiras."
    )
    st.caption(
        "A EULER recomenda verificações, nunca mudanças na operação da caldeira. Qualquer ação "
        "fica com os responsáveis técnicos da planta."
    )


def _fontes(r: dict) -> None:
    f = r["fonte"]
    p = f["projeto_mdl"]
    st.markdown(
        f"**Origem:** registros diários do projeto {p['numero']} do Mecanismo de "
        "Desenvolvimento Limpo (MDL), publicados pela ONU (UNFCCC) no pedido de emissão de "
        "créditos. A planilha está no repositório sem nenhuma alteração; o CSV só extrai as "
        "colunas diárias, sem mudar valores.\n\n"
        f"**Termos de uso:** {f['termos_de_uso']['trecho']}\n\n"
        f"**Aviso:** {f['aviso']}"
    )
    st.latex(
        r"c = \frac{\sum_{dias} m_{casca}}{\sum_{dias} (V_1 + V_2)} \qquad "
        r"\frac{\Delta c}{c} = \frac{c_2}{c_1} - 1"
    )
    st.caption(
        "c: consumo aparente (t/t); m: casca registrada; V: vapor de cada caldeira. A incerteza "
        "da balança (2% sem tipo, lido como limite: u = 2%/√3, D35) entra por época de "
        "calibração; a época comum aos dois períodos é o mesmo erro (D37). Estoque e medidores "
        "de vapor entram como incertezas que faltam."
    )
    for rotulo, url in (
        ("Página do projeto 1202 · UNFCCC", p["pagina"]),
        ("Pedido de emissão (planilha e verificação)", p["pedido_de_emissao"]),
        ("Planilha diária original", f["arquivos"]["1202_CER_Calc_Sheet_Rev1.xls"]["url"]),
        (
            "Relatório de verificação · DNV",
            f["documentos_consultados"]["relatorio_de_verificacao"]["url"],
        ),
        ("Termos de uso da UNFCCC", f["termos_de_uso"]["url"]),
    ):
        st.link_button(rotulo, url)
    with st.expander("Detalhes técnicos · integridade e arquivos"):
        for nome, info in f["arquivos"].items():
            st.markdown(f"`{nome}`")
            st.code(info["sha256"], language=None)
        st.caption(
            "SHA-256 conferido nos testes. Arquivo sem alteração não comprova exatidão da medição."
        )
        st.download_button(
            "Baixar o diário (CSV)", (DADOS / "diario.csv").read_bytes(), "diario.csv", "text/csv"
        )
        st.download_button(
            "Baixar a planilha original (XLS)",
            (DADOS / "1202_CER_Calc_Sheet_Rev1.xls").read_bytes(),
            "1202_CER_Calc_Sheet_Rev1.xls",
            "application/vnd.ms-excel",
        )
        st.download_button(
            "Baixar resultado auditável",
            json.dumps(
                {
                    "fonte": f,
                    "periodos": PERIODOS,
                    "conferencia": r["conferencia"],
                    "entalpia": r["entalpia"],
                    "comparacao": {
                        k: v for k, v in r["comparacao"].items() if k not in ("comparacao",)
                    }
                    | {"motor": r["comparacao"]["comparacao"].__dict__},
                    "hipoteses": r["hipoteses"],
                    "conclusao": r["conclusao"],
                },
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            "EULER_planta_brasileira_mdl1202.json",
            "application/json",
        )


def renderizar(r: dict) -> None:
    st.subheader("Planta brasileira real · 660 dias de duas caldeiras a casca de arroz")
    st.caption(
        "CASO PÚBLICO · cervejaria em Viamão (RS) · 05/11/2007 a 25/08/2009 · registros "
        "publicados no MDL da ONU · sem vínculo com a empresa"
    )
    with st.container(border=True):
        st.markdown("### O consumo de casca por tonelada de vapor mudou?")
        st.write(r["conclusao"])
    resposta, conferencia, hipoteses, fontes = st.tabs(
        ["Resposta", "Conferência dos registros", "Hipóteses e próximas medições", "Fontes"]
    )
    with resposta:
        _resposta(r)
    with conferencia:
        _conferencia(r)
    with hipoteses:
        _hipoteses(r)
    with fontes:
        _fontes(r)
