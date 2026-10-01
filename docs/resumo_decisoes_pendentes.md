# As 10 decisões pendentes mais importantes · 01/10/2026

Escolhidas entre as 50 propostas ainda sem aprovação em `docs/decisoes.md` (mais as partes
pendentes das D62–D66), pelo efeito no resultado e na demonstração de 30/10. Cada linha traz
o que a EULER faz hoje e a recomendação. **Nada aqui está aprovado**: vale o
comportamento atual até a resposta.

## Física · para os doutorandos

| # | Decisão | Hoje | Recomendação |
|---|---|---|---|
| 1 | **Qual combustível foi queimado?** (D22, D38, D51) | Central: "o que entra é o que queima"; lote sem amostra entra com a média dos medidos (declarado); FIFO indisponível quando queimaria lote sem qualidade; mínimo e máximo são limites contábeis | Aprovar o central com a hipótese declarada; pedir à fábrica a umidade da alimentação da caldeira 1×/semana, que fecha a lacuna sem modelo de pilha |
| 2 | **Incerteza sem tipo e orçamento incompleto** (D35, D36, D52) | Sem tipo = limite ±a (retangular); o que falta nunca vira zero; mudança vira "condicional", nunca "sim" | Aprovar; tornar o tipo obrigatório no cadastro de instrumentos para clientes reais |
| 3 | **Umidade: método e amostragem** (D21; valores do ato 1, D62) | Média simples das amostras do lote; o ato 1 usa ±1 ponto (limite) para a estufa, de especificação típica | Usar a incerteza que o laboratório declarar; amostras em duplicata para medir a representatividade (Q14, opção c): é a maior fonte não quantificada (viés de +2 p.p. muda η em +4,3%) |
| 4 | **Critério de relevância** (D29, D44) | Explicação só conta se o efeito ≥ 0,5 × a menor mudança detectável; sensibilidade publicada no JSON | Manter 0,5 até o piloto; com 1,0 os gases deixariam de explicar no demo, então o valor precisa de justificativa escrita |
| 5 | **Correlação e resíduo direto − indireto** (D37, D47, D54) | Mesmo instrumento: calcula r = 0 e r = 1; umidade e PCI, comuns aos dois caminhos, entram uma vez | Aprovar os dois níveis; registrar calibrações e trocas como eventos (definem quando r muda) |
| 6 | **Fronteira do balanço direto** (D27, D39, D46, D09) | Purga fora da energia útil; título x = 1 assumido; Δh intervalo a intervalo | Aprovar a fronteira; título medido quando houver (x = 0,98 reduziria Δh em 1,65% a 11 bar abs e água a 85 °C) |

## Produto · para o Adryan

| # | Decisão | Hoje | Recomendação |
|---|---|---|---|
| 7 | **Autoria e registro** (T19, fora do registro de decisões) | Repositório já privado (conferido em 01/10/2026); sem tag de versão nem autoria registrada | Definir os autores e registrar a versão para o INPI antes de 30/10 |
| 8 | **Saúde da caldeira** (D65, D66) | Referência = primeira metade das semanas; selo com 3 estados (mudou / estável / não dá para dizer); tabela com 3 situações | Aprovar como está; numa próxima versão, deixar o usuário escolher a referência no próprio painel |
| 9 | **Palavras na tela** (D63, D64) | "Explicações compatíveis" no lugar de "causas"; rótulos em português no lugar dos nomes das colunas | Manter "explicações compatíveis": só a verificação comprova uma causa (regra do produto) |
| 10 | **Limiares de qualidade** (D13, D14, D20) | Lacuna = intervalo > 2 × o típico; registro tardio > 60 min; umidade fora de média ± 3 desvios dos 10 primeiros lotes | Aprovar como padrão e tornar configurável por fábrica no piloto |

**Também pendente:** conferir a tabela de capacidades e o JSON (D28, D30) contra o
`EULER_ESPECIFICACAO_DETALHADA.md` quando o arquivo for colocado na pasta
(`docs/conferencia_especificacao.md`).

Detalhes, exemplos numéricos e as perguntas Q1–Q17: `docs/perguntas_revisores.md`.
