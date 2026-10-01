# Caso de demonstração · ato 1 (completo) · caldeira SINTÉTICA

> **Dados 100% sintéticos**, gerados por `python demo/gerar_caso_demo.py` (semente fixa).
> Nenhum dado real de cliente. Não editar os CSVs à mão: mude o gerador e gere de novo.

**Os mesmos registros de operação do ato 2** (`demo/caso_demo/`: diário, combustível,
amostras e eventos idênticos). Muda só o **cadastro de instrumentos**: aqui ele traz a
incerteza de todos os instrumentos, declarada como limite ±a (D62):

| Instrumento | Incerteza | Observação |
|---|---|---|
| Termômetro da água de alimentação | ±1 °C | especificação típica, assumida |
| Termômetro do ar de combustão | ±1 °C | especificação típica, assumida |
| Estufa de umidade (método de umidade) | ±1 ponto percentual | conservador; assumido |
| Calorímetro (PCI seco) | ±1,5% da leitura | conservador; assumido |
| Os seis instrumentos do ato 2 | os mesmos valores | agora com o tipo "limite" declarado (o mesmo que a EULER já supunha, D35) |

Nenhum valor foi escolhido para produzir a conclusão; todos estão pendentes de revisão.

## O que a investigação conclui (referência = semanas 1 a 4)

| Comparação | Resposta |
|---|---|
| Semanas 5–6 | Consumo por t de vapor **subiu 10,1%**. **Compatíveis com os dados:** mais calor saindo pela chaminé (+3,1%) e combustível mais úmido (+7,8%). **Descartados:** excesso de ar (O₂ estável) e vapor mais exigente. As duas explicações fecham a mudança dentro da incerteza. |
| Semana 7 | **Não dá para concluir** sobre o consumo: o medidor de vapor estava fora. |
| Semanas 5–6 × semana 8 (antes × depois da limpeza) | Consumo **caiu 4,5%**; compatível com os dados: menos calor saindo pela chaminé. |

Os testes `tests/test_demo.py` e `tests/test_fluxo_demo.py` conferem essa história.
