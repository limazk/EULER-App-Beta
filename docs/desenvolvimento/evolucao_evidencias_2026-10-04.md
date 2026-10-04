# Evolução da interpretação das evidências — 04/10/2026

## Auditoria inicial

Ponto de partida: commit `02acf32`, árvore de trabalho limpa. Revisão do professor
relatada pelo fundador: exemplos numéricos coerentes; atenção às hipóteses, dados,
incertezas e interpretação. Isso não equivale a aprovação integral do motor.

Arquitetura identificada:

- `euler/`: importação, qualidade, capacidades, rotas adaptativas, propriedades
  IF97, combustível, balanços direto/indireto, purga, UA, incerteza,
  comparação, baseline por carga, hipóteses e relatório HTML.
- `app/ensaio_horario.py`: comparação energética pública em PCS, separada do
  balanço térmico industrial; ajuste linear em janeiro, sem extrapolação.
- `app/robustez_ensaio.py`: modelos alternativos, referências alternativas,
  validação temporal, reamostragem em blocos e trilha por registro.
- `app/parecer_ensaio.py`: conclusão e relatório público. Lacuna: a auditoria
  aparecia nos detalhes, mas não determinava a conclusão principal.
- `validation/public/ensaio_horario/`: registros públicos preservados, fontes,
  auditoria versionada e hashes; `tests/golden/` é somente leitura.
- `app/paginas/`: Streamlit; estado compartilhado em `app/estado.py`.

Verificação inicial: **464 testes aprovados em 636,69 s**; três avisos conhecidos
do pandas nos testes que injetam valores não finitos. Lint aprovado; 144 arquivos
já formatados. Suíte executada antes das alterações no código.

## Escopo escolhido

Implementar P0 e integrar o P1 existente. Manter equações, fontes, preços e
seleção dos períodos. Acrescentar avaliação explícita da referência e das
dimensões de evidência, sem nota global nem percentual fictício de confiança.
Classificações são regras qualitativas de triagem, versionadas e revisáveis;
nunca probabilidades de causa ou certificação industrial.
Esta rubrica foi definida após conhecer o estudo: é uma interpretação
retrospectiva, não um protocolo pré-registrado ou uma validação independente.

Intervenções formais, verificação pós-intervenção e economia verificada (P2)
exigem um desenho de comparação e dados ainda ausentes. Permanecem próximas
etapas; campos correspondentes não serão preenchidos com economias presumidas.

## Evidência anterior que deve permanecer

| B10 | Fevereiro de 2023 | Março de 2023 |
|---|---:|---:|
| Desvio ajustado à carga | +2,093994% | +2,961084% |
| Energia adicional observada | 4.795,754851 GJ | 8.381,116318 GJ |
| Valorização condicional | US$ 35.052,79 | US$ 49.954,06 |
| Horas comparáveis / válidas | 441 / 672 | 553 / 720 |
| Sensibilidade, blocos de 3 dias | −0,270% a +5,030% | +0,286% a +5,993% |
| Interpretação | Menos conclusivo | Aumento persiste nas verificações |

Preço regional EIA, não fatura; mistura horária de combustíveis da B10
desconhecida. Não houve confirmação de causa, prejuízo ou recuperação. As
faixas de reamostragem não são incertezas dos instrumentos. As outras três
caldeiras e os sinais negativos continuam publicados.

## Referências metodológicas

Diagnóstico por resíduos, além de R²: [NIST](https://www.itl.nist.gov/div898/handbook/pmd/section4/pmd44.htm).
Avaliação temporal sem dados futuros no treino:
[Hyndman e Athanasopoulos](https://otexts.com/fpp3/tscv.html).
Essas fontes fundamentam práticas gerais, não certificam os limiares de
triagem nem os resultados da EULER. Revisão independente permanece necessária.

## Implementação

1. Contrato central `euler/evidencias.py`: sete dimensões independentes, motivos,
   classificação qualitativa, ID e hash. Sem nota global. Causa e economia não
   podem ser promovidas automaticamente; a tentativa é bloqueada.
2. `euler/referencia.py`: quantidade, lacunas, dispersão, resíduos, potenciais
   outliers, deriva entre metades, autocorrelação em pares temporais, validação
   cronológica, suporte de carga e regime informado. Não ajusta outro modelo,
   remove outliers ou escolhe outra referência. Limiares de triagem ficam
   publicados no resultado e requerem revisão: não são constantes universais.
3. `app/diagnostico_publico.py`: conecta dados, baseline e auditoria existentes.
   A força do sinal depende conjuntamente dos blocos, modelos, referências e
   retirada de um dia. Uma reversão ou faixa incluindo zero permanece visível.
   Auditoria ausente ou incompatível nunca herda um selo favorável.
4. `euler/evidencia_operacional.py`: conecta a investigação física existente,
   com estados legados preservados. Mantém equações e detectabilidade. Declara
   que dois agregados não bastam para avaliar estabilidade temporal. Publica
   energia do combustível já calculada, sem criar novo balanço de perdas.
5. Hipóteses e próxima medição: no caso público, roteiro explícito de metrologia,
   estados térmicos, combustível, regime e perdas. Na rota física, reaproveita
   a regra de próxima verificação e as hipóteses já existentes. A ordem é
   qualitativa; não há valor da informação calculado nem probabilidades causais.
6. Economia: desvio monetizado, oportunidade potencial e economia verificada
   são campos distintos. Os dois últimos continuam ausentes. Preço, moeda,
   unidade, período, fonte e premissas acompanham o valor.
7. Tela **Diagnóstico EULER**, parecer público, relatório e exportações usam o
   mesmo objeto. A investigação dos arquivos ativos também recebe esse resumo.
8. Ajustes de linguagem: ausência de mudança detectável não é prova de
   estabilidade; hipótese enfraquecida não é exclusão definitiva; repetir
   leituras não elimina deriva ou erro sistemático.
9. Rastreabilidade: hashes dos registros/fontes, parâmetros, método e resultado.
   Hash da tabela importada é explicitamente diferente do hash do arquivo bruto.
   O cache dos arquivos ativos passa a depender também do código do motor.

## Testes e reprodução

Novos testes cobrem estabilidade/instabilidade, ausências, regimes, suporte de
carga, unidades, degeneraçāo do MAD, sinais positivos/negativos/inconclusivos,
auditoria incompatível, promoção indevida a causa/economia, integridade e
consistência entre tela, diagnóstico e relatório. Fixtures didáticas não são
usadas como evidência pública. Nenhum golden ou tolerância foi alterado.

```text
pytest -q
ruff check .
ruff format --check .
python scripts/auditar_ensaio_publico.py --saida output/auditoria-publica
python scripts/diagnosticar_ensaio_publico.py --saida output/diagnostico-publico
streamlit run app/main.py
```

O último exportador publica todas as unidades, compara valores anteriores e
atuais e interrompe se a camada interpretativa mudar energia ou valorização.

## Resultado da validação final

- **477 testes aprovados**, incluindo os antigos, os novos e os golden, em
  519,08 s. Os três avisos do pandas já existiam na execução inicial e ocorrem
  em testes que deliberadamente fornecem dados não finitos.
- Lint aprovado e **157 arquivos** verificados pela formatação.
- Após o ajuste final de linguagem na investigação, **nove testes complementares**
  de interface e diagnóstico também passaram (49,23 s).
- Auditoria completa reexecutada com 2.000 repetições por configuração:
  resultado integral idêntico ao artefato anterior, incluindo as quatro unidades.
- Diagnósticos, relatórios e comparação antes/depois exportados sem alterar
  a energia ou o valor financeiro de qualquer mês/unidade.
- Conferência visual no navegador: diagnóstico público em fevereiro e março,
  distinção de evidência/referência/física e parecer principal coerente com a
  auditoria. Aplicação executável no endereço local habitual.

| B10 | Energia antes → depois | Valor condicional antes → depois | Nova interpretação |
|---|---|---|---|
| Fevereiro | 4.795,75 → 4.795,75 GJ | US$ 35.052,79 → US$ 35.052,79 | Robustez FRACA; referência MODERADA; física INSUFICIENTE |
| Março | 8.381,12 → 8.381,12 GJ | US$ 49.954,06 → US$ 49.954,06 | Robustez FORTE dentro do protocolo; referência MODERADA; física INSUFICIENTE |

“FORTE” não elimina as limitações da referência nem a ausência de incerteza
instrumental. As quantidades acima são restritas às horas comparáveis; a
classificação não as transforma em perdas recuperáveis.

## Limitações e próximos cinco avanços

1. Revisar com os professores e o especialista estatístico os limiares da
   rubrica e a adequação da referência. A revisão informal recebida não valida
   esta implementação nova.
2. Obter um piloto autorizado com medições sincronizadas, estados térmicos,
   combustível efetivo e histórico de calibração. Ainda não há dados de campo
   confirmados de uma planta brasileira.
3. Estender a avaliação automática da referência à série operacional importada,
   com variáveis adicionais e validação temporal por equipamento. A rota
   agregada atual informa explicitamente que não possui essa avaliação.
4. Implementar registro formal de intervenções e protocolo antes/depois,
   preservando mudanças concomitantes, condições comparáveis e incertezas.
5. Só então verificar economia líquida: preço contratual, combustível evitado,
   custos da ação e contrafactual documentado. Não inferir causalidade de um
   simples antes/depois.

## Arquivos da entrega

Criados:

- `euler/evidencias.py`, `euler/referencia.py`, `euler/evidencia_operacional.py`,
  `euler/relatorio_evidencias.py`.
- `app/diagnostico_publico.py`, `app/blocos/diagnostico.py`,
  `app/paginas/diagnostico.py`.
- `scripts/diagnosticar_ensaio_publico.py`.
- `tests/test_evidencias.py`, `tests/test_referencia.py`,
  `tests/test_evidencia_operacional.py`, `tests/test_diagnostico_publico.py`.
- Este relatório técnico.

Atualizados:

- `app/main.py`, `app/estado.py`, `app/formatacao.py`,
  `app/paginas/investigacao.py`, `app/parecer_ensaio.py`,
  `app/blocos/ensaio_horario.py`, `app/blocos/robustez_publica.py`.
- `euler/investigacao.py`, `euler/relatorio.py`.
- `tests/test_investigacao.py`: somente expectativa de texto, de “descartado”
  para “enfraquecido nestes dados”; critérios, tolerâncias e golden preservados.
- `README.md`, `docs/gestao/decisoes.md`.

## Escopo ainda não entregue

P2 permanece planejado: não há cadastro formal de intervenção nem economia
verificada. O balanço total de todas as perdas e o ranking quantitativo de
informação também permanecem fora do escopo. A interface apresenta os limites
sem impedir as análises que os dados já permitem.
