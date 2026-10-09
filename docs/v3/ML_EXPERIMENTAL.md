# ML experimental executável — EULER 3.0

Implementação offline da issue #25. Os testes usam somente séries **sintéticas**, com
seeds fixas. Nenhum dado de cliente, rede, IA generativa ou modelo baixado participa.
O recurso continua desabilitado para clientes em `availability.py`.

## Arquitetura e isolamento

- `common.py` concentra validação temporal, divisão treino/validação/teste, métricas e o
  `EscopoML` imutável (`organizacao_id`, `planta_id`, `equipamento_id`).
- `anomaly.py` implementa ML-01 por distância robusta multivariada (mediana/MAD).
- `forecasting.py` implementa ML-02 por autorregressão linear de um passo.
- `residuals.py` implementa ML-03 sobre resíduos fornecidos (`medido - saída_física`),
  sem importar, chamar ou modificar o motor termodinâmico.

Todo modelo treinado armazena o escopo completo. Cada inferência exige novamente esse
escopo, confere igualdade com o modelo e valida os IDs de todas as linhas. Escopo ausente,
divergente, parcialmente ausente ou misturado causa `AbstencaoML`: o comportamento é
fail-closed e não depende do chamador filtrar dados corretamente.

## Treinamento, backtesting e previsão futura

As divisões temporais são contíguas (treino → validação → teste), sem embaralhamento. No
ML-02, `backtest_um_passo()` exige observações históricas porque calcula métricas contra
alvos conhecidos; os lags anteriores apenas formam a janela, nunca ajustam o modelo.

`prever_proximo()` é uma operação diferente: recebe o modelo e apenas o histórico já
observado, usa os últimos lags e retorna o próximo valor ainda desconhecido. O resultado
declara timestamp, horizonte de um passo, unidade e origem. A cadência deve ser regular e
igual à do treino; portanto um passo horário não é confundido com três intervalos
irregulares. A inferência futura não publica intervalo de confiança, pois ainda não existe
calibração homologada para esse uso. Combustível recebido é rejeitado como alvo de consumo.

## Modelos, referências e métricas

- **ML-01:** o limiar é o maior entre 3,5 e o percentil 99 do score de treino. Precisão,
  revocação e taxa de falso alarme são comparadas a um baseline MAD univariado de três
  escalas. A variável mais incomum é explicação descritiva, não atribuição de causa.
- **ML-02:** MAE, RMSE e MAPE são comparados à persistência. Erros absolutos da validação
  geram uma faixa empírica nominal de 90% somente para o backtest.
- **ML-03:** compara a saída física original a uma correção de viés aprendida somente no
  treino e mede resíduos fora de uma faixa empírica de 95%. Unidades de medição e saída
  física precisam ser idênticas, e a comparação preserva pares do mesmo timestamp.

## Abstenção e limitações

Há abstenção para série vazia, timestamps ausentes, duplicados, fora de ordem ou irregulares,
IDs de escopo ausentes/divergentes, variáveis ausentes ou constantes, `NaN` em excesso,
`inf`/`-inf`, janelas completas insuficientes em qualquer segmento e unidade/proveniência
inválida. Missing nunca vira zero, estado normal ou medição disponível. Inferência de
anomalia exige período posterior ao treino.

Anomalia não significa causa, falha ou risco. Previsão não é comando operacional nem
economia verificada. Resíduo não prova causalidade. A faixa nominal de 90% do ML-02 cobriu
83,33% no cenário sintético; essa subcobertura evidencia que a calibração atual não pode ser
tratada como confiável em operação. Nenhuma métrica abaixo comprova desempenho industrial.

## Resultado sintético reproduzível

Com as seeds registradas em `tests/test_ml_experimental.py`:

- ML-01: 3/3 anomalias detectadas, precisão 1,00, revocação 1,00 e falso alarme 0,00;
  o baseline obteve o mesmo resultado, sem evidência de superioridade.
- ML-02: MAE 0,0418 GJ contra 0,8525 GJ da persistência, melhora de 95,09% apenas na
  série AR construída para ser previsível; cobertura empírica de 83,33% para a faixa
  nominal de 90%.
- ML-03: MAE residual 2,4095 GJ no motor original e 0,2713 GJ após correção offline do
  viés sintético; 6,67% dos resíduos de teste fora da faixa empírica de 95%.

## Avaliação autorizada e futura homologação

Uma avaliação com dados reais requer autorização e extração isolada por organização,
planta e equipamento, dicionário de unidade/proveniência, período temporal congelado e
registro de versão/seed. Deve-se definir antes da execução: baseline, métricas, limites de
falso alarme/erro, tratamento de missing e critérios de aprovação. Os resultados precisam
ser revisados por especialistas de processo sem alterar as saídas do motor físico.

Para homologação industrial ainda são necessários conjuntos representativos e externos ao
desenvolvimento, análise de drift e subgrupos, calibração temporal independente, limites de
segurança, trilha de auditoria, monitoramento, rollback, revisão de privacidade e aprovação
humana formal. Até lá, os módulos servem apenas a avaliação offline experimental.

## Rollback

Remover os módulos experimentais, o teste e este documento. Nenhum schema, dado,
configuração produtiva ou algoritmo científico é alterado.
