# Busca de dados públicos de uma planta brasileira (05/10/2026)

Pedido do Adryan: encontrar dados completos de uma caldeira brasileira para validar a EULER.

**Resultado:** o histórico mais completo achado vem dos documentos públicos do **Mecanismo de
Desenvolvimento Limpo (MDL)** da ONU: a cervejaria AmBev em Viamão (RS), com **660 dias
seguidos** de casca de arroz, vapor por caldeira, pressão e horas de operação (05/11/2007 a
25/08/2009). Está no repositório e roda no motor: `validation/public/cervejaria_rs/` e aba
**Planta brasileira · RS** em Dados reais testados (D99).

Nenhuma fonte pública brasileira encontrada tem a cadeia inteira (estoque medido, umidade/PCI,
água de alimentação e gases). O piloto com uma planta autorizada continua sendo a validação
completa.

## Como os dados do MDL foram achados

1. Planilha oficial de todos os projetos MDL (PNUMA/UNEP-CCC, `cdm-pipeline.xlsx`): 764
   projetos no Brasil; filtrados os de biomassa, troca de combustível e eficiência com
   créditos emitidos (42), porque só esses publicaram relatórios de monitoramento.
2. Para cada candidato, a página do projeto e a de cada pedido de emissão na UNFCCC (as
   páginas exigem navegador por causa de uma checagem anti-robô). Os pedidos de emissão
   trazem, além do relatório, a **planilha de cálculo**, onde estão os dados mês a mês ou
   dia a dia.
3. Termos de uso da UNFCCC: textos, dados e documentos oficiais são de domínio público e podem
   ser copiados sem alteração, com a fonte citada.

## O que cada fonte tem de fato (conferido nos arquivos)

| Fonte | Período e frequência | Combustível | Vapor | Outros | Situação |
|---|---|---|---|---|---|
| **MDL 1202 · AmBev Águas Claras do Sul (Viamão/RS)**, 2 caldeiras a casca de arroz de 19 t/h | 05/11/2007–25/08/2009, **diário** | casca de arroz e de carvalho (t); óleo e sebo da reserva | por caldeira (totalizador lido 1×/dia), pressão, horas | balança ±2% e datas de calibração (verificação DNV); exemplo de projeto do fabricante (PDD) | **Importado (D99)** |
| MDL 0429 · Klabin Piracicaba (SP), 4 caldeiras de papel reciclado, óleo → gás natural | 2001–jan/2011, **mensal** | gás natural (m³ da Comgas e do medidor da Klabin, dias de leitura) | só dez/2006–mai/2007 (6 meses) | eficiência em t/TJ revista três vezes (347,76 · 367,55 · 361,20); fevereiro/2009 preenchido com o valor de fevereiro/2008 (1.470.416 m³) e depois corrigido para 323.681 m³; medidor sem calibração jul/2010–jan/2011 | Candidato para um teste de **qualidade de dados** (preenchimento, dois medidores, calibração vencida) |
| MDL 0484 · Solvay Indupa (Santo André/SP), 2 caldeiras de 62 t/h, óleo → gás natural | 2004–2011, mensal | gás natural por equipamento, PCI mensal da Comgas | não publicado mês a mês | divisão igual do gás entre as duas caldeiras | Só combustível |
| Resende (2019), UFU · caldeira de 180 t/h a cavaco | 4 ensaios de ~2 h | cavaco pesado, PCS e umidade | vapor, pressão, temperatura | água de alimentação 171 °C, mas entalpia usada de 487 kJ/kg (a 171 °C a IF97 dá ~725 kJ/kg) | Ensaio curto; candidato a teste de **conferência de cálculo publicado** |
| Brand e Giesel (2017), Energia na Agricultura · caldeiras CF8 e CF9 de papel e celulose (SC) | médias anuais 2012–2015 | biomassa, BPF e piche | médias mensais por ano | umidade antes e depois de um secador (set/2014) | Só médias e gráficos |
| Diniz (2014), UTFPR · papel jornal | médias de seca e chuva | consumo específico | — | — | Já usado (aba Biomassa · UTFPR) |
| Cortes-Rodríguez et al. (2016), 6 caldeiras a bagaço (SP) | ensaios ASME PTC 4 | — | — | perda nos gases 4,6–7,3% | Não baixado (Springer, acesso pago) |
| ONS · geração por usina | horária | — | — | só energia elétrica | Conferência de ordem de grandeza |
| IBAMA · RAPP | anual | lenha e cavaco por empresa | — | — | Conferência de ordem de grandeza |

Repositório da UTFPR (ROCA) fora do ar durante a busca (erro 502 do lado deles).

## Próximos passos possíveis

- **Klabin:** importar as três planilhas de cálculo (também domínio público) como teste de
  qualidade de dados: a EULER deve apontar o mês preenchido, a diferença entre os dois
  medidores de gás e o período sem calibração.
- **UFU:** reproduzir os quatro ensaios com a IF97 e mostrar o efeito da entalpia da água de
  alimentação usada no trabalho.
- **Outros projetos MDL brasileiros** com planilha de cálculo: os 42 com emissão estão
  listados no `cdm-pipeline.xlsx`; os de cogeneração a bagaço (ACM0006) podem ter vapor e
  bagaço mês a mês.
