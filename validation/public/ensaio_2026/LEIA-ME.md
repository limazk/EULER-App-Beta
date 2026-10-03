# Ensaio público de 03/10/2026

## Resultado e alcance

A EULER importou 7.200 registros públicos de temperatura sem alterar os valores,
reconheceu a origem pública e bloqueou eficiência e energia do vapor por falta de dados.
Em outro conjunto, os cálculos de 15 estados de água e vapor foram confrontados com
CoolProp/HEOS (IAPWS-95): maior diferença relativa de aproximadamente 0,0176%.
Isso verifica cálculos para os pontos examinados, não a precisão dos sensores nem o
desempenho completo do produto. Não há perda financeira ou economia comprovada neste ensaio.

Abra **Referência → Testes com dados públicos** no aplicativo. Essa tela executa
os módulos atuais, mostra a conferência e permite carregar o recorte real na sessão.
Os pontos sem datas permanecem em uma avaliação própria; não viram um diário inventado.

## 1. Caldeira subcrítica: três cargas publicadas

Fonte: Ohijeagbon, Angula, Lasode e Paulus (2026),
[Mendeley Data, versão 1](https://data.mendeley.com/datasets/wr267xjngz/1),
DOI 10.17632/wr267xjngz.1, licença CC BY 4.0.
A planilha original acompanha este diretório. `subcritica.json` identifica as células
de origem e o SHA-256. Os autores descrevem médias de registros industriais, com
processamento secundário. Não tivemos acesso ao historiador original.

| Carga | Vapor publicado | Combustível/vapor calculado | Potência para o vapor, condicional |
|---|---:|---:|---:|
| 70,73% | 96,23 t/h | 126,74 kg/t | 71,35 MW |
| 92,65% | 125,91 t/h | 127,55 kg/t | 90,76 MW |
| 100% | 136,03 t/h | 128,04 kg/t | 97,88 MW |

As potências usam vazão × (entalpia do vapor − entalpia da água). As funções de
entalpia são as do motor; essa multiplicação de pontos médios é uma conta auxiliar
do ensaio, não execução do balanço temporal completo. O módulo `fluxo_entalpia_vapor`
também é executado, e seu resultado tem outra fronteira (sem subtrair água de entrada).

**Condições e problemas da fonte:**

- Pressão declarada como estática em MPa, sem base absoluta/manométrica explícita.
  A conferência interpreta P como absoluta. Validar isso com a fonte é necessário
  antes de usar as potências como resultados industriais confirmados.
- Sem datas, duração dos patamares, incertezas instrumentais ou preços. Os pontos
  correspondem a cargas distintas, não a um antes/depois de manutenção.
- Razão kg/t: a linha da massa de combustível tem rótulo de mistura carvão/ar;
  o ar aparece separadamente. Registramos a interpretação sem corrigir a origem.
- Divergências entre fonte e IF97 atingem 0,99% em entalpias da água.
  Não alteramos o motor nem as tolerâncias para fazê-las desaparecer.
- Oxigênio em massa aparece como 7,9% e fração 0,078; pressões crescem através do
  economizador; manual cita outro DOI. Merecem esclarecimento dos autores.
- O valor calorífico é PCS/GCV em base seca ao ar. Não foi substituído por PCI.
  Gases e eficiências globais não foram validados a partir dessas tabelas.

`euler.deteccao.comparar` retorna diferença de aproximadamente +1,296 kg/t entre
a menor e a maior carga, com `detectavel=null`. Essa é a resposta adequada sem
incerteza: diferença numérica não equivale a perda evitável.

## 2. Zhejiang: série industrial primária

Fonte: Cao et al. (2025),
[Figshare, versão 1](https://doi.org/10.6084/m9.figshare.28868849.v1), CC0;
[artigo de Hu et al.](https://doi.org/10.1038/s41597-025-05096-4).
Arquivo `xinan_uncompleted_data.csv.zip`, ID 53975393,
[download original](https://ndownloader.figshare.com/files/53975393).
MD5 do ZIP conferido: `98f4ef127b2d2aa181e115deb96a8073`.

- 86.400 linhas e 30 sinais, a cada cinco segundos, 27/03–01/04/2022.
- Arquivo original preservado com 30 lacunas, no sinal da água de dessuperaquecimento.
  Nenhum preenchimento AutoReg foi utilizado.
- Temperatura de saída do vapor: 517,05–550,49 °C; média 537,52 °C.
- 7.037 leituras (8,14%) fora de 530–545 °C. O artigo informa 8,6%; a diferença
  permanece registrada. É uma classificação dos autores, não prova de perda térmica.

`diario.csv` seleciona exatamente uma em cada 12 linhas observadas, começando na
primeira (7.200 linhas); não faz médias. Mapeia somente `TE_8332A.AV_0#` para
`t_vapor_c`, com unidades confirmadas no artigo. Fuso +08:00 inferido da localização,
identificado em cada linha. Temperaturas e datas originais são preservadas na seleção.
ID da caldeira é um identificador local, não a tag de ativo fornecida pela planta.

Não mapeamos pressão, vazão ou O2 para cálculos físicos sem confirmar unidades e base.
A ausência de pressão, água de alimentação, combustível e preço impede balanço
completo, extrato de compras e cálculo financeiro. Testa importação e abstenção.

## Reprodução e próximos dados

### Complemento financeiro: médias brasileiras com preço publicado

Retomamos um caso da pesquisa anterior: Carlos Bartolotto Filho, Unisanta (2015),
[dissertação original](https://unisanta.br/wp-content/uploads/2025/04/Teses-Auditoria-Ambiental_129-2015-Carlos-Bartolotto-Filho.pdf),
tabelas 6, 7, 14 e 15 (páginas do PDF 56, 59 e 63). `unisanta.json` preserva
os valores transcritos. Gás natural; preço adotado de R$ 1,10/kg nos dois períodos.
Não se trata de cotação atual ou nota fiscal auditada.

- 2010: 7.562 kg/h de combustível e 119,39 t/h de vapor → R$ 69,67/t de vapor.
- 2011: 7.458 kg/h de combustível e 123,85 t/h de vapor → R$ 66,24/t de vapor.
- Diferença calculada: R$ 3,43/t, redução de 4,93% na intensidade de custo.
- Diferença bruta de gasto horário: R$ 114,40/h. Não compara igual produção.
- À produção de 2011, projetando linearmente a intensidade de 2010, a diferença
  é aproximadamente R$ 425,14/h. Não é linha de base ajustada por carga ou economia medida.

Executamos `euler.deteccao.comparar` com os custos específicos: diferença disponível,
detectabilidade inconclusiva por ausência de incerteza. As contas de massa/preço são
auxiliares desta auditoria; não simulamos um histórico para forçar a investigação completa.
A equação de custo publicada na dissertação usa outra abordagem, por entalpia, e fornece
outros números; aqui usamos diretamente massa/preço. Excluímos totais anuais inconsistentes.
A retirada do pré-aquecedor é relatada junto à mudança de combustível de partida:
não isolamos causalidade. Sem anualização ou economia atribuída à EULER.

A tela também permite escolher outro preço: cenário explicitamente separado do histórico.
O ensaio valida a aritmética monetária e sua apresentação, não a recuperação futura.

Nova fonte localizada para testes físicos mais completos: [Morrin/UCD, EPA Ireland](https://eparesearch.epa.ie/safer/iso19115/displayISO19115.jsp?isoID=250).
O catálogo oferece seis ensaios com consumo, temperaturas, vazão, gases e orçamento
de incerteza. Trata-se de caldeira doméstica de água quente a gás (18 kW), não de vapor
industrial. Apenas o catálogo foi conferido nesta etapa; nenhum resultado desses arquivos
é apresentado como teste executado da EULER.

No ambiente do projeto: `python scripts/validar_ensaio_publico.py --saida resultado.json`.
Com CoolProp instalado, acrescente `--conferir-heos` para recalcular a referência
independente. Isso não é necessário para usar o aplicativo. Testes:
`pytest tests/test_ensaio_2026.py`.

A referência HEOS armazenada foi produzida de P/T ou P/título, sem usar as entalpias
da fonte como entrada. Concordância entre duas formulações de propriedades da água
não é uma segunda medição industrial. Golden e equações físicas não foram alterados.

Para validar economia e intervenções, ainda precisamos de uma mesma planta com
consumo e vapor sincronizados, condições da água/vapor, ensaios do combustível,
preços e eventos; depois, comparação antes/depois com incerteza e carga controladas.
Dados de carvão não comprovam automaticamente desempenho em biomassa brasileira.
