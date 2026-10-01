"""Motor de investigação: regras → JSON de investigação (T13; E12, E14, E15).

Pergunta: "O consumo de combustível mudou. O que os registros sustentam, quais
explicações continuam possíveis e qual verificação separa essas explicações?"

Compara um período de **referência** com um de **comparação** (cada um entre duas
medições de estoque) e devolve um dicionário serializável em JSON com:

- `o_que_mudou`: consumo específico, custo do vapor e indicadores, com incerteza;
- `hipoteses`: cada explicação com status `sustentada`, `possivel`, `descartada`
  ou `nao_avaliavel`, o porquê, o efeito estimado e a verificação que a testa;
- `independencia` (E12): o que os caminhos direto e indireto compartilham;
- `o_que_falta`, `proxima_verificacao` e `conclusao` (com abstenção explícita);
- `valor_em_jogo`: só preenchido quando há base nos dados; senão `null` com motivo.

Formato proposto (D28): a seção 7 da spec v0.3 não estava disponível.
O texto nunca traz comando operacional: só verificações (AGENTS.md, regra 1).
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isnan, log, sqrt

import pandas as pd

from euler import __version__
from euler.deteccao import Comparacao, comparar
from euler.direto import MEDICOES_DIRETO, BalancoDireto, balanco_direto
from euler.formato import num, pct
from euler.indireto import ResultadoPerdaGases, perda_gases
from euler.io import Pacote
from euler.periodos import ResumoPeriodo, resumir_periodo
from euler.tipos import AnaliseBloqueada, Grandeza
from euler.vapor import P_ATM_NIVEL_DO_MAR_BAR, delta_h_mj_kg

MEDICOES_INDIRETO = (
    "temperatura dos gases",
    "O₂ nos gases",
    "temperatura do ar",
    "umidade das amostras",
    "PCI seco das amostras",
    "composição elementar",
)
STATUS = ("sustentada", "possivel", "descartada", "nao_avaliavel")


# ---------------------------------------------------------------- caminho indireto


@dataclass
class Indireto:
    """Perda nos gases de um período, com incerteza de primeira ordem (E15)."""

    resultado: ResultadoPerdaGases | None
    incerteza_pp: float | None
    entradas: dict[str, float]
    bloqueio: AnaliseBloqueada | None = None


def _entradas_indireto(r: ResumoPeriodo) -> dict[str, float] | AnaliseBloqueada:
    faltas = []
    for chave, nome in (
        ("t_gases_c", "temperatura dos gases"),
        ("o2_seco_pct", "O₂ nos gases"),
        ("t_ar_c", "temperatura do ar de combustão"),
    ):
        if chave not in r.leituras:
            faltas.append(nome)
    if r.umidade_mistura is None:
        faltas.append("umidade medida dos lotes")
    if r.composicao is None or r.pci_seco_mistura is None:
        faltas.append("análise elementar e PCI seco do combustível")
    if faltas:
        return AnaliseBloqueada(
            "Perda nos gases não calculada: falta " + ", ".join(faltas) + ".", faltas
        )
    return {
        "t_gases_c": r.leituras["t_gases_c"].media,
        "o2_seco_pct": r.leituras["o2_seco_pct"].media,
        "umidade_bu_frac": r.umidade_mistura.valor,
        "t_ar_c": r.leituras["t_ar_c"].media,
    }


def _perda(r: ResumoPeriodo, entradas: dict[str, float], p_gases: float) -> ResultadoPerdaGases:
    return perda_gases(
        composicao_seca=r.composicao,
        pci_seco_mj_kg=r.pci_seco_mistura,
        p_gases_bar_abs=p_gases,
        **entradas,
    )


def indireto_periodo(r: ResumoPeriodo, p_gases: float) -> Indireto:
    """Perda nos gases com as médias do período e incerteza por derivadas parciais."""
    entradas = _entradas_indireto(r)
    if isinstance(entradas, AnaliseBloqueada):
        return Indireto(None, None, {}, entradas)
    try:
        res = _perda(r, entradas, p_gases)
    except AnaliseBloqueada as b:
        return Indireto(None, None, entradas, b)
    incertezas = {
        "t_gases_c": r.leituras["t_gases_c"].incerteza,
        "o2_seco_pct": r.leituras["o2_seco_pct"].incerteza,
        "t_ar_c": r.leituras["t_ar_c"].incerteza,
        "umidade_bu_frac": r.umidade_mistura.incerteza,
    }
    soma = 0.0
    for chave, u in incertezas.items():
        if u is None:
            return Indireto(res, None, entradas)
        passo = {"t_gases_c": 1.0, "o2_seco_pct": 0.1, "t_ar_c": 1.0, "umidade_bu_frac": 0.005}[
            chave
        ]
        try:
            mais = _perda(r, {**entradas, chave: entradas[chave] + passo}, p_gases).perda_pct
        except AnaliseBloqueada:
            return Indireto(res, None, entradas)
        soma += ((mais - res.perda_pct) / passo * u) ** 2
    return Indireto(res, sqrt(soma), entradas)


def _efeito_isolado(
    ref: ResumoPeriodo, ind_ref: Indireto, ind_comp: Indireto, chave: str, p_gases: float
) -> float | None:
    """Mudança na perda (p.p.) trocando só uma entrada da referência pela da comparação."""
    if ind_ref.resultado is None or chave not in ind_comp.entradas:
        return None
    try:
        trocada = _perda(ref, {**ind_ref.entradas, chave: ind_comp.entradas[chave]}, p_gases)
    except AnaliseBloqueada:
        return None
    return trocada.perda_pct - ind_ref.resultado.perda_pct


# ---------------------------------------------------------------- utilidades de texto


def _subiu(delta: float) -> str:
    return "subiu" if delta > 0 else "caiu"


def _sinal(x: float, casas: int = 1) -> str:
    x = round(float(x), casas) + 0.0  # evita "-0,0"
    return ("+" if x >= 0 else "") + num(x, casas)


def _limpar(obj):
    """Converte tipos do numpy e NaN em tipos simples, para o JSON."""
    if isinstance(obj, dict):
        return {k: _limpar(v) for k, v in obj.items()}
    if isinstance(obj, list | tuple):
        return [_limpar(v) for v in obj]
    if hasattr(obj, "item") and not isinstance(obj, str):
        obj = obj.item()
    if isinstance(obj, float) and isnan(obj):
        return None
    return obj


def _grandeza_json(g: Grandeza | None) -> dict | None:
    if g is None:
        return None
    return {
        "valor": g.valor,
        "unidade": g.unidade,
        "origem": g.origem,
        "incerteza": g.incerteza,
        "nota": g.nota,
    }


def _comparacao_json(c: Comparacao) -> dict:
    return {
        "nome": c.nome,
        "unidade": c.unidade,
        "referencia": c.referencia,
        "comparacao": c.comparacao,
        "variacao": c.delta,
        "incerteza_variacao": c.incerteza_delta,
        "detectavel": c.detectavel,
    }


def _delta_h_comparacao(r: ResumoPeriodo, b: BalancoDireto) -> Grandeza | None:
    """Δh do período com incerteza propagada de pressão e água de alimentação."""
    if b.delta_h_mj_kg is None:
        return None
    p, t = r.leituras["p_vapor_bar_abs"], r.leituras["t_agua_alim_c"]
    if p.incerteza is None or t.incerteza is None:
        return Grandeza(b.delta_h_mj_kg.valor, "MJ/kg", "estimado")
    base = b.delta_h_mj_kg.valor
    try:
        d_p = delta_h_mj_kg(p.media + 0.1, "saturado_seco", t.media) - base
        d_t = delta_h_mj_kg(p.media, "saturado_seco", t.media + 1) - base
    except AnaliseBloqueada:
        return Grandeza(base, "MJ/kg", "estimado")
    u = sqrt((d_p / 0.1 * p.incerteza) ** 2 + (d_t * t.incerteza) ** 2)
    return Grandeza(base, "MJ/kg", "estimado", u)


def _custo_vapor(r: ResumoPeriodo, b: BalancoDireto) -> Grandeza | None:
    """Custo do combustível por tonelada de vapor: R$/GJ × GJ/t (E14)."""
    if r.preco_brl_gj is None or b.intensidade_gj_por_t is None:
        return None
    i = b.intensidade_gj_por_t
    valor = r.preco_brl_gj * i.valor
    u = None if i.incerteza is None else r.preco_brl_gj * i.incerteza
    return Grandeza(valor, "R$/t de vapor", "estimado", u, "preço da energia × intensidade")


# ---------------------------------------------------------------- hipóteses


def _status_fator(
    c: Comparacao,
    sentido_consumo: int | None,
    efeito_consumo: float | None,
    efeito_minimo_pct: float | None,
) -> str:
    """Regra comum (D29): um fator só sustenta a explicação se
    1. mudou de forma detectável (maior que a variação normal);
    2. o efeito esperado no consumo é pelo menos metade da menor mudança de consumo
       que os dados conseguem detectar (senão, não apareceria no consumo);
    3. empurra o consumo no mesmo sentido da mudança observada (quando conhecida)."""
    if not c.disponivel:
        return "nao_avaliavel"
    if c.detectavel is False:
        return "descartada"
    if c.detectavel is None:
        return "possivel"
    if (
        efeito_minimo_pct is not None
        and efeito_consumo is not None
        and abs(efeito_consumo) < efeito_minimo_pct
    ):
        return "descartada"
    if sentido_consumo and efeito_consumo is not None and efeito_consumo * sentido_consumo < 0:
        return "descartada"
    return "sustentada"


def _hipotese(
    id_: str,
    titulo: str,
    status: str,
    porque: str,
    verificacao: str,
    medicoes: tuple[str, ...] | list[str],
    efeito_perda_pp: float | None = None,
    efeito_consumo_pct: float | None = None,
) -> dict:
    assert status in STATUS
    return {
        "id": id_,
        "titulo": titulo,
        "status": status,
        "porque": porque,
        "efeito": {"perda_gases_pp": efeito_perda_pp, "consumo_pct": efeito_consumo_pct},
        "medicoes": list(medicoes),
        "verificacao": verificacao,
    }


def _porque_fator(c: Comparacao, nome: str, unidade_txt: str, casas: int, fmt=num) -> str:
    """Frase sobre a mudança de um fator. `nome` já vem com artigo ("a temperatura dos gases")."""
    inicio = nome[0].upper() + nome[1:]
    if not c.disponivel:
        return f"Faltam leituras para comparar {nome} nos dois períodos."
    if fmt is pct:
        variacao = f"{pct(c.referencia)} → {pct(c.comparacao)}"
        faixa = None if c.incerteza_delta is None else pct(c.incerteza_delta)
    else:
        variacao = f"{num(c.referencia, casas)} → {num(c.comparacao, casas)} {unidade_txt}".strip()
        faixa = (
            None
            if c.incerteza_delta is None
            else f"{num(c.incerteza_delta, casas)} {unidade_txt}".strip()
        )
    if c.detectavel is False:
        return f"{inicio} ficou estável ({variacao}): a diferença está dentro da variação normal (±{faixa})."
    if c.detectavel is None:
        return f"{inicio} variou ({variacao}), mas há poucos dados para saber se é mais que a variação normal."
    return f"{inicio} {_subiu(c.delta)} de forma detectável ({variacao})."


def investigar(
    pacote: Pacote,
    referencia: tuple[pd.Timestamp, pd.Timestamp],
    comparacao: tuple[pd.Timestamp, pd.Timestamp],
) -> dict:
    """Compara dois períodos e devolve o JSON de investigação (ver docstring do módulo)."""
    ref, comp = resumir_periodo(pacote, *referencia), resumir_periodo(pacote, *comparacao)
    b_ref, b_comp = balanco_direto(ref), balanco_direto(comp)
    p_gases = pacote.p_atm_bar or P_ATM_NIVEL_DO_MAR_BAR
    i_ref, i_comp = indireto_periodo(ref, p_gases), indireto_periodo(comp, p_gases)

    def leitura(chave: str, nome: str, unidade: str) -> Comparacao:
        return comparar(nome, unidade, ref.leituras.get(chave), comp.leituras.get(chave))

    c_tg = leitura("t_gases_c", "temperatura dos gases", "°C")
    c_o2 = leitura("o2_seco_pct", "O₂ nos gases", "%")
    c_co = leitura("co_ppm", "CO nos gases", "ppm")
    c_w = comparar("umidade do combustível", "fração", ref.umidade_mistura, comp.umidade_mistura)
    c_dh = comparar(
        "energia por kg de vapor",
        "MJ/kg",
        _delta_h_comparacao(ref, b_ref),
        _delta_h_comparacao(comp, b_comp),
    )
    c_cons = comparar("consumo específico", "t/t", b_ref.consumo_t_por_t, b_comp.consumo_t_por_t)
    c_eta = comparar("eficiência direta", "fração", b_ref.eficiencia, b_comp.eficiencia)
    c_custo = comparar(
        "custo do vapor", "R$/t", _custo_vapor(ref, b_ref), _custo_vapor(comp, b_comp)
    )
    c_perda = comparar(
        "perda nos gases",
        "% do PCI",
        None
        if i_ref.resultado is None
        else Grandeza(i_ref.resultado.perda_pct, "%", "estimado", i_ref.incerteza_pp),
        None
        if i_comp.resultado is None
        else Grandeza(i_comp.resultado.perda_pct, "%", "estimado", i_comp.incerteza_pp),
    )

    # ------------------------------------------------ o que mudou: consumo
    sentido = None
    if c_cons.disponivel:
        variacao_pct = c_cons.delta / c_cons.referencia
        faixa = (
            f" (incerteza ±{pct(c_cons.incerteza_delta / c_cons.referencia)})"
            if c_cons.incerteza_delta is not None
            else ""
        )
        de_para = (
            f"de {num(c_cons.referencia, 3)} para {num(c_cons.comparacao, 3)} t por t de vapor"
        )
        if c_cons.detectavel:
            sentido = 1 if c_cons.delta > 0 else -1
            frase_consumo = (
                f"O consumo de combustível por tonelada de vapor {_subiu(c_cons.delta)} "
                f"{pct(abs(variacao_pct))} ({de_para}){faixa}."
            )
        elif c_cons.detectavel is False:
            frase_consumo = (
                f"O consumo por tonelada de vapor variou {_sinal(100 * variacao_pct)}% ({de_para}), "
                f"dentro da incerteza das medições{faixa}: não dá para afirmar que mudou."
            )
        else:
            frase_consumo = (
                f"O consumo por tonelada de vapor variou {_sinal(100 * variacao_pct)}% ({de_para}); "
                "sem incerteza declarada dos instrumentos, não dá para dizer se é mais que o erro "
                "de medição."
            )
    else:
        motivos = [b.motivo for b in (*b_ref.bloqueios, *b_comp.bloqueios)]
        frase_consumo = "Não dá para saber se o consumo por tonelada de vapor mudou: " + " ".join(
            dict.fromkeys(motivos)
        )

    # ------------------------------------------------ efeitos de cada fator
    eta_ref = (
        b_ref.eficiencia.valor
        if b_ref.eficiencia is not None
        else (None if i_ref.resultado is None else 1 - i_ref.resultado.perda_pct / 100)
    )

    def efeito_consumo_por_perda(dp: float | None) -> float | None:
        return None if dp is None or eta_ref is None else 100 * dp / 100 / eta_ref

    ef_tg = _efeito_isolado(ref, i_ref, i_comp, "t_gases_c", p_gases)
    ef_o2 = _efeito_isolado(ref, i_ref, i_comp, "o2_seco_pct", p_gases)
    ef_w_perda = _efeito_isolado(ref, i_ref, i_comp, "umidade_bu_frac", p_gases)
    ef_w_pci = None
    if ref.pci_umido_mistura is not None and comp.pci_umido_mistura is not None:
        ef_w_pci = -100 * log(comp.pci_umido_mistura.valor / ref.pci_umido_mistura.valor)
    ef_w = None
    if ef_w_pci is not None:
        ef_w = ef_w_pci + (efeito_consumo_por_perda(ef_w_perda) or 0)
    ef_dh = None if not c_dh.disponivel else 100 * log(c_dh.comparacao / c_dh.referencia)

    # menor efeito relevante (D29): metade da menor mudança de consumo detectável
    efeito_minimo = None
    if c_cons.incerteza_delta is not None:
        efeito_minimo = 50 * c_cons.incerteza_delta / c_cons.referencia
    elif c_perda.incerteza_delta is not None and eta_ref:
        efeito_minimo = 0.5 * c_perda.incerteza_delta / eta_ref

    def pequeno_demais(efeito: float | None) -> str:
        if efeito_minimo is None or efeito is None or abs(efeito) >= efeito_minimo:
            return ""
        return (
            f" O efeito esperado no consumo ({_sinal(efeito, 2)}%) é pequeno demais para aparecer "
            f"nos dados (menor mudança detectável ≈ {num(2 * efeito_minimo)}%)."
        )

    hipoteses = []
    # temperatura dos gases
    st_tg = _status_fator(c_tg, sentido, efeito_consumo_por_perda(ef_tg), efeito_minimo)
    porque = _porque_fator(c_tg, "a temperatura dos gases", "°C", 1)
    porque += pequeno_demais(efeito_consumo_por_perda(ef_tg)) if c_tg.detectavel else ""
    if st_tg == "sustentada" and ef_tg is not None:
        porque += f" Só isso muda a perda nos gases em {_sinal(ef_tg)} p.p. do PCI."
    hipoteses.append(
        _hipotese(
            "temperatura_gases",
            "Mais calor saindo pela chaminé (temperatura dos gases)",
            st_tg,
            porque,
            "Comparar a leitura do termopar da chaminé com um termômetro de referência. Se a "
            "leitura se confirmar, inspecionar as superfícies de troca (fuligem ou incrustação) "
            "na próxima parada programada.",
            ("temperatura dos gases",),
            ef_tg,
            efeito_consumo_por_perda(ef_tg),
        )
    )
    # excesso de ar
    st_o2 = _status_fator(c_o2, sentido, efeito_consumo_por_perda(ef_o2), efeito_minimo)
    porque = _porque_fator(c_o2, "o O₂ nos gases", "%", 1)
    porque += pequeno_demais(efeito_consumo_por_perda(ef_o2)) if c_o2.detectavel else ""
    if st_o2 == "sustentada" and ef_o2 is not None:
        porque += f" Só isso muda a perda nos gases em {_sinal(ef_o2)} p.p. do PCI."
    hipoteses.append(
        _hipotese(
            "excesso_ar",
            "Excesso de ar diferente (O₂ nos gases)",
            st_o2,
            porque,
            "Conferir a calibração do analisador de O₂ e comparar com uma medição portátil no "
            "mesmo ponto.",
            ("O₂ nos gases",),
            ef_o2,
            efeito_consumo_por_perda(ef_o2),
        )
    )
    # umidade do combustível
    st_w = _status_fator(c_w, sentido, ef_w, efeito_minimo)
    porque = _porque_fator(c_w, "a umidade do combustível recebido", "", 3, fmt=pct)
    porque += pequeno_demais(ef_w) if c_w.detectavel else ""
    forn_maior = None
    if c_w.disponivel:
        mudancas = {
            f: comp.umidade_por_fornecedor[f] - ref.umidade_por_fornecedor[f]
            for f in comp.umidade_por_fornecedor
            if f in ref.umidade_por_fornecedor
        }
        if mudancas:
            forn_maior = max(mudancas, key=mudancas.get)
            if st_w == "sustentada":
                porque += (
                    f" Cada tonelada entrega menos energia ({_sinal(ef_w_pci or 0)}% de combustível "
                    f"por energia). A maior alta foi no fornecedor {forn_maior} "
                    f"({pct(ref.umidade_por_fornecedor[forn_maior])} → "
                    f"{pct(comp.umidade_por_fornecedor[forn_maior])})."
                )
    hipoteses.append(
        _hipotese(
            "umidade_combustivel",
            "Combustível mais úmido (menos energia por tonelada)",
            st_w,
            porque,
            "Conferir a amostragem de umidade dos lotes"
            + (f" do fornecedor {forn_maior}" if forn_maior and st_w == "sustentada" else "")
            + " (método de estufa e número de amostras por lote).",
            ("umidade das amostras", "PCI seco das amostras"),
            ef_w_perda,
            ef_w,
        )
    )
    # condição do vapor
    st_dh = _status_fator(c_dh, sentido, ef_dh, efeito_minimo)
    if not c_dh.disponivel:
        porque = (
            "Faltam pressão do vapor, altitude ou temperatura da água de alimentação em um dos "
            "períodos."
        )
    else:
        porque = (
            "A energia por kg de vapor (pressão e água de alimentação) variou "
            f"{_sinal(ef_dh, 2)}%"
            + (": dentro da variação normal." if c_dh.detectavel is False else ".")
            + (pequeno_demais(ef_dh) if c_dh.detectavel else "")
        )
    hipoteses.append(
        _hipotese(
            "condicao_vapor",
            "Vapor mais exigente (pressão ou água de alimentação mais fria)",
            st_dh,
            porque,
            "Conferir as leituras de pressão do vapor e de temperatura da água de alimentação.",
            ("pressão do vapor", "temperatura da água de alimentação"),
            None,
            ef_dh,
        )
    )
    # perdas não medidas (resíduo entre os dois caminhos)
    residuo = u_residuo = None
    if c_eta.disponivel and c_perda.disponivel:
        residuo = -c_eta.delta * 100 - c_perda.delta  # p.p. de outras perdas
        if c_eta.incerteza_delta is not None and c_perda.incerteza_delta is not None:
            u_residuo = sqrt((100 * c_eta.incerteza_delta) ** 2 + c_perda.incerteza_delta**2)
    purgas_registradas = ref.purgas_n is not None and comp.purgas_n is not None
    if residuo is None:
        st_res = "nao_avaliavel"
        porque = (
            "Sem balanço direto e perda nos gases nos dois períodos, não dá para ver se sobra "
            "perda sem explicação."
        )
    elif u_residuo is None:
        st_res = "possivel"
        porque = (
            f"O balanço direto mostra {_sinal(residuo)} p.p. de outras perdas, mas sem incerteza "
            "declarada não dá para saber se é real."
        )
    elif abs(residuo) <= u_residuo:
        st_res = "descartada"
        porque = (
            "O balanço direto e a perda nos gases contam a mesma história, dentro da incerteza "
            f"(diferença de {_sinal(residuo)} p.p., incerteza ±{num(u_residuo)} p.p.)."
        )
    elif residuo > 0:
        st_res = "possivel"
        porque = (
            f"O balanço direto mostra {num(residuo)} p.p. a mais de perda do que a chaminé explica "
            f"(incerteza ±{num(u_residuo)} p.p.). Pode ser purga, perda pelo casco, vazamento de "
            "vapor ou combustão incompleta: os registros atuais não separam essas causas."
        )
    else:
        st_res = "descartada"
        porque = (
            f"O balanço direto mostra {num(-residuo)} p.p. de perda a menos do que a chaminé "
            "explica: não indica perda extra."
        )
    if st_res != "descartada":
        if not purgas_registradas:
            porque += " As purgas não foram registradas."
        if c_co.detectavel and c_co.delta > 0:
            porque += f" O CO subiu ({num(c_co.referencia, 0)} → {num(c_co.comparacao, 0)} ppm)."
    hipoteses.append(
        _hipotese(
            "perdas_nao_medidas",
            "Outras perdas não medidas (purga, casco, vazamentos, combustão incompleta)",
            st_res,
            porque,
            "Registrar número e duração das purgas em todos os turnos, medir CO nos gases e "
            "procurar vazamentos de vapor e de condensado.",
            ("balanço direto", "perda nos gases", "purgas"),
            residuo,
            efeito_consumo_por_perda(residuo) if st_res != "descartada" else None,
        )
    )

    # ------------------------------------------------ independência dos caminhos (E12)
    compartilhadas = [m for m in MEDICOES_INDIRETO if m in MEDICOES_DIRETO]
    independencia = {
        "caminho_direto": list(MEDICOES_DIRETO),
        "caminho_indireto": list(MEDICOES_INDIRETO),
        "compartilham": compartilhadas,
        "independentes": not compartilhadas,
        "nota": (
            "O balanço direto e a perda nos gases usam a mesma umidade e o mesmo PCI das "
            "amostras: se a umidade estiver errada, os dois erram juntos. Por isso contam como "
            "evidências só parcialmente independentes. A temperatura dos gases e o O₂ aparecem "
            "só no caminho indireto; o vapor e os estoques, só no direto."
        ),
    }

    # ------------------------------------------------ o que falta
    falta: list[str] = []
    for r in (ref, comp):
        for b in r.bloqueios.values():
            falta += b.falta
    for b in (*b_ref.bloqueios, *b_comp.bloqueios):
        falta += b.falta
    for ind in (i_ref, i_comp):
        if ind.bloqueio is not None:
            falta += ind.bloqueio.falta
    if not purgas_registradas:
        falta.append("registro de purgas (número e duração) nos dois períodos")
    for nome in dict.fromkeys(b_ref.sem_incerteza + b_comp.sem_incerteza):
        falta.append(f"incerteza declarada do(a) {nome} (instrumentos.csv)")
    for r in (ref, comp):
        if r.fracao_massa_sem_umidade:
            falta.append(
                f"umidade de {r.lotes_sem_umidade} lote(s) do período {r.rotulo()} "
                f"({pct(r.fracao_massa_sem_umidade)} da massa)"
            )
    falta = list(dict.fromkeys(falta))

    # ------------------------------------------------ conclusão e abstenção
    sustentadas = [h for h in hipoteses if h["status"] == "sustentada"]
    possiveis = [h for h in hipoteses if h["status"] == "possivel"]
    abstem, motivo = False, ""
    if not c_cons.disponivel:
        abstem, motivo = True, "o consumo por tonelada de vapor não pode ser calculado"
    elif not c_cons.detectavel:
        abstem, motivo = True, "a variação do consumo não é maior que a incerteza das medições"
    elif any(h["id"] == "perdas_nao_medidas" for h in possiveis):
        abstem, motivo = True, "parte da mudança não é explicada pelos registros"
    elif not sustentadas:
        abstem, motivo = (
            True,
            "nenhuma das causas medidas mudou o suficiente para explicar o consumo",
        )

    if abstem:
        texto = f"Não dá para concluir: {motivo}."
        if sustentadas:
            texto += (
                " Mesmo assim, os dados sustentam: "
                + "; ".join(h["titulo"].lower() for h in sustentadas)
                + "."
            )
    else:
        texto = "Os dados sustentam: " + "; ".join(h["titulo"].lower() for h in sustentadas) + "."

    # ------------------------------------------------ próxima verificação
    if not c_cons.disponivel:
        faltas_consumo = [f for b in (*b_ref.bloqueios, *b_comp.bloqueios) for f in b.falta]
        prox = {
            "acao": "Registrar o que falta para fechar o balanço: "
            + "; ".join(dict.fromkeys(faltas_consumo))
            + ".",
            "separa": [h["id"] for h in hipoteses if h["status"] in ("sustentada", "possivel")],
            "porque": "Sem o consumo por tonelada de vapor, não dá para medir o tamanho do efeito.",
        }
    elif any(h["id"] == "perdas_nao_medidas" for h in possiveis):
        h = next(h for h in hipoteses if h["id"] == "perdas_nao_medidas")
        prox = {
            "acao": h["verificacao"],
            "separa": ["perdas_nao_medidas"] + [x["id"] for x in sustentadas],
            "porque": "É a parte da mudança que os registros atuais não explicam.",
        }
    elif sustentadas:
        principal = max(sustentadas, key=lambda h: abs(h["efeito"]["consumo_pct"] or 0))
        prox = {
            "acao": principal["verificacao"],
            "separa": [principal["id"]],
            "porque": "Confirma a explicação de maior efeito antes de qualquer decisão.",
        }
    else:
        prox = {
            "acao": "Manter os registros e repetir a comparação com mais semanas de dados.",
            "separa": [],
            "porque": "Com mais dados, a incerteza diminui e mudanças menores ficam visíveis.",
        }

    # ------------------------------------------------ valor em jogo (só com base)
    valor_em_jogo, motivo_valor = None, ""
    if (
        c_cons.detectavel
        and c_cons.delta > 0
        and comp.vapor_t is not None
        and comp.preco_brl_t is not None
    ):
        extra_t = c_cons.delta * comp.vapor_t.valor
        valor = extra_t * comp.preco_brl_t
        valor_em_jogo = {
            "valor_brl": valor,
            "incerteza_brl": None
            if c_cons.incerteza_delta is None
            else c_cons.incerteza_delta * comp.vapor_t.valor * comp.preco_brl_t,
            "combustivel_extra_t": extra_t,
            "origem": "estimado",
            "base": (
                f"{num(extra_t, 0)} t de combustível a mais no período {comp.rotulo()}, em relação "
                f"ao consumo por tonelada de vapor da referência, ao preço médio pago "
                f"(R$ {num(comp.preco_brl_t)}/t). Não é promessa de economia."
            ),
        }
    else:
        motivo_valor = (
            "Sem aumento de consumo detectável com vapor e preço conhecidos: nenhum valor é "
            "estimado (regra: não inventar números)."
        )

    # ------------------------------------------------ custo do vapor (E14)
    custo = None
    if c_custo.disponivel and ref.preco_brl_gj and comp.preco_brl_gj:
        efeito_preco = 100 * log(comp.preco_brl_gj / ref.preco_brl_gj)
        efeito_intensidade = 100 * log(c_custo.comparacao / c_custo.referencia) - efeito_preco
        custo = {
            **_comparacao_json(c_custo),
            "efeito_preco_pct": efeito_preco,
            "efeito_intensidade_pct": efeito_intensidade,
            "frase": (
                f"O custo do combustível por tonelada de vapor foi de R$ {num(c_custo.referencia)} "
                f"para R$ {num(c_custo.comparacao)} ({_sinal(100 * c_custo.delta / c_custo.referencia)}%): "
                f"{_sinal(efeito_preco)}% pelo preço da energia comprada (R$/GJ) e "
                f"{_sinal(efeito_intensidade)}% pela energia gasta por tonelada de vapor. "
                "Variação de preço não é perda de eficiência (E14)."
            ),
        }

    def periodo_json(r: ResumoPeriodo, b: BalancoDireto, i: Indireto) -> dict:
        return {
            "inicio": r.inicio.isoformat(),
            "fim": r.fim.isoformat(),
            "rotulo": r.rotulo(),
            "leituras_diario": r.n_leituras_diario,
            "vapor_t": _grandeza_json(r.vapor_t),
            "combustivel_kg": _grandeza_json(r.combustivel_kg),
            "umidade_mistura": _grandeza_json(r.umidade_mistura),
            "pci_umido_mistura": _grandeza_json(r.pci_umido_mistura),
            "composicao_origem": r.composicao_origem,
            "eficiencia_direta": _grandeza_json(b.eficiencia),
            "consumo_t_por_t": _grandeza_json(b.consumo_t_por_t),
            "perda_gases_pct": None if i.resultado is None else i.resultado.perda_pct,
            "perda_gases_incerteza_pp": i.incerteza_pp,
            "preco_brl_t": r.preco_brl_t,
            "preco_brl_gj": r.preco_brl_gj,
            "purgas_n": r.purgas_n,
            "eventos": [
                {
                    "instante": e["instante"].isoformat(),
                    "tipo": e["tipo"],
                    "descricao": e["descricao"],
                }
                for e in r.eventos
            ],
            "bloqueios": [b.motivo for b in [*r.bloqueios.values(), *b.bloqueios]]
            + ([] if i.bloqueio is None else [i.bloqueio.motivo]),
        }

    diario = pacote.dados("diario")
    caldeira = (
        None if diario is None or diario.empty else str(diario["caldeira_id"].dropna().iloc[0])
    )
    return _limpar(
        {
            "versao_euler": __version__,
            "formato": "investigacao/0.1 (proposta D28)",
            "caldeira_id": caldeira,
            "periodos": {
                "referencia": periodo_json(ref, b_ref, i_ref),
                "comparacao": periodo_json(comp, b_comp, i_comp),
            },
            "o_que_mudou": {
                "frase": frase_consumo,
                "consumo_especifico": _comparacao_json(c_cons),
                "custo_vapor": custo,
                "indicadores": [
                    _comparacao_json(c) for c in (c_tg, c_o2, c_co, c_w, c_dh, c_perda, c_eta)
                ],
            },
            "hipoteses": hipoteses,
            "independencia": independencia,
            "o_que_falta": falta,
            "proxima_verificacao": prox,
            "conclusao": {"abstencao": abstem, "motivo": motivo, "texto": texto},
            "valor_em_jogo": valor_em_jogo,
            "valor_em_jogo_motivo": motivo_valor,
            "criterios": {
                "efeito_minimo_relevante_consumo_pct": efeito_minimo,
                "nota": "detectável = maior que a incerteza da diferença (k = 2); relevância: D29",
            },
        }
    )
