# Matriz de validação física da EULER (Fase R)

Cada linha é uma verificação **executável** (teste automático) com a referência usada, a
tolerância e o motivo dela. Gerada na Fase R (01/10/2026) pelo agente de programação.
**Nenhuma linha é aprovação científica**: ver a legenda I / V / R em
`docs/revisao_motor_fisico.md`.

Tipos de verificação:

- **Independente**: a referência não usa o código do motor nem as mesmas hipóteses
  (tabela publicada, outra implementação, outro método numérico, cálculo à mão a partir
  das equações publicadas).
- **Consistência**: dados sintéticos gerados com hipóteses parecidas com as do motor.
  Mostra que o motor recupera o que foi plantado, **não** que a física está certa.
- **Regra**: comportamento exigido (bloqueio, aviso, recusa), sem valor numérico de
  referência.

Rodar tudo: `pip install -e ".[dev,validacao]"` e `pytest -q tests/test_validacao_*.py`.
Sem CoolProp e Cantera, as linhas que dependem deles são **puladas** (não falham).

## V-A · Água e vapor (`tests/test_validacao_vapor.py`)

| ID | O que verifica | Entrada | Esperado (fonte) | Motor (diferença) | Tolerância · por quê | Tipo | Situação |
|---|---|---|---|---|---|---|---|
| V-A1 | Entalpia da água, região 1 | (300 K; 3 MPa), (500 K; 3 MPa) | 115,331273 e 975,542239 kJ/kg (IAPWS R7-97(2012), Tabela 5) | ≤ 1·10⁻⁷ kJ/kg | 10⁻³ kJ/kg: acima do arredondamento (9 algarismos), muito abaixo de qualquer efeito | independente | passa¹ |
| V-A2 | Entalpia do vapor, região 2 | (300 K; 3,5 kPa), (700 K; 3,5 kPa) | 2549,91145 e 3335,68375 kJ/kg (Tabela 15) | ≤ 4·10⁻⁶ kJ/kg | idem | independente | passa¹ |
| V-A3 | Temperatura de saturação | 0,1; 1; 10 MPa | 372,755919; 453,035632; 584,149488 K (Tabela 36) | ≤ 4·10⁻⁷ K | 10⁻⁵ K: idem | independente | passa¹ |
| V-A4 | Unidades bar ↔ MPa, kJ ↔ MJ | 10 bar abs | T_sat(1 MPa), Tabela 36 | ≤ 4·10⁻⁷ K | idem | independente | passa |
| V-A5 | Δh do golden V01 por outra formulação | 10 bar abs, saturado seco, água a 80 °C | IAPWS-95 (CoolProp 8.0, HEOS) | 0,075 kJ/kg | 0,1 kJ/kg (0,004%), escolhida **depois** de ver a diferença; ~200× menor que o efeito de x = 0,99 | independente | passa (conferir limites IF97 × IAPWS-95) |
| V-A6 | Vapor úmido pelo título | x = 0,98 a 10 bar abs | h_f + x·h_fg (à mão) | 4·10⁻¹⁶ MJ/kg | relativa 10⁻⁶ | independente | passa |
| V-A7 | Golden V01 do kit | 10 bar abs, 80 °C | 2,4414 MJ/kg (`tests/golden`) | — | do kit (não alterada) | independente | passa |
| V-A8 | Eficiência nunca é entrada (E13) | assinaturas das funções | nenhuma recebe eficiência | — | — | regra | passa (`test_direto.py`) |

¹ Os valores das tabelas foram conferidos em duas implementações independentes (`iapws`
e CoolProp, backend IF97), porque o site iapws.org estava bloqueado na sessão. **Pendente:
conferir no documento original.**

## V-B · Combustão e chaminé (`tests/test_validacao_combustao.py`, `tests/test_indireto.py`)

| ID | O que verifica | Entrada | Esperado (fonte) | Motor (diferença) | Tolerância · por quê | Tipo | Situação |
|---|---|---|---|---|---|---|---|
| V-B1 | Conservação de massa por elemento | 5 composições sorteadas, w 20–55%, O₂ 4–12% | entra (comb. seco + ar + água) = sai (gases secos + água) | 2·10⁻¹⁶ (relativa) | relativa 10⁻¹²: identidade algébrica | independente | passa |
| V-B2 | λ pela fórmula fechada | O₂ = 2, 4, 8, 12, 16% | bissecção de y_O₂(λ) (outro método) | ≤ 10⁻⁹ | relativa 10⁻⁹: precisão da bissecção | independente | passa |
| V-B3 | G01 passo a passo | 180 °C, 8%, w 40% | a = 0,0432448; λ = 1,611; perda 11,773% (E1–E6 à mão) | 0 (mesmo número) | igualdade com o cálculo à mão | independente | passa |
| V-B4 | Orvalho da água nos gases | G01 | T_sat(p_H₂O) pela IAPWS-95 (CoolProp) | < 0,05 K | 0,05 K: IF97 × IAPWS-95 | independente | passa |
| V-B5 | ΔH sensível pelos polinômios NASA (modo experimental) | N₂, O₂, CO₂, H₂O; 25→180, 25→300, 1→450 °C | equações de estado de referência (CoolProp) a 100 Pa | máx. 0,11% (CO₂, 25→180 °C) | 0,3%: ajustes de dados diferentes; típico < 0,1% | independente | passa |
| V-B6 | Coeficientes NASA copiados sem erro | 6 espécies | `nasa_gas.yaml` do Cantera 3.2.0 (NASA TM-4513) | igual | relativa 10⁻¹² | independente | passa |
| V-B7 | ΔH de combustão do CO | 298,15 K | 393,51 − 110,53 kJ/mol (formação, NIST-JANAF) | < 0,05 kJ/mol | 0,05 kJ/mol: arredondamento dos valores citados | independente | passa (valores de formação **citados de memória: conferir**) |
| V-B8 | Umidade absoluta do ar | 25 °C, UR 60% | 0,622·φ·p_sat/(p − φ·p_sat), p_sat = 3,1699 kPa | 0,005% | relativa 10⁻³: p_sat com 5 algarismos | independente | passa |
| V-B9 | O₂ úmido ↔ seco | G01 | ida pelas quantidades de gás, volta pela função | < 10⁻¹² p.p. | precisão da bissecção | independente | passa |
| V-B10 | Perda por CO | 200 ppm, G01 | x_CO · n_gases_secos · ΔH_c ÷ PCI (à mão) | 0,0001% | relativa 10⁻⁴: ΔH_c com 6 algarismos | independente | passa |
| V-B11 | Golden G01–G12 do kit | 12 casos | `tests/golden/casos_referencia.csv` | dentro da tolerância do kit | do kit (não alterada) | independente | passa |
| V-B12 | O motor não usa as ferramentas de verificação | código de `euler/` | sem `import CoolProp` / `cantera` | — | — | regra | passa |
| V-B13 | Entradas fisicamente impossíveis | O₂ ≥ 21% ou < 0; gases abaixo do orvalho; gases mais frios que o ar; composição incompleta ou > 1 | bloqueio com motivo | — | — | regra | passa (`test_indireto.py`) |
| V-B14 | Polinômio fora da faixa | ar a 10 °C (SO₂ começa em 300 K) | aviso de extrapolação | — | — | regra | passa |
| V-B15 | cp(T) × constante | G01–G12 | diferença de −0,30 a −0,41 p.p. (< 0,5 p.p., critério do T07) | — | 0,5 p.p. do T07 | consistência | passa |

## V-C · Combustível, estoque e pátio (`tests/test_validacao_combustivel_incerteza.py`, `tests/test_combustivel.py`, `tests/test_demo.py`)

| ID | O que verifica | Entrada | Esperado (fonte) | Motor | Tolerância · por quê | Tipo | Situação |
|---|---|---|---|---|---|---|---|
| V-C1 | Cenários do pátio | S₀ = 10 t a 10 MJ/kg; lotes 20 t a 8 e 20 t a 9; S₁ = 10 t | recebido 8,50; FIFO 8,75; mín. 8,25; máx. 9,00 (à mão, no docstring) | igual | relativa 10⁻⁶ | independente | passa |
| V-C2 | Qualidade muda entre recebimento e queima | degrau de umidade 30% → 45% com estoque | FIFO > recebido; mín ≤ recebido, FIFO ≤ máx; fração de estoque = (S₀+S₁)/M | igual | — | regra | passa |
| V-C3 | Recebimento no mesmo instante da medição de estoque | lote às 07:30 | bloqueio "mesmo horário" (D49) | igual | — | regra | passa |
| V-C4 | Período sem estoque no limite | início 1 h depois da medição | bloqueio "estoque inicial" | igual | — | regra | passa |
| V-C5 | Totalizador reiniciado no período | −1.000 t no meio | vapor bloqueado, "reiniciou" | igual | — | regra | passa |
| V-C6 | Períodos sobrepostos | referência contém a comparação | recusa (D50) | igual | — | regra | passa |
| V-C7 | E5, E9, E10 e bloqueios | golden P01–P05; balanço negativo; lote sem massa; sem estoque | valores do kit; bloqueio com motivo | igual | do kit | independente + regra | passa |
| V-C8 | Gerador do demo: totalizador conta durante a lacuna do diário | arquivo gerado | vazão através da lacuna ≈ vazão típica (±20%) | 1,00 (a versão antiga dava 0,058) | 20%: variação diária da carga | regressão | passa |
| V-C9 | Gerador do demo: entregas antes da medição de estoque seguinte | arquivo gerado | todas antes das 07:30 do dia seguinte | sim | — | regressão (proteção; a versão antiga não violava com a semente atual) | passa |

## V-D · Incerteza (GUM e Monte Carlo)

Monte Carlo segundo a ideia do JCGM 101:2008 (propagação de distribuições): sorteia os
erros (400.000 amostras) e mede a dispersão do resultado; é **outro método**, sem a
aproximação de primeira ordem usada no motor.

| ID | O que verifica | Esperado | Motor × Monte Carlo | Tolerância · por quê | Tipo | Situação |
|---|---|---|---|---|---|---|
| V-D1 | Conversão da incerteza declarada | padrão → u; expandida k → U/k (GUM 4.3.3); limite ou sem tipo → a/√3 (GUM 4.3.7) | igual | — | regra (seções do GUM **a conferir**) | passa |
| V-D2 | A mesma medição de estoque fecha um período e abre o outro | efeitos se somam na diferença (r = 1 exato) | +0,19% | 1%: erro estatístico do MC | independente | passa |
| V-D3 | Mesmo medidor nos dois períodos (r = 1) e medidor trocado (r = 0) | r = 1 quase cancela; r = 0 soma | −0,08% e +0,12% | 3%: termos de segunda ordem | independente | passa |
| V-D4 | Hipótese compartilhada (umidade) nos dois caminhos do resíduo | propagação conjunta | −0,24% (tratar como independentes erraria 7,9%) | 2% | independente | passa |
| V-D5 | Componente sistemático do medidor não cai com √n | 3 dias × 21 dias | mesma contribuição | igualdade | regra | passa |
| V-D6 | Erro da balança comum às pesagens (D45) | n·u/M | igual | relativa 10⁻¹² | regra | passa |

## V-E · Investigação

| ID | O que verifica | Esperado | Resultado | Tipo | Situação |
|---|---|---|---|---|---|
| V-E1 | Explicações concorrentes: gases mais quentes (+perda) e combustível mais seco ao mesmo tempo; perda do período calculada pela calculadora de referência do `lab/` | umidade `sustentada` ("Combustível mais seco…"); temperatura dos gases `oposta` (não `descartada`); fechamento "fecha"; conclusão diz que compensou; próxima verificação cita as duas | igual | consistência² | passa |
| V-E2 | Casos A, B, C, contraexemplo da purga, semana sem vapor (`test_investigacao.py`) | explicação plantada recuperada; abstenção quando falta dado ou sobra mudança | igual | consistência² | passa |
| V-E3 | Fator detectável mas pequeno demais (D29) | `descartada` com o motivo | igual | regra | passa |
| V-E4 | Sem comando operacional | JSON e relatório sem verbos proibidos (lista em `relatorio.py`) | igual | regra | passa |
| V-E5 | Caso de demonstração (semanas 5–6, 7, 8) | o gabarito do `LEIAME.md` | igual | consistência³ | passa |

² O construtor de casos (`tests/construtor_caso.py`) usa a perda da tabela golden e o Δh do
próprio módulo `euler.vapor`: as hipóteses são as mesmas do motor.
³ O gerador do demo não importa o motor, mas usa sensibilidades do mesmo documento de
física e um modelo de pilha próprio (média dos últimos 12 lotes). **Não é validação
independente.**

## O que ainda não foi verificado (e por quê)

| ID | Falta | Por quê | Como fechar |
|---|---|---|---|
| P-1 | Valores das tabelas IAPWS lidos no documento original | site bloqueado na sessão | revisor confere as Tabelas 5, 15 e 36 da R7-97(2012) |
| P-2 | Texto das seções do GUM e do JCGM 101 citadas | bipm.org bloqueado; seções citadas de memória | revisor confere 4.3.3, 4.3.7, 5.1.3, 5.2.2, 6.2.1, 6.3.3 |
| P-3 | Entalpias de formação NIST-JANAF (CO, CO₂) | webbook.nist.gov bloqueado | conferir na tabela JANAF |
| P-4 | **Comparação com uma caldeira real medida** | não há dados reais no repositório (regra do projeto) | ensaio de desempenho com método normalizado, escolhido pelo revisor, com dados anonimizados |
| P-5 | Título do vapor, base do O₂, orvalho ácido, purga, uso do pátio | dependem de medição ou de decisão (Q1, Q2, Q5, Q6, Q7) | respostas em `docs/perguntas_revisores.md` |
| P-6 | Representatividade da amostragem de umidade | não há dados de amostras em duplicata | Q14 |
