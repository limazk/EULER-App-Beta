"""Adapter do diagnóstico físico existente; não recalcula perdas ou hipóteses."""

from copy import deepcopy
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path

from euler.economia import valorizar_diferenca
from euler.evidencias import assinatura, consolidar, dimensao

ESTADOS = {
    "sustentada": "compatível",
    "oposta": "incompatível com o sentido do desvio",
    "possivel": "parcialmente compatível",
    "descartada": "enfraquecida",
    "nao_avaliavel": "não avaliável",
}


def fontes_pacote(pacote) -> dict:
    """Hash de representação CSV das tabelas originais preservadas, não do arquivo bruto."""
    return {
        "tabelas_originais": {
            nome: {
                "sha256": sha256(
                    imp.original.to_csv(index=False, lineterminator="\n").encode("utf-8")
                ).hexdigest(),
                "linhas": len(imp.original),
                "colunas": list(imp.original.columns),
            }
            for nome, imp in pacote.importacoes.items()
        },
        "formato_hash": "CSV UTF-8 LF da tabela original preservada pelo importador; não bytes do arquivo enviado",
        "p_atm_bar": pacote.p_atm_bar,
        "avisos": [asdict(a) for a in pacote.avisos],
        "metodo_sha256": {
            str(p.relative_to(Path(__file__).resolve().parent)): sha256(
                p.read_text(encoding="utf-8").encode("utf-8")
            ).hexdigest()
            for p in sorted(Path(__file__).resolve().parent.rglob("*.py"))
        },
    }


def diagnosticar_investigacao(j: dict, fontes: dict) -> dict:
    """Avalia suficiência de uma comparação agregada sem inventar diagnósticos temporais."""
    c = deepcopy(j["o_que_mudou"]["consumo_especifico"])
    ref, comp = j["periodos"]["referencia"], j["periodos"]["comparacao"]
    hs = [
        {**deepcopy(h), "estado_interpretacao": ESTADOS[h["status"]], "causa_comprovada": False}
        for h in j["hipoteses"]
    ]
    sustentada = any(h["status"] == "sustentada" for h in hs)
    faltas = j["o_que_falta"]
    avisos = fontes.get("avisos", [])
    erros = [a for a in avisos if a.get("gravidade") == "erro"]
    dims = {
        "qualidade_dados": dimensao(
            "FRACA" if erros else "MODERADA",
            [
                "Importação preserva originais e avisos; qualidade depende de cobertura e metrologia.",
                f"{len(avisos)} avisos no pacote; {len(erros)} classificados como erro.",
            ],
            {
                "cobertura_referencia": ref["cobertura_diario"],
                "cobertura_comparacao": comp["cobertura_diario"],
            },
        ),
        "referencia": dimensao(
            "INSUFICIENTE",
            [
                "Comparação agregada: estabilidade estatística da referência ainda não avaliada nesta rota."
            ],
        ),
        "robustez_estatistica": dimensao(
            "INSUFICIENTE",
            [
                "Incerteza física não substitui validação temporal, resíduos ou reamostragem de uma série."
            ],
        ),
        "consistencia_temporal": dimensao(
            "INSUFICIENTE", ["Dois agregados não demonstram persistência temporal."]
        ),
        "evidencia_fisica": dimensao(
            "MODERADA" if sustentada else "INSUFICIENTE",
            [
                "Há explicação compatível segundo o modelo físico e suas hipóteses; não é causa confirmada."
                if sustentada
                else "A comparação não sustenta atribuição física específica."
            ],
        ),
        "cobertura_variaveis": dimensao(
            "FRACA" if faltas else "MODERADA",
            [
                "Pré-requisitos físicos avaliados pelo motor; variáveis ausentes não foram completadas."
            ],
            {"pendencias": faltas},
        ),
        "incerteza": dimensao(
            "INSUFICIENTE"
            if c["detectabilidade"] is None
            else "FRACA"
            if c["faltam_na_incerteza"]
            else "MODERADA",
            [
                "Orçamento determinístico e hipóteses de correlação preservados; completude deve ser revisada."
            ],
            {"detectabilidade": c["detectabilidade"], "faltam": c["faltam_na_incerteza"]},
        ),
    }
    prox = j["proxima_verificacao"]
    acoes = [
        {
            "ordem": 1,
            "acao": prox["acao"],
            "porque": prox["porque"],
            "separa": prox["separa"],
            "origem": "Regra de investigação física existente",
        }
    ]
    vapor = (comp.get("vapor_t") or {}).get("valor")
    valor = valorizar_diferenca(c["variacao"], vapor, comp["preco_brl_t"])
    return consolidar(
        {
            "equipamento": j["caldeira_id"],
            "periodo": comp["rotulo"],
            "observacao": c,
            "origem_dados": j["origem_dados"],
            "dimensoes": dims,
            "conclusao": j["conclusao"]["texto"] + " Causa física não confirmada.",
            "hipoteses": hs,
            "dados_faltantes": faltas,
            "proximas_medicoes": acoes,
            "economia": {
                "desvio_estimado": valor,
                "moeda": "BRL",
                "preco": comp["preco_brl_t"],
                "unidade_preco": "BRL/t de combustível",
                "periodo": comp["rotulo"],
                "origem_preco": "Preço por tonelada recebido pelo motor, derivado dos registros de combustível.",
                "premissas": [
                    "Mesmo preço e mesma produção de vapor na comparação.",
                    "Valorização aritmética do desvio, sem confirmação de prejuízo ou recuperação.",
                ],
                "oportunidade_potencial": None,
                "economia_verificada": None,
            },
            "limitacoes": [
                "Classificação não substitui revisão física nem validação de campo.",
                "A análise estatística temporal da referência agregada ainda não está disponível.",
                "Não há balanço completo de todas as perdas: radiação, CO/incombustos e outras parcelas podem faltar.",
                "Registro formal de intervenção e verificação de economia ainda não implementados.",
            ],
            "metodos": {
                "criterios": j["criterios"],
                "periodos": j["periodos"],
                "baseline": "Comparação física agregada existente, não modelo temporal multivariável",
                "hipoteses": "Regras existentes euler/investigacao.py; estados legados preservados",
                "economia": "E13: diferença t/t × vapor t × preço BRL/t",
            },
            "fontes": {**fontes, "resultado_fisico_sha256": assinatura(j)},
        }
    )
