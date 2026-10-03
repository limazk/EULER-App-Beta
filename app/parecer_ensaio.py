"""Parecer descritivo do ensaio EPA (D84), sem diagnóstico físico ou ordem operacional."""

from euler.formato import num

VERIFICACOES = [
    {
        "onde": "Medições e registros",
        "conferir": "Conferir medidores de vapor e combustível, calibrações, unidades e horários dos registros.",
        "para_que": "Distinguir mudança de consumo de erro de medição ou de sincronização.",
    },
    {
        "onde": "Condições do processo",
        "conferir": "Comparar pressão e temperatura do vapor, temperatura da água de alimentação, partidas e paradas nas mesmas horas.",
        "para_que": "A mesma massa de vapor pode exigir energia diferente. Carga semelhante, sozinha, não garante condições equivalentes.",
    },
    {
        "onde": "Combustível e custo",
        "conferir": "Confirmar combustível efetivamente queimado, poder calorífico, participação de cada combustível e preço do contrato/fatura.",
        "para_que": "Recalcular o valor com a realidade da planta e separar custos variáveis de parcelas fixas.",
    },
]

INVESTIGACOES = [
    {
        "onde": "Combustão e gases",
        "dados": "Temperatura dos gases e do ar, O₂ e CO, combustível e carga sincronizados.",
        "resposta": "Avaliar se há evidências compatíveis com mudança de combustão ou perda pelos gases.",
    },
    {
        "onde": "Troca de calor",
        "dados": "Temperaturas de entrada/saída, vazões, pressões e histórico de inspeção/manutenção.",
        "resposta": "Investigar desempenho térmico; temperatura alta isolada não comprova incrustação.",
    },
    {
        "onde": "Purga e retorno de condensado",
        "dados": "Vazão/massa e condições da purga, temperatura da água e registros do retorno de condensado.",
        "resposta": "Avaliar energia descartada e mudanças na necessidade de aquecer água de reposição.",
    },
]


def parecer(unidade: dict) -> dict:
    """Resume sinais e cobertura; consistência descritiva não confirma detectabilidade.

    Valores em GJ e USD, restritos às horas comparáveis do ensaio. Nenhum limiar
    de urgência, probabilidade de causa ou perda recuperável é inferido.
    """
    meses = unidade["comparacoes"]
    positivos = sum(m["delta_gj"] > 0 for m in meses)
    sensivel = bool(meses) and all(
        m["sensibilidade"]
        and all(s["delta_gj"] is not None and s["delta_gj"] > 0 for s in m["sensibilidade"])
        for m in meses
    )
    if len(meses) >= 2 and positivos == len(meses):
        status, titulo = "investigar", "Investigar aumento de consumo"
        conclusao = (
            "A energia consumida ficou acima da referência ajustada à produção nos dois meses. "
            + (
                "O aumento também aparece na comparação por faixas de produção."
                if sensivel
                else "A conclusão depende do método de comparação; confira a sensibilidade."
            )
        )
    elif meses and all(m["delta_gj"] <= 0 for m in meses):
        status, titulo = "sem_aumento", "Sem aumento nos períodos comparados"
        conclusao = (
            "O consumo ficou igual ou abaixo da referência nas horas comparáveis. "
            "Isso não comprova economia recuperada nem certifica a saúde da caldeira."
        )
    else:
        status, titulo = "variavel", "Resultado varia entre os períodos"
        conclusao = (
            "Não há aumento persistente nos dois meses. Examine cada período e sua cobertura."
        )
    return {
        "status": status,
        "titulo": titulo,
        "conclusao": conclusao,
        "sensibilidade_consistente": sensivel,
        "horas": sum(m["horas_comparaveis"] for m in meses),
        "fora_faixa": sum(m["horas_fora_faixa"] for m in meses),
        "energia_gj": sum(m["delta_gj"] for m in meses),
        "valor_usd": sum(m["valor_referencia_usd"] for m in meses),
        "perda_confirmada": None,
        "economia_recuperavel": None,
        "intervencao_indicada": False,
        "verificacoes": VERIFICACOES,
    }


def relatorio_texto(resultado: dict, unidade: str) -> str:
    """Memória legível e exportável: mesmos números, fontes e limites da tela."""
    u, f = resultado["unidades"][unidade], resultado["fonte"]
    p = parecer(u)
    linhas = [
        f"# EULER — ensaio público · {unidade}",
        f"{f['instalacao']} · janeiro a março de 2023 · análise retrospectiva exploratória",
        "Sem vínculo com a instalação; não é monitoramento ao vivo nem auditoria certificada.",
        f"## {p['titulo']}",
        p["conclusao"],
        f"Horas comparáveis: {p['horas']}; horas válidas fora da faixa: {p['fora_faixa']}.",
        f"Diferença energética: {num(p['energia_gj'])} GJ.",
        f"Diferença valorizada a preço regional: US$ {num(p['valor_usd'])}.",
        "Perda física/financeira confirmada: não apurada. Economia recuperável: não apurada.",
        "## Memória de cálculo",
        (
            "Janeiro: referência estatística energia = intercepto + inclinação × produção de vapor. "
            "Fevereiro/março: observado menos referência, somente dentro da faixa de carga de janeiro."
        ),
        "Valor = diferença (GJ) × preço (US$/GJ). O mesmo preço é aplicado ao observado e à referência de cada mês.",
    ]
    for m in u["comparacoes"]:
        linhas.append(
            f"- {m['mes']}: {num(m['delta_pct'])}%; {num(m['delta_gj'])} GJ × "
            f"US$ {num(m['preco_usd_gj'], 6)}/GJ = US$ {num(m['valor_referencia_usd'])}; "
            f"{m['horas_comparaveis']}/{m['horas_validas']} horas válidas comparadas."
        )
    linhas += [
        (
            "Preço EIA industrial Illinois: fevereiro US$8,02/mil pés cúbicos; março US$6,54. "
            "Conversão: 1,040 MMBtu/mil pés cúbicos e 1,05505585262 GJ/MMBtu. Conta usa precisão completa."
        ),
        "## Limites",
        (
            "Preço e poder calorífico regionais, não contrato/amostra da planta. B10 registra carvão "
            "secundário no cadastro EPA, sem participação horária: valorização integral como gás é condicional."
        ),
        (
            "Sem incertezas, condições de água/vapor ou eventos suficientes para confirmar causa ou perda. "
            "Hora completa não garante regime estável. Janeiro não é referência certificada como ideal. "
            "B10 destacada após triagem das quatro unidades. Sem extrapolação anual."
        ),
        "## Orientação ao operador",
        (
            "Verificação dos registros indicada; intervenção operacional não indicada por este ensaio. "
            "Não altera setpoints nem substitui os procedimentos de segurança da planta."
        ),
    ]
    for v in p["verificacoes"]:
        linhas.append(f"- {v['onde']}: {v['conferir']} Objetivo: {v['para_que']}")
    linhas += [
        "## Fontes e integridade",
        f["url"],
        f["preco_fonte"],
        f["calor_fonte"],
        f"SHA-256 do recorte: {f['recorte_sha256']}",
    ]
    return "\n\n".join(linhas)
