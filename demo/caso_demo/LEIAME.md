# Caso de demonstração · caldeira SINTÉTICA

> **Dados 100% sintéticos**, gerados por `python demo/gerar_caso_demo.py` (semente fixa).
> Nenhum dado real de cliente. Não editar os CSVs à mão: mude o gerador e gere de novo.

**Caldeira fictícia `CALD-DEMO-01`:** 20 t/h nominal, cavaco de madeira, vapor saturado a
~10 bar manométrico, água de alimentação a ~85 °C, **altitude 1.000 m** (usada pelo app
para a pressão atmosférica). Período: **03/08/2026 a 28/09/2026 (8 semanas)**, leituras a
cada 2 h, 3 fornecedores (F1, F2, F3), estoque medido toda segunda às 07:30.

## O que foi plantado (gabarito do demo)

| # | Fato | Quando | O que a EULER deve mostrar |
|---|---|---|---|
| 1 | Degrau de **+32 °C** na temperatura dos gases, **sem evento** que explique | a partir de 31/08 08:00 | Perda nos gases maior; consumo por tonelada de vapor maior |
| 2 | Umidade do **F3 subindo** de ~44% para ~56% | ao longo das 8 semanas | Alertas de umidade acima da faixa; F3 é o mais barato por tonelada e o **mais caro por energia** |
| 3 | **Medidor de vapor fora** (totalizador sem leitura), reinstalado **zerado** | 14/09 08:00 a 21/09 08:00 | "Não dá para concluir" sobre a eficiência nessa semana; aviso de totalizador reiniciado |
| 4 | **Limpeza** dos tubos de fumaça, parada de 4 h | 21/09 14:00 | Temperatura dos gases volta ao normal depois da limpeza |
| 5 | **Lacuna** de ~1,5 dia no diário | 12/09 04:00 a 13/09 16:00 | Aviso de lacuna |
| 6 | ~6% dos lotes **sem amostra** de umidade | espalhados | "Energia não determinada" nesses lotes |
| 7 | Alguns registros do turno da noite anotados no fim do turno | espalhados | Avisos de registro tardio |

Preços (R$/t úmida): F1 ≈ 180, F2 ≈ 170, F3 ≈ 160. Umidade: F1 ≈ 38%, F2 ≈ 45%.

## O que a investigação deve concluir (referência = semanas 1 a 4)

| Comparação | Resposta esperada |
|---|---|
| Semanas 5–6 | Consumo por t de vapor **subiu ~10%**; os dados sustentam **duas causas**: cavaco mais úmido (sobretudo F3) e temperatura dos gases (+32 °C). |
| Semana 7 | **Não dá para concluir** sobre o consumo (sem vapor medido); a temperatura dos gases continua alta. |
| Semana 8 | Depois da limpeza a temperatura volta ao normal; o consumo ainda está ~5% maior e **sobra a umidade** como causa. |

## Modelo do gerador (independente do motor `euler`)

Energia útil = vapor × 2,424 MJ/kg; rendimento = 0,80 − 0,00076·(T_gases − 186) −
0,10·(umidade − 0,42); PCI úmido = (1 − w)·18,5 − 2,442·w; combustível queimado =
energia útil ÷ (rendimento × PCI úmido). As sensibilidades vêm de
`docs/fisica_para_revisao.md`. O gerador não importa nada de `euler/` (AGENTS.md, regra 7).
