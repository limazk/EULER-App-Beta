"""Resumo dos testes com dados reais publicados (tela e prévia usam o mesmo quadro).

Os números vêm das execuções do motor (ensaio_cervejaria, ensaio_publico, ensaio_horario);
nada é digitado à mão.
"""

from diagnostico_publico import diagnosticos
from parecer_ensaio import parecer

from euler.economia import comparar_consumos
from euler.formato import num
from euler.tipos import Grandeza

AVISO = (
    "Nenhum destes dados é de cliente da EULER. Já há o histórico diário real de uma planta "
    "brasileira (660 dias, publicado no MDL da ONU), mas sem estoque medido, umidade da casca e "
    "água de alimentação: a validação completa ainda depende de uma planta piloto autorizada."
)


def linha_cervejaria(c: dict) -> dict:
    """Linha da planta brasileira (ensaio_cervejaria.executar())."""
    k = c["conferencia"]
    cmp = c["comparacao"]
    sinal = "menos" if cmp["variacao_pct"] < 0 else "mais"
    return {
        "Caso": "Planta brasileira · cervejaria, RS",
        "Dados": f"{k['dias']} dias reais de 2 caldeiras a casca de arroz (2007–2009)",
        "O que a EULER fez": "conferiu a planilha, comparou dois anos com incerteza (GUM) "
        "e listou as explicações",
        "Resultado": f"{num(abs(cmp['variacao_pct']), 1)}% {sinal} casca por t de vapor; "
        "não estabelecido (faltam estoque e incerteza do vapor)",
        "O que falta": "estoque nas datas de corte, umidade/PCI e água de alimentação",
    }


def linhas_resumo(r: dict, h: dict, c: dict | None = None) -> list[dict]:
    """Uma linha por caso público: dados, o que a EULER fez, resultado e o que falta.

    r: resultado de ensaio_publico.executar(); h: de ensaio_horario.executar();
    c: de ensaio_cervejaria.executar() (planta brasileira, primeira linha quando houver).
    """
    unidades = {}
    for un in ("B10", "B08", "B07", "B06"):
        u = h["unidades"][un]
        unidades[un] = (parecer(u, diagnosticos(h, un)), u)
    p10, u10 = unidades["B10"]
    meses = " e ".join(
        f"{'+' if m['delta_pct'] >= 0 else '−'}{num(abs(m['delta_pct']), 1)}%"
        for m in u10["comparacoes"]
    )
    situacao_b10 = "investigar" if p10["status"] == "investigar" else "sem aumento"
    sem = [un for un, (p, _) in unidades.items() if p["status"] != "investigar"]
    aumento = comparar_consumos(
        Grandeza(0.30, "t/t", "estimado"), Grandeza(0.35, "t/t", "estimado"), 1200.0, 26.53, "USD"
    )
    f = r["caso_financeiro"]
    maior = max(abs(e["delta_heos_pct"]) for e in r["estados"])
    return ([linha_cervejaria(c)] if c is not None else []) + [
        {
            "Caso": "Caldeiras EPA · EUA",
            "Dados": "registros horários de 4 caldeiras (2023)",
            "O que a EULER fez": "referência de janeiro ajustada à produção; fevereiro e março comparados",
            "Resultado": f"B10: energia {meses} em fevereiro e março ({situacao_b10}); "
            + ", ".join(sem)
            + ": sem aumento",
            "O que falta": "incerteza dos instrumentos, combustível efetivo e contrato",
        },
        {
            "Caso": "Biomassa · UTFPR (Brasil)",
            "Dados": "médias publicadas da seca e da chuva",
            "O que a EULER fez": "comparação de consumo e valorização",
            "Resultado": f"+{num(aumento['aumento_pct'], 1)}% de biomassa por t de vapor; "
            "a conta publicada foi reproduzida",
            "O que falta": "séries brutas e incertezas",
        },
        {
            "Caso": "Custo do vapor · Unisanta (Brasil)",
            "Dados": "médias de 2010 e 2011, gás natural",
            "O que a EULER fez": "custo do combustível por t de vapor",
            "Resultado": f"{num(f['reducao_pct'], 1)}% menor por t de vapor (calculado)",
            "O que falta": "registros brutos; duas mudanças no mesmo período",
        },
        {
            "Caso": "Caldeira a carvão · três cargas",
            "Dados": "médias operacionais publicadas (2026)",
            "O que a EULER fez": "15 estados de água e vapor conferidos com outra biblioteca",
            "Resultado": f"maior diferença {num(maior, 3)}%",
            "O que falta": "preços, incertezas e tipo de pressão",
        },
        {
            "Caso": "Série · Zhejiang (China)",
            "Dados": f"{num(r['zhejiang']['linhas'], 0)} leituras por minuto (2022)",
            "O que a EULER fez": "importação real com lacunas preservadas",
            "Resultado": f"{num(r['importacao']['linhas'], 0)} registros importados, sem preenchimento",
            "O que falta": "combustível, vazão e pressão confirmadas",
        },
    ]
