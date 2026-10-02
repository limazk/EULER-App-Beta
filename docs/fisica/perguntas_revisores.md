# Perguntas para os revisores do motor físico

Para: professores / doutorandos que revisam a física da EULER. Preparado pelo agente de
programação em 01/10/2026. Cada pergunta traz **a hipótese atual**, **por que importa**,
**alternativas** e um **exemplo numérico** calculado com o código (versão indicada em
`docs/fisica/revisao_motor_fisico.md`, seção 5). Os números são de casos sintéticos: servem para
dar a ordem de grandeza, não descrevem nenhuma caldeira real.

Como responder: escreva a escolha e a fonte ao lado da pergunta (ou em
`docs/fisica/fisica_para_revisao.md`); a decisão correspondente em `docs/gestao/decisoes.md` passa de
"pendente" para "aprovada por …". **Enquanto não houver resposta, o comportamento atual
continua marcado como proposta.**

Os efeitos citados são **sensibilidades calculadas nas condições indicadas** (casos
sintéticos), não constantes universais nem valores medidos numa instalação.

## Pauta da reunião: três decisões prioritárias

Recomendação da auditoria externa de 01/10/2026: começar por estas três, cada uma com um
exemplo e a consequência no relatório. As perguntas Q1–Q17 ficam como apêndice.

### Decisão 1 · Qual combustível foi realmente queimado? (Q7, D22, D38, D51)
- **Hoje:** o cenário central é "o que entra é o que queima"; lotes sem amostra entram com
  a média dos medidos (hipótese agora declarada). O FIFO fica indisponível quando
  queimaria massa sem qualidade conhecida. Mínimo e máximo são limites contábeis.
- **Exemplo (demo, semanas 5–6):** o FIFO não pode ser calculado (86 t que ele queimaria
  vêm de lotes sem amostra). Na semana 1, η = 79,3% no cenário central, com limites
  contábeis de 72,2% a 95,5%. O limite de cima é incompatível com a perda nos gases de
  12,4% calculada para o mesmo período (mesma fronteira e base PCI); é cenário, não
  intervalo de confiança, e não é cortado.
- **No relatório:** o FIFO indisponível e a hipótese dos lotes sem amostra aparecem em
  "O que falta saber"; a faixa do pátio aparece na tela "Dados e limites".
- **Decidir:** medir a umidade do pátio ou da alimentação? Aceitar a média dos medidos para
  lotes sem amostra, ou bloquear? Qual modelo de pilha descreve o manejo do cliente?

### Decisão 2 · Como medir a umidade e o estado do vapor (Q1, Q14, D21, D52)
- **Hoje:** sem a incerteza do método de umidade cadastrada, a mudança da umidade recebida
  só é "condicional" (vale se o erro da estufa se repetir nos dois períodos) e **não** vira
  explicação. Título do vapor assumido x = 1.
- **Exemplo (demo, semanas 5–6):** umidade 43,2% → 46,4%; parte conhecida da incerteza
  ±1,7 p.p. → "condicional"; a EULER se abstém e pede o cadastro. Com uma incerteza de
  método de 0,5 ponto (valor **ilustrativo**, não está no demo), a diferença passa a
  ±1,9 p.p., a mudança passa a "sim" e a umidade volta a ser explicação compatível. Título
  x = 0,98 em vez de 1 reduziria Δh em 1,65% (a 11 bar abs, água a 85 °C).
- **No relatório:** "Não dá para concluir: o resto da mudança seria explicado por
  combustível mais úmido (menos energia por tonelada), mas essa mudança ainda não está
  confirmada, porque falta cadastrar a incerteza do método de umidade (estufa)"; próxima
  verificação: cadastrar essa incerteza.
- **Decidir:** que incerteza declarar para o método de umidade (e com que tipo)? Quantas
  amostras por lote? Medir o título?

### Decisão 3 · Como interpretar incertezas, correlações e o critério D29 (Q8, Q9, Q11, Q16)
- **Hoje:** incerteza sem tipo = limite ±a (hipótese do projeto, D35; o GUM 4.3.7 só trata
  de limites conhecidos). Erro do mesmo instrumento: calculamos r = 0 e r = 1. Fator de
  relevância D29 = 0,5.
- **Exemplo (demo, semanas 5–6):** consumo +10,1%; incerteza ±3,6% com r = 0 e ±1,1% com
  r = 1. Com D29 = 0,5 a temperatura dos gases é explicação compatível (efeito +3,1%,
  limiar 1,8%); com D29 = 1,0 seria descartada. "3% da leitura" sem tipo dá u = 1,73%;
  com k = 2, daria 1,50%.
- **No relatório:** "Mudou de forma detectável?" mostra quatro estados (sim / só se o erro
  do mesmo instrumento se repetir / não / sem incerteza para dizer).
- **Decidir:** manter a leitura "sem tipo = limite"? Aceitar os dois extremos de r ou
  fixar outro valor? Qual fator D29?

---

## Apêndice: perguntas Q1–Q17

Prioridade: **A** = pode mudar a conclusão de uma investigação; **B** = muda números
absolutos, raramente a conclusão; **C** = forma de apresentar.

| # | Tema | Prioridade | Decisão ligada |
|---|---|---|---|
| Q1 | Título do vapor e energia útil | B | D09, D46 |
| Q2 | Base do O₂ (seca × úmida) | A | D43 |
| Q3 | Umidade do ar de combustão | B | D41 |
| Q4 | CO e incombustos | B | D10, D42 |
| Q5 | Orvalho ácido | B | D06, D07 |
| Q6 | Purga e fronteira do balanço direto | B | D27, D39 |
| Q7 | Uso do pátio: recebido × queimado | **A** | D22, D38 |
| Q8 | Correlação do erro do mesmo instrumento entre períodos | **A** | D37 |
| Q9 | Critério de relevância D29 | **A** | D29, D44 |
| Q10 | Fonte de cp(T) | B | D40 |
| Q11 | Como ler a incerteza declarada (k, limites) | **A** | D35, D36 |
| Q12 | Balança e medição de estoque: parte sistemática | B | D45 |
| Q13 | Constante de vaporização no PCI úmido (E5) | C | E5 |
| Q14 | Representatividade da amostra de umidade | **A** | D21 |
| Q15 | Média simples × média ponderada pela carga | B | D25 |
| Q16 | Detecção com U = 2u e muitas comparações | **A** | D25, D37 |
| Q17 | Fechamento: efeitos um por vez, compostos em log | B | D48 |

---

### Q1 · Título do vapor e energia útil
- **Hipótese atual:** vapor saturado seco, x = 1, quando o título não é medido (D09).
  Energia útil intervalo a intervalo quando há p e T_a em todos os intervalos (D46).
- **Por que importa:** η direta é proporcional a Δh. Um título menor que 1 reduz a energia
  útil real e faz a EULER **superestimar** η. Nas comparações entre períodos o efeito
  cancela se o título for o mesmo nos dois.
- **Alternativas:** (a) manter x = 1 e informar a sensibilidade (atual); (b) adotar um
  x típico por tipo de caldeira (precisa de fonte); (c) exigir medição (calorímetro de
  estrangulamento) para η absoluta.
- **Exemplo:** 11 bar abs, água a 85 °C, Δh = 2,424 MJ/kg. x = 0,99 → Δh −0,82%;
  x = 0,98 → −1,65%. Uma η de 0,80 com x = 0,98 real seria 0,787.

### Q2 · Base do O₂ (seca × úmida)
- **Hipótese atual:** o O₂ informado está em **base seca** (E2). Existe a conversão
  úmida → seca (`o2_seco_equivalente`, D43), mas o motor não sabe a base do analisador.
- **Por que importa:** analisadores in situ (zircônia) medem em base úmida; extrativos
  com condicionamento, em base seca. Ler úmido como seco subestima λ e a perda.
- **Alternativas:** (a) campo obrigatório "base do O₂" no cadastro do analisador;
  (b) assumir úmida para zircônia in situ; (c) bloquear a perda sem a base declarada.
- **Exemplo:** G01 (180 °C, w = 40%): 8,0% úmido equivale a 9,44% seco; a perda passa de
  11,77% para 12,92% (+1,15 p.p.). Nos 12 casos golden: +0,44 a +1,69 p.p.

### Q3 · Umidade do ar de combustão
- **Hipótese atual:** ar seco (como no golden). A umidade do ar é opcional (D41).
- **Por que importa:** a água do ar também sai aquecida pela chaminé.
- **Alternativas:** (a) desprezar (atual); (b) usar T e UR do ar quando medidas;
  (c) usar um valor climático do local (precisa de fonte).
- **Exemplo:** 25 °C e UR 60% → W = 0,0119 kg/kg de ar seco → +0,20 p.p. no G01.
  Pequeno para comparações no mesmo clima; pode aparecer entre estações do ano.

### Q4 · CO e incombustos
- **Hipótese atual:** combustão completa no λ e na perda; CO > 200 ppm só gera aviso (D10).
  A perda por CO existe como função separada e **não** é somada (D42).
- **Por que importa:** com CO alto, parte do combustível não libera energia; isso aparece
  no resíduo "outras perdas" e pode ser confundido com purga ou casco.
- **Alternativas:** (a) manter separado (atual); (b) somar a perda por CO quando o CO for
  medido; (c) incluir carbono nas cinzas (exige análise das cinzas).
- **Exemplo:** G01: 200 ppm → 0,11% do PCI; 1.000 ppm → 0,55% do PCI
  (ΔH_c(CO) = 282,98 MJ/kmol; valores de formação NIST-JANAF a conferir).

### Q5 · Orvalho ácido
- **Hipótese atual:** só o orvalho da **água** (T_sat na pressão parcial, D06); sem SO₃.
  O alerta de aproximação ao orvalho não tem valor padrão (D07).
- **Por que importa:** o orvalho ácido é mais alto que o da água; abaixo dele há corrosão e
  a perda calculada deixa de valer (condensação).
- **Alternativas:** (a) manter só água (cavaco tem pouco enxofre); (b) adotar uma
  correlação publicada de orvalho ácido — **o revisor escolhe a fonte; nenhuma foi
  implementada nem terá coeficiente inventado**; (c) margem fixa sobre o orvalho da água.
- **Exemplo:** G01: orvalho da água = 56,7 °C (conferido com a IAPWS-95 a ±0,05 K).

### Q6 · Purga e fronteira do balanço direto
- **Hipótese atual:** purga **fora** da energia útil (D27, D39). Ela entra, junto com casco,
  cinzas e vazamentos, no resíduo "outras perdas".
- **Por que importa:** define o que é "eficiência". Se a purga for tratada como útil, η sobe.
- **Alternativas:** (a) fora (atual); (b) dentro, se a purga for medida; (c) estimar a
  purga pela razão de concentração (exige condutividade da água).
- **Exemplo (hipotético):** purga contínua de 2% do vapor a 11 bar abs, água a 85 °C:
  energia da purga = 0,35% da energia útil; com 5%, 0,88%.

### Q7 · Uso do pátio: recebido × queimado (prioridade alta)
- **Hipótese atual:** a qualidade do combustível queimado não é conhecida. O motor mostra
  cenários: `recebido` ("o que entra é o que queima", D22; lotes sem amostra com a média
  dos medidos, D51), `fifo` (indisponível se queimaria massa sem qualidade conhecida) e os
  limites `minimo`/`maximo` (D38). O efeito da umidade sai com a faixa recebido–FIFO; o
  resíduo que muda de veredito conforme o cenário fica `nao_avaliavel`.
- **Por que importa:** em períodos curtos o estoque é grande perto do consumido. No demo,
  (S₀+S₁)/M_f vai de 17% (4 semanas) a 81% (1 semana).
- **Alternativas:** (a) cenários (atual); (b) medir a umidade do **pátio** ou da
  alimentação da fornalha; (c) modelo de pilha (mistura completa, LIFO) se o cliente
  descrever o manejo; (d) exigir períodos longos (≥ 4 semanas). Cortar os limites num teto
  para parecerem plausíveis **não** é alternativa: esconderia quanto o pátio pesa.
- **Exemplo:** semana 1 do demo: η = 0,793 (recebido), limites contábeis 0,722–0,955. O de
  cima é incompatível com a perda nos gases de 12,4% do mesmo período (mesma fronteira e
  base); não é intervalo de confiança. Semanas 1–4: 0,775–0,842. Nas semanas 5–6 o FIFO
  não pode ser calculado (lotes sem amostra), e o efeito da umidade fica só no cenário
  recebido (+7,8% no consumo).

### Q8 · Correlação do erro do mesmo instrumento entre períodos (prioridade alta)
- **Hipótese atual:** mesma leitura nos dois períodos → r = 1 exato. Mesmo instrumento sem
  calibração ou troca entre os períodos → r desconhecido; o motor calcula r = 0 e r = 1 e
  chama de `condicional` o que só aparece com r = 1 (D37). Instrumento trocado → r = 0.
- **Por que importa:** é o que decide se uma mudança pequena de consumo é detectável.
- **Alternativas:** (a) dois extremos (atual); (b) adotar um r intermediário (precisa de
  justificativa); (c) separar no cadastro a parte sistemática (calibração) da aleatória.
- **Exemplo:** semanas 1–4 × 5–6 do demo: Δconsumo = +10,1%; U = ±3,6% com r = 0 e ±1,1%
  com r = 1. Semana 8 (medidor reinstalado): ±3,7% nos dois casos.

### Q9 · Critério de relevância D29 (prioridade alta)
- **Hipótese atual:** um fator só é "explicação compatível" se o efeito esperado no
  consumo for ≥ **0,5 ×** U(Δconsumo) com r = 0.
- **Por que importa:** o fator 0,5 não tem fonte; ele decide se fatores médios entram.
  O JSON mostra o que mudaria com 0 e com 1,0 (`criterios.sensibilidade_d29`).
- **Alternativas:** 0 (qualquer fator detectável e no sentido certo); 0,5 (atual); 1,0
  (só fatores que sozinhos seriam detectáveis no consumo); outro critério (ex.: fração da
  mudança observada).
- **Exemplo:** semanas 5–6: limiar 1,8%. Temperatura dos gases: efeito +3,1% → compatível.
  Com fator 1,0 (limiar 3,6%) seria descartada; com 0, a condição do vapor (efeito 0,01%)
  viraria "possível".

### Q10 · Fonte de cp(T)
- **Hipótese atual:** cp constante (1,05 e 1,90 kJ/kg·K) é a **referência** (golden). O modo
  cp(T) experimental usa os polinômios NASA (TM-4513, via Cantera 3.2.0) (D40).
- **Por que importa:** a perda absoluta muda; as diferenças entre períodos mudam pouco.
- **Alternativas:** (a) NASA 7 coeficientes (implementado, experimental); (b) tabelas
  NIST-JANAF; (c) Shomate (NIST WebBook); (d) manter constante e declarar o viés.
- **Exemplo:** G01–G12: cp(T) dá −0,30 a −0,41 p.p. em relação ao constante. NASA ×
  equações de referência (CoolProp, 100 Pa) para N₂, O₂, CO₂ e H₂O entre 1 e 450 °C:
  diferença máxima 0,11% em ΔH.

### Q11 · Como ler a incerteza declarada (prioridade alta)
- **Hipótese atual:** colunas `incerteza_tipo` e `incerteza_k`. `limite` → u = a/√3 (GUM
  4.3.7, limites conhecidos). Sem tipo, ou "expandida" sem k → **hipótese do projeto**: o
  valor é lido como limite e recebe o mesmo modelo retangular. O GUM não determina isso.
  Resultados com U = 2u, sem prometer 95% (D35, D36; GUM 6.3.3 dá as condições para ~95%).
- **Por que importa:** muda a largura de todos os intervalos e, com isso, o que é
  detectável.
- **Alternativas:** (a) limite por padrão (atual: mais cauteloso que k = 2, menos que
  supor incerteza-padrão); (b) k = 2 por padrão (antiga D24); (c) bloquear sem tipo
  declarado.
- **Exemplo:** estoque com "3% da leitura": u = 1,73% (retangular) × 1,50% (k = 2).
  Diferença de 15% na largura do intervalo.

### Q12 · Balança e medição de estoque: parte sistemática
- **Hipótese atual:** o erro da balança é tratado como comum a todas as pesagens do período
  (n·u, D45). Cada medição de estoque tem seu próprio erro; a parte sistemática comum do
  método de levantamento do estoque **não** está incluída (listada em `nao_incluidos`).
- **Por que importa:** E9 depende de estoques medidos com método grosseiro.
- **Alternativas:** (a) atual; (b) cadastrar separadamente a parte sistemática e a
  aleatória de cada instrumento; (c) para o estoque, usar a dispersão de medições
  repetidas.
- **Exemplo:** semana 1 do demo, 27 pesagens, M = 786 t: balança 0,10% (n·u) × 0,02%
  (√n·u). Estoques: 0,58% e 0,66%. Total u = 0,88%.

### Q13 · Constante de vaporização no PCI úmido (E5)
- **Hipótese atual:** PCI_u = (1 − w)·PCI_s − 2,442·w, com 2,442 MJ/kg a 25 °C.
- **Por que importa:** pouco; define a referência de temperatura da água evaporada.
- **Alternativas:** 2,442 (25 °C, atual); 2,5 (0 °C); valor da norma usada pelo laboratório.
- **Exemplo:** w = 40%: 10,123 × 10,100 MJ/kg (−0,23%).

### Q14 · Representatividade da amostra de umidade (prioridade alta)
- **Hipótese atual:** umidade do lote = média das amostras do lote (D21); a
  representatividade da amostra **não** entra no orçamento (listada em `nao_incluidos`).
- **Por que importa:** é a maior fonte não quantificada. Um viés de amostragem (ex.: amostra
  da superfície, mais seca) muda o PCI e a eficiência na mesma proporção.
- **Alternativas:** (a) atual; (b) exigir número mínimo de amostras e método (ISO 18135
  para amostragem, ISO 18134 para umidade — **conferir edições**); (c) estimar a
  incerteza por amostras em duplicata.
- **Exemplo:** viés de +2 p.p. (40% → 42%): PCI úmido −4,1% → η +4,3%.

### Q15 · Média simples × média ponderada pela carga
- **Hipótese atual:** médias simples das leituras do período; incerteza pelo erro-padrão
  das médias diárias (D25).
- **Por que importa:** a perda nos gases varia com a carga; o combustível também.
- **Alternativas:** (a) simples (atual); (b) ponderar pela vazão de vapor de cada intervalo.
- **Exemplo:** no demo, a diferença na perda é de 0,02 a 0,04 p.p. Em plantas reais pode
  ser maior se T_gases subir com a carga.

### Q16 · Detecção com U = 2u e muitas comparações (prioridade alta)
- **Hipótese atual:** "detectável" = |Δ| > U = 2u da diferença, indicador por indicador.
- **Por que importa:** a investigação compara cerca de 8 indicadores; com vários testes,
  algum pode passar por acaso. Por outro lado, um critério mais rígido aumenta as
  abstenções.
- **Alternativas:** (a) atual; (b) k maior para indicadores secundários; (c) exigir que o
  fechamento feche (D48) antes de aceitar uma explicação.
- **Exemplo:** se os 8 indicadores fossem independentes e normais, cada um com ~4,6% de
  chance de passar de 2u por acaso, a chance de pelo menos um passar seria ~31%. Hoje o
  que segura é a exigência adicional de relevância e sentido (Q9) e o fechamento.

### Q17 · Fechamento: efeitos um por vez, compostos em log
- **Hipótese atual:** cada efeito é calculado mudando um fator por vez; os efeitos são
  somados em pontos logarítmicos (D48).
- **Por que importa:** interações entre fatores (ex.: umidade × temperatura dos gases) são
  desprezadas.
- **Alternativas:** (a) atual; (b) calcular o efeito conjunto (todos os fatores juntos) e
  mostrar a interação.
- **Exemplo:** semanas 5–6: observado +10,1%, soma dos efeitos +11,2% → "fecha" dentro
  da incerteza.
