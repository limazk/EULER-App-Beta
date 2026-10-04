"""Adapta o ensaio real e sua auditoria ao contrato central, sem novas contas físicas."""

from hashlib import sha256
from pathlib import Path

import pandas as pd
from ensaio_horario import DADOS, preparar
from robustez_ensaio import carregar_auditoria

from euler.evidencias import (
    assinatura,
    consistencia_publica,
    consolidar,
    dimensao,
    robustez_publica,
)
from euler.referencia import avaliar_referencia

ROOT = Path(__file__).resolve().parents[1]


def _hipoteses(robustez: dict) -> tuple[list, list]:
    """Lacunas específicas do recorte, não ausência inferida para a planta inteira."""
    itens = [
        (
            "instrumentacao",
            "Medições e sincronização",
            "não avaliável",
            "Indicador Measured não informa deriva, calibração ou incerteza.",
            "Conferir calibração, incerteza, unidades e horários dos medidores de energia e vapor.",
            "Distingue mudança real de erro ou deriva de medição.",
            ["instrumentacao", "carga", "combustivel"],
        ),
        (
            "estado_termico",
            "Água de alimentação e estado do vapor",
            "não avaliável",
            "Massa de vapor semelhante não garante a mesma energia útil.",
            "Obter temperatura e pressão da água, pressão e estado/temperatura do vapor nas mesmas horas.",
            "Permite testar mudanças na energia útil exigida antes de atribuir o resíduo a perdas.",
            ["estado_termico", "perdas_termicas"],
        ),
        (
            "combustivel",
            "Combustível efetivamente queimado",
            "não avaliável",
            "Composição, poder calorífico e participação horária dos combustíveis não disponíveis.",
            "Obter composição, base PCI/PCS, repartição de combustíveis e preço efetivamente contratado.",
            "Testa a base energética e a valorização; preço sozinho não explica aumento energético.",
            ["combustivel", "instrumentacao"],
        ),
        (
            "carga",
            "Carga e condições operacionais",
            "parcialmente compatível",
            "Produção de vapor incluída no baseline; regime e condições térmicas não foram normalizados.",
            "Obter registros de partidas, paradas e mudanças de operação sincronizados com as horas analisadas.",
            "Separa alterações de regime de mudanças persistentes nas mesmas condições.",
            ["carga", "perdas_termicas"],
        ),
        (
            "combustao",
            "Combustão e excesso de ar",
            "não avaliável",
            "O recorte não fornece os sinais térmicos e de composição necessários ao balanço.",
            "Obter O₂ em base declarada, CO e temperaturas de gases e ar, com combustível e carga.",
            "Permite avaliar perdas nos gases; temperatura isolada não identifica causa.",
            ["combustao", "perdas_termicas"],
        ),
        (
            "perdas_termicas",
            "Transferência de calor, purga e incrustação",
            "não avaliável",
            "Não há vazões e estados térmicos suficientes; fouling não pode ser inferido do resíduo.",
            "Consultar inspeções e obter medições de purga e do trocador conforme avaliação técnica.",
            "Distingue rotas de perda; UA aparente não confirma incrustação.",
            ["perdas_termicas", "combustao"],
        ),
    ]
    hips, acoes = [], []
    for i, (id_, titulo, estado, evidencia, acao, porque, separa) in enumerate(itens, 1):
        if id_ == "carga" and robustez["sinal"] == "aumento":
            evidencia += (
                " Explicação somente por volume de vapor fica enfraquecida nos métodos testados."
            )
        hips.append(
            {
                "id": id_,
                "titulo": titulo,
                "estado_interpretacao": estado,
                "evidencias": [evidencia],
                "causa_comprovada": False,
            }
        )
        acoes.append(
            {
                "ordem": i,
                "acao": acao,
                "porque": porque,
                "separa": separa,
                "origem": "Roteiro qualitativo: verificar medição, demanda útil e combustível antes das perdas.",
            }
        )
    return hips, acoes


def diagnosticos(resultado: dict, unidade: str) -> list[dict]:
    """Um resultado por período, sem esconder períodos negativos/inconclusivos.

    Só usa auditoria cuja assinatura foi verificada e cujos resultados correspondem
    à execução atual. Preserva GJ em PCS, preço regional e horas do cálculo original.
    """
    u, fonte = resultado["unidades"][unidade], resultado["fonte"]
    auditoria = carregar_auditoria()
    if auditoria and auditoria["fonte_sha256"] != fonte["recorte_sha256"]:
        auditoria = None
    au = auditoria["unidades"].get(unidade) if auditoria else None
    caminho = DADOS / "ingredion_2023q1.csv"
    if sha256(caminho.read_bytes()).hexdigest() != fonte["recorte_sha256"]:
        raise ValueError("Dados do diagnóstico não correspondem ao recorte executado.")
    bruto = pd.read_csv(caminho, dtype={"Unit ID": str})
    d, _ = preparar(bruto[bruto["Unit ID"] == unidade])
    ref = d[d.mes == "2023-01"]
    previstos = u["intercepto_gj_h"] + u["inclinacao_gj_t"] * ref.vapor_t
    hashes = {
        p: sha256((ROOT / p).read_text(encoding="utf-8").encode("utf-8")).hexdigest()
        for p in ("app/diagnostico_publico.py", "euler/evidencias.py", "euler/referencia.py")
    }
    saida = []
    for mes in u["comparacoes"]:
        am = next((a for a in au["meses"] if a["mes"] == mes["mes"]), None) if au else None
        if am and any(
            am[a] != mes[b]
            for a, b in (
                ("delta_original_gj", "delta_gj"),
                ("delta_original_pct", "delta_pct"),
                ("horas_comparaveis", "horas_comparaveis"),
                ("valor_condicional_usd", "valor_referencia_usd"),
            )
        ):
            am = None
        rob = robustez_publica(am, auditoria["repeticoes"] if auditoria else None)
        referencia = avaliar_referencia(
            observado=ref.energia_gj,
            previsto=previstos,
            unidade="GJ/hora registrada",
            instantes=pd.to_datetime(ref.Date) + pd.to_timedelta(ref.Hour, unit="h"),
            carga=ref.vapor_t,
            carga_comparacao=d[d.mes == mes["mes"]].vapor_t,
            unidade_carga="t/h",
            intervalo_horas=1,
            validacao_temporal=au["diagnostico"]["validacao_temporal"] if au else None,
        )
        if rob["sinal"] == "nao_avaliavel":
            observacao = (
                "Aumento"
                if mes["delta_gj"] > 0
                else "Redução"
                if mes["delta_gj"] < 0
                else "Diferença nula"
            )
            conclusao = f"{observacao} observado no cálculo original; robustez não avaliável."
        else:
            conclusao = rob["conclusao"]
        conclusao += " Os dados disponíveis não permitem atribuir uma causa física específica."
        hips, acoes = _hipoteses(rob)
        cobertura = mes["horas_comparaveis"] / mes["horas_validas"]
        dimensoes = {
            "qualidade_dados": dimensao(
                "MODERADA",
                [
                    "Recorte íntegro, duplicatas bloqueadas e exclusões registradas.",
                    "Validade dos registros não comprova calibração nem regime estável.",
                ],
                u["qualidade"],
            ),
            "referencia": referencia,
            "robustez_estatistica": rob,
            "consistencia_temporal": consistencia_publica(
                am,
                {
                    "dias_comparaveis": mes["dias_comparaveis"],
                    "dias_delta_positivo": mes["dias_delta_positivo"],
                },
            ),
            "evidencia_fisica": dimensao(
                "INSUFICIENTE",
                ["Sem estados de água/vapor e combustível para fechar balanço térmico."],
            ),
            "cobertura_variaveis": dimensao(
                "FRACA",
                ["Carga observada; faltam condições térmicas, regime, mistura e eventos."],
                {
                    "horas_comparaveis": mes["horas_comparaveis"],
                    "horas_validas": mes["horas_validas"],
                    "fracao": cobertura,
                },
            ),
            "incerteza": dimensao(
                "INSUFICIENTE", ["Sem orçamento instrumental. Reamostragem não o substitui."]
            ),
        }
        saida.append(
            consolidar(
                {
                    "equipamento": unidade,
                    "periodo": mes["mes"],
                    "origem_dados": "públicos EPA/PUDL",
                    "observacao": {
                        "unidade": "GJ",
                        "base_calorifica": "PCS",
                        "tipo": "energia_condicionada_a_carga",
                        "referencia": mes["energia_referencia_gj"],
                        "comparacao": mes["energia_observada_gj"],
                        "variacao": mes["delta_gj"],
                        "variacao_pct": mes["delta_pct"],
                        "incerteza_variacao": None,
                    },
                    "dimensoes": dimensoes,
                    "conclusao": conclusao,
                    "hipoteses": hips,
                    "dados_faltantes": [
                        h["evidencias"][0]
                        for h in hips
                        if h["estado_interpretacao"] == "não avaliável"
                    ],
                    "proximas_medicoes": acoes,
                    "economia": {
                        "desvio_estimado": mes["valor_referencia_usd"],
                        "moeda": "USD",
                        "oportunidade_potencial": None,
                        "economia_verificada": None,
                        "preco": mes["preco_usd_gj"],
                        "unidade_preco": "USD/GJ PCS",
                        "periodo": mes["mes"],
                        "combustivel": "gás natural, valorização condicional",
                        "origem_preco": fonte["preco_fonte"],
                        "data_informacao": mes["mes"],
                        "data_publicacao": None,
                        "premissas": [
                            fonte["preco_tipo"],
                            fonte["calor_tipo"],
                            "Mistura horária desconhecida; valor não é fatura, prejuízo ou economia recuperável.",
                        ],
                    },
                    "limitacoes": fonte["limitacoes"] + referencia["limitacoes"],
                    "metodos": {
                        "baseline": "E = a + b V; OLS apenas janeiro; sem extrapolar",
                        "intercepto_gj_h": u["intercepto_gj_h"],
                        "inclinacao_gj_t": u["inclinacao_gj_t"],
                        "normalizacao": ["produção de vapor"],
                        "referencia": "2023-01",
                        "origens": {
                            "energia": "medido conforme indicador EPA",
                            "vapor": "informado pela fonte EPA",
                            "energia_esperada": "estimado",
                            "estado_termico": "ausente",
                        },
                        "economia": "Diferença GJ × preço USD/GJ; mesmos preços no observado e esperado",
                        "ranking_medicoes": "Ordem qualitativa por dependências diagnósticas, não valor da informação quantificado.",
                    },
                    "fontes": {
                        "dados": fonte,
                        "chaves_registro": ["Facility ID", "Unit ID", "Date", "Hour"],
                        "arquivo": str(caminho.relative_to(ROOT)),
                        "filtro": f"Unit ID={unidade}; janeiro e {mes['mes']}",
                        "regras_inclusao": "preparar(): hora=1, Measured, energia/vapor positivos finitos, suporte janeiro",
                        "resultado_motor_sha256": assinatura(u),
                        "auditoria_sha256": assinatura(auditoria) if am else None,
                        "metodo_sha256": hashes,
                        "auditoria_mes": am,
                    },
                }
            )
        )
    return saida
