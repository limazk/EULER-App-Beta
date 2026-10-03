# EULER — auditoria de robustez do ensaio público

03/10/2026 · Mesmo recorte EPA/PUDL · Ingredion Argo · Janeiro a março de 2023

## O que foi testado

Reprodução da conta original, comparação de métodos nas mesmas horas, mudança da referência, teste cronológico dentro de janeiro, influência de dias isolados e reamostragem em blocos de dias. Nenhum registro novo ou sintético foi usado como evidência. Reamostragens reutilizam os registros reais; não são medições novas.

A B10 já havia sido selecionada após triagem. Este aprofundamento é retrospectivo. Não foi escolhido o método que fornece maior valor. Todas as unidades são publicadas.

## Resultados por unidade e período

|Unidade / mês|Original (%)|Modelos, mesmas horas (%)|Referências alternativas (%)|Horas comuns dos modelos|
|---|---:|---:|---:|---:|
|B06 / 2023-02|-0,099|-0,110 a -0,095|indisponível|427|
|B06 / 2023-03|-0,348|-0,652 a -0,348|indisponível|31|
|B07 / 2023-02|-1,925|-2,021 a -1,766|-3,597 a -0,869|593|
|B07 / 2023-03|-0,264|-0,837 a -0,681|-2,914 a 0,336|437|
|B08 / 2023-02|-1,986|-1,994 a -1,978|-2,406 a -1,617|627|
|B08 / 2023-03|-1,140|-1,119 a -1,061|-1,668 a -0,810|634|
|B10 / 2023-02|2,094|2,108 a 2,432|0,962 a 2,312|246|
|B10 / 2023-03|2,961|2,748 a 3,139|2,515 a 3,746|174|

As faixas de métodos e referências são sensibilidades, não intervalos de confiança. Cada comparação de métodos usa uma população comum; as demais análises podem cobrir populações diferentes, identificadas no JSON.

## B06: estabilidade da referência e dependência temporal

- Treino até 2023-01-14; teste 2023-01-15 a 2023-01-21: 0/0 horas; viés indisponível%. Erro absoluto médio: indisponível GJ/h.

- Treino até 2023-01-21; teste 2023-01-22 a 2023-01-31: 0/198 horas; viés indisponível%. Erro absoluto médio: indisponível GJ/h.

Esses trechos não têm regime estável certificado. Viés revela mudança ou inadequação do modelo, sem separar as duas explicações.

- Correlação dos resíduos separados por 1 h: 0,838 (197 pares separados exatamente pelo intervalo indicado; não se exige observação nas horas intermediárias).

- Correlação dos resíduos separados por 24 h: 0,081 (174 pares separados exatamente pelo intervalo indicado; não se exige observação nas horas intermediárias).

### 2023-02

- Blocos de 1 dias: percentis 2,5–97,5 de -0,820% a 0,767%; 2000/2000 repetições válidas.

- Blocos de 3 dias: percentis 2,5–97,5 de -1,001% a 1,703%; 1946/2000 repetições válidas.

- Blocos de 7 dias: percentis 2,5–97,5 de -0,288% a 26,615%; 1723/2000 repetições válidas.

- Retirar um dia da comparação: -0,158% a -0,017%.

- Redução da energia reportada que zeraria o desvio, mantendo a referência: -0,099%. Se negativo, seria necessário aumentar a energia reportada. É uma sensibilidade algébrica, não erro de medição identificado.

### 2023-03

- Blocos de 1 dias: percentis 2,5–97,5 de -1,731% a 1,893%; 1995/2000 repetições válidas.

- Blocos de 3 dias: percentis 2,5–97,5 de -1,726% a 3,072%; 1946/2000 repetições válidas.

- Blocos de 7 dias: percentis 2,5–97,5 de -1,248% a 26,459%; 1753/2000 repetições válidas.

- Retirar um dia da comparação: -0,832% a 1,244%.

- Redução da energia reportada que zeraria o desvio, mantendo a referência: -0,350%. Se negativo, seria necessário aumentar a energia reportada. É uma sensibilidade algébrica, não erro de medição identificado.

## B07: estabilidade da referência e dependência temporal

- Treino até 2023-01-14; teste 2023-01-15 a 2023-01-21: 168/168 horas; viés -1,485%. Erro absoluto médio: 4,893 GJ/h.

- Treino até 2023-01-21; teste 2023-01-22 a 2023-01-31: 229/240 horas; viés -2,881%. Erro absoluto médio: 6,088 GJ/h.

Esses trechos não têm regime estável certificado. Viés revela mudança ou inadequação do modelo, sem separar as duas explicações.

- Correlação dos resíduos separados por 1 h: 0,963 (743 pares separados exatamente pelo intervalo indicado; não se exige observação nas horas intermediárias).

- Correlação dos resíduos separados por 24 h: 0,697 (720 pares separados exatamente pelo intervalo indicado; não se exige observação nas horas intermediárias).

### 2023-02

- Blocos de 1 dias: percentis 2,5–97,5 de -2,553% a -1,191%; 2000/2000 repetições válidas.

- Blocos de 3 dias: percentis 2,5–97,5 de -3,081% a -1,107%; 2000/2000 repetições válidas.

- Blocos de 7 dias: percentis 2,5–97,5 de -3,443% a -0,925%; 2000/2000 repetições válidas.

- Retirar um dia da comparação: -1,977% a -1,852%.

- Redução da energia reportada que zeraria o desvio, mantendo a referência: -1,963%. Se negativo, seria necessário aumentar a energia reportada. É uma sensibilidade algébrica, não erro de medição identificado.

### 2023-03

- Blocos de 1 dias: percentis 2,5–97,5 de -1,400% a 1,170%; 2000/2000 repetições válidas.

- Blocos de 3 dias: percentis 2,5–97,5 de -2,605% a 1,023%; 2000/2000 repetições válidas.

- Blocos de 7 dias: percentis 2,5–97,5 de -2,644% a 0,576%; 2000/2000 repetições válidas.

- Retirar um dia da comparação: -0,335% a -0,181%.

- Redução da energia reportada que zeraria o desvio, mantendo a referência: -0,265%. Se negativo, seria necessário aumentar a energia reportada. É uma sensibilidade algébrica, não erro de medição identificado.

## B08: estabilidade da referência e dependência temporal

- Treino até 2023-01-14; teste 2023-01-15 a 2023-01-21: 167/168 horas; viés 0,161%. Erro absoluto médio: 0,899 GJ/h.

- Treino até 2023-01-21; teste 2023-01-22 a 2023-01-31: 239/240 horas; viés -1,497%. Erro absoluto médio: 4,491 GJ/h.

Esses trechos não têm regime estável certificado. Viés revela mudança ou inadequação do modelo, sem separar as duas explicações.

- Correlação dos resíduos separados por 1 h: 0,930 (743 pares separados exatamente pelo intervalo indicado; não se exige observação nas horas intermediárias).

- Correlação dos resíduos separados por 24 h: 0,690 (720 pares separados exatamente pelo intervalo indicado; não se exige observação nas horas intermediárias).

### 2023-02

- Blocos de 1 dias: percentis 2,5–97,5 de -2,324% a -1,587%; 2000/2000 repetições válidas.

- Blocos de 3 dias: percentis 2,5–97,5 de -2,591% a -1,460%; 2000/2000 repetições válidas.

- Blocos de 7 dias: percentis 2,5–97,5 de -2,748% a -1,586%; 2000/2000 repetições válidas.

- Retirar um dia da comparação: -2,021% a -1,953%.

- Redução da energia reportada que zeraria o desvio, mantendo a referência: -2,026%. Se negativo, seria necessário aumentar a energia reportada. É uma sensibilidade algébrica, não erro de medição identificado.

### 2023-03

- Blocos de 1 dias: percentis 2,5–97,5 de -1,537% a -0,703%; 2000/2000 repetições válidas.

- Blocos de 3 dias: percentis 2,5–97,5 de -1,770% a -0,530%; 2000/2000 repetições válidas.

- Blocos de 7 dias: percentis 2,5–97,5 de -1,853% a -0,577%; 2000/2000 repetições válidas.

- Retirar um dia da comparação: -1,170% a -1,104%.

- Redução da energia reportada que zeraria o desvio, mantendo a referência: -1,154%. Se negativo, seria necessário aumentar a energia reportada. É uma sensibilidade algébrica, não erro de medição identificado.

## B10: estabilidade da referência e dependência temporal

- Treino até 2023-01-14; teste 2023-01-15 a 2023-01-21: 160/168 horas; viés 0,233%. Erro absoluto médio: 5,446 GJ/h.

- Treino até 2023-01-21; teste 2023-01-22 a 2023-01-31: 220/240 horas; viés 1,563%. Erro absoluto médio: 9,957 GJ/h.

Esses trechos não têm regime estável certificado. Viés revela mudança ou inadequação do modelo, sem separar as duas explicações.

- Correlação dos resíduos separados por 1 h: 0,584 (743 pares separados exatamente pelo intervalo indicado; não se exige observação nas horas intermediárias).

- Correlação dos resíduos separados por 24 h: 0,556 (720 pares separados exatamente pelo intervalo indicado; não se exige observação nas horas intermediárias).

### 2023-02

- Blocos de 1 dias: percentis 2,5–97,5 de 0,222% a 3,614%; 2000/2000 repetições válidas.

- Blocos de 3 dias: percentis 2,5–97,5 de -0,270% a 5,030%; 2000/2000 repetições válidas.

- Blocos de 7 dias: percentis 2,5–97,5 de 1,056% a 5,559%; 2000/2000 repetições válidas.

- Retirar um dia da comparação: 1,850% a 2,162%.

- Redução da energia reportada que zeraria o desvio, mantendo a referência: 2,051%. Se negativo, seria necessário aumentar a energia reportada. É uma sensibilidade algébrica, não erro de medição identificado.

### 2023-03

- Blocos de 1 dias: percentis 2,5–97,5 de 0,931% a 4,489%; 2000/2000 repetições válidas.

- Blocos de 3 dias: percentis 2,5–97,5 de 0,286% a 5,993%; 2000/2000 repetições válidas.

- Blocos de 7 dias: percentis 2,5–97,5 de 1,841% a 6,081%; 2000/2000 repetições válidas.

- Retirar um dia da comparação: 2,908% a 3,012%.

- Redução da energia reportada que zeraria o desvio, mantendo a referência: 2,876%. Se negativo, seria necessário aumentar a energia reportada. É uma sensibilidade algébrica, não erro de medição identificado.

## Interpretação e aplicação

Os percentis são faixas condicionais de reamostragem, não orçamento de incerteza instrumental. Dependência superior ao bloco e mudança persistente de regime continuam possíveis. Não há p-valor confirmatório nem probabilidade de causa. Janeiro não é operação ideal certificada. Não se conclui saúde da caldeira por R² ou pelo sinal isolado.

A conta financeira original é preservada. Preço médio industrial regional EIA, poder calorífico regional e uso integral de gás são condições da valorização. A B10 também registra carvão secundário, sem participação horária conhecida. Não é fatura, prejuízo comprovado ou dinheiro recuperável. Desvios negativos não são descartados nem as parcelas positivas são chamadas de perda líquida da planta.

A ação sustentada é conferir medições, condições da água/vapor e combustível. Intervenção exige avaliação técnica. Revisão independente deste protocolo permanece pendente.

## Como reproduzir e conferir

Executar `python scripts/auditar_ensaio_publico.py --saida output/auditoria-publica` no ambiente do projeto. O CSV conserva as 8.034 linhas originais e acrescenta decisão e cálculo por hora. Campos vazios em linhas excluídas não significam zero. O manifesto confere os arquivos produzidos; o JSON identifica dados e código.

SHA-256 do recorte: `53ff6a441b5f2574a34f169b2714a6688bf97b7f53bd44b5169486968fe9eb3b`. Semente: 20261003. Repetições por mês, unidade e tamanho de bloco: 2000.

## Fontes

- EPA/PUDL: https://zenodo.org/records/21738530

- EIA preços: https://www.eia.gov/dnav/ng/hist/n3035il3m.htm

- EIA calor: https://www.eia.gov/dnav/ng/NG_CONS_HEAT_DCU_SIL_A.htm

- NIST diagnóstico: https://www.itl.nist.gov/div898/handbook/pmd/section4/pmd44.htm

- Avaliação temporal: https://otexts.com/fpp3/tscv.html

- Dependência e blocos: https://otexts.com/fpp3/bootstrap.html