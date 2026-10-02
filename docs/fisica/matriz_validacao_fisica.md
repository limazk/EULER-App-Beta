# Matriz de validação física da EULER

Cada linha é uma verificação **executável** (teste automático) com a referência usada, a
tolerância e o motivo dela. Criada na Fase R e reclassificada depois da auditoria externa
de 01/10/2026 (versão examinada `2cd4dc3`). **Nenhuma linha é aprovação científica**: ver
a legenda I / V / R em `docs/fisica/revisao_motor_fisico.md`.

## Categorias (o que cada verificação demonstra)

A auditoria mostrou que "verificação independente" misturava coisas diferentes. Agora cada
linha tem **uma** categoria:

| Categoria | O que é | O que demonstra | O que **não** demonstra |
|---|---|---|---|
| **1 · Externa** | referência fora do projeto: tabela publicada, outra formulação, outra base de dados | que o número bate com uma fonte reconhecida, no ponto testado | que as hipóteses do modelo valem para uma caldeira real |
| **2 · Outro método** | mesmas equações, resolvidas de outro jeito (à mão, outro algoritmo, Monte Carlo, derivada pela cadeia inteira) | que a implementação faz o que as equações dizem | que as equações estão certas |
| **3 · Identidade** | ida e volta, identidade algébrica, ou conta que usa números do próprio motor | coerência interna | nada sobre a referência externa |
| **4 · Regra** | comportamento exigido: bloqueio, aviso, recusa, texto | que o produto não conclui além dos dados | nada sobre números |
| **Consistência** | dados sintéticos gerados com hipóteses parecidas com as do motor | que o motor recupera o que foi plantado | que a física está certa |
| **Regressão** | proteção contra a volta de um erro já corrigido | que o erro não voltou | — |
| **Golden** | valores do kit revisado pela equipe (`tests/golden/`, não editados) | igualdade com a referência do projeto | conferência externa dos próprios valores golden |

Rodar: `pip install -e ".[dev,validacao]"` e `pytest -q`. Sem CoolProp e Cantera, as linhas
que dependem deles são **puladas** (não falham). Na auditoria, o CI do GitHub rodou tudo
(243 testes, nenhum pulado); numa reprodução local em Windows, o Controle de Aplicativo
bloqueou a biblioteca do CoolProp — limitação daquele ambiente, não divergência física.

## Resumo (57 linhas)

| Categoria | Linhas |
|---|---|
| 1 · Externa | 10: V-A1, V-A2, V-A3, V-A4, V-A5, V-A9, V-B4\*, V-B5, V-B6, V-B7 |
| 2 · Outro método | 8: V-B2, V-B3, V-B8, V-C1, V-D2, V-D3, V-D4, V-D7 |
| 3 · Identidade | 5: V-A6, V-B1, V-B9, V-B10, V-D8 |
| 4 · Regra | 25: V-A8, V-B12, V-B13, V-B14, V-B16, V-B17, V-C2 a V-C6, V-C10 a V-C13, V-D1, V-D5, V-D6, V-D9, V-D10, V-E3, V-E4, V-E6, V-E7, V-E8 |
| Consistência | 4: V-B15, V-E1, V-E2, V-E5 |
| Regressão | 2: V-C8, V-C9 |
| Golden | 3: V-A7, V-B11, V-C7 |

\* V-B4 é mista: a pressão parcial da água vem do motor; só T_sat vem da IAPWS-95.

## V-A · Água e vapor (`tests/test_validacao_vapor.py`)

| ID | O que verifica | Entrada | Esperado (fonte) | Motor (diferença) | Tolerância · por quê | Categoria | Situação |
|---|---|---|---|---|---|---|---|
| V-A1 | Entalpia da água, região 1 | (300 K; 3 MPa), (500 K; 3 MPa) | 115,331273 e 975,542239 kJ/kg (IAPWS R7-97(2012), Tabela 5) | ≤ 1·10⁻⁷ kJ/kg | 10⁻³ kJ/kg: acima do arredondamento das tabelas | 1 · externa | passa¹ |
| V-A2 | Entalpia do vapor, região 2 | (300 K; 3,5 kPa), (700 K; 3,5 kPa) | 2549,91145 e 3335,68375 kJ/kg (Tabela 15) | ≤ 4·10⁻⁶ kJ/kg | idem | 1 · externa | passa¹ |
| V-A3 | Temperatura de saturação | 0,1; 1; 10 MPa | 372,755919; 453,035632; 584,149488 K (Tabela 36) | ≤ 4·10⁻⁷ K | 10⁻⁵ K | 1 · externa | passa¹ |
| V-A4 | Unidades bar ↔ MPa | 10 bar abs | T_sat(1 MPa), Tabela 36 | ≤ 4·10⁻⁷ K | idem | 1 · externa | passa¹ |
| V-A5 | Δh do golden V01 por outra formulação | 10 bar abs, saturado seco, água a 80 °C | IAPWS-95 (CoolProp 8.0, HEOS) | 0,075 kJ/kg | 0,1 kJ/kg, escolhida **depois** de ver a diferença (por isso V-A9) | 1 · externa | passa |
| V-A9 | Δh em **pontos reservados**, definidos antes de rodar | 18 pontos: 2–40 bar abs × água 20–150 °C (até 5 °C abaixo da saturação) | IAPWS-95 (CoolProp 8.0) | máx. 0,0065% | 0,01% de Δh, fixada **antes**: a EULER mostra η com 0,1 p.p. (≈ 0,125% relativo), 10× maior | 1 · externa | passa (folga de 35%) |
| V-A6 | Vapor úmido pelo título | x = 0,98 a 10 bar abs | h_f + x·h_fg, com h_f e h_g **do próprio módulo** | 4·10⁻¹⁶ MJ/kg | relativa 10⁻⁶ | 3 · identidade | passa |
| V-A7 | Golden V01 do kit | 10 bar abs, 80 °C | 2,4414 MJ/kg | — | do kit | golden | passa |
| V-A8 | Eficiência nunca é entrada (E13) | assinaturas | nenhuma função recebe eficiência | — | — | 4 · regra | passa |

¹ Valores conferidos no documento oficial pela auditoria externa (R7-97(2012), páginas
impressas 9, 17 e 36). Nesta sessão o site continuou bloqueado; aqui eles também batem com
duas implementações (`iapws` e CoolProp IF97).

## V-B · Combustão e chaminé (`tests/test_validacao_combustao.py`, `tests/test_indireto.py`)

| ID | O que verifica | Entrada | Esperado (fonte) | Motor (diferença) | Tolerância · por quê | Categoria | Situação |
|---|---|---|---|---|---|---|---|
| V-B1 | Conservação de massa por elemento | 5 composições sorteadas | entra = sai, com as massas de gases **do motor** | 2·10⁻¹⁶ | relativa 10⁻¹² | 3 · identidade | passa |
| V-B2 | λ pela fórmula fechada | O₂ = 2–16% | bissecção de y_O₂(λ) | ≤ 10⁻⁹ | precisão da bissecção | 2 · outro método | passa |
| V-B3 | G01 passo a passo | 180 °C, 8%, w 40% | E1–E6 à mão | 0 | igualdade | 2 · outro método | passa |
| V-B4 | Orvalho da água | G01 | T_sat(p_H₂O) pela IAPWS-95; p_H₂O **do motor** | < 0,05 K | IF97 × IAPWS-95 | 1 · externa (mista) | passa |
| V-B5 | ΔH sensível NASA (modo experimental) | N₂, O₂, CO₂, H₂O; 1–450 °C | equações de referência (CoolProp) a 100 Pa | máx. 0,11% | 0,3%: ajustes de dados diferentes | 1 · externa | passa |
| V-B6 | Coeficientes NASA copiados sem erro | 6 espécies | `nasa_gas.yaml` do Cantera 3.2.0 (NASA TM-4513) | igual | relativa 10⁻¹² | 1 · externa (rastreabilidade) | passa |
| V-B7 | ΔH de combustão do CO | 298,15 K | −393,51 − (−110,53) kJ/mol, **valores CODATA** no NIST WebBook | < 0,05 kJ/mol | arredondamento | 1 · externa | passa² |
| V-B8 | Umidade absoluta do ar | 25 °C, UR 60% | mesma fórmula à mão, p_sat = 3,1699 kPa | 0,005% | p_sat com 5 algarismos | 2 · outro método | passa |
| V-B9 | O₂ úmido ↔ seco | G01 | ida pelas quantidades de gás do motor, volta pela função | < 10⁻¹² p.p. | bissecção | 3 · identidade | passa |
| V-B10 | Perda por CO | 200 ppm, G01 | mesma fórmula, com n_gases **do motor** | 0,0001% | ΔH_c com 6 algarismos | 3 · identidade | passa |
| V-B11 | Golden G01–G12 | 12 casos | `tests/golden/casos_referencia.csv` | dentro da tolerância do kit | do kit | golden | passa |
| V-B12 | O motor não usa as ferramentas de verificação | código de `euler/` | sem `import CoolProp` / `cantera` | — | — | 4 · regra | passa |
| V-B13 | Entradas impossíveis | O₂ ≥ 21%; abaixo do orvalho; gases mais frios que o ar; composição inválida | bloqueio com motivo | — | — | 4 · regra | passa |
| V-B14 | Polinômio fora da faixa | ar a 10 °C (SO₂ desde 300 K) | aviso de extrapolação | — | — | 4 · regra | passa |
| V-B15 | cp(T) × constante | G01–G12 | −0,30 a −0,41 p.p. (< 0,5 p.p. do T07) | — | critério do T07 | consistência | passa |
| V-B16 | **O₂ úmido fora do domínio (A5)** | 20,9% úmido, w 40% | recusa com motivo (antes: 20,58% seco, menor que o úmido) | recusa | — | 4 · regra | passa |
| V-B17 | O₂ seco ≥ úmido (A5) | 24 combinações O₂ 0,5–18% × w 10–60% | seco ≥ úmido | sim | — | 4 · regra | passa |

² Valores conferidos pela auditoria externa no NIST WebBook (CODATA). A tabela JANAF dá
−393,52 kJ/mol para o CO₂ (0,01 kJ/mol de diferença, dentro da tolerância).

## V-C · Combustível, estoque e pátio

Arquivos: `tests/test_validacao_combustivel_incerteza.py`, `tests/test_confiabilidade.py`,
`tests/test_combustivel.py`, `tests/test_demo.py`.

| ID | O que verifica | Entrada | Esperado | Motor | Tolerância | Categoria | Situação |
|---|---|---|---|---|---|---|---|
| V-C1 | Cenários do pátio | S₀ = 10 t a 10 MJ/kg; 20 t a 8 e 20 t a 9; S₁ = 10 t | recebido 8,50; FIFO 8,75; mín. 8,25; máx. 9,00 (à mão) | igual | relativa 10⁻⁶ | 2 · outro método | passa |
| V-C2 | Qualidade muda entre recebimento e queima | degrau de umidade com estoque | FIFO > recebido; mín ≤ … ≤ máx | igual | — | 4 · regra | passa |
| V-C3 | Recebimento no instante do estoque | lote às 07:30 | bloqueio (D49) | igual | — | 4 · regra | passa |
| V-C4 | Período sem estoque no limite | início fora da medição | bloqueio | igual | — | 4 · regra | passa |
| V-C5 | Totalizador reiniciado | −1.000 t no meio | vapor bloqueado | igual | — | 4 · regra | passa |
| V-C6 | Períodos sobrepostos | — | recusa (D50) | igual | — | 4 · regra | passa |
| V-C7 | E5, E9, E10 e bloqueios | golden P01–P05; casos inválidos | valores do kit; bloqueio | igual | do kit | golden + regra | passa |
| V-C8 | Gerador: totalizador conta na lacuna | arquivo gerado | vazão na lacuna ≈ típica (±20%) | 1,00 (antes 0,058) | variação diária da carga | regressão | passa |
| V-C9 | Gerador: entregas antes da medição seguinte | arquivo gerado | todas antes das 07:30 | sim | — | regressão (proteção) | passa |
| V-C10 | **FIFO com massa sem qualidade (A1)** | contraexemplo da auditoria: S₀ = 10 t sem PCI | FIFO indisponível com motivo (antes: 8,333 MJ/kg só da parte conhecida) | indisponível | — | 4 · regra | passa |
| V-C11 | **A1 até o relatório** | lote sem amostra no estoque do período seguinte | FIFO fora da eficiência, do JSON e com aviso em "o que falta" e no relatório; hipótese do cenário "recebido" explícita | igual | — | 4 · regra | passa |
| V-C12 | **Consumo zero (A4)** | estoques iguais, sem recebimentos | bloqueio com motivo, sem falha (antes: divisão por zero) | igual | — | 4 · regra | passa |
| V-C13 | **Totalizador parado (A4)** | vapor zero no período | bloqueio com motivo; investigação se abstém (antes: divisão por zero) | igual | — | 4 · regra | passa |

## V-D · Incerteza

| ID | O que verifica | Esperado | Resultado | Tolerância | Categoria | Situação |
|---|---|---|---|---|---|---|
| V-D1 | Conversão da incerteza declarada | padrão → u; expandida com k → U/k (GUM 4.3.3); limite → a/√3 (GUM 4.3.7); **sem tipo → a/√3 por hipótese do projeto (D35)**, não por determinação do GUM | igual | — | 4 · regra | passa |
| V-D2 | Mesma medição de estoque nos dois períodos | r = 1 exato; efeitos se somam | Monte Carlo × fórmula: +0,19% | 1%: erro do MC | 2 · outro método³ | passa |
| V-D3 | Mesmo medidor (r = 1) e medidor trocado (r = 0) | — | −0,08% e +0,12% | 3% | 2 · outro método³ | passa |
| V-D4 | Hipótese compartilhada (umidade) | propagação conjunta | −0,24% | 2% | 2 · outro método³ | passa |
| V-D5 | Sistemático do medidor não cai com √n | 3 × 21 dias | igual | igualdade | 4 · regra | passa |
| V-D6 | Balança: erro comum às pesagens (D45) | n·u/M | igual | 10⁻¹² | 4 · regra | passa |
| V-D7 | **Resíduo publicado por `investigar`: cada fonte entra uma vez (A2)** | contribuição de umidade, PCI seco, água de alimentação e temperatura dos gases, nos dois períodos = derivada do resíduo **perturbando os dados** × incerteza da fonte | igual | 1%: derivada central × derivada à frente do motor | 2 · outro método (integração) | passa |
| V-D8 | Combinação r = 0 e r = 1 a partir das contribuições publicadas | mesma fonte somada dentro do período antes de combinar os períodos | igual | 10⁻⁹ | 3 · identidade | passa |
| V-D9 | **Orçamento completo / parcial / indisponível (A3)** | o que falta nunca vira zero; comparação parcial nunca diz "sim" | igual | — | 4 · regra | passa |
| V-D10 | **Sem instrumentos cadastrados (A3)** | Δh e η sem incerteza; resíduo "não avaliável" com o que falta; relatório sem "±0,0" (antes: Δh com incerteza 0 e resíduo "descartado") | igual | — | 4 · regra | passa |

³ V-D2 a V-D4 verificam a **função de combinação** com modelos simples montados no próprio
teste. Não executam a montagem real da investigação; foi por isso que o A2 passou. A
montagem real é verificada por V-D7 e V-D8.

## V-E · Investigação

| ID | O que verifica | Esperado | Categoria | Situação |
|---|---|---|---|---|
| V-E1 | Explicações concorrentes (perda do período pela calculadora do `lab/`) | umidade `sustentada`; temperatura dos gases `oposta`; fechamento "fecha" | consistência⁴ | passa |
| V-E2 | Casos A, B, C, purga, semana sem vapor | explicação plantada recuperada; abstenção quando falta dado | consistência⁴ | passa |
| V-E3 | Fator detectável mas pequeno demais (D29) | `descartada` com o motivo | 4 · regra | passa |
| V-E4 | Sem comando operacional | JSON e relatório sem verbos proibidos | 4 · regra | passa |
| V-E5 | Caso de demonstração | o gabarito do `demo/caso_demo/LEIAME.md` (revisto depois do A3) | consistência⁵ | passa |
| V-E6 | **Explicação só condicional (A3)** | umidade sem incerteza do método: não vira explicação; fechamento mostra que fecharia se confirmada; próxima verificação = cadastrar o que falta | 4 · regra | passa |
| V-E7 | **Relatório com os quatro estados da detecção** | sim / só se o erro se repetir / não / sem incerteza: textos diferentes | 4 · regra | passa |
| V-E8 | **Tela mostra o fator oposto e o fechamento** (falha encontrada nesta revisão: a tela não exibia as hipóteses `oposta`, só o relatório) | caso V-E1 aberto na tela real: rótulo "Mudou no sentido contrário" e frase de fechamento | 4 · regra | passa |

⁴ O construtor de casos usa a perda da tabela golden e o Δh do próprio `euler.vapor`.
⁵ O gerador do demo não importa o motor, mas usa sensibilidades do mesmo documento de
física. **Não é validação independente.**

## O que ainda não foi verificado

| ID | Falta | Situação | Como fechar |
|---|---|---|---|
| P-1 | Tabelas IAPWS no documento original | **conferido pela auditoria externa** (páginas 9, 17 e 36) | — |
| P-2 | Seções do GUM | auditoria conferiu 4.3.3, 4.3.7, 5.2.2 e 6.3.3; **faltam 5.1.3 e 6.2.1**. A 4.3.7 **não** autoriza tratar incerteza sem tipo como limite: isso é hipótese do projeto (D35) | revisor |
| P-3 | Entalpias de formação | **conferido pela auditoria** (CODATA no NIST WebBook) | — |
| P-4 | **Comparação com uma caldeira real** | não feita; sem dados reais no repositório | ensaio de referência com dados autorizados e critérios definidos antes de ver os resultados |
| P-5 | Título, base do O₂, orvalho ácido, purga, uso do pátio | dependem de medição ou decisão | `docs/fisica/perguntas_revisores.md` |
| P-6 | Representatividade da amostragem de umidade | sem amostras em duplicata | Q14 |
| P-7 | **Casos reservados independentes da lógica do motor** | não existem: todos os casos de investigação usam hipóteses do motor | montar casos por outra pessoa ou outro cálculo, guardados fora do alcance de quem ajusta o motor |
