# ML experimental executável — primeira versão

Implementação offline da issue #25. Os exemplos e testes usam dados **sintéticos** com
seed fixa; nenhum dado de cliente, rede, IA generativa ou modelo baixado participa.

## Modelos e métricas

- **ML-01:** distância multivariada robusta usando mediana/MAD. O limiar é o maior entre
  3,5 e o percentil 99 do treino. A avaliação informa precisão, revocação e taxa de falso
  alarme, comparadas a um baseline univariado de três escalas robustas.
- **ML-02:** regressão linear autorregressiva de um passo, treinada apenas no primeiro
  bloco temporal. Compara MAE, RMSE e MAPE com persistência. O erro absoluto da validação
  calibra uma faixa empírica de 90%; ela não é garantia probabilística industrial. A API
  exige proveniência explícita e recusa combustível recebido como se fosse consumo.
- **ML-03:** analisa `medido - saída_física` sem chamar ou modificar o motor. Compara o
  resultado físico original com correção de viés aprendida no treino e reporta resíduos
  fora da faixa empírica de 95%.

## Condições de abstenção e limites

Timestamps precisam ser únicos e crescentes. Organização, planta e equipamento não podem
ser misturados. Amostras insuficientes, variáveis constantes e excesso de valores ausentes
interrompem o cálculo; missing nunca vira zero ou estado normal. As divisões são contíguas
no tempo (treino → validação → teste), sem embaralhamento.

Anomalia não significa causa, falha ou risco. Previsão não é comando operacional nem
economia verificada. Correlação/resíduo não prova causalidade. Os modelos permanecem sem
integração com UI ou dados reais e `disponibilidade()` continua desabilitada até validação
industrial, versionamento e aprovação humana.

## Resultado reproduzível do teste sintético

Com as seeds registradas em `tests/test_ml_experimental.py`:

- ML-01: 3/3 anomalias detectadas, precisão 1,00, revocação 1,00 e falso alarme
  0,00; o baseline robusto univariado obteve o mesmo resultado, portanto não há evidência
  de superioridade neste caso.
- ML-02: MAE 0,0418 GJ contra 0,8525 GJ da persistência; melhora de 95,09% **somente
  na série AR sintética construída para ser previsível**, com cobertura empírica de 83,33%
  para a faixa nominal de 90%.
- ML-03: MAE residual 2,4095 GJ no motor original e 0,2713 GJ após correção offline do
  viés sintético; 6,67% dos resíduos de teste ficaram fora da faixa empírica de 95%.

Esses números verificam execução e avaliação temporal, não desempenho industrial.

## Rollback

Remover os novos módulos `common.py`, `anomaly.py`, `forecasting.py`, `residuals.py`, o
teste e este documento. Nenhum schema, dado, configuração produtiva ou motor é alterado.
