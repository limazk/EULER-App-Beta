# Exemplos de relatório para revisão do texto (T14)

Gerados por `python scripts/gerar_exemplos_relatorio.py` a partir do **caso de demonstração
sintético** (`demo/caso_demo/`). Referência = semanas 1 a 4 (03/08 a 31/08/2026).

| Arquivo | Comparação | O que o relatório deve dizer |
|---|---|---|
| `01_semanas_5_6_umidade_a_confirmar` | semanas 5–6 | O consumo subiu ~10%. A temperatura dos gases (+32 °C) é explicação compatível; a umidade só é **condicional** (falta a incerteza do método de umidade). **Não dá para concluir**; próxima verificação: cadastrar essa incerteza e conferir a amostragem de umidade. |
| `02_abstencao_sem_vapor` | semana 7 | **Não dá para concluir** sobre o consumo: o medidor de vapor estava fora. Mesmo assim, a temperatura dos gases está alta. Próxima verificação: registrar o vapor. |
| `03_semana_8_umidade_a_confirmar` | semana 8 | Depois da limpeza a temperatura voltou ao normal; o consumo ainda está ~5% maior. A umidade fecharia a mudança, mas é só condicional: **não dá para concluir**, com o mesmo pedido de cadastro. |

O caso "o consumo subiu e nenhuma explicação medida cobre a mudança" (purga não registrada) está coberto
pelos testes automáticos (`tests/test_investigacao.py`, contraexemplo).

## O que revisar (Adryan)
- O texto está claro para o cliente (supervisor de utilidades / gerente de manutenção)?
- Alguma frase soa como **ordem** para a caldeira? (Não pode: só verificações.)
- Algum número sem unidade ou sem origem?
- A "abstenção" ficou clara e útil, ou soa como falha?

Os arquivos `.pdf` são os mesmos relatórios impressos em A4.
