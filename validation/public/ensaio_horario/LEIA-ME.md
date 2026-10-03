# Ensaio horário real — Ingredion Argo, primeiro trimestre de 2023

Este pacote contém 8.034 registros públicos com vapor informado, referentes às
quatro unidades B06, B07, B08 e B10 da instalação EPA 54556. Não contém dados
sintéticos nem dados de clientes. É um recorte da EPA CAMPD arquivado pela
Catalyst Cooperative/PUDL. Não implica participação ou validação da Ingredion.

## Origem e seleção

- Fonte: https://zenodo.org/records/21738530 — `epacems-2023.zip`, membro
  `epacems-2023q1.csv`. O trimestre contém 8.417.520 linhas.
- MD5 do ZIP conferido: `1419551207d1698b02caff78569d16ea`.
- Seleção: linhas com `Steam Load (1000 lb/hr)` não ausente e `Facility ID = 54556`.
  Não há preenchimento dos horários ausentes. Os valores originais das 14 colunas
  selecionadas são preservados; a serialização CSV foi refeita pelo pandas.
- A instalação foi escolhida por aderência ao mercado de ingredientes alimentícios.
  Todas as quatro unidades são apresentadas. B10 foi destacada **depois da triagem**.
  Não é um teste cego/prospectivo e não mede sensibilidade/especificidade comercial.
- Janeiro é referência; fevereiro e março são comparações cronológicas.
  Março é repetição retrospectiva do sinal, não prova de intervenção realizada.
- Identificador, URLs, hashes, preços e ressalvas em `fontes.json`.

## O que a execução faz

1. Rejeita duplicatas e mistura de unidades; preserva lacunas. Usa somente horas
   completas, com energia e vapor positivos e indicador EPA `Measured`.
2. Converte 1.000 lb em 0,45359237 t e 1 MMBtu em 1,05505585262 GJ.
   Cada linha já representa uma hora completa: não aplica trapézios nem integra
   o tempo entre leituras. Energia reportada mantém sua base PCS.
3. Ajusta, só em janeiro, energia/h = a + b × vapor/h. Compara os meses seguintes
   apenas dentro da faixa de vapor observada em janeiro. Preserva resíduos negativos.
4. Executa `euler.deteccao.comparar` em GJ/t na distribuição de carga da comparação.
   Sem incerteza instrumental completa, `detectavel` permanece ausente.
5. Executa `euler.economia.valorizar_energia` em GJ × USD/GJ. Não usa GJ como
   toneladas de combustível nem altera o baseline físico que exige regime estável.
6. Confere os coeficientes/resultados contra mínimos quadrados por decomposição
   numérica independente e o dinheiro com Decimal. Testa faixas de 5 e 10 t/h,
   com pelo menos 10 registros de referência por faixa; informa a cobertura própria.

Essa rota de ensaio é **nova e exploratória**, integrada à tela de dados públicos.
Não é a investigação completa por estoque, balanço direto/indireto ou atribuição
de causas. Uma hora completa não comprova regime estacionário.

## Dinheiro: referência regional, não a fatura da planta

A EIA publica preço industrial de Illinois de US$ 8,02 por mil pés cúbicos em
fevereiro/2023 e US$ 6,54 em março/2023. O poder calorífico médio regional anual
é 1.040 Btu/pé cúbico, equivalente a **1,040 MMBtu por mil pés cúbicos**.

`USD/GJ = (USD/mil pés³) ÷ (1,040 MMBtu/mil pés³ × 1,05505585262 GJ/MMBtu)`.

Cada mês usa o mesmo preço para consumo observado e referência, isolando o efeito
aritmético de quantidade. Não há câmbio, anualização, recuperação presumida ou
crédito de economia. Preços e poder calorífico são médias regionais, não contrato
ou análise de combustível da empresa. B10 informa gás primário e carvão secundário;
não há repartição horária de combustíveis neste pacote. Valorizar toda a diferença
como gás é **condicional**. Não chamá-la de prejuízo comprovado da Ingredion.

Fontes oficiais:

- https://www.eia.gov/dnav/ng/hist/n3035il3m.htm
- https://www.eia.gov/dnav/ng/NG_CONS_HEAT_DCU_SIL_A.htm
- Definição dos campos de operação: https://www.epa.gov/system/files/documents/2024-12/ecmps_emissions_reporting_instructions-12202024.pdf

## O que continua faltando

Pressão/temperatura do vapor e da água, incertezas/calibrações, confirmação do
método de medição, participação de cada combustível, composição/poder calorífico
da planta, regime e eventos operacionais. Sem esses registros não se fecha eficiência
térmica, não se separa causa e não se quantifica economia recuperável. O modelo pode
refletir condições omitidas; janeiro não é certificado como operação ótima.

Próxima investigação sugerida: conferir medidores, condições de vapor/água,
combustíveis e eventos da B10 nos períodos, depois testar hipóteses de combustão,
purga e troca térmica conforme os dados disponíveis. Não prescrever ajustes de operação.

## Reproduzir

Com as dependências do projeto:

```text
python scripts/validar_ensaio_horario.py --saida resultado_horario.json
pytest tests/test_ensaio_horario.py -q
```

O teste independente, a interface e os downloads usam o mesmo recorte. Os dados
ativos da empresa/demonstração não são substituídos por este ensaio.
