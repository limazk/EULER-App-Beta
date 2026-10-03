# Auditoria do motor físico e das rotas adaptativas

Revisão de 2 de outubro de 2026. Base de integração: PR #11, commit `560f94d`,
construído sobre a principal `b2c28e3`. Comparação também com o PR #3, commit `3c52ced`.
Este parecer é uma auditoria de implementação e de coerência dimensional. Não substitui
o parecer dos professores, ensaio industrial, conformidade normativa ou validação em campo.

## Resultado e estratégia de integração

O princípio de responder apenas às perguntas sustentadas pelos dados foi mantido. O sistema
pode calcular propriedades e fluxo de entalpia do vapor quando a eficiência está bloqueada.
Ter uma coluna presente é apenas um caminho candidato; o cálculo ainda verifica as linhas,
a simultaneidade, o regime, a cobertura e o domínio físico.

O PR #3 divergiu de correções já integradas. Substituir a principal pelo conteúdo desse PR
retiraria pressão independente da água na purga, proteção contra valores não finitos,
tratamento de erro numérico de baseline perfeito, regressões e organização dos documentos.
Essas partes foram preservadas da principal. O snapshot Wonji e seus testes foram incorporados
separadamente, sem importar essas regressões e sem mudar tolerâncias.

## Problemas encontrados e correções

1. **Combustível ausente causava exceção interna.** O vapor era acrescentado a uma lista antes
   de validar o combustível; uma falha acrescentava outro valor e desalinhava as listas.
   Agora ambos são calculados antes de registrar a linha. Intervalos válidos permanecem disponíveis.
2. **Paradas eram apagadas antes da integração.** Isso podia unir pontos dos dois lados da
   parada e produzir cobertura artificial de 100%. A linha do tempo permanece inteira;
   extremos não estáveis invalidam os intervalos adjacentes, sem encurtar o denominador.
3. **Partida, transiente e regime ausente alimentavam um balanço estacionário.** Na rota nova,
   somente intervalos com ambos os extremos explicitamente estáveis entram no resultado.
   Isto não garante estabilidade entre amostras nem constitui um modelo dinâmico.
4. **Estado ausente virava vapor seco automaticamente.** A rota adaptativa bloqueia por padrão.
   Uma opção explícita da API permite cenário com x = 1, sempre marcado como hipótese; a tela
   não ativa essa opção. O caminho legado mantém sua hipótese histórica identificada.
5. **Pressão do vapor era reutilizada na água.** A nova rota por vazões exige pressão própria
   da água no mesmo ponto de sua temperatura. O campo já existente foi documentado também
   para esse uso; não foi criada uma tag obrigatória para todo o produto.
6. **Duplicatas temporais e várias caldeiras podiam ser combinadas.** A nova integração bloqueia
   essas entradas com motivo. Datas inválidas também são recusadas.
7. **Mudança de estado podia ser unida por integração.** Não há trapézio entre extremos de estados
   distintos. Trechos válidos de cada estado podem contribuir com suas energias separadas;
   não se calcula uma temperatura/título médio entre estados.
8. **Importação com dois aliases podia gerar colunas duplicadas ou escolher uma silenciosamente.**
   Nomes equivalentes concorrentes são bloqueados com instrução para selecionar uma única coluna.
   O arquivo original continua preservado.
9. **Mapa da purga omitia a pressão da água de referência.** Requisito corrigido, alinhado à D77.
10. **Tela confundia sinais presentes com cálculo aprovado.** Os caminhos agora são apresentados
    como candidatos; resultados mostram cobertura e limites. Leituras e intervalos descartados
    são informados. Média de leituras não é descrita como média ponderada no tempo.
11. **Valores não finitos podiam chegar às propriedades do vapor.** Guardas acrescentadas;
    condições fora do domínio IF97 suportado produzem bloqueio legível.
12. **Planilha de entrada estava atrás das novas colunas opcionais.** Regenerada pelo esquema,
    preservando o conteúdo de demonstração. O contrato foi regenerado pela mesma fonte.

## Equações e caminhos conferidos

| Caminho | Relação e unidade | Resultado da revisão |
|---|---|---|
| Pressão | p_abs = p_man + p_atm, bar; IF97 recebe MPa = bar/10 | Conversão conferida; pressão pertence ao ponto medido. |
| Vapor | h(P,T), h(P,x); kJ/kg da biblioteca dividido por 1000 | Estados seco, úmido e superaquecido preservados; não usar P/T de saturação para inventar título. |
| Energia do vapor | Soma de massa × diferença de entalpia; t × MJ/kg = GJ | Fluxo legado por totalizador preservado; estados declarados inconsistentes bloqueiam energia. |
| Fluxo do vapor | t/h × 1000/3600 × MJ/kg = MW | Fluxo de entalpia isolado não é calor útil nem eficiência. |
| Balanço por vazões | Integral de m_dot × (h_vapor − h_água) / integral da potência do combustível | Mesmos intervalos válidos nos dois lados; MW × hora × 3,6 = GJ; cobertura publicada. |
| Combustível | kg/h × PCI em MJ/kg / 3600 = MW | PCI precisa corresponder à base da massa; potência fornecida não comprova medição independente. |
| Purga | kg × [h_líquido saturado(P_purga) − h_água(P_água,T_água)] / 1000 = GJ | Pressões independentes, massa registrada e fronteira bruta preservadas. |
| Economizador | Q = m_dot × (h_saída − h_entrada), MW; UA = Q/LMTD, MW/K | Quatro temperaturas, água líquida e pressão própria; diferenças terminais positivas; contracorrente equivalente. |
| Baseline por carga | y = a + bx; s² = soma dos resíduos²/(n−2) | Mínimos quadrados, mínimo computacional de três pontos, sem extrapolação e sem previsão não positiva. |
| Erro de previsão | s_pred = s × raiz[1 + 1/n + (x−média x)²/Sxx] | Inclui nova observação. Residual normalizado não é probabilidade nem intervalo com cobertura declarada. |
| Incerteza de Δh | Derivadas de P, T_água e T_vapor ou x; propagação por componentes | Mesma função física do valor central; ausência de incerteza não vira zero. Limites de primeira ordem permanecem. |

O ajuste do baseline usa somente a referência e exclui períodos não explicitamente estáveis;
os resíduos são calculados depois da referência. Não substitui a detecção principal.
O UA é calculado nas condições médias após validar cada linha: não deve ser chamado de média
dos UAs. A perda por purga não fecha automaticamente o resíduo nem prova a causa do desvio.

## Hipóteses e limitações que continuam

- O caminho legado do balanço direto ainda avalia a entalpia da água à pressão do vapor.
  A nova rota por vazões foi separada dessa aproximação; a revisão do legado permanece pendente.
- Saturado seco, x = 1, permanece como hipótese explícita de compatibilidade em dados legados.
- Inferência de superaquecimento por T > Tsat + 1 °C é uma regra do protótipo, sem orçamento
  metrológico completo para a classificação de fase. Precisa de revisão junto aos instrumentos.
- A cobertura mínima padrão de 50% e o fator de lacuna 3 são parâmetros de software,
  não critérios normativos nem prova de representatividade do período inteiro.
- Trapézios supõem variação linear entre extremos aceitos. Não há garantia sobre eventos
  não registrados entre leituras; duas amostras esparsas não comprovam continuidade.
- O novo balanço não dispõe de propagação completa de incerteza. Pode usar potência térmica
  fornecida pela planta, cuja base PCI/PCS e origem devem ser verificadas para evitar circularidade.
- Razões acima de 100% são sinalizadas para análise da base calorífica, fronteira e medições;
  não são truncadas artificialmente para parecer válidas.
- Purga assume líquido saturado na origem e não desconta recuperação de flash/calor.
- UA assume pressão constante e contracorrente equivalente, sem fator geométrico; não prova incrustação.
- Baseline empírico não inclui erros de medição em ambos os eixos nem autocorrelação explícita.
- As novas rotas estão na tela Dados e limites. A investigação causal e o relatório clássico
  ainda usam os períodos do fluxo legado; não foi afirmada integração completa de todo o SaaS.
- Dados públicos são testes parciais. Não existe nesta revisão validação em planta brasileira,
  economia demonstrada, diagnóstico causal validado ou certificação por norma industrial.

## Evidência e referências

Regressões novas verificam lacunas de combustível, regimes, ausência de estado, opção explícita
de cenário seco, pressão independente da água, valores infinitos, caldeiras distintas,
duplicatas, requisitos de purga e ambiguidades de aliases. Casos adicionais preservam o fluxo
do lado do vapor quando o combustível falta e impedem unir estados diferentes no mesmo trapézio.
Golden, tolerâncias e dados de demonstração não foram alterados.

A comparação com Wonji preserva a diferença de aproximadamente 2,1%, sem chamar discordância
de validação. O PDF original não pôde ser reaberto nesta sessão; a transcrição e a interpretação
de pressão absoluta/manométrica continuam pendentes de reconferência documental.

- [IAPWS R7-97(2012): formulação industrial de água e vapor](https://www.iapws.org/relguide/IF97-Rev.html).
- [NIST: previsão de uma resposta individual e sua incerteza](https://www.itl.nist.gov/div898/handbook/pmd/section5/pmd512.htm).
- [Dissertação Wonji-Shoa, registro institucional](https://etd.aau.edu.et/items/d499f255-f077-4f4c-9f8e-2a5d6663d91c).
- Dados e proveniência em `validation/public/` e testes independentes em `tests/test_validacao_*.py`.

**Parecer:** manter os módulos que já respeitam essas fronteiras como partes do protótipo.
Tratar balanço por vazões, UA, purga e baseline como recursos com limites explícitos e revisão
humana pendente. A prontidão comercial depende de validação de campo, além dos testes de código.
