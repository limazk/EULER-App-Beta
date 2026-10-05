"""Planta brasileira real: 660 dias de duas caldeiras a casca de arroz (MDL, projeto 1202).

Fonte: planilha diária pública do Mecanismo de Desenvolvimento Limpo (UNFCCC) da cervejaria
AmBev em Viamão/RS, de 05/11/2007 a 25/08/2009 (validation/public/cervejaria_rs). Não é dado
de cliente e não implica participação da AmBev.

O que esta rota faz, com o motor da EULER:
1. confere a planilha (calendário, lacunas, totais, capacidade das caldeiras) sem preencher
   nada: célula vazia continua ausente;
2. confere a entalpia do vapor da planilha contra a IF97 (E8);
3. pergunta se a casca por tonelada de vapor mudou entre o mesmo trecho do calendário de
   dois anos e responde com o orçamento de incerteza (GUM) e `euler.deteccao.comparar`;
4. lista as explicações que continuam possíveis e a verificação que separa cada uma.

Hipóteses e limites (ver LEIA-ME da pasta e D99):
- A coluna diária de biomassa não é o queimado no dia: os documentos divergem sobre a origem
  (volume no galpão × densidade, no PDD; notas fiscais e balança, na verificação). Só somas
  longas são usadas, e chamadas de "consumo aparente" (casca registrada ÷ vapor).
- O estoque no início e no fim de cada período não foi publicado: entra como incerteza que
  falta (nunca zero). O mesmo para a incerteza dos medidores de vapor.
- A balança tem exatidão de 2% declarada pelo verificador, sem tipo: lida como limite ±a,
  u = a/√3 (D35). Cada calibração abre uma época; épocas iguais nos dois períodos são o mesmo
  erro (chave "instrumento:BALANCA@data", D37).
- Sem PCI, umidade e temperatura da água de alimentação, eficiência e energia útil ficam
  bloqueadas. Sem preço publicado da casca, não há valor em dinheiro.
"""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path

import numpy as np
import pandas as pd

from euler.deteccao import comparar
from euler.formato import num
from euler.incerteza import Componente, Falta, Orcamento, incerteza_padrao
from euler.tipos import Grandeza
from euler.vapor import h_agua_mj_kg, h_vapor_mj_kg

DADOS = Path(__file__).resolve().parents[1] / "validation/public/cervejaria_rs"
KGF_CM2_EM_BAR = 0.980665  # 1 kgf/cm² = 0,980665 bar (definição)
# A tabela de vapor da própria planilha põe 0 kgf/cm² a 99,09 °C: pressão referida a
# 1 kgf/cm² absoluto. A conferência usa essa convenção e mostra a sensibilidade a 1,01325 bar.
P_REFERENCIA_TABELA_BAR = KGF_CM2_EM_BAR
P_ATM_NIVEL_DO_MAR_BAR = 1.01325

# Mesmo trecho do calendário nos dois anos (dados de 05/11/2007 a 25/08/2009): o corte é
# simétrico e não depende dos resultados; cortes alternativos ficam em `sensibilidade`.
PERIODOS = {
    "1º período": ("2007-11-05", "2008-08-25"),
    "2º período": ("2008-11-05", "2009-08-25"),
}


@cache
def fontes() -> dict:
    """Metadados e fatos documentados (URLs, SHA-256, páginas) do caso."""
    return json.loads((DADOS / "fontes.json").read_text(encoding="utf-8"))


def carregar() -> pd.DataFrame:
    """Diário extraído da planilha pública, sem preencher nada (ausente ≠ zero)."""
    d = pd.read_csv(DADOS / "diario.csv", float_precision="round_trip")
    d["data"] = pd.to_datetime(d["data"], format="%Y-%m-%d")
    return d


def _vapor_dia(d: pd.DataFrame) -> pd.Series:
    """Vapor das duas caldeiras no dia; NaN se nenhuma das duas tem registro."""
    return d[["cald1_vapor_t", "cald2_vapor_t"]].sum(axis=1, min_count=1)


def _biomassa_dia(d: pd.DataFrame) -> pd.Series:
    """Casca registrada no dia (arroz + carvalho); NaN se as duas células estão vazias."""
    return d[["casca_arroz_t", "casca_carvalho_t"]].sum(axis=1, min_count=1)


def _datas(d: pd.DataFrame, filtro: pd.Series) -> list[str]:
    return [f"{x:%d/%m/%Y}" for x in d.loc[filtro, "data"]]


def conferir(d: pd.DataFrame) -> dict:
    """Conferência da planilha: calendário, lacunas, totais e registros impossíveis.

    Nada é corrigido: os achados são listados com as datas, para quem tem o registro
    original conferir.
    """
    f = fontes()["fatos_documentados"]
    cap = f["caldeiras"]["capacidade_t_h"]
    calendario = pd.date_range(d.data.min(), d.data.max())
    vapor = _vapor_dia(d)
    biomassa = _biomassa_dia(d)
    total_em_branco = d.vapor_total_t.isna() & vapor.notna()
    diverge = d.vapor_total_t.notna() & (d.vapor_total_t - vapor.fillna(0)).abs().gt(0.01)
    acima = []
    for n in (1, 2):
        horas, vap = d[f"cald{n}_horas"], d[f"cald{n}_vapor_t"]
        excesso = vap.gt(cap * horas) & horas.notna()
        for _, linha in d[excesso].iterrows():
            acima.append(
                {
                    "data": f"{linha.data:%d/%m/%Y}",
                    "caldeira": n,
                    "horas": float(linha[f"cald{n}_horas"]),
                    "vapor_t": float(linha[f"cald{n}_vapor_t"]),
                    "media_t_h": float(linha[f"cald{n}_vapor_t"] / linha[f"cald{n}_horas"]),
                    "pct_capacidade": float(
                        100 * linha[f"cald{n}_vapor_t"] / (cap * linha[f"cald{n}_horas"])
                    ),
                }
            )
    energia_em_branco = []
    for n in (1, 2):
        falta = (
            d[f"cald{n}_energia_tj"].isna()
            & d[f"cald{n}_vapor_t"].notna()
            & d[f"cald{n}_entalpia_tj_t"].gt(0)
        )
        energia_em_branco += [(n, x) for x in _datas(d, falta)]
    # vapor ÷ casca em janelas de 1, 7 e 30 dias (percentis 5, 50 e 95): a dispersão diária
    # mostra que a casca do dia não é a queimada no dia; só somas longas fazem sentido
    janelas = {1: (vapor / biomassa).where(biomassa.gt(0) & vapor.gt(0))}
    for dias in (7, 30):
        janelas[dias] = vapor.rolling(dias).sum() / biomassa.rolling(dias).sum()
    janelas = {k: [float(x) for x in r.quantile([0.05, 0.5, 0.95])] for k, r in janelas.items()}
    sem_vapor = d[vapor.isna()]
    totais = {
        "vapor_t": float(d.cald1_vapor_t.sum() + d.cald2_vapor_t.sum()),
        "biomassa_t": float(d.casca_arroz_t.sum() + d.casca_carvalho_t.sum()),
        "oleo_equivalente_t": float(d.oleo_equivalente_t.sum()),
        "vapor_coluna_total_t": float(d.vapor_total_t.sum()),
    }
    verificados = f["totais_verificados"]
    return {
        "dias": len(d),
        "inicio": f"{d.data.min():%d/%m/%Y}",
        "fim": f"{d.data.max():%d/%m/%Y}",
        "dias_fora_do_calendario": len(calendario.difference(d.data)),
        "datas_repetidas": int(d.data.duplicated().sum()),
        "celulas_vazias": {
            "casca de arroz": int(d.casca_arroz_t.isna().sum()),
            "vapor da caldeira 1": int(d.cald1_vapor_t.isna().sum()),
            "vapor da caldeira 2": int(d.cald2_vapor_t.isna().sum()),
            "pressão da caldeira 1": int(d.cald1_p_vapor_kgf_cm2.isna().sum()),
            "pressão da caldeira 2": int(d.cald2_p_vapor_kgf_cm2.isna().sum()),
        },
        "dias_sem_vapor_registrado": len(sem_vapor),
        "dias_sem_vapor_fim_de_semana": int(sem_vapor.data.dt.dayofweek.ge(5).sum()),
        "casca_nos_dias_sem_vapor_t": float(_biomassa_dia(sem_vapor).sum()),
        "dias_sem_biomassa_registrada": int(biomassa.isna().sum()),
        "total_diario_em_branco": _datas(d, total_em_branco),
        "vapor_dos_totais_em_branco_t": float(vapor[total_em_branco].sum()),
        "total_diario_diferente_da_soma": _datas(d, diverge),
        "energia_em_branco": energia_em_branco,
        "acima_da_capacidade": acima,
        "capacidade_t_h": cap,
        "razao_vapor_biomassa": janelas,
        "totais": totais,
        "totais_verificados": verificados,
        "confere_com_verificacao": {
            "vapor": round(totais["vapor_t"]) == verificados["vapor_t"],
            "biomassa": round(totais["biomassa_t"]) == verificados["biomassa_t"],
            "oleo_equivalente": round(totais["oleo_equivalente_t"])
            == verificados["oleo_equivalente_t"],
        },
    }


@cache
def _h_vapor_kj_kg(p_kgf_cm2: float, p_ref_bar: float) -> float:
    p_abs = p_kgf_cm2 * KGF_CM2_EM_BAR + p_ref_bar
    return 1000 * h_vapor_mj_kg(p_abs, "saturado_seco")


def entalpia(d: pd.DataFrame) -> dict:
    """Entalpia do vapor saturado da planilha × IF97 da EULER, dia a dia (E8).

    A planilha registra a entalpia total (desde 0 °C, em TJ/t) que tirou da sua tabela de
    vapor saturado. Comparamos com h_g(p) da IF97, com a pressão em kgf/cm² convertida em
    bar absoluto pela convenção da própria tabela (1 kgf/cm² abs) e, para sensibilidade,
    pela atmosfera ao nível do mar.
    """
    linhas = []
    for n in (1, 2):
        p, h = d[f"cald{n}_p_vapor_kgf_cm2"], d[f"cald{n}_entalpia_tj_t"]
        ok = p.gt(0) & h.gt(0)
        linhas += [(n, float(pp), 1e6 * float(hh)) for pp, hh in zip(p[ok], h[ok], strict=True)]
    resultado = {"dias_caldeira": len(linhas)}
    for nome, p_ref in (
        ("tabela", P_REFERENCIA_TABELA_BAR),
        ("nivel_do_mar", P_ATM_NIVEL_DO_MAR_BAR),
    ):
        rel = [100 * (h / _h_vapor_kj_kg(p, p_ref) - 1) for _, p, h in linhas]
        resultado[nome] = {"min_pct": float(min(rel)), "max_pct": float(max(rel))}
    p_med = float(np.median([p for _, p, _ in linhas]))
    p_abs = p_med * KGF_CM2_EM_BAR + P_REFERENCIA_TABELA_BAR
    hg = h_vapor_mj_kg(p_abs, "saturado_seco")
    # quanto a energia útil fica abaixo da energia da planilha por 10 °C de água de alimentação
    passo = h_agua_mj_kg(p_abs, 90.0) - h_agua_mj_kg(p_abs, 80.0)
    resultado.update(
        {
            "p_mediana_kgf_cm2": p_med,
            "h_g_kj_kg": float(1000 * hg),
            "pct_por_10c_de_agua": float(100 * passo / hg),
        }
    )
    return resultado


def _recorte(d: pd.DataFrame, inicio: str, fim: str) -> pd.DataFrame:
    return d[(d.data >= pd.Timestamp(inicio)) & (d.data <= pd.Timestamp(fim))]


def periodo(d: pd.DataFrame, inicio: str, fim: str) -> dict:
    """Somas de um período, só com dias registrados (dias sem registro são contados)."""
    x = _recorte(d, inicio, fim)
    vapor, biomassa = _vapor_dia(x), _biomassa_dia(x)
    v, m = float(vapor.sum()), float(biomassa.sum())
    return {
        "inicio": inicio,
        "fim": fim,
        "dias": len(x),
        "vapor_t": v,
        "biomassa_t": m,
        "carvalho_t": float(x.casca_carvalho_t.sum()),
        "oleo_equivalente_t": float(x.oleo_equivalente_t.sum()),
        "consumo_t_t": m / v,
        "vapor_por_biomassa": v / m,
        "carga_t_dia": v / len(x),
        "biomassa_t_dia": m / len(x),
        "dias_sem_vapor": int(vapor.isna().sum()),
        "dias_sem_biomassa": int(biomassa.isna().sum()),
    }


def epocas_balanca() -> list[tuple[str, str | None]]:
    """Épocas de calibração da balança: (início, calibração que a encerra)."""
    cal = fontes()["fatos_documentados"]["balanca"]["calibracoes"]
    inicios = [fontes()["projeto_mdl"]["periodo_monitorado"][0], *cal]
    return list(zip(inicios, [*cal, None], strict=True))


def orcamento(d: pd.DataFrame, inicio: str, fim: str) -> Orcamento:
    """Incerteza relativa do consumo aparente (casca ÷ vapor) de um período (GUM).

    Balança: 2% declarado sem tipo → limite, u = a/√3 (D35). O erro sistemático se repete
    dentro de uma época de calibração; a contribuição de cada época é proporcional à massa
    pesada nela (chave por época, D37). O que não foi publicado entra em `faltam`.
    """
    u_balanca = incerteza_padrao(fontes()["fatos_documentados"]["balanca"]["exatidao_pct"])[0]
    x = _recorte(d, inicio, fim)
    biomassa = _biomassa_dia(x)
    total = float(biomassa.sum())
    componentes = []
    for ini, fim_epoca in epocas_balanca():
        dentro = x.data >= pd.Timestamp(ini)
        if fim_epoca is not None:
            dentro &= x.data < pd.Timestamp(fim_epoca)
        massa = float(biomassa[dentro].sum())
        if massa > 0:
            componentes.append(
                Componente(
                    f"balança rodoviária (época iniciada em {pd.Timestamp(ini):%d/%m/%Y})",
                    massa / total * u_balanca / 100,
                    "instrumental",
                    f"instrumento:BALANCA@{ini}",
                    entrada="biomassa_t",
                )
            )
    return Orcamento(
        componentes,
        nao_incluidos=[
            "umidade e PCI da casca (sem amostras publicadas)",
            "origem da coluna diária de biomassa (o PDD e a verificação divergem)",
        ],
        faltam=[
            Falta("incerteza dos medidores de vapor (não declarada)", sistematica=True),
            Falta("variação do estoque de casca no início e no fim do período", sistematica=False),
        ],
    )


def comparar_periodos(d: pd.DataFrame) -> dict:
    """O consumo aparente mudou entre os dois períodos? Resposta pelo motor (E-deteccao)."""
    (na, (ia, fa)), (nb, (ib, fb)) = PERIODOS.items()
    a, b = periodo(d, ia, fa), periodo(d, ib, fb)
    oa, ob = orcamento(d, ia, fa), orcamento(d, ib, fb)
    ga = Grandeza(a["consumo_t_t"], "t/t", "estimado", None, "casca registrada ÷ vapor", oa)
    gb = Grandeza(b["consumo_t_t"], "t/t", "estimado", None, "casca registrada ÷ vapor", ob)
    c = comparar("Consumo aparente de casca", "t/t", ga, gb)
    # o que seria preciso para a diferença inteira vir de uma só fonte
    estoque_a = a["biomassa_t"] - b["consumo_t_t"] * a["vapor_t"]
    estoque_b = a["consumo_t_t"] * b["vapor_t"] - b["biomassa_t"]
    projeto = fontes()["fatos_documentados"]["exemplo_de_projeto_do_fabricante"]
    return {
        "nomes": (na, nb),
        "periodos": (a, b),
        "variacao_pct": 100 * (b["consumo_t_t"] / a["consumo_t_t"] - 1),
        "comparacao": c,
        "u_balanca_k2": c.incerteza_delta_correlacionada,
        "faltam": list(c.faltam),
        "nao_incluidos": list(dict.fromkeys(oa.nao_incluidos + ob.nao_incluidos)),
        "estoque_1o_periodo_t": estoque_a,
        "estoque_1o_periodo_dias": estoque_a / a["biomassa_t_dia"],
        "estoque_2o_periodo_t": estoque_b,
        "estoque_2o_periodo_dias": estoque_b / b["biomassa_t_dia"],
        "medidor_vapor_pct": 100 * (a["consumo_t_t"] / b["consumo_t_t"] - 1),
        "carga_pct": 100 * (b["carga_t_dia"] / a["carga_t_dia"] - 1),
        "carvalho_pct_1o": 100 * a["carvalho_t"] / a["biomassa_t"],
        "projeto_vapor_por_biomassa": projeto["vapor_kg_h"] / projeto["consumo_kg_h"],
    }


def _bloco(d: pd.DataFrame, inicio: str, fim_exclusivo: str | None, rotulo: str) -> dict:
    fim = (
        f"{d.data.max():%Y-%m-%d}"
        if fim_exclusivo is None
        else f"{pd.Timestamp(fim_exclusivo) - pd.Timedelta(days=1):%Y-%m-%d}"
    )
    p = periodo(d, inicio, fim)
    return {"rotulo": rotulo, **p}


def sensibilidade(d: pd.DataFrame) -> dict:
    """Outros cortes do mesmo registro: a conclusão não pode depender da escolha do período."""
    meio = d.data.iloc[len(d) // 2]
    metades = [
        _bloco(d, f"{d.data.min():%Y-%m-%d}", f"{meio:%Y-%m-%d}", "1ª metade"),
        _bloco(d, f"{meio:%Y-%m-%d}", None, "2ª metade"),
    ]
    balanca = [
        _bloco(d, ini, fim, f"de {pd.Timestamp(ini):%d/%m/%Y}") for ini, fim in epocas_balanca()
    ]
    cal_vapor = fontes()["fatos_documentados"]["medidores_de_vapor"]["calibracoes_vazao"]
    inicios = [f"{d.data.min():%Y-%m-%d}", *cal_vapor]
    vapor = [
        _bloco(d, ini, fim, f"de {pd.Timestamp(ini):%d/%m/%Y}")
        for ini, fim in zip(inicios, [*cal_vapor, None], strict=True)
    ]
    return {"metades": metades, "epocas_balanca": balanca, "epocas_medidor_vapor": vapor}


def mensal(d: pd.DataFrame) -> dict:
    """Série mensal (consumo aparente e carga) e a correlação descritiva entre as duas."""
    x = d.assign(vapor=_vapor_dia(d), biomassa=_biomassa_dia(d), mes=d.data.dt.to_period("M"))
    m = x.groupby("mes").agg(
        dias=("data", "size"), vapor_t=("vapor", "sum"), biomassa_t=("biomassa", "sum")
    )
    m["consumo_t_t"] = m.biomassa_t / m.vapor_t
    m["carga_t_dia"] = m.vapor_t / m.dias
    r = float(np.corrcoef(m.consumo_t_t, m.carga_t_dia)[0, 1])
    linhas = [
        {"mes": mes.strftime("%m/%Y"), **{k: float(v) for k, v in linha.items()}}
        for mes, linha in m.iterrows()
    ]
    return {"meses": linhas, "correlacao_consumo_carga": r, "n_meses": len(linhas)}


def _datas_br(datas: list[str]) -> str:
    textos = [pd.Timestamp(x).strftime("%d/%m/%Y") for x in datas]
    return ", ".join(textos[:-1]) + " e " + textos[-1] if len(textos) > 1 else textos[0]


def hipoteses(c: dict, m: dict) -> list[dict]:
    """Explicações que continuam possíveis e a verificação que separa cada uma.

    Nenhuma é declarada causa: os registros não têm as medições que as separariam.
    """
    a, b = c["periodos"]
    fd = fontes()["fatos_documentados"]
    cmp = c["comparacao"]
    balanca_explica = abs(cmp.delta) <= cmp.incerteza_delta_correlacionada
    return [
        {
            "titulo": "Estoque de casca diferente nas pontas dos períodos",
            "o_que_os_registros_mostram": (
                "Para a diferença inteira vir do estoque, o galpão precisaria ter ganhado "
                f"{num(c['estoque_1o_periodo_t'], 0)} t ao longo do 1º período "
                f"(≈ {num(c['estoque_1o_periodo_dias'], 0)} dias de consumo) ou perdido "
                f"{num(c['estoque_2o_periodo_t'], 0)} t ao longo do 2º "
                f"(≈ {num(c['estoque_2o_periodo_dias'], 0)} dias), ou uma combinação. O projeto "
                "descreve área de estoque para no mínimo 5 dias."
            ),
            "verificacao": (
                "Medir o estoque do galpão nas datas de corte (volume × densidade medida) ou "
                "obter o inventário mensal citado no PDD."
            ),
        },
        {
            "titulo": "Umidade ou poder calorífico da casca diferentes entre os anos",
            "o_que_os_registros_mostram": "Não há amostras de umidade nem de PCI publicadas.",
            "verificacao": (
                "Amostrar umidade (ISO 18134) e PCI (ISO 18125) por lote e por fornecedor "
                "nos dois períodos."
            ),
        },
        {
            "titulo": "Carga maior no 2º período",
            "o_que_os_registros_mostram": (
                f"O vapor médio foi de {num(a['carga_t_dia'], 0)} para "
                f"{num(b['carga_t_dia'], 0)} t/dia ({'+' if c['carga_pct'] >= 0 else '−'}"
                f"{num(abs(c['carga_pct']), 0)}%). Nos {m['n_meses']} meses, a correlação entre "
                f"carga e consumo aparente foi de {num(m['correlacao_consumo_carga'], 2)} "
                "(negativa: meses de carga maior, menos casca por tonelada). Compatível, não é prova."
            ),
            "verificacao": (
                "Comparar trechos de carga parecida com estoque medido nas pontas, ou ensaiar "
                "a caldeira em duas cargas."
            ),
        },
        {
            "titulo": "Medidores de vapor (calibrados em "
            + _datas_br(fd["medidores_de_vapor"]["calibracoes_vazao"][:1])
            + ")",
            "o_que_os_registros_mostram": (
                "Para explicar tudo, os medidores teriam de ler "
                f"{num(c['medidor_vapor_pct'], 1)}% a mais no 2º período. A incerteza deles "
                "não foi declarada."
            ),
            "verificacao": "Certificado da calibração com o erro encontrado antes do ajuste.",
        },
        {
            "titulo": "Balança (calibrada em " + _datas_br(fd["balanca"]["calibracoes"]) + ")",
            "o_que_os_registros_mostram": (
                f"Exatidão de {num(fd['balanca']['exatidao_pct'], 0)}% declarada pelo verificador: "
                f"incerteza da diferença de ±{num(cmp.incerteza_delta_correlacionada, 4)} t/t "
                "(k = 2), contra uma diferença de "
                f"{num(abs(cmp.delta), 4)} t/t. "
                + (
                    "Sozinha, a balança pode explicar a diferença."
                    if balanca_explica
                    else "Sozinha, a balança não explica a diferença."
                )
            ),
            "verificacao": "Certificados das calibrações com o erro encontrado antes do ajuste.",
        },
        {
            "titulo": "Casca de carvalho só no 1º período",
            "o_que_os_registros_mostram": (
                f"{num(c['carvalho_pct_1o'], 1)}% da massa do 1º período; o PCI dela não foi "
                "publicado."
            ),
            "verificacao": "PCI da casca de carvalho.",
        },
    ]


def conclusao(c: dict) -> str:
    """Frase principal: o que os registros sustentam e o que não sustentam (abstenção)."""
    cmp = c["comparacao"]
    sentido = "menos" if c["variacao_pct"] < 0 else "mais"
    inicio = (
        f"Os registros mostram {num(abs(c['variacao_pct']), 1)}% {sentido} casca por tonelada "
        "de vapor no 2º período."
    )
    if cmp.detectabilidade == "sim":
        return inicio + " A diferença está estabelecida pela incerteza declarada."
    if cmp.detectabilidade == "nao":
        return inicio + " A diferença cabe na incerteza conhecida: não há mudança a investigar."
    return (
        inicio + " Isso não basta para dizer que a caldeira mudou de consumo: o estoque nas "
        "pontas dos períodos não foi publicado, os medidores de vapor não têm incerteza "
        "declarada e não há umidade nem PCI da casca. A diferença é maior que a parte conhecida "
        "da incerteza (a balança), então vale investigar; a medição que mais separa as "
        "explicações é o estoque do galpão nas datas de corte."
    )


def executar() -> dict:
    """Roda o caso inteiro e devolve tudo o que a tela e a prévia mostram."""
    d = carregar()
    c = comparar_periodos(d)
    s = sensibilidade(d)
    m = mensal(d)
    return {
        "fonte": fontes(),
        "conferencia": conferir(d),
        "entalpia": entalpia(d),
        "comparacao": c,
        "sensibilidade": s,
        "mensal": m,
        "hipoteses": hipoteses(c, m),
        "conclusao": conclusao(c),
        "bloqueado": [
            (
                "Eficiência da caldeira: faltam PCI e umidade da casca e a temperatura da água "
                "de alimentação."
            ),
            "Combustível queimado por período: falta o estoque medido no início e no fim.",
            "Valor em dinheiro: não há preço da casca publicado.",
        ],
    }
