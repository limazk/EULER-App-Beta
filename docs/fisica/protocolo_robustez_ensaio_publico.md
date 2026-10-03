# Protocolo de robustez do ensaio público — v1, 03/10/2026

Escopo: o mesmo recorte EPA/PUDL de Ingredion Argo, janeiro a março de 2023.
Extensão retrospectiva de um resultado já examinado, **não pré-registro nem
validação cega**. Não buscar outro caso nem ajustar critérios para preservar
o sinal da B10. Publicar as quatro unidades e os dois meses, inclusive reversões.

## Pergunta e regras fixadas antes da execução desta extensão

O resíduo de energia condicionado à produção de vapor resiste a escolhas
razoáveis de referência, modelo e dependência temporal? Não se testa aqui
causa, eficiência térmica, erro instrumental ou economia recuperável.

1. Conservar o resultado original: ajuste linear em janeiro; comparação de
   fevereiro/março apenas na faixa de carga de janeiro, sem preencher dados.
2. Exportar cada linha original com decisão de inclusão e, quando comparável,
   energia de referência, diferença e valorização condicional. Conferir somas
   contra o motor e preservar SHA-256 dos dados, fontes, código e saídas.
3. Comparar linear, quadrático e intensidades por faixas de 5 e 10 t/h **nas
   mesmas horas**. Cada faixa exige ao menos dez horas de janeiro. Publicar
   horas excluídas; esta população pode ser menor que a do resultado original.
   Nenhum modelo é eleito por produzir o maior aumento.
4. Avaliar o ajuste linear cronologicamente dentro de janeiro: dias 1–14
   predizem 15–21; dias 1–21 predizem 22–31. Publicar cobertura, viés e erro
   absoluto. Não presumir ausência de mudança em janeiro nem chamar esses
   trechos de controles negativos conhecidos.
5. Trocar janeiro completo por 1–15 e 16–31, usando a interseção das faixas
   de carga dos três ajustes. Registrar se o sinal muda. Retirar um dia de
   comparação de cada vez para verificar influência de dias isolados.
6. Reamostrar pares carga/energia em blocos móveis de 1, 3 e 7 dias de
   calendário, separadamente em referência e comparação, com novo ajuste em
   cada repetição: 2.000 repetições e semente 20261003. Blocos não atravessam
   o fim do mês; dias sem observações elegíveis têm contribuição vazia, não
   medição zero. Percentis 2,5 e 97,5 são uma **faixa de sensibilidade da
   reamostragem**, condicionada à amostra, método e suporte original. Não são
   intervalo metrológico, probabilidade de causa ou teste confirmatório.
   Dependência mais longa e não estacionariedade podem invalidar inferência.
7. Calcular a redução proporcional da energia reportada no mês que zeraria
   o resíduo, mantendo a referência fixa. Esse ponto de equilíbrio mede
   vulnerabilidade a deriva/condições omitidas; não estima erro real.
8. Preservar preço regional e mistura desconhecida como hipóteses. Não somar
   somente os desvios positivos para chamar de perda da planta; não anualizar.

## Reprodutibilidade e limites

Entradas públicas congeladas; nenhuma nova medição é gerada. A integridade
usa SHA-256 dos bytes originais do CSV. As assinaturas dos arquivos de texto
do método normalizam apenas quebras de linha para LF, permitindo reprodução
entre Windows e Linux; não normalizam valores dos dados.
O procedimento de reamostragem
reutiliza observações reais para examinar sensibilidade, sem alimentar o motor
como se fossem medições novas. Fixtures artificiais existem só nos testes de
unidade e não integram a evidência pública. Não há limiar de alarme calibrado
nem correção por seleção da B10/múltiplas comparações: resultados descritivos.

As fontes abaixo fundamentam diagnóstico de resíduos, avaliação temporal e
preservação de dependência por blocos; não certificam esta implementação nem
este tamanho de bloco. Revisão independente por estatístico e engenheiro
continua indicada, especialmente para adequação da referência.

- NIST, diagnóstico de modelos: https://www.itl.nist.gov/div898/handbook/pmd/section4/pmd44.htm
- Hyndman e Athanasopoulos, avaliação temporal: https://otexts.com/fpp3/tscv.html
- Hyndman e Athanasopoulos, reamostragem por blocos: https://otexts.com/fpp3/bootstrap.html
