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
| 3 | Saturação e entalpias | `vapor.t_sat_c`, `h_vapor_mj_kg`, `h_agua_mj_kg` | IAPWS-IF97 (pacote `iapws`) | bar abs, °C, MJ/kg | — | regiões 1, 2, 4 | — | consistência IF97×IAPWS-95 (0,075 kJ/kg no V01, ver V-A5)⁽ᶜ⁾ | unid. + golden V01 | **I, V** (seção 3.1) | — |
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
| 15 | Razão de ar λ | `indireto.razao_ar` | forma fechada de y_O₂ (E2) | — ; O₂ **base seca** | M | ar seco 21/79; CO desprezado | — | **base do analisador**; CO | golden | I, V (golden do kit) | **ALTO** se o analisador medir base úmida: a perda fica **subestimada** em 0,44 a 1,69 p.p. (G01: 1,15 p.p.)⁽ᶜ⁾ |
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
| 26 | **Resíduo direto − indireto (H5)** | `investigacao.investigar` | resíduo = −Δη − Δperda; u em quadratura | p.p. | E | **caminhos independentes** | Δη, Δperda | **correlação pela umidade** (+1 p.p. de w move o resíduo −2,07 p.p. com η ≈ 0,84 e w ≈ 0,45, como no demo; −1,75 p.p. com η = 0,80 e w = 0,40) | integração | I | **ALTO**: E12 registrado em texto, não aplicado no cálculo |
| 27 | Hipóteses da investigação | `investigacao.investigar` | regras: detectável + relevante (D29) + sentido | — | — | efeitos isolados (um fator por vez) | — | interação entre fatores | casos A, B, C, purga | I | vocabulário "sustentada" mistura compatível e comprovado |
| 28 | Valor em jogo | `investigacao.investigar` | Δconsumo × vapor × preço | R$ | E | preço médio do período | u do consumo | — | caso A | I | ok (só com base) |

⁽ᶜ⁾ **Corrigido depois do diagnóstico.** A primeira versão desta matriz dizia "< 0,05 kJ/kg"
(linha 3) e "−0,75 a −0,93 p.p." (linha 15); os dois números foram recalculados na
verificação (seção 3) e estavam errados. O de O₂ é maior do que o informado antes.

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

### 1.5 Situação de cada linha depois da Fase R

| # | Antes | Depois | O que mudou | Verificação (ver `docs/matriz_validacao_fisica.md`) |
|---|---|---|---|---|
| 3 | I, V | I, V | — | V-A1 a V-A5 |
| 4 | I, V | I, V | sensibilidade ao título no resultado (x = 0,99 → −0,82%) | V-A6 |
| 5 | I | I | bordas como componente de modelo; medidor com chave do instrumento | V-C5, V-D3, V-D5 |
| 6 | I | I | intervalo a intervalo quando possível; Δh com incerteza (D46) | — |
| 8 | I | I, V | recebimento no instante do estoque bloqueia (D49); estoques com sinal e chave; balança n·u (D45) | V-C3, V-C4, V-C7, V-D2, V-D6 |
| 10 | I | I, V | cenários recebido / FIFO / mín. / máx. (D38) | V-C1, V-C2 |
| 12 | I | I | fronteira declarada (D39); faixa pelo pátio | V-A8 |
| 15 | I, V | I, V | conversão O₂ úmido → seco disponível (D43) | V-B2, V-B9 |
| 16 | I, V | I, V | umidade do ar opcional (D41) | V-B1, V-B8 |
| 17 | I, V | I, V | modo cp(T) experimental (D40); constante continua referência | V-B5, V-B6, V-B11, V-B15 |
| 18 | I | I, V | — | V-B4 |
| 19 | não existia | I, V (experimental) | `perda_co_pct` (D42), fora da investigação | V-B7, V-B10 |
| 24 | I (erro) | I, V | GUM 4.3.3 / 4.3.7 (D35) | V-D1 |
| 25 | I (erro) | I, V | correlação por fonte do erro, r = 0 e r = 1 (D37) | V-D2, V-D3 |
| 26 | I (erro) | I, V | umidade compartilhada propagada em conjunto (D47) | V-D4 |
| 27 | I | I | vocabulário e status `oposta` (D44); fechamento em log (D48) | V-E1 a V-E5 (consistência) |

Nenhuma linha passou para **R**.

---

## 2. Referências usadas

Endereços registrados para o revisor conferir; os marcados com † estavam **bloqueados**
na rede da sessão e foram citados de memória técnica ou conferidos indiretamente.

| Ref. | Título · versão | Endereço | Onde é usada |
|---|---|---|---|
| R1 | IAPWS R7-97(2012), *Revised Release on the IAPWS Industrial Formulation 1997 for the Thermodynamic Properties of Water and Steam* | http://www.iapws.org/relguide/IF97-Rev.html † | Tabelas 5, 15 e 36 (V-A1 a V-A4); motor via pacote `iapws` 1.5.5 |
| R2 | IAPWS R6-95(2018), *Revised Release on the IAPWS Formulation 1995 for the Thermodynamic Properties of Ordinary Water Substance for General and Scientific Use* | http://www.iapws.org/relguide/IAPWS-95.html † | verificação independente (CoolProp, backend HEOS): V-A5, V-B4 |
| R3 | CoolProp 8.0.0 — I. H. Bell, J. Wronski, S. Quoilin, V. Lemort, *Ind. Eng. Chem. Res.* 53(6), 2498–2508, 2014 | https://coolprop.org | equações de estado de referência de N₂, O₂, CO₂ e H₂O (V-B5); **só nos testes** |
| R4 | B. J. McBride, S. Gordon, M. A. Reno, *Coefficients for Calculating Thermodynamic and Transport Properties of Individual Species*, NASA TM-4513, 1993 | https://ntrs.nasa.gov/citations/19940013151 | polinômios de 7 coeficientes do modo cp(T) experimental (D40) |
| R5 | Cantera 3.2.0, arquivo `data/nasa_gas.yaml` (transcrição de R4) | https://www.cantera.org | origem da cópia dos coeficientes, conferida por teste (V-B6); **só nos testes** |
| R6 | JCGM 100:2008, *Evaluation of measurement data — Guide to the expression of uncertainty in measurement* (GUM) | https://www.bipm.org/en/committees/jc/jcgm/publications † | seções 4.3.3, 4.3.7, 5.1.3, 5.2.2, 6.2.1, 6.3.3 (D35–D37) |
| R7 | JCGM 101:2008, *Supplement 1 to the GUM — Propagation of distributions using a Monte Carlo method* | idem † | método das verificações V-D2 a V-D4 |
| R8 | NIST-JANAF Thermochemical Tables, 4ª ed. (M. W. Chase, *J. Phys. Chem. Ref. Data*, Monografia 9, 1998) | https://janaf.nist.gov † | ΔfH°(CO₂) = −393,51 e ΔfH°(CO) = −110,53 kJ/mol a 298,15 K (V-B7) |
| R9 | `docs/fisica_para_revisao.md` (E1–E15) e `tests/golden/` | repositório | especificação e valores de referência do kit |
| R10 | `lab/referencia_perda_gases.py` | repositório | calculadora de referência escrita fora do motor (V-E1) |

Não foram usados: tabelas Shomate do NIST WebBook (bloqueado), normas de ensaio de
caldeiras (não disponíveis na sessão), dados de caldeiras reais (proibidos no repositório).

---

## 3. Resultados da verificação

Detalhe linha a linha em `docs/matriz_validacao_fisica.md`. Resumo:

- **Água e vapor:** o motor reproduz as tabelas de verificação da IF97 com diferença
  ≤ 4·10⁻⁶ kJ/kg e ≤ 4·10⁻⁷ K. Contra a formulação científica (IAPWS-95), o Δh do
  golden V01 difere 0,075 kJ/kg (0,003%).
- **Combustão:** massa conservada por elemento (2·10⁻¹⁶); λ igual à solução numérica;
  G01 refeito à mão igual ao motor; orvalho igual à IAPWS-95 (< 0,05 K). No modo cp(T)
  experimental, os polinômios NASA ficam a no máximo 0,11% das equações de referência
  (CoolProp) entre 1 e 450 °C.
- **Combustível e pátio:** os quatro cenários do pátio batem com o exemplo resolvido à mão;
  dados problemáticos (recebimento no instante do estoque, falta de estoque no limite,
  totalizador reiniciado, períodos sobrepostos) bloqueiam com motivo.
- **Incerteza:** as fórmulas de primeira ordem concordam com Monte Carlo a 0,24% ou menos
  nos três casos de correlação (mesma medição, mesmo instrumento, mesma hipótese). Tratar a
  umidade compartilhada como independente erraria 7,9% (V-D4).
- **Investigação:** os casos são de **consistência** (dados gerados com as mesmas hipóteses
  do motor): mostram que as regras recuperam o que foi plantado, inclusive explicações que se
  compensam (V-E1). Não são validação da física.
- **Suíte completa:** `pytest -q` → todos os testes passam (número registrado na seção 5);
  `ruff check .` e `ruff format --check .` sem erros. Os golden e suas tolerâncias não
  foram alterados.

O que a verificação **não** cobre está no fim da matriz (P-1 a P-6). O mais importante:
**o motor nunca foi comparado com uma caldeira real medida** (P-4).

---

## 4. O que foi corrigido ou acrescentado

### 4.1 Erros do diagnóstico

| ID | Correção | Onde | Decisão | Teste |
|---|---|---|---|---|
| ER-1 | Dispersão entre lotes passou a ser "dispersão do processo" (serve para saber se a umidade recebida mudou); saiu do orçamento do PCI e de η | `periodos._mistura` | D38 | V-C2 |
| ER-2 | Incerteza declarada lida pelo tipo (padrão / expandida com k / limite); sem tipo → a/√3 | `incerteza.incerteza_padrao`, `io/esquemas.py` | D35 | V-D1 |
| ER-3 | Diferença entre períodos com correlação pela fonte do erro; três níveis de detecção | `incerteza.u_diferenca`, `deteccao.comparar` | D37 | V-D2, V-D3 |
| ER-4 | Resíduo H5 com a umidade compartilhada propagada em conjunto | `investigacao.investigar` | D47 | V-D4 |
| ER-5 | Recebimento no instante de uma medição de estoque bloqueia | `periodos._combustivel` | D49 | V-C3 |
| ER-6 | Combustível queimado ≠ recebido: cenários do pátio e conclusões restritas | `periodos._cenarios`, `direto`, `investigacao` | D38 | V-C1, V-C2 |
| ER-7 | Fechamento comparava % simples com soma de efeitos multiplicativos (dava "sobra" falsa de 5,3% no caso B); agora em pontos log | `investigacao.investigar` | D48 | `test_investigacao.py` (caso B) |
| ER-8 | Fator que mudou no sentido contrário saía como "descartado" e o título dizia o sentido errado ("mais úmido" quando ficou mais seco); agora `oposta` e títulos pelo sentido real | `investigacao`, `relatorio`, tela | D44 | V-E1 |
| ER-9 | Pesagens tratadas como independentes (√n) sem informação para isso; agora n·u (erro comum) | `periodos._combustivel` | D45 | V-D6 |

ER-9 foi introduzido na primeira parte desta fase e corrigido na segunda. Também nesta
fase, um erro de estrutura (o bloco das `opostas` entrou no meio do `if/else` da próxima
verificação) foi pego pelo teste do caso A antes do commit e corrigido; o teste V-E1
agora cobre esse caminho.

### 4.2 Acréscimos

- `euler/incerteza.py` (novo): orçamento por componente com sinal, natureza
  (instrumental / aleatória / modelo), chave da fonte do erro e lista do que **não** foi
  incluído.
- `euler/propriedades_gases.py` (novo, experimental): polinômios NASA e ΔH de combustão do CO.
- `euler/indireto.py`: modo cp(T) experimental, umidade do ar, perda por CO, O₂ úmido →
  seco, aviso de extrapolação do polinômio.
- `euler/direto.py`: fronteira declarada, energia útil intervalo a intervalo, faixa de η
  pelos cenários do pátio, sensibilidade ao título.
- `instrumentos.csv`: colunas opcionais `incerteza_tipo` e `incerteza_k`.
- JSON de investigação `investigacao/0.2`: `causa_comprovada: false` em toda hipótese,
  `fechamento`, `criterios.sensibilidade_d29`, cenários do pátio por período.
- Testes de verificação independente (`tests/test_validacao_*.py`) e de regressão do
  gerador do demo; extra opcional `validacao` (CoolProp, Cantera) instalado no CI.

### 4.3 Efeito nas conclusões do caso de demonstração

| Comparação | Antes (`97ad0c6`) | Depois |
|---|---|---|
| Semanas 1–4 × 5–6 | consumo +10,1% (±3,1%); "os dados sustentam" T_gases e umidade | consumo +10,1% (±3,6% com r = 0; ±1,1% com r = 1); **explicações compatíveis** T_gases e umidade; fechamento +11,2% × +10,1% "fecha"; com fator D29 = 1,0, T_gases seria descartada |
| Semanas 1–4 × 7 | abstenção (sem vapor); "os dados sustentam" T_gases | abstenção; T_gases "mudou de forma detectável" (sem dizer que explica) |
| Semanas 1–4 × 8 | consumo +5,2% (±3,2%); umidade | consumo +5,2% (±3,7%, medidor reinstalado: r = 0 nos dois casos); umidade compatível, efeito +5,3% a +7,7% conforme o pátio |

As conclusões de cima não mudaram; mudaram as palavras, as incertezas e o que fica
explícito como dependente de hipótese.

---

## 5. Versão após as correções

- **Commit:** ver `PROGRESSO.md` (linha "Fase R"), que registra o commit final desta fase.
- Testes, lint e formatação: ver a mesma linha.

---

## 6. Limites: o que o motor ainda **não** pode sustentar

1. **Causa comprovada.** A EULER só diz "explicação compatível com os dados". Comprovar
   exige a verificação indicada (ex.: conferir a amostragem de umidade, inspecionar os tubos).
2. **Eficiência absoluta como número firme.** η depende do título (não medido), do uso do
   pátio, da amostragem de umidade e da fronteira (purga fora). Use a faixa, não o número,
   e nunca para garantia contratual. Os limites do pátio são contábeis: o de cima pode
   passar do fisicamente possível (ex.: 95,5% na semana 1 do demo, com 12,4% de perda nos
   gases) e só mostra quanto o pátio pode pesar.
3. **Conclusões de períodos curtos com estoque grande.** Quando o estoque é comparável ao
   consumido, o efeito da umidade e o resíduo dependem do pátio; o motor marca
   `nao_avaliavel` ou mostra a faixa.
4. **O que é o resíduo "outras perdas".** Purga, casco, vazamentos e CO não se separam com os
   registros atuais.
5. **Perda nos gases absoluta sem a base do O₂.** Se o analisador medir em base úmida, a
   perda fica subestimada em até ~1,7 p.p. Comparações entre períodos sofrem menos se a
   base for a mesma.
6. **Mudança detectável sem incerteza cadastrada.** Sem a incerteza dos instrumentos, o
   motor não decide (`None`) e se abstém.
7. **Validade fora do caso sintético.** Nenhum resultado foi comparado com uma caldeira
   real medida (P-4).
8. **Comandos para a caldeira.** Fora do escopo por regra: a saída é sempre uma
   verificação, nunca uma ordem.

Decisões abertas: `docs/perguntas_revisores.md` (Q1–Q17) e `docs/decisoes.md` (D35–D50).
