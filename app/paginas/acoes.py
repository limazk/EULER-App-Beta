"""Investigações e ações: do desvio à verificação, com histórico (D94).

A EULER recomenda verificações e registra o que os responsáveis técnicos decidiram e
fizeram; não gera comando operacional. Encerrar não significa causa confirmada.
"""

import pandas as pd
import streamlit as st
from acompanhamento_ui import (
    autor,
    brl,
    chave_form,
    data,
    executar,
    exigir_autor,
    periodo,
    planta_e_equipamento,
    recarregar,
)
from componentes import cabecalho, md

from euler.acompanhamento import (
    ESTADOS,
    RESULTADOS,
    TIPOS_INTERVENCAO,
    TRANSICOES,
    adicionar_evidencia,
    adotar_referencia_pos_intervencao,
    avaliar_intervencao,
    custos_servico,
    definir_responsavel,
    encerrar,
    intervencoes,
    investigacao,
    investigacoes,
    mudar_estado,
    registrar_custo_servico,
    registrar_intervencao,
    ultima_avaliacao,
)
from euler.formato import num

RESULTADO_ACAO = {
    "positivo": ("Melhoria associada à ação", "green"),
    "negativo": ("Piora detectável depois da ação", "red"),
    "inconclusivo": ("Inconclusivo", "gray"),
    "nao_avaliavel": ("Ainda não avaliável", "gray"),
}
TIPOS_EVENTO = {
    "criada": "Aberta",
    "ocorrencia": "Nova ocorrência",
    "evidencia": "Evidência",
    "estado": "Situação",
    "acao": "Ação registrada",
    "verificacao": "Verificação",
    "responsavel": "Responsável",
    "encerrada": "Encerrada",
}


def form_acao(a, eq, nome_autor, investigacao_id=None, chave="acao") -> None:
    with st.form(chave_form(f"form_{chave}")):
        c1, c2 = st.columns(2)
        quando = c1.date_input("Data da ação", value=None, format="DD/MM/YYYY")
        tipo = c2.selectbox("Tipo", list(TIPOS_INTERVENCAO), format_func=TIPOS_INTERVENCAO.get)
        descricao = st.text_input("O que foi feito")
        c3, c4, c5 = st.columns(3)
        responsavel = c3.text_input("Responsável (opcional)")
        custo = c4.number_input("Custo da ação (R$, opcional)", min_value=0.0, value=None)
        origem = c5.text_input("Origem do custo (nota, orçamento)")
        concomitantes = st.text_area(
            "Outras mudanças no mesmo período (uma por linha)",
            help="Ex.: troca de fornecedor, mudança de carga. Elas impedem associar o resultado só a esta ação.",
        )
        if st.form_submit_button("Registrar ação") and exigir_autor(nome_autor):
            if quando is None:
                st.error("Informe a data da ação.")
                return
            executar(
                lambda: registrar_intervencao(
                    a, eq["id"], pd.Timestamp(quando).tz_localize("America/Sao_Paulo"), tipo,
                    descricao, nome_autor, responsavel=responsavel or None,
                    investigacao_id=investigacao_id,
                    concomitantes=[x.strip() for x in concomitantes.splitlines() if x.strip()],
                    custo_brl=custo, custo_origem=origem or None,
                ),
                "Ação registrada. Avalie quando houver períodos completos depois dela.",
recarregar_tela=True,
            )  # fmt: skip


def detalhe_investigacao(a, eq, inv, nome_autor) -> None:
    d = inv["dados"]
    st.markdown(f"#### #{inv['id']} · {inv['titulo']}")
    st.badge(ESTADOS[inv["estado"]], color="blue" if inv["estado"] != "encerrada" else "gray")
    if inv["estado"] == "encerrada":
        st.info(
            f"Encerrada como **{RESULTADOS.get(d.get('resultado'), d.get('resultado'))}**: "
            f"{d.get('motivo_encerramento')}. Encerrar não significa causa confirmada."
        )
    desvio = d.get("desvio") or {}
    if desvio.get("frase"):
        st.markdown(md(f"**Desvio que motivou:** {desvio['frase']}"))
    prox = d.get("proxima_verificacao") or {}
    if prox.get("acao"):
        with st.container(border=True):
            st.markdown(md(f"**Próxima verificação:** {prox['acao']}"))
            if prox.get("porque"):
                st.caption(prox["porque"])
    st.caption(
        f"Responsável: {inv['responsavel'] or 'não informado'} · aberta em {data(inv['criada_em'])}"
    )
    with st.expander("Hipóteses, evidências e limitações"):
        for h in d.get("hipoteses", []):
            st.markdown(
                md(
                    f"- **{h['titulo']}** · evidência {h['evidencia'].lower()} · "
                    f"{brl(h.get('impacto_brl'))} associado (não somar) · {h['verificacao']}"
                )
            )
        for x in d.get("limitacoes", []):
            st.caption(x)
    with st.expander(f"Histórico ({len(inv['eventos'])})"):
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Quando": data(e["quando"]),
                        "O quê": TIPOS_EVENTO.get(e["tipo"], e["tipo"]),
                        "Quem": e["autor"] or "—",
                        "Detalhe": e["texto"] or "",
                    }
                    for e in inv["eventos"]
                ]
            ),
            hide_index=True,
            width="stretch",
        )
    if inv["estado"] == "encerrada":
        with st.form(chave_form(f"reabrir_{inv['id']}")):
            motivo = st.text_input("Motivo da reabertura")
            if st.form_submit_button("Reabrir investigação") and exigir_autor(nome_autor):
                executar(
                    lambda: mudar_estado(a, inv["id"], "em_investigacao", nome_autor, motivo),
                    "Reaberta.",
                    recarregar_tela=True,
                )
        return
    aba = st.tabs(
        ["Evidência", "Situação e responsável", "Registrar ação", "Encerrar"],
        key=f"inv_aba_{inv['id']}",
    )
    with aba[0], st.form(chave_form(f"evid_{inv['id']}")):
        texto = st.text_area("O que foi verificado ou medido")
        ref = st.text_input("Onde está o documento ou a medição (opcional)")
        if st.form_submit_button("Adicionar evidência") and exigir_autor(nome_autor):
            executar(
                lambda: adicionar_evidencia(a, inv["id"], texto, nome_autor, ref or None),
                "Evidência registrada.",
                recarregar_tela=True,
            )
    with aba[1]:
        opcoes = sorted(TRANSICOES[inv["estado"]] - {"encerrada"})
        with st.form(chave_form(f"estado_{inv['id']}")):
            novo = st.selectbox("Nova situação", opcoes, format_func=ESTADOS.get)
            motivo = st.text_input("Motivo")
            if st.form_submit_button("Mudar situação") and exigir_autor(nome_autor):
                executar(
                    lambda: mudar_estado(a, inv["id"], novo, nome_autor, motivo),
                    "Situação atualizada.",
                    recarregar_tela=True,
                )
        with st.form(chave_form(f"resp_{inv['id']}")):
            resp = st.text_input("Responsável", value=inv["responsavel"] or "")
            if st.form_submit_button("Definir responsável") and exigir_autor(nome_autor):
                executar(
                    lambda: definir_responsavel(a, inv["id"], resp, nome_autor),
                    "Responsável definido.",
                    recarregar_tela=True,
                )
    with aba[2]:
        st.caption(
            "A ação fica ligada a esta investigação; o resultado vem da avaliação posterior."
        )
        form_acao(a, eq, nome_autor, inv["id"], chave=f"acao_inv_{inv['id']}")
    with aba[3], st.form(chave_form(f"enc_{inv['id']}")):
        resultado = st.selectbox("Resultado", list(RESULTADOS), format_func=RESULTADOS.get)
        motivo = st.text_input("Motivo do encerramento")
        st.caption("Inconclusiva é um resultado válido. Encerrar não significa causa confirmada.")
        if st.form_submit_button("Encerrar investigação") and exigir_autor(nome_autor):
            executar(
                lambda: encerrar(a, inv["id"], resultado, motivo, nome_autor),
                "Investigação encerrada.",
                recarregar_tela=True,
            )


def aba_investigacoes(a, eq, nome_autor) -> None:
    todas = investigacoes(a, eq["id"])
    if not todas:
        st.info(
            "Nenhuma investigação ainda. Elas são abertas a partir de um fechamento com desvio "
            "ou hipótese a verificar."
        )
        st.page_link(
            "paginas/fechamentos.py", label="Ir para Fechamentos", icon=":material/event_available:"
        )
        return
    ordem = sorted(todas, key=lambda x: (x["estado"] == "encerrada", -x["id"]))
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "#": x["id"],
                    "Investigação": x["titulo"],
                    "Situação": ESTADOS[x["estado"]],
                    "Ocorrências": sum(e["tipo"] in ("criada", "ocorrencia") for e in x["eventos"]),
                    "Responsável": x["responsavel"] or "—",
                    "Atualizada": data(x["atualizada_em"]),
                }
                for x in ordem
            ]
        ),
        hide_index=True,
        width="stretch",
    )
    escolhida = st.selectbox(
        "Abrir investigação",
        [x["id"] for x in ordem],
        format_func=lambda i: f"#{i} · {next(x['titulo'] for x in ordem if x['id'] == i)}",
        key="acoes_inv_sel",
    )
    detalhe_investigacao(a, eq, investigacao(a, escolhida), nome_autor)


def avaliacao(a, eq, it, nome_autor) -> None:
    av = ultima_avaliacao(a, it["id"])
    c1, c2 = st.columns(2)
    if c1.button("Avaliar agora", key=f"av_{it['id']}") and exigir_autor(nome_autor):
        with st.spinner("Comparando a referência com os períodos depois da ação…"):
            ok = executar(lambda: avaliar_intervencao(a, it["id"], nome_autor))
        if ok:  # redesenha fora do indicador de espera (senão sobram restos na tela)
            recarregar("Avaliação registrada.")
    if av is None:
        st.caption("Ainda não avaliada.")
        return
    r = av["resultado"]
    rotulo, cor = RESULTADO_ACAO[r["resultado"]]
    st.badge(rotulo, color=cor)
    st.write(r["frase"])
    dif = r.get("diferenca_observada")
    if dif:
        st.markdown(
            md(
                f"**Diferença observada** ({periodo(dif['periodo_depois'])}): consumo por tonelada de "
                f"vapor {num(dif['consumo_antes_t_t'], 3)} → {num(dif['consumo_depois_t_t'], 3)} t/t; "
                f"desvio da referência ajustada {brl(dif['desvio_brl'])}."
            )
        )
    m = r.get("melhoria_associada")
    st.markdown(
        md(
            f"**Melhoria associada à ação:** {brl(m['custo_brl'])} (faixa {brl(m['faixa_brl'][0])} a {brl(m['faixa_brl'][1])}). {m['nota']}"
            if m and m.get("custo_brl") is not None
            else "**Melhoria associada à ação:** não estabelecida."
        )
    )
    ev = r.get("economia_verificada")
    if ev and ev.get("valor_brl") is not None:
        st.markdown(
            md(
                f"**Economia verificada ({ev['protocolo']}):** {brl(ev['valor_brl'])} no período avaliado. "
                + (
                    f"Benefício líquido: {brl(ev['beneficio_liquido_brl'])}. "
                    if ev.get("beneficio_liquido_brl") is not None
                    else ""
                )
                + ev["nota_custos"]
            )
        )
    elif ev:
        st.markdown("**Economia verificada:** critérios do protocolo não atendidos.")
        for x in ev.get("criterios_nao_atendidos", []):
            st.caption(f"• {x}")
    else:
        st.markdown("**Economia verificada:** não se aplica sem melhoria associada.")
    detalhes = (r.get("comparabilidade") or {}).get("motivos", []) + r.get("periodos_excluidos", [])
    if r.get("faltam"):
        detalhes += r["faltam"]
    if detalhes:
        with st.expander("Por que não foi possível associar ou verificar"):
            for x in detalhes:
                st.caption(f"• {x}")
    if dif:
        with c2.popover("Adotar a referência depois desta ação"):
            st.caption(
                "Cria nova versão da referência com os períodos depois da ação, para acompanhar se o "
                "desempenho se mantém. Versões anteriores continuam reproduzíveis."
            )
            motivo = st.text_input("Motivo", key=chave_form(f"refmot_{it['id']}"))
            confirmar = st.checkbox(
                "Confirmo, mesmo que o período seja pior que a referência atual",
                key=chave_form(f"refconf_{it['id']}"),
            )
            if st.button("Adotar referência", key=f"ref_{it['id']}") and exigir_autor(nome_autor):
                executar(
                    lambda: adotar_referencia_pos_intervencao(
                        a, it["id"], nome_autor, motivo, confirmar
                    ),
                    "Nova versão da referência registrada.",
                    recarregar_tela=True,
                )


def aba_acoes(a, eq, nome_autor) -> None:
    with st.expander("Registrar uma ação"):
        form_acao(a, eq, nome_autor)
    lista = intervencoes(a, eq["id"])
    if not lista:
        st.caption("Nenhuma ação registrada.")
    for it in reversed(lista):
        with st.container(border=True):
            st.markdown(
                f"**#{it['id']} · {data(it['data'])} · {TIPOS_INTERVENCAO.get(it['tipo'], it['tipo'])}** · {it['descricao']}"
            )
            st.caption(
                f"Responsável: {it['responsavel'] or 'não informado'} · custo "
                + (
                    f"{brl(it['custo_brl'])} ({it['custo_origem']})"
                    if it["custo_brl"] is not None
                    else "não informado"
                )
                + (f" · investigação #{it['investigacao_id']}" if it["investigacao_id"] else "")
            )
            if it["dados"].get("concomitantes"):
                st.caption("Mudanças no mesmo período: " + "; ".join(it["dados"]["concomitantes"]))
            avaliacao(a, eq, it, nome_autor)
    with st.expander("Custos de medição e acompanhamento"):
        st.caption(
            "Entram no benefício líquido das ações verificadas na mesma janela. Horas de equipe não viram dinheiro aqui."
        )
        custos = custos_servico(a, eq["id"])
        if custos:
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "Data": data(x["data"]),
                            "Tipo": x["tipo"],
                            "Descrição": x["descricao"],
                            "Valor": brl(x["valor_brl"]),
                            "Origem": x["origem"],
                        }
                        for x in custos
                    ]
                ),
                hide_index=True,
                width="stretch",
            )
        with st.form(chave_form("custo_servico")):
            c1, c2, c3 = st.columns(3)
            quando = c1.date_input("Data", value=None, format="DD/MM/YYYY")
            tipo = c2.selectbox(
                "Tipo",
                ["medicao", "acompanhamento", "outro"],
                format_func=lambda t: {
                    "medicao": "Medição",
                    "acompanhamento": "Acompanhamento",
                    "outro": "Outro",
                }[t],
            )
            valor = c3.number_input("Valor (R$)", min_value=0.0, value=None)
            descricao = st.text_input("Descrição")
            origem = st.text_input("Origem (nota, contrato)")
            if st.form_submit_button("Registrar custo") and exigir_autor(nome_autor):
                if quando is None or valor is None:
                    st.error("Informe data e valor.")
                else:
                    executar(
                        lambda: registrar_custo_servico(
                            a, eq["id"], pd.Timestamp(quando).tz_localize("America/Sao_Paulo"),
                            tipo, descricao, valor, origem, nome_autor,
                        ),
                        "Custo registrado.",
recarregar_tela=True,
                    )  # fmt: skip


def mostrar() -> None:
    nome_autor = autor()
    with planta_e_equipamento(passo=("investigar", "acao", "resultado")) as ctx:
        if ctx is None:
            return
        _, _, a, eq = ctx
        abertas = len(investigacoes(a, eq["id"], abertas=True))
        n_acoes = len(intervencoes(a, eq["id"]))
        c1, c2 = st.columns(2)
        c1.metric("Investigações abertas", abertas, border=True)
        c2.metric("Ações registradas", n_acoes, border=True)
        # rótulos fixos: a aba escolhida continua aberta depois de gravar
        abas = st.tabs(["Investigações", "Ações e resultados"], key="acoes_aba")
        with abas[0]:
            aba_investigacoes(a, eq, nome_autor)
        with abas[1]:
            aba_acoes(a, eq, nome_autor)


cabecalho(
    "Investigações e ações",
    "Do desvio à verificação: o que a equipe investigou, decidiu e qual foi o resultado.",
    "Acompanhar a planta",
)
mostrar()
