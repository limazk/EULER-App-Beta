"""Gera o caso de demonstração SINTÉTICO da EULER em demo/caso_demo/ (T18).

Caldeira fictícia de 20 t/h a cavaco, 8 semanas (03/08 a 28/09/2026), 3 fornecedores.
Fatos plantados de propósito (o "gabarito" do demo, ver demo/caso_demo/LEIAME.md):
  1. degrau de +32 °C na temperatura dos gases a partir de 31/08 08:00, sem evento que explique;
  2. umidade do fornecedor F3 subindo de ~42% para ~54% ao longo das 8 semanas;
  3. medidor de vapor fora de 14/09 08:00 a 21/09 08:00 (totalizador sem leitura) e
     reinstalado zerado — período em que não dá para concluir;
  4. limpeza dos tubos de fumaça em 21/09 14:00: a temperatura dos gases volta ao normal;
  5. lacuna de ~1,5 dia no diário (12/09 a 13/09) e alguns registros tardios no turno da noite.

Modelo simplificado do gerador (independente do motor `euler`, AGENTS.md regra 7):
  energia útil = vapor × 2,424 MJ/kg (10 bar man, água a 85 °C);
  rendimento = 0,80 − 0,00076·(T_g − 186) − 0,10·(w − 0,42) (sensibilidades do doc de física);
  PCI úmido = (1 − w)·18,5 − 2,442·w; combustível queimado = energia útil / (rendimento · PCI).

Uso: python demo/gerar_caso_demo.py      (sempre gera os mesmos arquivos: semente fixa)
"""

from __future__ import annotations

import csv
import io
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

PASTA = Path(__file__).resolve().parent / "caso_demo"
FUSO = timezone(timedelta(hours=-3))
INICIO = datetime(2026, 8, 3, 8, 0, tzinfo=FUSO)
DIAS = 56
CALDEIRA = "CALD-DEMO-01"

DELTA_H_MJ_KG = 2.424
PCI_SECO = 18.5
H_VAP = 2.442
DEGRAU = datetime(2026, 8, 31, 8, 0, tzinfo=FUSO)
LIMPEZA = datetime(2026, 9, 21, 14, 0, tzinfo=FUSO)
VAPOR_FORA = (datetime(2026, 9, 14, 8, 0, tzinfo=FUSO), datetime(2026, 9, 21, 8, 0, tzinfo=FUSO))
LACUNA = (datetime(2026, 9, 12, 4, 0, tzinfo=FUSO), datetime(2026, 9, 13, 16, 0, tzinfo=FUSO))

FORNECEDORES = {
    # preço R$/t úmida, umidade inicial, umidade final
    "F1": (180.0, 0.38, 0.38),
    "F2": (170.0, 0.45, 0.45),
    "F3": (160.0, 0.42, 0.54),
}
PARTICIPACAO = {"F1": 0.35, "F2": 0.35, "F3": 0.30}


def _iso(t: datetime) -> str:
    return t.isoformat(timespec="seconds")


def _turno(t: datetime) -> tuple[str, str]:
    if 6 <= t.hour < 14:
        return "A", "OP-01"
    if 14 <= t.hour < 22:
        return "B", "OP-02"
    return "C", "OP-03"


def _pci_umido(w: float) -> float:
    return (1 - w) * PCI_SECO - H_VAP * w


def _csv(cabecalho: list[str], linhas: list[list]) -> str:
    saida = io.StringIO()
    escritor = csv.writer(saida, lineterminator="\n")
    escritor.writerow(cabecalho)
    escritor.writerows(linhas)
    return saida.getvalue()


def gerar() -> dict[str, str]:
    """Devolve {nome_do_arquivo: conteúdo CSV}."""
    rng = np.random.default_rng(2026)
    diario, combustivel, amostras = [], [], []

    # ------------------------------------------------ diário (a cada 2 h)
    totalizador = 48_210.0
    leituras = []  # (instante, vapor_t no intervalo, t_gases) para o modelo de combustível
    medidor_novo = False
    for i in range(DIAS * 12):
        t = INICIO + timedelta(hours=2 * i)
        turno, operador = _turno(t)
        dia_hora = t.hour + t.minute / 60
        vazao = 14.8 + 1.6 * np.sin((dia_hora - 9) / 24 * 2 * np.pi) + rng.normal(0, 0.4)
        parada = LIMPEZA <= t < LIMPEZA + timedelta(hours=4)
        if parada:
            vazao = 0.0
        vapor = max(vazao, 0) * 2
        t_gases = 186 + rng.normal(0, 2.5)
        if DEGRAU <= t < LIMPEZA:
            t_gases += 32
        leituras.append((t, vapor, t_gases))

        if LACUNA[0] <= t < LACUNA[1]:
            continue  # período sem registro no diário

        if VAPOR_FORA[0] <= t < VAPOR_FORA[1]:
            leitura_tot = ""
            medidor_novo = True
            ocorrencia = "medidor de vapor em manutenção" if t == VAPOR_FORA[0] else ""
        else:
            if medidor_novo:
                totalizador, medidor_novo = 0.0, False
            totalizador += vapor
            leitura_tot = f"{totalizador:.1f}"
            ocorrencia = ""
        if t == LIMPEZA:
            ocorrencia = "parada para limpeza dos tubos de fumaça"

        atraso_min = int(rng.integers(2, 9))
        if turno == "C" and t.hour == 2 and rng.random() < 0.12:
            atraso_min = (6 - t.hour) * 60 + 5  # anotado no fim do turno
        registrado = t + timedelta(minutes=atraso_min)
        purga = 1 if t.hour % 4 == 0 else 0
        diario.append(
            [
                CALDEIRA,
                _iso(t),
                _iso(registrado),
                turno,
                operador,
                "parada" if parada else "estavel",
                f"{10.0 + rng.normal(0, 0.12):.1f}",
                "" if parada else f"{t_gases:.0f}",
                "CHAMINE-1",
                "" if parada else f"{7.5 + rng.normal(0, 0.3):.1f}",
                "ANALIS-01",
                "" if parada else f"{max(0, 80 + rng.normal(0, 25)):.0f}",
                f"{85 + rng.normal(0, 0.8):.0f}",
                f"{22 + 5 * np.sin((dia_hora - 9) / 24 * 2 * np.pi) + rng.normal(0, 0.8):.0f}",
                purga,
                20 * purga,
                leitura_tot,
                "",
                ocorrencia,
                "true" if VAPOR_FORA[0] <= t < VAPOR_FORA[1] else "false",
                "sintetico",
            ]
        )

    # ------------------------------------------------ combustível: entregas, pilha e estoques
    estoque_real = 260_000.0
    recentes: list[tuple[float, float]] = []  # (massa, umidade) dos últimos lotes
    n_lote = 0
    for dia in range(DIAS):
        manha = INICIO + timedelta(days=dia)
        if dia % 7 == 0:
            medido = round(estoque_real * (1 + rng.normal(0, 0.015)), -2)
            momento = manha - timedelta(minutes=30)
            combustivel.append(
                [_iso(momento), "estoque", "", "", f"{medido:.0f}", "", "", "", "", "sintetico"]
            )

        # consumo do dia pelo modelo simplificado
        do_dia = [x for x in leituras if manha <= x[0] < manha + timedelta(days=1)]
        w_pilha = (
            sum(m * w for m, w in recentes[-12:]) / sum(m for m, _ in recentes[-12:])
            if recentes
            else 0.42
        )
        queimado = 0.0
        for _, vapor, t_gases in do_dia:
            rendimento = 0.80 - 0.00076 * (t_gases - 186) - 0.10 * (w_pilha - 0.42)
            queimado += vapor * 1000 * DELTA_H_MJ_KG / (rendimento * _pci_umido(w_pilha))

        # entregas: repõem o consumo previsto e puxam o estoque para ~260 t
        caminhoes = max(2, round((queimado + (260_000 - estoque_real) * 0.3) / 30_000))
        for k in range(caminhoes):
            n_lote += 1
            forn = rng.choice(list(PARTICIPACAO), p=list(PARTICIPACAO.values()))
            preco_t, w0, w1 = FORNECEDORES[forn]
            w = float(np.clip(w0 + (w1 - w0) * dia / (DIAS - 1) + rng.normal(0, 0.015), 0.25, 0.65))
            massa = float(round(rng.normal(30_000, 1_500), -1))
            preco = round(massa / 1000 * (preco_t + rng.normal(0, 2)), 2)
            chegada = manha + timedelta(hours=1 + 3 * k, minutes=int(rng.integers(0, 50)))
            lote = f"L-{n_lote:04d}"
            combustivel.append(
                [
                    _iso(chegada),
                    "recebimento",
                    forn,
                    lote,
                    f"{massa:.0f}",
                    "",
                    "",
                    "",
                    f"{preco:.2f}",
                    "sintetico",
                ]
            )
            recentes.append((massa, w))
            estoque_real += massa
            if rng.random() > 0.06:  # ~6% dos lotes ficam sem amostra de umidade
                amostras.append(
                    [
                        f"A-{n_lote:04d}",
                        lote,
                        _iso(chegada + timedelta(hours=1)),
                        f"{w + rng.normal(0, 0.005):.3f}",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "estufa_ISO18134",
                        "interno",
                        "sintetico",
                    ]
                )
        estoque_real -= queimado

        # análise completa semanal de um lote de cada fornecedor (laboratório)
        if dia % 7 == 2:
            for forn in FORNECEDORES:
                lotes_forn = [r for r in combustivel if r[1] == "recebimento" and r[2] == forn]
                if not lotes_forn:
                    continue
                ref = lotes_forn[-1]
                c = 0.50 + rng.normal(0, 0.004)
                h = 0.06 + rng.normal(0, 0.001)
                o = 0.9935 - c - h - 0.003 - 0.0005
                amostras.append(
                    [
                        f"LAB-{forn}-{dia:02d}",
                        ref[3],
                        _iso(manha + timedelta(hours=10)),
                        "",
                        f"{PCI_SECO + rng.normal(0, 0.15):.2f}",
                        f"{c:.4f}", f"{h:.4f}", f"{o:.4f}", "0.0030", "0.0005", "0.0065",
                        "analise_elementar_e_calorimetria",
                        "LAB-SINT",
                        "sintetico",
                    ]
                )  # fmt: skip
    fim = INICIO + timedelta(days=DIAS) - timedelta(minutes=30)
    combustivel.append([_iso(fim), "estoque", "", "", f"{round(estoque_real * (1 + rng.normal(0, 0.015)), -2):.0f}", "", "", "", "", "sintetico"])  # fmt: skip
    combustivel.sort(key=lambda r: r[0])

    eventos = [
        ["2026-08-17T10:00:00-03:00", "calibracao", "Calibração do analisador de O₂ (ANALIS-01)", "SUP-01", "sintetico"],
        [_iso(VAPOR_FORA[0]), "troca_instrumento", "Medidor de vapor retirado para manutenção", "SUP-01", "sintetico"],
        [_iso(VAPOR_FORA[1]), "troca_instrumento", "Medidor de vapor reinstalado (totalizador zerado)", "SUP-01", "sintetico"],
        [_iso(LIMPEZA), "limpeza", "Limpeza dos tubos de fumaça (parada de 4 h)", "SUP-01", "sintetico"],
    ]  # fmt: skip
    instrumentos = [
        ["ANALIS-01", "analisador_o2", "CHAMINE-1", "pct_seco", "0.1", "0.3", "2026-08-17", "sintetico"],
        ["TERMO-01", "termopar_gases", "CHAMINE-1", "c", "1", "2", "2026-06-10", "sintetico"],
        ["MANOM-01", "manometro", "TUBULAO", "bar", "0.1", "0.2", "2026-05-02", "sintetico"],
        ["MED-VAPOR-01", "medidor_vazao_vapor", "LINHA-VAPOR", "pct_da_leitura", "0.1", "2", "2026-09-21", "sintetico"],
        ["BALANCA-01", "balanca_rodoviaria", "PORTARIA", "kg", "10", "50", "2026-03-15", "sintetico"],
    ]  # fmt: skip

    return {
        "diario.csv": _csv(
            ["caldeira_id", "instante_observado", "instante_registrado", "turno", "operador_id", "regime", "p_vapor_bar_man", "t_gases_c", "ponto_gases_id", "o2_seco_pct", "instrumento_o2_id", "co_ppm", "t_agua_alim_c", "t_ar_c", "purgas_n", "purgas_s", "totalizador_vapor_t", "producao", "ocorrencia", "flag_instrumento_indisponivel", "origem_dado"],
            diario,
        ),
        "combustivel.csv": _csv(
            ["data", "tipo", "fornecedor_id", "lote_id", "massa_kg", "volume_m3", "densidade_kg_m3", "origem_densidade", "preco_brl", "origem_dado"],
            combustivel,
        ),
        "amostras.csv": _csv(
            ["amostra_id", "lote_id", "data", "umidade_bu_frac", "pci_seco_mj_kg", "C", "H", "O", "N", "S", "cinzas", "metodo", "laboratorio", "origem_dado"],
            amostras,
        ),
        "eventos.csv": _csv(["instante", "tipo", "descricao", "autorizado_por", "origem_dado"], eventos),
        "instrumentos.csv": _csv(
            ["instrumento_id", "tipo", "ponto", "unidade", "resolucao", "incerteza_declarada", "ultima_verificacao", "observacao"],
            instrumentos,
        ),
    }  # fmt: skip


if __name__ == "__main__":
    PASTA.mkdir(exist_ok=True)
    for nome, conteudo in gerar().items():
        (PASTA / nome).write_text(conteudo, encoding="utf-8")
        print(f"demo/caso_demo/{nome}: {conteudo.count(chr(10)) - 1} linhas")
