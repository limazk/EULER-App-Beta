# Exemplos de relatório para revisão do texto (T14)

Gerados por `python scripts/gerar_exemplos_relatorio.py` a partir do **caso de demonstração
sintético** (`demo/caso_demo/`). Referência = semanas 1 a 4 (03/08 a 31/08/2026).

| Arquivo | Comparação | O que o relatório deve dizer |
|---|---|---|
| `01_conclusao_duas_causas` | semanas 5–6 | O consumo subiu ~10%; os dados sustentam **duas causas**: cavaco mais úmido (sobretudo F3) e temperatura dos gases (+32 °C); próxima verificação: amostragem de umidade do F3. |
| `02_abstencao_sem_vapor` | semana 7 | **Não dá para concluir** sobre o consumo: o medidor de vapor estava fora. Mesmo assim, a temperatura dos gases está alta. Próxima verificação: registrar o vapor. |
| `03_depois_da_limpeza_sobra_umidade` | semana 8 | Depois da limpeza a temperatura voltou ao normal; o consumo ainda está ~5% maior e **a umidade explica**. |

O caso "o consumo subiu e nenhuma causa medida explica" (purga não registrada) está coberto
pelos testes automáticos (`tests/test_investigacao.py`, contraexemplo).

## O que revisar (Adryan)
- O texto está claro para o cliente (supervisor de utilidades / gerente de manutenção)?
- Alguma frase soa como **ordem** para a caldeira? (Não pode: só verificações.)
- Algum número sem unidade ou sem origem?
- A "abstenção" ficou clara e útil, ou soa como falha?

Os arquivos `.pdf` são os mesmos relatórios impressos em A4.
