# EULER — resultado do ensaio com registros horários reais

**3 de outubro de 2026 · estudo exploratório, sem vínculo com a instalação analisada**

A EULER encontrou um desvio persistente na energia consumida por uma caldeira de
uma indústria de ingredientes alimentícios. A diferença permanece após considerar
a produção de vapor. É uma demonstração de triagem com dados operacionais reais;
a causa, a perda térmica e a parcela recuperável continuam sem comprovação.

## Dados e comparação

Usamos registros públicos da **Ingredion Incorporated Argo Plant**, Illinois, EUA,
EPA 54556, nas unidades B06, B07, B08 e B10. O recorte contém **8.034 registros
horários com vapor informado**, de janeiro a março de 2023, extraídos de um
arquivo EPA/PUDL com 8.417.520 linhas trimestrais. Não são médias fornecidas
prontas nem dados gerados artificialmente.

Janeiro foi adotado como referência; fevereiro e março, como comparação. Somente
horas completas, energia/vapor positivos e indicador EPA `Measured` foram usados.
Para a comparação condicionada à carga, foram excluídas as horas fora da faixa
de produção observada em janeiro. Valores negativos foram mantidos.

A B10 foi destacada depois de analisar o conjunto. **Não é validação prospectiva**
nem demonstração de que o software encontraria qualquer defeito em qualquer planta.
Janeiro é uma referência estatística, não uma operação certificada como ideal.

## Resultado da B10

| Indicador | Fevereiro/2023 | Março/2023 |
|---|---:|---:|
| Horas completas válidas | 672 | 720 |
| Horas dentro da faixa de janeiro | 441 | 553 |
| Horas válidas excluídas por carga fora da faixa | 231 | 167 |
| Energia acima da referência por carga | 4.795,75 GJ | 8.381,12 GJ |
| Diferença relativa à referência por carga | **+2,09%** | **+2,96%** |
| Valorização condicional pelo preço regional de gás | **US$ 35.052,79** | **US$ 49.954,06** |

**Total condicional: US$ 85.006,85**, correspondente somente às **994 horas
comparáveis** desses dois meses. Não extrapolamos para horas excluídas nem para um ano.

Nas outras unidades, o desvio por carga foi negativo: B06 −0,10%/−0,35%;
B07 −1,92%/−0,26%; B08 −1,99%/−1,14%, respectivamente em fevereiro/março.
A B06 tem baixa cobertura comparável, especialmente em março: apenas 31 horas.
Esses números não são economia comprovada, nem devem ser somados como efeito
líquido da fábrica, pois cobrem conjuntos diferentes de horas e equipamentos.

## O dinheiro tem uma condição explícita

Usamos a média industrial de Illinois publicada pela EIA: **US$ 8,02 por mil pés
cúbicos em fevereiro e US$ 6,54 em março**, convertida com o poder calorífico
médio regional anual de **1,040 MMBtu por mil pés cúbicos**. Dentro de cada mês,
o mesmo preço valoriza observado e referência.

É uma referência econômica rastreável. **Não é a fatura nem o preço contratado
pela Ingredion.** A B10 informa gás natural primário e carvão secundário no
cadastro da EPA; a proporção horária não está disponível. Portanto, tratar toda
a diferença como gás é uma condição do cenário de valorização. Os US$ 85 mil
não podem ser apresentados como prejuízo efetivo ou economia recuperável da empresa.

## Conferências e significado do teste

- O ajuste foi recalculado por um método numérico independente; a valorização
  foi conferida com aritmética Decimal. As contas coincidem dentro da precisão numérica.
- Uma segunda comparação, por faixas de 5 e 10 t de vapor/h, mantém o sinal
  positivo da B10. Os desvios variam de +2,43% a +3,55%, conforme mês e faixa.
  Cada alternativa tem cobertura própria e não é um intervalo de confiança.
- Os testes também verificam exclusão de dados substituídos, horas parciais e
  dados ausentes, bloqueio de duplicatas, conservação de reduções e ausência de
  confirmação sem incertezas. Os arquivos de referência golden não foram alterados.
- Esta execução exercita uma **nova rota exploratória** de série energética,
  o comparador da EULER e a valorização explícita de energia. Não executa a
  investigação completa de estoque, o balanço direto/indireto ou diagnóstico causal.

**O que fica demonstrado:** a EULER consegue transformar registros horários reais
em uma comparação rastreável, localizar uma unidade com desvio e dimensionar sua
ordem de grandeza econômica sob um preço explicitado. Isso ajuda a priorizar
onde investigar e quais dados pedir.

**O que falta para fechar o diagnóstico:** incertezas/calibrações, confirmação do
método de medição, pressão/temperatura do vapor e da água, regime, combustível
efetivamente usado e eventos operacionais. Só depois se poderá distinguir
condições de processo, erro de medição e perda física; e verificar quanto seria
recuperável antes/depois de uma intervenção. Hora completa não garante regime estável.

## Fontes e reprodução

- [EPA CAMPD, arquivo preservado pela PUDL](https://zenodo.org/records/21738530).
- [EIA: preço industrial do gás em Illinois, série mensal](https://www.eia.gov/dnav/ng/hist/n3035il3m.htm).
- [EIA: poder calorífico do gás entregue em Illinois](https://www.eia.gov/dnav/ng/NG_CONS_HEAT_DCU_SIL_A.htm).

O arquivo original recortado, hashes e método estão em
`validation/public/ensaio_horario/`. A execução pode ser repetida com
`python scripts/validar_ensaio_horario.py --saida resultado_horario.json`.
A tela **Referência → Testes com dados públicos** permite alternar as quatro
caldeiras e baixar os registros sem substituir os dados ativos da aplicação.
