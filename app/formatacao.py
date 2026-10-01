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
    "descartada": ("Descartada pelos dados", "gray", ":material/cancel:"),
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


def selo_deteccao(c) -> str:
    texto = mudou_detectavel(c)
    if texto == "—":
        return texto
    cor, curto = SELO_DETECCAO[c["detectabilidade"]]
    if c["detectabilidade"] == "condicional":
        return f":{cor}-badge[{curto}] {texto}"
    if c["detectabilidade"] == "nao":
        return f":{cor}-badge[{curto}] variação normal"
    return f":{cor}-badge[{curto}]"


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


def linhas_por_periodo(pacote) -> list[dict]:
    """Uma linha por período entre medições de estoque (tabela "Período a período")."""
    p_gases = pacote.p_atm_bar or P_ATM_NIVEL_DO_MAR_BAR
    linhas = []
    for inicio, fim in periodos_entre_estoques(pacote):
        r = resumir_periodo(pacote, inicio, fim)
        b = balanco_direto(r)
        ind = indireto_periodo(r, p_gases)
        bloqueios = [x.motivo for x in b.bloqueios] + (
            [ind.bloqueio.motivo] if ind.bloqueio else []
        )
        linhas.append(
            {
                "Período": f"{inicio:%d/%m} a {fim:%d/%m}",
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
