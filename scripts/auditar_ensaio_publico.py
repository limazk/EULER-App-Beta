"""Audita o mesmo recorte público, sem rede; exporta JSON, CSV e relatório legível.

Uso: python scripts/auditar_ensaio_publico.py --saida output/auditoria-publica
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "app")]
from robustez_ensaio import auditar


def relatorio(r):
    linhas = [
        "# EULER — auditoria de robustez do ensaio público",
        "03/10/2026 · Mesmo recorte EPA/PUDL · Ingredion Argo · Janeiro a março de 2023",
        "## O que foi testado",
        (
            "Reprodução da conta original, comparação de métodos nas mesmas horas, mudança da "
            "referência, teste cronológico dentro de janeiro, influência de dias isolados e "
            "reamostragem em blocos de dias. Nenhum registro novo ou sintético foi usado como "
            "evidência. Reamostragens reutilizam os registros reais; não são medições novas."
        ),
        (
            "A B10 já havia sido selecionada após triagem. Este aprofundamento é retrospectivo. "
            "Não foi escolhido o método que fornece maior valor. Todas as unidades são publicadas."
        ),
        "## Resultados por unidade e período",
        "|Unidade / mês|Original (%)|Modelos, mesmas horas (%)|Referências alternativas (%)|Horas comuns dos modelos|",
        "|---|---:|---:|---:|---:|",
    ]

    def fmt(x):
        return "indisponível" if x is None else f"{x:.3f}".replace(".", ",")

    def faixa(itens):
        vals = [x["delta_pct"] for x in itens if x["delta_pct"] is not None]
        return "indisponível" if not vals else f"{fmt(min(vals))} a {fmt(max(vals))}"

    for nome, u in r["unidades"].items():
        for m in u["meses"]:
            linhas.append(
                f"|{nome} / {m['mes']}|{fmt(m['delta_original_pct'])}|"
                f"{faixa(m['modelos']['metodos'])}|{faixa(m['referencias']['metodos'])}|"
                f"{m['modelos']['horas_comuns']}|"
            )
    linhas += [
        (
            "As faixas de métodos e referências são sensibilidades, não intervalos de confiança. "
            "Cada comparação de métodos usa uma população comum; as demais análises podem "
            "cobrir populações diferentes, identificadas no JSON."
        )
    ]
    for nome, u in r["unidades"].items():
        linhas += [f"## {nome}: estabilidade da referência e dependência temporal"]
        for v in u["diagnostico"]["validacao_temporal"]:
            linhas.append(
                f"- Treino até {v['treino_fim']}; teste {v['teste_inicio']} a {v['teste_fim']}: "
                f"{v['horas_comparaveis']}/{v['horas_teste']} horas; viés {fmt(v['vies_pct'])}%. "
                f"Erro absoluto médio: {fmt(v['erro_absoluto_medio_gj_h'])} GJ/h."
            )
        linhas.append(
            "Esses trechos não têm regime estável certificado. Viés revela mudança ou "
            "inadequação do modelo, sem separar as duas explicações."
        )
        for lag, v in u["diagnostico"]["autocorrelacao_residuos"].items():
            linhas.append(
                f"- Correlação dos resíduos separados por {lag} h: {fmt(v['correlacao'])} "
                f"({v['pares']} pares separados exatamente pelo intervalo indicado; "
                "não se exige observação nas horas intermediárias)."
            )
        for m in u["meses"]:
            linhas.append(f"### {m['mes']}")
            for b in m["reamostragem"]:
                linhas.append(
                    f"- Blocos de {b['bloco_dias']} dias: percentis 2,5–97,5 "
                    f"de {fmt(b['quantil_025_pct'])}% a {fmt(b['quantil_975_pct'])}%; "
                    f"{b['validas']}/{r['repeticoes']} repetições válidas."
                )
            v = m["retirada_de_um_dia_pct"]
            linhas.append(f"- Retirar um dia da comparação: {fmt(v['min'])}% a {fmt(v['max'])}%.")
            linhas.append(
                f"- Redução da energia reportada que zeraria o desvio, mantendo a referência: "
                f"{fmt(m['reducao_energia_reportada_para_zerar_pct'])}%. "
                "Se negativo, seria necessário aumentar a energia reportada. "
                "É uma sensibilidade algébrica, não erro de medição identificado."
            )
    linhas += [
        "## Interpretação e aplicação",
        (
            "Os percentis são faixas condicionais de reamostragem, não orçamento de incerteza "
            "instrumental. Dependência superior ao bloco e mudança persistente de regime continuam "
            "possíveis. Não há p-valor confirmatório nem probabilidade de causa. Janeiro não é "
            "operação ideal certificada. Não se conclui saúde da caldeira por R² ou pelo sinal isolado."
        ),
        (
            "A conta financeira original é preservada. Preço médio industrial regional EIA, "
            "poder calorífico regional e uso integral de gás são condições da valorização. "
            "A B10 também registra carvão secundário, sem participação horária conhecida. "
            "Não é fatura, prejuízo comprovado ou dinheiro recuperável. Desvios negativos não são "
            "descartados nem as parcelas positivas são chamadas de perda líquida da planta."
        ),
        (
            "A ação sustentada é conferir medições, condições da água/vapor e combustível. "
            "Intervenção exige avaliação técnica. Revisão independente deste protocolo permanece pendente."
        ),
        "## Como reproduzir e conferir",
        (
            "Executar `python scripts/auditar_ensaio_publico.py --saida output/auditoria-publica` "
            "no ambiente do projeto. O CSV conserva as 8.034 linhas originais e acrescenta decisão "
            "e cálculo por hora. Campos vazios em linhas excluídas não significam zero. "
            "O manifesto confere os arquivos produzidos; o JSON identifica dados e código."
        ),
        (
            f"SHA-256 do recorte: `{r['fonte_sha256']}`. Semente: {r['semente']}. "
            f"Repetições por mês, unidade e tamanho de bloco: {r['repeticoes']}."
        ),
        "## Fontes",
        "- EPA/PUDL: https://zenodo.org/records/21738530",
        "- EIA preços: https://www.eia.gov/dnav/ng/hist/n3035il3m.htm",
        "- EIA calor: https://www.eia.gov/dnav/ng/NG_CONS_HEAT_DCU_SIL_A.htm",
        "- NIST diagnóstico: https://www.itl.nist.gov/div898/handbook/pmd/section4/pmd44.htm",
        "- Avaliação temporal: https://otexts.com/fpp3/tscv.html",
        "- Dependência e blocos: https://otexts.com/fpp3/bootstrap.html",
    ]
    # Markdown exige linhas de tabela adjacentes, sem parágrafos intermediários.
    texto = ""
    anterior = ""
    for linha in linhas:
        texto += ("\n" if linha.startswith("|") and anterior.startswith("|") else "\n\n") + linha
        anterior = linha
    return texto.lstrip()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, required=True)
    parser.add_argument(
        "--atualizar-app",
        action="store_true",
        help="Atualiza a auditoria distribuída na tela local.",
    )
    args = parser.parse_args()
    args.saida.mkdir(parents=True, exist_ok=True)
    r, linhas = auditar()
    (args.saida / "auditoria_robustez.json").write_text(
        json.dumps(r, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8"
    )
    linhas.to_csv(args.saida / "trilha_por_hora.csv", index=False)
    (args.saida / "RELATORIO.md").write_text(relatorio(r), encoding="utf-8")
    manifesto = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(args.saida.iterdir())
        if p.name in {"auditoria_robustez.json", "trilha_por_hora.csv", "RELATORIO.md"}
    }
    (args.saida / "manifesto.json").write_text(json.dumps(manifesto, indent=2), encoding="utf-8")
    if args.atualizar_app:
        destino = ROOT / "validation/public/ensaio_horario"
        (destino / "auditoria_robustez.json").write_bytes(
            (args.saida / "auditoria_robustez.json").read_bytes()
        )
        (destino / "ROBUSTEZ.md").write_bytes((args.saida / "RELATORIO.md").read_bytes())
    for nome, u in r["unidades"].items():
        print(nome, json.dumps(u, ensure_ascii=False))
