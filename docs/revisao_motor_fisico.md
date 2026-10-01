# Revisão do motor físico da EULER (Fase R)

> **Situação deste documento:** revisão técnica feita por agente de programação (Claude), a
> pedido do Adryan em 01/10/2026. **Nada aqui é aprovação científica.** Os itens só passam a
> "revisado por especialista" quando um revisor humano (doutorando/professor) assinar em
> `docs/fisica_para_revisao.md`. Testes passando significam apenas que o código faz o que foi
> especificado, não que a especificação esteja certa.

- **Versão examinada (diagnóstico):** commit `97ad0c6` (branch `claude/new-session-xytynj`).
- **Versão após as correções:** ver a seção 5 (registrada no fim da fase).
- **Spec v0.3:** **não encontrada** (repositório, branches, arquivos enviados; o conector do
  Google Drive desta sessão não tem permissão de leitura). Requisitos que **não puderam ser
  conferidos** contra ela: tabela de capacidades (seção 4 → D30), formato do JSON de
  investigação (seção 7 → D28), critérios de detecção de degrau (seção 8, T12), contrato de
  dados original (T02 → D12).
- **Acesso a fontes:** os sites iapws.org, webbook.nist.gov e bipm.org estão bloqueados pela
  rede desta sessão. Por isso as verificações usam **implementações independentes reconhecidas,
  instaladas pelo PyPI**, com a fonte dos dados registrada (seção 3). O texto do GUM foi
  citado por seção, de memória técnica: **o revisor deve conferir as seções citadas**.

Legenda de situação usada em todo o documento:

| Sigla | Significado |
|---|---|
| **I** | implementado no código e coberto por testes de comportamento |
| **V** | verificado contra referência **independente** do motor (tabela publicada, outra implementação, cálculo à mão) |
| **R** | revisado e aprovado por especialista humano — **nenhum item está nesta situação** |

---

## 1. Diagnóstico (versão `97ad0c6`)

### 1.1 Matriz dos cálculos

Abreviações: M = medido, E = estimado, A = assumido. "u" = incerteza.

| # | Cálculo e finalidade | Arquivo · função | Equação · referência | Variáveis · unidades · base | Dados | Hipóteses · domínio | u considerada | u omitida | Testes | Situação | Pendência · impacto |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Pressão absoluta do vapor | `vapor.p_absoluta_bar` | p_abs = p_man + p_atm (E8) | bar | p_man M; p_atm E | manômetro mede relativo ao ambiente | — | p_atm do dia (±10 mbar) | unid. | I | baixo impacto (Δh muda 0,7 kJ/kg por 0,2 bar) |
| 2 | p_atm sem barômetro | `vapor.p_atm_por_altitude_bar` | atmosfera padrão ISA | bar; altitude m | E | troposfera padrão | — | clima (±1%) | unid. | I | baixo |
| 3 | Saturação e entalpias | `vapor.t_sat_c`, `h_vapor_mj_kg`, `h_agua_mj_kg` | IAPWS-IF97 (pacote `iapws`) | bar abs, °C, MJ/kg | — | regiões 1, 2, 4 | — | consistência IF97×IAPWS-95 (<0,05 kJ/kg) | unid. + golden V01 | **I, V** (seção 3.1) | — |
| 4 | Energia por kg de vapor | `vapor.delta_h_mj_kg` | Δh = h_s(p, x) − h_a(p, T_a) (E8) | MJ/kg | p, T_a M; x A (= 1) | vapor saturado seco; água líquida na pressão da caldeira | — | **título x**: x = 0,98 reduz Δh em 1,65% | golden V01 | I, V | **título não medido**: viés sistemático em η absoluto; cancela nas comparações se x for constante |
| 5 | Vapor do período | `periodos._vapor` | diferença do totalizador; bordas pela vazão média (D31) | t | M (+E nas bordas) | totalizador acumulado; reinício bloqueia | medidor (declarada, lida como k = 2) | bordas; tipo da u declarada | integração | I | ver item 24 |
| 6 | Energia útil | `direto.balanco_direto` | Q_s = M_vapor · Δh(p̄, T̄_a) (E8, D26) | GJ | E | condições médias do período | herdada do vapor | Δh(p, T_a) | integração | I | médias × intervalo: 0,001% no demo (desprezível) |
| 7 | PCI úmido | `combustivel.pci_umido` | (1 − w)·PCI_s − 2,442·w (E5) | MJ/kg úmido; w base úmida | w M; PCI_s M/A | 2,442 MJ/kg a 25 °C | — | método de umidade | golden P01–P05 | I, V (à mão) | pergunta E5 em aberto |
| 8 | Combustível queimado | `combustivel.combustivel_queimado_kg`, `periodos._combustivel` | M_f = S₀ + ΣR − S₁ (E9) | kg úmido | S M; R M | estoques no instante exato dos limites; recebimento em (início, fim] | estoque (declarada, k = 2) | pesagem; **recebimento no mesmo instante da medição de estoque é atribuído sem aviso** | unid. + integração | I | ordem de eventos simultâneos não verificada |
| 9 | Massa por volume | `io/combustivel.importar_combustivel` | m = V·ρ (D18) | kg | E | densidade declarada | — | densidade | unid. | I | sem u para massa estimada |
| 10 | **Qualidade do combustível queimado** | `periodos._mistura` | PCI_u queimado = média (massa) dos lotes **recebidos** no período (D22) | MJ/kg | E | **o que entra é o que queima** | "dispersão entre lotes ÷ √n" | modelo do pátio; método de umidade | integração | I | **ALTO**: (S₀+S₁)/M_f = 71% numa semana, 29% em 2 semanas, 17% em 4 semanas no demo |
| 11 | Energia do combustível | `direto.balanco_direto` | E_f = M_f · PCI_u queimado (E10) | GJ | E | item 10 | herdada | item 10 | integração | I | herda o item 10 |
| 12 | Eficiência direta | `direto.balanco_direto` | η = Q_s / E_f (E10, E13) | fração | E | mesma fronteira; purga fora (D27) | vapor, estoque, PCI | título x; modelo do pátio | E13 (assinaturas) + integração | I | é resultado (E13 ok); u mal composta (itens 24–26) |
| 13 | Consumo específico | `direto.balanco_direto` | M_f / M_vapor | t/t | E | — | vapor, estoque | pesagem | integração | I | **independe da qualidade do combustível** (bom indicador primário) |
| 14 | O₂ estequiométrico | `indireto.oxigenio_estequiometrico` | C/12 + H/4 + S/32 − O/32 (E1) | kmol/kg seco | composição M/A | combustão completa | — | — | unid. + golden | I, V (à mão) | — |
| 15 | Razão de ar λ | `indireto.razao_ar` | forma fechada de y_O₂ (E2) | — ; O₂ **base seca** | M | ar seco 21/79; CO desprezado | — | **base do analisador**; CO | golden | I, V (golden do kit) | **ALTO** se o analisador medir base úmida: −0,75 a −0,93 p.p. na perda |
| 16 | Gases secos e água | `indireto.perda_gases` | E3, E4 (massas molares inteiras) | kg/kg seco | E | **sem umidade do ar** | — | umidade do ar (+0,20 p.p. a 25 °C, UR 60%) | golden | I, V (golden) | pergunta E4 |
| 17 | Perda sensível nos gases | `indireto.perda_gases` | E6, cp constante 1,05 / 1,90 | % do PCI | E | cp constante; T_ar como limite inferior | — | **cp(T)**: −0,30 a −0,41 p.p. (G01–G12) | golden G01–G12 | I, V (golden do kit) | modo cp(T) bloqueado (D08) |
| 18 | Orvalho da água | `indireto._t_orvalho_agua_c` | T_sat(p_H₂O) (D06) | °C | E | sem orvalho ácido, sem umidade do ar | — | — | unid. | I | orvalho ácido não modelado |
| 19 | Perda por CO | — | — | — | — | — | — | — | — | **não existe** | 0,11% do PCI a 200 ppm; 0,55% a 1.000 ppm |
| 20 | Médias do período | `deteccao.estatistica_diaria`, `periodos.resumir_periodo` | média simples; erro-padrão das médias diárias (D25) | — | M | dias independentes | aleatória (dispersão diária) | autocorrelação entre dias; ponderação pela carga (0,04 p.p. no demo) | integração | I | moderado |
| 21 | Perda nos gases do período | `investigacao.indireto_periodo` | E6 com médias; u por derivadas parciais (E15) | % do PCI | E | condições médias | dispersão diária de T_g, O₂, T_ar; dispersão entre lotes de w | viés dos instrumentos (cancela em diferenças) | integração | I | — |
| 22 | Composição do período | `periodos._composicao` | média das análises; senão a mais próxima (A) | fração seca | M/A | — | — | método de análise | integração | I | baixo |
| 23 | Extrato R$/GJ | `combustivel.extrato_por_fornecedor` | E11 | R$/GJ | E | PCI seco por fornecedor (D19); umidade média do lote (D21) | — | amostragem por lote | unid. + F1–F3 | I, V (tabela F1–F3) | perguntas E11 |
| 24 | **Tipo da incerteza declarada** | `periodos.incerteza_relativa_instrumento` | declarada ÷ 2 (D24) | — | A | **toda u declarada é k = 2** | — | — | integração | I | **erro de método**: o GUM 4.3.7 manda tratar limites ±a como retangulares (u = a/√3) quando não há outra informação |
| 25 | **Diferença entre períodos** | `deteccao.comparar` | u(Δ) = √(u_a² + u_b²) | — | — | **componentes independentes entre períodos** | — | correlação do mesmo instrumento (GUM 5.2) | unid. | I | **ALTO**: Δconsumo do demo ±2,92% (independente) × ±0,72% (medidor comum) |
| 26 | **Resíduo direto − indireto (H5)** | `investigacao.investigar` | resíduo = −Δη − Δperda; u em quadratura | p.p. | E | **caminhos independentes** | Δη, Δperda | **correlação pela umidade** (+1 p.p. de w move o resíduo −2,07 p.p.) | integração | I | **ALTO**: E12 registrado em texto, não aplicado no cálculo |
| 27 | Hipóteses da investigação | `investigacao.investigar` | regras: detectável + relevante (D29) + sentido | — | — | efeitos isolados (um fator por vez) | — | interação entre fatores | casos A, B, C, purga | I | vocabulário "sustentada" mistura compatível e comprovado |
| 28 | Valor em jogo | `investigacao.investigar` | Δconsumo × vapor × preço | R$ | E | preço médio do período | u do consumo | — | caso A | I | ok (só com base) |

### 1.2 Erros demonstráveis (corrigir)

| ID | Onde | O que está errado | Evidência | Efeito |
|---|---|---|---|---|
| ER-1 | `periodos._mistura` | A "incerteza" do PCI e da umidade da mistura é o erro-padrão da dispersão entre lotes. Todos os lotes são conhecidos (não é amostra), então isso não é incerteza de medição. Além disso, mistura uma média ponderada pela massa com um desvio-padrão sem ponderação. | código | u de η e de E_f sem significado físico |
| ER-2 | `periodos.incerteza_relativa_instrumento` (D24) | Toda incerteza declarada é lida como expandida k = 2. | GUM (JCGM 100:2008) 4.3.7: limites ±a sem outra informação → u = a/√3 | u subestimada em 13% quando o valor é limite (0,5a × 0,577a) |
| ER-3 | `deteccao.comparar`, `investigacao` | O erro sistemático do mesmo instrumento é tratado como independente entre períodos. | GUM 5.2 (grandezas correlacionadas) | Δconsumo do demo: ±2,92% em vez de ±0,72% (abstenção desnecessária) — ou subestimada quando o instrumento muda entre os períodos |
| ER-4 | `investigacao` (H5) | Resíduo direto − indireto combina em quadratura dois termos que compartilham a umidade e o PCI. | +1 p.p. de umidade desloca o resíduo em −2,07 p.p. | E12 não aplicado no número |
| ER-5 | `periodos._combustivel` | Recebimento com o mesmo horário da medição de estoque é colocado no período sem aviso. | código | E9 errado em até 1 lote (~30 t) |
| ER-6 | `periodos._mistura` (D22) | A qualidade dos lotes **recebidos** é usada como qualidade do combustível **queimado** sem limitar as conclusões. | (S₀+S₁)/M_f até 71% | η e resíduo H5 podem estar fortemente enviesados em períodos curtos |

### 1.3 Simplificações aceitáveis (documentar, não necessariamente mudar)

- Condições médias de pressão e água de alimentação no lugar do cálculo intervalo a
  intervalo: diferença de 0,001% no demo (item 6).
- Média simples das leituras no lugar da média ponderada pela carga: 0,02–0,04 p.p. no demo
  (item 20). Pode ser maior em plantas reais, onde a temperatura dos gases sobe com a carga.
- Massas molares inteiras (E3, E4), argônio somado ao nitrogênio (ar 21/79).
- cp constante como **referência** (golden). Superestima a perda em 0,30–0,41 p.p. (item 17).

### 1.4 Decisões abertas (dependem de revisor ou do cliente)

Título do vapor; base do analisador de O₂; umidade do ar; CO e incombustos; orvalho ácido;
purga dentro ou fora da fronteira; uso do pátio (FIFO, mistura, LIFO); correlação dos erros
dos instrumentos entre períodos; critério de relevância D29; fonte de cp(T). Ver a seção 6
e `docs/perguntas_revisores.md`.
