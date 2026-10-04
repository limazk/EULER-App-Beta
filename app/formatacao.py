"""Formatação dos resultados para as telas (sem Streamlit e sem contas novas).

Os números vêm prontos do motor (JSON da investigação, resumo de cada período); aqui só se
escolhe unidade, casas decimais e o selo de cada estado. Usado pelas telas e pela prévia
interativa (scripts/gerar_previa.py), para as duas mostrarem exatamente o mesmo texto.
"""

from euler.direto import balanco_direto
from euler.formato import num, pct
from euler.investigacao import indireto_periodo
from euler.periodos import periodos_entre_estoques, resumir_periodo
from euler.relatorio import mudou_detectavel
from euler.vapor import P_ATM_NIVEL_DO_MAR_BAR

STATUS = {
    "sustentada": ("Compatível com os dados (não comprovada)", "blue", ":material/check_circle:"),
    "oposta": ("Mudou no sentido contrário (compensou parte)", "violet", ":material/swap_vert:"),
    "possivel": ("Continua possível", "orange", ":material/help:"),
    "descartada": ("Enfraquecida nestes dados", "gray", ":material/cancel:"),
    "nao_avaliavel": ("Não dá para avaliar", "gray", ":material/block:"),
}

# Selo curto dos quatro estados da detecção (azul = mudou; laranja = só com uma condição;
# cinza = não mudou ou sem incerteza para dizer). No condicional, o selo vem seguido do texto
# do relatório (mudou_detectavel), que diz a condição. O selo não quebra linha: texto longo
# fica fora dele.
SELO_DETECCAO = {
    "sim": ("blue", "Sim"),
    "condicional": ("orange", "Condicional"),
    "nao": ("gray", "Não"),
    None: ("gray", "Sem incerteza para dizer"),
}


def partes_do_selo(c) -> tuple[str, str, str] | None:
    """(cor, selo curto, texto depois do selo) da detecção; None quando não há variação."""
    texto = mudou_detectavel(c)
    if texto == "—":
        return None
    cor, curto = SELO_DETECCAO[c["detectabilidade"]]
    if c["detectabilidade"] == "condicional":
        return cor, curto, texto
    if c["detectabilidade"] == "nao":
        return cor, curto, "diferença dentro da incerteza"
    return cor, curto, ""


def selo_deteccao(c) -> str:
    """Selo da detecção em Markdown do Streamlit (ex.: ":blue-badge[Sim]")."""
    partes = partes_do_selo(c)
    if partes is None:
        return "—"
    cor, curto, resto = partes
    return f":{cor}-badge[{curto}]" + (f" {resto}" if resto else "")


# Séries diárias que podem ir para o gráfico: coluna → (botão, título, unidade, formato).
SERIES = {
    "t_gases_c": ("Gases na chaminé", "Temperatura dos gases na chaminé", "°C", ".0f"),
    "o2_seco_pct": ("O₂", "O₂ nos gases (base seca)", "%", ".1f"),
    "co_ppm": ("CO", "CO nos gases", "ppm", ".0f"),
    "t_ar_c": ("Ar de combustão", "Temperatura do ar de combustão", "°C", ".1f"),
    "t_agua_alim_c": ("Água de alimentação", "Temperatura da água de alimentação", "°C", ".1f"),
}


def valor_formatado(v, unidade: str) -> str:
    if v is None:
        return "—"
    if unidade == "fração":
        return pct(v)
    casas = 3 if unidade == "MJ/kg" else 1
    return f"{num(v, casas)} {unidade}"


def diferenca(c) -> str:
    """Diferença comparação − referência, com a incerteza dela (os dois vêm do JSON)."""
    if c["variacao"] is None:
        return "—"
    unidade = c["unidade"]
    escala, rotulo, casas = 1.0, unidade, 1
    if unidade == "fração":
        escala, rotulo = 100.0, "p.p."
    elif unidade == "%":
        rotulo = "p.p."
    elif unidade == "% do PCI":
        rotulo = "p.p. do PCI"
    elif unidade == "MJ/kg":
        casas = 3
    v = escala * c["variacao"]
    texto = f"{'+' if v >= 0 else '−'}{num(abs(v), casas)} {rotulo}"
    if c["incerteza_variacao"] is not None:
        return f"{texto} (± {num(escala * c['incerteza_variacao'], casas)})"
    if c.get("faltam_na_incerteza"):
        return f"{texto} (incerteza incompleta)"
    return texto


def com_incerteza(valor: float, incerteza: float | None, fmt, orcamento=None) -> str:
    """Valor ± U; sem incerteza completa, diz isso (nunca mostra ± 0, auditoria A3)."""
    if incerteza is not None:
        return f"{fmt(valor)} ± {fmt(incerteza)}"
    if orcamento is not None and orcamento.faltam:
        return f"{fmt(valor)} (incerteza incompleta)"
    return fmt(valor)


def faixa_patio(cenarios: dict[str, float] | None) -> str:
    """Limites da eficiência pelos cenários do pátio (D38)."""
    if not cenarios or "minimo" not in cenarios or "maximo" not in cenarios:
        return "—"
    return f"{pct(cenarios['minimo'])} a {pct(cenarios['maximo'])}"


SITUACAO_PERIODO = {
    "Dá para concluir": "green",
    "Com limites": "orange",
    "Não dá para concluir": "red",
}
"""Situação de cada período na tabela resumida (D66) e a cor do selo."""

COLUNAS_RESUMO = ("Período", "Eficiência", "Consumo por t de vapor", "Situação")
"""Colunas da tabela resumida; as demais ficam em "ver detalhes" (D66)."""


def _curto(g, fmt) -> str:
    """Valor ± U quando a incerteza está completa; senão só o valor (a situação diz o resto)."""
    if g is None:
        return "✕"
    return fmt(g.valor) if g.incerteza is None else f"{fmt(g.valor)} ± {fmt(g.incerteza)}"


def _situacao(eficiencia, consumo, sem_perda_gases: bool) -> str:
    """Não dá: falta a eficiência ou o consumo. Com limites: falta a incerteza completa ou a
    perda nos gases (o motivo fica nos detalhes). Dá para concluir: tudo calculado."""
    if eficiencia is None or consumo is None:
        return "Não dá para concluir"
    if eficiencia.incerteza is None or consumo.incerteza is None or sem_perda_gases:
        return "Com limites"
    return "Dá para concluir"


def linhas_por_periodo(pacote) -> list[dict]:
    """Uma linha por período entre medições de estoque (tabela "Período a período").

    Cada linha traz as colunas da tabela resumida (`COLUNAS_RESUMO`) e as de detalhe.
    """
    p_gases = pacote.p_atm_bar or P_ATM_NIVEL_DO_MAR_BAR
    linhas = []
    for inicio, fim in periodos_entre_estoques(pacote):
        r = resumir_periodo(pacote, inicio, fim)
        b = balanco_direto(r)
        ind = indireto_periodo(r, p_gases)
        bloqueios = [x.motivo for x in b.bloqueios] + (
            [ind.bloqueio.motivo] if ind.bloqueio else []
        )
        consumo = b.consumo_t_por_t
        linhas.append(
            {
                "Período": f"{inicio:%d/%m} a {fim:%d/%m}",
                "Eficiência": _curto(b.eficiencia, pct),
                "Consumo por t de vapor": "✕"
                if consumo is None
                else f"{_curto(consumo, lambda v: num(v, 3))} t/t",
                "Situação": _situacao(b.eficiencia, consumo, ind.resultado is None),
                "Vapor (t)": "✕" if r.vapor_t is None else num(r.vapor_t.valor, 0),
                "Combustível (t)": "✕"
                if r.combustivel_kg is None
                else num(r.combustivel_kg.valor / 1000, 0),
                "Eficiência direta": "✕"
                if b.eficiencia is None
                else com_incerteza(
                    b.eficiencia.valor, b.eficiencia.incerteza, pct, b.eficiencia.orcamento
                ),
                "Estoque / consumido": "—"
                if r.fracao_estoque is None
                else pct(r.fracao_estoque, 0),
                "Eficiência conforme o pátio": faixa_patio(b.eficiencia_cenarios),
                "Perda nos gases": "✕"
                if ind.resultado is None
                else f"{num(ind.resultado.perda_pct, 1)}% do PCI",
                "Por que não dá": " ".join(dict.fromkeys(bloqueios)) or "—",
            }
        )
    return linhas


# Painel Saúde da caldeira (D65): selo geral e situação de cada período.
SELO_SAUDE = {
    "mudou": ("orange", "Mudou"),
    "estavel": ("green", "Estável"),
    "nao_da_para_dizer": ("gray", "Não dá para dizer"),
}
SITUACAO_SAUDE = {
    "referencia": "Referência",
    "mudou": "Mudou",
    "estavel": "Estável",
    "nao_da_para_dizer": "Não dá para dizer",
}
COR_SAUDE = {"referencia": "blue", "mudou": "orange", "estavel": "green"}


def texto_consumo(p) -> str:
    """Consumo de um período do painel Saúde: valor ± U (t/t), ou ✕ quando não há."""
    if p.consumo is None:
        return "✕"
    u = p.consumo.incerteza
    return num(p.consumo.valor, 3) + ("" if u is None else f" ± {num(u, 3)}")


def variacao_referencia(p) -> str:
    """Variação do consumo do período em relação à referência (%), ou — quando não há."""
    c = p.comparacao
    if c is None or not c.disponivel:
        return "—"
    v = 100 * c.delta / c.referencia
    return f"{'+' if v >= 0 else '−'}{num(abs(v), 1)}%"
