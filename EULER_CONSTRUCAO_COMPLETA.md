# EULER · Arquivo mestre de construção do software

> **Para o Claude Code:** este arquivo contém tudo o que você precisa para construir, comigo, o protótipo do software da EULER. Leia-o inteiro antes de agir. A Parte 1 diz como trabalhar comigo; a Parte 2 é o plano em etapas; a Parte 3 traz os arquivos que você deve criar exatamente como estão.

---

## PARTE 1 · Como trabalhar comigo

**Quem sou eu:** Adryan, fundador da EULER, estudante da UnB. **Não sou programador.** Vou construir o protótipo inteiro com você e depois entregar para a equipe de desenvolvimento avaliar se continua a partir dele. Por isso, o código precisa estar limpo, testado e documentado.

**Regras de conversa:**
1. Fale em português simples. Explique **antes** o que vai fazer e **depois** o que fez, em poucas linhas.
2. Trabalhe **uma etapa por vez** (Parte 2). No início de cada etapa, mostre um plano curto e espere meu "ok". No fim, pare e me diga o que eu devo olhar.
3. Faça você mesmo tudo o que for possível: criar pastas, instalar pacotes, rodar comandos, testes e commits. Só me peça para agir quando for impossível (por exemplo, instalar o Python, fazer login no GitHub ou aprovar algo). Nesse caso, me dê o passo exato, um de cada vez.
4. **Para eu ver o software:** deixe o app rodando em segundo plano (`streamlit run app/main.py`) e me diga o endereço (normalmente http://localhost:8501) e **exatamente onde clicar** para ver o que mudou. Se houver painel de pré-visualização disponível, use-o. Tire também prints das telas alteradas (Playwright), salve em `prints/` e me liste os arquivos.
5. Quando algo não aparece no app (um cálculo interno), me mostre um exemplo de entrada e saída numa tabela.
6. Ao final de cada etapa: rode `pytest -q` e `ruff check .`, faça commit com mensagem clara e **atualize o `PROGRESSO.md`** (etapa concluída, o que funciona, o que ficou pendente, próximo passo). Nas próximas sessões eu vou dizer só "continue": leia o `PROGRESSO.md` e siga.
7. Se algo quebrar: volte ao último commit que funcionava e me explique o que aconteceu, sem jargão.
8. Se faltar uma decisão de produto ou de física que este arquivo não responde, **não decida sozinho**: me pergunte com 2 ou 3 opções e a sua recomendação.
9. Siga sempre as regras invioláveis do `AGENTS.md` (Parte 3).

---

## PARTE 2 · Plano de construção (etapas)

Prazo externo: o protótipo precisa estar demonstrável antes de **15/11/2026** (edital Fábrica de Spinoff da UnB).

| Etapa | Tickets (ver `docs/backlog_agentes.md`) | O que o Adryan vai ver ao final |
|---|---|---|
| **0 · Preparar** | — | Verificar Python 3.11+ e Git (se faltar, me guiar na instalação). Criar todos os arquivos da Parte 3 exatamente como estão, `git init`, ambiente virtual `.venv`, instalar dependências, primeiro commit. Eu vejo: a lista de arquivos criados e os testes golden aparecendo como "skipped". |
| **1 · Fundação** | T01 | O app abre no navegador com a tela inicial da EULER e o rodapé de segurança. |
| **2 · Física** | T06, T07 (modo constante), T08 | Testes golden passando. Uma página "Calculadora de referência" no app: escolho temperatura dos gases, O₂ e umidade e vejo a perda nos gases, o λ e o PCI úmido (com aviso "simulação, valores de referência em revisão"). |
| **3 · Entrada de dados** | T02, T03, T05 | Tela "Importar dados": subo os CSVs de `templates/` e vejo a lista de avisos de qualidade. Planilha modelo .xlsx em `templates/`. |
| **4 · Extrato por fornecedor** | T09 | Tela "Extrato por fornecedor" com R$/GJ por fornecedor e a frase "O fornecedor mais barato por tonelada nem sempre é o mais barato por energia." |
| **5 · Investigação** | T11, T13 (e T10 se der tempo) | Telas "Dados e limites" (o que dá e o que não dá para concluir, e por quê) e "Investigação" (hipóteses, o que falta, próxima verificação). |
| **6 · Relatório** | T14 | Botão "Gerar relatório" que cria um HTML com os 5 blocos; 3 exemplos em `docs/exemplos_relatorio/` para eu revisar o texto. |
| **7 · Demonstração** | T18, T15 | Caso sintético completo em `demo/`; fluxo inteiro no app em menos de 5 minutos; roteiro de 2 minutos para o vídeo do edital. |
| **8 · Entrega aos devs** | T19 | Revisão crítica do próprio código, `HANDOFF.md` sincero (o que está pronto, o que é provisório, riscos, o que falta), README atualizado e repositório privado no GitHub. |
| Extras (se sobrar tempo) | T04, T12, T16 | Mapeamento automático de colunas, detecção de degrau, registro de horas. |

Observações:
- **T17 (benchmark cego)** deve ser feito depois por outra pessoa, num repositório separado. Não crie o gerador de gabarito neste projeto; registre isso no `HANDOFF.md`.
- Os valores de `tests/golden/` estão **pendentes de revisão científica** por doutorandos. Na Etapa 8, gere também uma versão em PDF de `docs/fisica_para_revisao.md` para eu enviar aos revisores.
- Quando um revisor corrigir um item (E1–E15), eu vou pedir: "atualize o golden com a correção do revisor X no item Ey". Só nesse caso `tests/golden/` pode mudar.

---

## PARTE 3 · Arquivos a criar exatamente como estão

Crie cada arquivo abaixo no caminho indicado, com o conteúdo entre as linhas `~~~~`. Não altere os valores numéricos.

### Arquivo 1: `CLAUDE.md`

~~~~
# CLAUDE.md

As regras do projeto ficam num arquivo só, compartilhado com outros agentes (ex.: Codex):

@AGENTS.md

## Como trabalhar com o Adryan (fundador, não programador)
- Português simples; explique antes e depois de agir; uma etapa por vez, com plano curto e "ok" dele.
- Deixe o app rodando (`streamlit run app/main.py`), informe o endereço e onde clicar para ver o que mudou; salve prints em `prints/`.
- Ao fim de cada etapa: `pytest -q`, `ruff check .`, commit e atualização do `PROGRESSO.md`.
- Quando ele disser "continue": leia `PROGRESSO.md` e siga o plano em `EULER_CONSTRUCAO_COMPLETA.md` (Parte 2).
- Decisões de produto ou de física não especificadas: pergunte com opções e recomendação.
~~~~

### Arquivo 2: `AGENTS.md`

~~~~
# AGENTS.md · EULER (lido por Codex, Claude Code e outros agentes)

## O que é este projeto
EULER é um SaaS de **investigação física** para caldeiras industriais. Ele **soma** aos registros que a fábrica já tem (diário do operador, recebimentos de combustível, amostras, eventos) e responde:

> "O consumo de combustível mudou. O que os registros sustentam, quais explicações continuam possíveis e qual verificação separa essas explicações?"

Às vezes a resposta certa é **"não dá para concluir"** + a próxima medição. Essa abstenção é uma funcionalidade, não uma falha.

## Regras invioláveis
1. **Nunca** gerar comando operacional para a caldeira (abrir válvula, mudar setpoint, ajustar queimador). O software investiga e recomenda **verificações**. Ver rodapé de segurança em `docs/visao_produto.md`.
2. **Ausente ≠ zero.** Nada é preenchido, interpolado ou corrigido em silêncio. Toda correção guarda original, novo valor, motivo, autor e data.
3. **Unidades SI internamente:** kg, MJ, °C/K, bar **absoluto**. Converter na entrada; nomear colunas com a unidade (`t_gases_c`, `p_vapor_bar_abs`).
4. **Toda análise tem pré-requisitos** (`euler/capacidades.py`). Se faltar dado, a análise é **bloqueada** com motivo legível. Nunca usar porcentagem arbitrária para "completar" perdas.
5. **Não inventar números:** sem probabilidades fictícias, sem economia estimada sem base. Campos sem base ficam `null`.
6. **Não editar `tests/golden/`** nem tolerâncias de teste. Esses valores são revisados por doutorandos (física/química). Se um teste golden falhar, o código está errado até prova em contrário: pare e descreva a divergência no PR.
7. **Separação do benchmark:** o repositório `euler-bench` (gerador de dados "verdade" e gabaritos) **não** pode ser lido nem importado pelo `euler-core`. Não compartilhar a rotina de perda nos gases entre os dois.
8. Sem dados reais de clientes no repositório. Só dados sintéticos ou públicos, marcados como tal.

## Stack e comandos
- Python 3.11 · pandas · numpy · `iapws` (IF97) · pytest · ruff · streamlit
- Instalar: `pip install -e ".[dev]"`
- Testes: `pytest -q`  · Lint: `ruff check . && ruff format --check .`
- App: `streamlit run app/main.py`

## Estrutura
```
euler/
  io/             adaptadores CSV → tabelas normalizadas (preserva original)
  qualidade.py    lacunas, duplicatas, unidades, totalizador reiniciado, registro tardio
  capacidades.py  quais análises estão habilitadas/bloqueadas e por quê
  vapor.py        entalpias IF97
  combustivel.py  combustível queimado no período, energia, extrato por fornecedor
  direto.py       balanço direto
  indireto.py     perda nos gases (base PCI)
  deteccao.py     linha de base, degrau, comparação entre períodos
  investigacao.py regras → JSON de investigação
  relatorio.py    JSON → relatório em linguagem simples (HTML/PDF)
app/              Streamlit
tests/            unidade + golden (somente leitura para agentes)
docs/             contrato de dados, física, decisões
```

## Como trabalhar
- **Uma tarefa = um branch = um PR pequeno.** Siga o ticket em `docs/backlog_agentes.md`.
- Antes de codar, escreva/atualize os testes do ticket. Depois implemente até passarem.
- Funções puras e com docstring: entrada, saída, unidades, hipóteses, referência da equação (ex.: "E7 em docs/fisica_para_revisao.md").
- Toda hipótese física nova vai para `docs/decisoes.md` (data, decisão, motivo, quem revisa).
- No PR, descreva: o que mudou, como testar, o que ficou fora, dúvidas para revisão humana.
- Se a tarefa exigir decisão de produto ou de física não especificada, **não decida sozinho**: liste as opções no PR.

## Estilo de texto para o usuário final (telas e relatórios)
Português claro, frases curtas, sem jargão desnecessário. Números sempre com unidade e origem (`medido`, `estimado`, `assumido`). Nunca "IA prevê", "economia garantida" ou "comprovado" sem evidência.
~~~~

### Arquivo 3: `PROGRESSO.md`

~~~~
# PROGRESSO da construção

| Etapa | Status | Data | O que funciona | Pendências |
|---|---|---|---|---|
| 0 · Preparar | a fazer | | | |
| 1 · Fundação | a fazer | | | |
| 2 · Física | a fazer | | | |
| 3 · Entrada de dados | a fazer | | | |
| 4 · Extrato por fornecedor | a fazer | | | |
| 5 · Investigação | a fazer | | | |
| 6 · Relatório | a fazer | | | |
| 7 · Demonstração | a fazer | | | |
| 8 · Entrega aos devs | a fazer | | | |

**Próximo passo:** Etapa 0.
~~~~

### Arquivo 4: `docs/visao_produto.md`

~~~~
# EULER · Visão de produto (resumo para a equipe e para os agentes)

## Em uma frase
O sistema que diz **quanto de energia a fábrica comprou, quanto virou vapor e onde o resto foi parar**, para qualquer caldeira, com os dados que ela já tem.

## O teste de startup
A EULER consegue vender e atender o **centésimo cliente sem os fundadores na sala**? Toda decisão de produto deve aproximar a resposta de "sim".

## As 6 peças
1. **Motor de investigação** (física + estatística + abstenção). A vantagem difícil de copiar. A IA pode explicar e redigir; quem conclui é a física.
2. **Entrada de dados sem atrito.** Planilha, caderno, app de checklist, balança; depois sensores. Valor desde o primeiro dia (N0).
3. **Entregas que viram rotina.** Extrato de energia por fornecedor (M1), fechamento mensal do custo do vapor (M5), ações verificadas (M4), pacote anual de inspeção e carbono (M6).
4. **Atendimento automático.** Cadastro, mapeamento de colunas, relatório e alertas sem gente; humanos só para exceções.
5. **Canal de parceiros.** Fabricantes, manutenção, inspeção e fornecedores de instrumentos revendem ou usam a EULER como "cérebro" (API / white-label).
6. **Efeito de rede.** Com consentimento: comparação anônima entre plantas e base de qualidade de combustível por fornecedor.

## Fases
| Fase | Clientes | Construir |
|---|---|---|
| 0 · Edital (até 15/11/2026) | 0 | Motor + importador + extrato por fornecedor + relatório automático, com dados públicos/sintéticos |
| 1 · Provar valor | 1–10 | Investigação + extrato + fechamento mensal; medir horas por cliente |
| 2 · Escalar | 10–50 | Cadastro sozinho, alertas, registro de ações, comparação entre plantas, API |
| 3 · Plataforma | 50+ | White-label, multiplanta, outras utilidades (vapor, purgadores, ar comprimido, refrigeração) e equipamentos térmicos (secadores, fornos) |

## O que NÃO construir
Hardware próprio · controle automático da caldeira · personalizações por cliente · painel genérico de dados.

## Métrica-guia
**Horas de atendimento por cliente por mês** (meta hipotética: ~10 h no 1º piloto → < 1 h a partir do 50º cliente).

## Rodapé de segurança (obrigatório no app e nos relatórios)
> Ferramenta de registro e apoio à investigação. Não emite comandos operacionais nem substitui procedimentos da instalação, alarmes, intertravamentos ou a avaliação do responsável técnico. Não é um Registro de Segurança conforme a NR-13.
~~~~

### Arquivo 5: `docs/backlog_agentes.md`

~~~~
# EULER · Backlog para agentes (Codex / Claude Code) · Fase 0 (edital, até 15/11/2026)

Cada ticket cabe numa sessão de agente (≈1–4 h de trabalho humano equivalente). Formato: **Objetivo · Arquivos · Aceite · Não fazer · Revisão**.
Responsáveis sugeridos: **P1** física/core · **P2** benchmark (repo separado) · **P3** dados/app · **AD** Adryan (produto) · **REV** doutorandos.
Se algum ticket já foi feito na semana 1, marque como concluído e siga.

Legenda de status: ☐ a fazer · ◐ em andamento · ☑ pronto (testes passando + revisão humana)

---

## Bloco 1 · Fundação

**T01 · Repositório e CI** — P3 ☐
- Objetivo: `euler-core` com `pyproject.toml`, ruff, pytest, CI no GitHub Actions; copiar `AGENTS.md`, `CLAUDE.md`, `docs/`, `tests/golden/` deste kit.
- Aceite: `pytest -q` e `ruff check .` rodam no CI; PR template com seções "O que mudou / Como testar / Fora do escopo / Dúvidas".
- Não fazer: nenhum código de física.

**T02 · Contrato de dados e planilhas modelo** — AD + P3 ☐
- Objetivo: `docs/contrato_dados.md` (da spec v0.3) + `templates/*.csv` (deste kit) + uma planilha modelo .xlsx com abas iguais aos CSVs e instruções para o operador.
- Aceite: cada coluna com unidade, obrigatoriedade e exemplo; planilha abre no Excel/Google Sheets e exporta CSV que o importador aceita.
- Não fazer: colunas sem unidade no nome.

## Bloco 2 · Entrada de dados (o software se vira sozinho)

**T03 · Importador de `diario.csv` com qualidade** — P3 ☐
- Objetivo: `euler/io/diario.py` + `euler/qualidade.py`: lê, normaliza, preserva original, detecta lacunas, duplicatas, totalizador reiniciado, registro tardio, unidades suspeitas.
- Aceite: testes com CSV sintético contendo cada problema; relatório de importação legível (lista de avisos com linha e motivo).
- Não fazer: preencher ou interpolar valores.

**T04 · Mapeamento inteligente de colunas** — P3 ☐ *(novo, reduz horas de atendimento)*
- Objetivo: `euler/io/mapeamento.py`: reconhece sinônimos de colunas ("Temp. chaminé", "T gases", "temperatura fumaça" → `t_gases_c`) por dicionário + regras; o que não reconhecer vira pergunta na tela ("Esta coluna é…?"). Salva o mapeamento por cliente para reuso.
- Aceite: 20 cabeçalhos realistas de teste, ≥ 80% mapeados automaticamente, 0 mapeamentos errados silenciosos (na dúvida, pergunta).
- Não fazer: usar IA generativa no protótipo (fica para a Fase 1).

**T05 · Importador de `combustivel.csv`, `amostras.csv`, `eventos.csv`, `instrumentos.csv`** — P3 ☐
- Aceite: mesmas regras do T03; volume sem densidade declarada gera aviso e bloqueia conversão para massa.

## Bloco 3 · Motor físico

**T06 · `vapor.py` (IF97)** — P1 ☐
- Objetivo: entalpia do vapor e da água de alimentação; conversão manométrica → absoluta com `p_atm` configurável.
- Aceite: passa `tests/golden/vapor_referencia.csv` (E8).

**T07 · `indireto.py` · perda nos gases** — P1 ☐
- Objetivo: E1–E7 com dois modos: `modelo_cp="constante"` (reproduz o golden) e `modelo_cp="variavel"` (cp(T), fonte definida pelo REV).
- Aceite: modo constante passa `tests/golden/casos_referencia.csv` com tolerância 0,01 p.p.; modo variável difere do constante em < 0,5 p.p. nos casos G01–G10 (até o REV aprovar outro critério); bloqueia cálculo fora do domínio (E7) com motivo.
- Não fazer: copiar código do `euler-bench`.

**T08 · `combustivel.py` · queimado no período e energia** — P1 ☐
- Objetivo: E5, E9, E10 (parte da energia).
- Aceite: passa `tests/golden/pci_umido_referencia.csv`; sem estoque final → análise bloqueada com motivo.

**T09 · Extrato de energia por fornecedor (M1)** — P1 ☐ *(novo, principal argumento de valor)*
- Objetivo: E11. Para cada lote/fornecedor: energia entregue, R$/GJ, umidade e origem do dado; ranking por R$/GJ; alerta quando a umidade do lote foge da faixa histórica do fornecedor.
- Aceite: reproduz a tabela F1–F3 de `docs/fisica_para_revisao.md`; lote sem umidade medida aparece como "energia não determinada" (nunca assume).
- Não fazer: acusar fornecedor; texto neutro ("umidade acima da faixa histórica").

**T10 · `direto.py` · eficiência direta** — P1 ☐
- Objetivo: E10 + E13 (não circularidade) + incerteza de primeira ordem (E15).
- Aceite: teste que falha se a eficiência for usada como entrada; resultado com intervalo.

**T11 · `capacidades.py`** — P1 ☐
- Objetivo: tabela da seção 4 da spec v0.3 como regras testáveis; inclui "Extrato por fornecedor" (requer recebimentos + umidade por lote + preço).
- Aceite: um teste por linha da tabela (habilita quando tem, bloqueia com motivo quando falta).

**T12 · `deteccao.py` · degrau e comparação de períodos** — P1 ☐
- Aceite: critérios da seção 8 da spec v0.3 (degrau +30 °C em ≤ 3 leituras em ≥ 95/100; falsos alertas ≤ 5/100), medidos pelo P2 no benchmark.

## Bloco 4 · Investigação e entrega automática

**T13 · `investigacao.py` · JSON de investigação** — P1 ☐
- Objetivo: regras → JSON da seção 7 da spec v0.3, com E12 (marcar evidências que compartilham medição).
- Aceite: caso A/B/C sintético gera hipóteses corretas; contraexemplo (purga não medida) gera abstenção; `valor_em_jogo` só preenchido com base.

**T14 · `relatorio.py` · relatório automático em linguagem simples** — P3 + AD ☐ *(novo, reduz horas)*
- Objetivo: JSON → HTML (e PDF) com 5 blocos fixos: **O que mudou · O que os dados sustentam · Explicações possíveis · O que falta saber · Próxima verificação**. Rodapé de segurança obrigatório.
- Aceite: AD aprova o texto de 3 relatórios gerados; nenhum relatório contém comando operacional (teste com lista de verbos proibidos).

**T15 · App Streamlit** — P3 ☐
- Telas: (1) Importar e mapear, (2) Dados e limites (capacidades), (3) Investigação, (4) **Extrato por fornecedor**, (5) Relatório.
- Aceite: fluxo completo com o caso de demonstração em < 5 min, sem ajuda.

**T16 · Registro de horas de atendimento** — P3 ☐ *(novo, métrica de escala)*
- Objetivo: tabela simples `atendimento.csv` (cliente, data, tarefa, minutos) + resumo "horas por cliente por mês".
- Aceite: existe e é usada desde o primeiro piloto.

## Bloco 5 · Prova e edital

**T17 · Benchmark cego** — P2 (repo `euler-bench`) ☐
- Objetivo: gerador com modelo "verdade" mais completo + casos reservados + gabarito com SHA-256 publicado antes da rodada.
- Aceite: relatório de acertos/erros/abstenções do `euler-core` contra o gabarito.

**T18 · Caso de demonstração ponta a ponta** — AD + P3 ☐
- Objetivo: caldeira sintética de 20 t/h a cavaco, claramente marcada como sintética: 3 fornecedores, 8 semanas, um degrau de temperatura, um fornecedor com umidade subindo, um período sem dado (abstenção).
- Aceite: roteiro de 2 minutos para o vídeo do edital usando o app.

**T19 · Congelar versão para o INPI** — P3 + AD ☐
- Objetivo: tag de versão, hash do código, lista de autores (commits com nome real), README da versão.

---

## Fase 1 (depois do edital, só listado)
Alertas automáticos · registro de ações e verificação do resultado (M4) · fechamento mensal do custo do vapor (M5) · várias caldeiras e plantas · login e nuvem · API para parceiros · foto do caderno (OCR) · assistente de dúvidas com base nos dados do cliente · comparação anônima entre plantas · base de qualidade por fornecedor.
~~~~

### Arquivo 6: `docs/fisica_para_revisao.md`

~~~~
# EULER · Física e cálculos para revisão científica

**Para:** doutorandos/professores revisores (termodinâmica, combustão, química).
**Objetivo:** validar cada equação, hipótese e valor de referência antes que vire código. Cada item tem um código (E1, E2…), que é citado nas docstrings do software. Quando um item for aprovado, ele vira teste automático em `tests/golden/`, que os agentes de programação não podem alterar.

**Como revisar:** para cada item, marque uma opção e, se houver correção, escreva a forma correta e a referência bibliográfica.

| Status | Significado |
|---|---|
| ☐ Aprovado | pode virar código e teste como está |
| ☐ Aprovado com ressalva | vale dentro do domínio indicado |
| ☐ Corrigir | escrever a versão correta |
| ☐ Fora do escopo | não usar no protótipo |

Convenções: frações mássicas em **base seca** (C, H, O, N, S, cinzas); umidade `w` em **base úmida** (kg de água / kg de combustível úmido); pressões em **bar absoluto**; energia em MJ; referência térmica `T_ref = 25 °C`.

---

## Bloco A · Combustão e perda nos gases

**E1 · Oxigênio estequiométrico** (kmol O₂ por kg de combustível seco)
`a = C/12 + H/4 + S/32 − O/32`
Revisor: ☐ ☐ ☐ ☐ · Observações:

**E2 · Razão de ar λ a partir do O₂ medido em base seca** (combustão completa, ar seco 21/79)
Gases secos por kg seco: `n_CO2 = C/12`, `n_SO2 = S/32`, `n_O2 = (λ−1)a`, `n_N2 = (79/21)λa + N/28`.
`y_O2 = n_O2 / (n_CO2 + n_SO2 + n_O2 + n_N2)` → resolver para λ (forma fechada no código de referência).
Pergunta: ignorar CO e incombustos no cálculo de λ é aceitável quando CO < ~200 ppm?
Revisor: ☐ ☐ ☐ ☐ · Observações:

**E3 · Massa de gases secos** (kg/kg seco)
`m_gs = 44·n_CO2 + 64·n_SO2 + 32·n_O2 + 28·n_N2`
Revisor: ☐ ☐ ☐ ☐ · Observações:

**E4 · Água nos gases** (kg/kg seco)
`m_H2O = 9H + w/(1−w)`
Pergunta: incluir a umidade do ar de combustão? (hoje: não)
Revisor: ☐ ☐ ☐ ☐ · Observações:

**E5 · PCI úmido** (MJ/kg úmido)
`PCI_u = (1−w)·PCI_seco − 2,442·w`
Pergunta: 2,442 MJ/kg a 25 °C é a convenção correta para PCI? O PCI_seco já desconta a água formada pelo H?
Revisor: ☐ ☐ ☐ ☐ · Observações:

**E6 · Perda sensível nos gases, base PCI, por kg seco**
`q_g = [m_gs·∫cp_gs dT + m_H2O·∫cp_H2O(v) dT] (de T_ar a T_g) / (PCI_seco − 2,442·w/(1−w))`
- Modo **referência** (só para teste): cp constantes 1,05 kJ/kg·K (gases secos) e 1,90 kJ/kg·K (vapor d'água).
- Modo **motor**: cp(T) por espécie. **Fonte proposta para cp(T): a definir pelo revisor** (ex.: polinômios NASA/Shomate do NIST).
Revisor: ☐ ☐ ☐ ☐ · Observações:

**E7 · Domínio de validade da perda nos gases**
- Não calcular se `T_g` < ponto de orvalho estimado dos gases (condensação).
- Plausibilidade: sem economizador ou pré-aquecedor, `T_g` deve ficar acima de `T_sat(p) + aproximação mínima`. Ex.: a 10 bar abs, T_sat ≈ 179,9 °C. Qual aproximação mínima (°C) usar como alerta?
Revisor: ☐ ☐ ☐ ☐ · Observações:

**Valores de referência a conferir** (composição C 50%, H 6%, O 43%, N 0,3%, S 0,05%, base seca; PCI_seco 18,5 MJ/kg; T_ar 25 °C; cp constantes):

| Caso | T_g (°C) | O₂ seco (%) | w | λ | Perda (%) |
|---|---|---|---|---|---|
| G01 referência | 180 | 8 | 0,40 | 1,611 | **11,773** |
| G02 | 150 | 8 | 0,40 | 1,611 | 9,494 |
| G03 | 210 | 8 | 0,40 | 1,611 | 14,052 |
| G04 | 250 | 8 | 0,40 | 1,611 | 17,090 |
| G05 | 180 | 4 | 0,40 | 1,234 | 9,611 |
| G06 | 180 | 6 | 0,40 | 1,397 | 10,548 |
| G07 | 180 | 10 | 0,40 | 1,903 | 13,444 |
| G08 | 180 | 8 | 0,30 | 1,611 | 10,979 |
| G09 | 180 | 8 | 0,45 | 1,611 | 12,307 |
| G10 | 180 | 8 | 0,50 | 1,611 | 12,981 |
| G11 | 180 | 8 | 0,3104 | 1,611 | 11,049 |
| G12 | 292,2 | 8 | 0,3104 | 1,611 | 19,047 |

Sensibilidades derivadas (para conferência): ≈0,076 p.p./°C; ≈0,71 p.p. por ponto de O₂ (entre 6 e 10%); ≈0,10 p.p. por ponto de umidade.
Peça ao revisor: recalcular **G01, G05 e G10 de forma independente** (planilha, EES ou à mão) e registrar o valor obtido.

---

## Bloco B · Vapor e balanço direto

**E8 · Energia útil do vapor**
`Q_s = Σ M_s · (h_s(p, T ou x) − h_a(p, T_a))`, entalpias pela IAPWS-IF97.
- Pressão manométrica → absoluta: `p_abs = p_man + p_atm(local)`. Qual `p_atm` usar sem barômetro (altitude do local)?
- Referência: 10 bar abs, vapor saturado seco, água de alimentação a 80 °C → **Δh = 2,4414 MJ/kg**; T_sat = 179,89 °C.
- Pergunta: como tratar o título do vapor (x < 1) quando não há medição? Hoje: assumido x = 1, marcado como `assumido`.
Revisor: ☐ ☐ ☐ ☐ · Observações:

**E9 · Combustível queimado no período**
`M_f = estoque_inicial + Σ recebimentos − estoque_final` (mesma base de umidade)
Pergunta: como propagar a incerteza de estoque medido por volume (densidade aparente)?
Revisor: ☐ ☐ ☐ ☐ · Observações:

**E10 · Energia do combustível e eficiência direta**
`E_f = Σ M_f,i · PCI_u,i` · `η_D = Q_s / E_f` (mesmo período e mesma fronteira)
Pergunta: a purga deve entrar como saída de energia útil, perda ou ficar fora da fronteira?
Revisor: ☐ ☐ ☐ ☐ · Observações:

---

## Bloco C · Extrato de energia por fornecedor (novo, motor M1)

**E11 · Energia entregue por lote e custo por energia**
- Energia do lote: `E_lote = M_lote · PCI_u(w_lote)` (MJ)
- Custo por energia: `R$/GJ = preço_total_lote / (E_lote/1000)`
- Exemplo (PCI_seco 18,5; 30 t por lote):

| Fornecedor | w | R$/t úmida | PCI_u (MJ/kg) | Energia (GJ) | R$/GJ |
|---|---|---|---|---|---|
| F1 | 0,38 | 180 | 10,542 | 316,3 | 17,07 |
| F2 | 0,45 | 170 | 9,076 | 272,3 | 18,73 |
| F3 | 0,52 | 160 | 7,610 | 228,3 | 21,02 |

O mais barato por tonelada é o mais caro por energia. Perguntas ao revisor:
- Qual a incerteza típica de umidade por estufa (ISO 18134) e por medidor portátil?
- Quantas amostras por lote para representar a umidade (amostragem)? *(Área de afinidade com a pesquisadora de pós-colheita.)*
- O PCI_seco pode ser assumido constante por fornecedor, ou precisa de amostra periódica?
Revisor: ☐ ☐ ☐ ☐ · Observações:

---

## Bloco D · Lógica de investigação (não é só fórmula)

**E12 · Independência dos dois caminhos.** Balanço direto (E8–E10) e perda nos gases (E1–E6) só contam como "duas evidências" se não compartilharem a mesma medição ou premissa (ex.: a mesma umidade assumida). O software deve marcar quando compartilham.
Revisor: ☐ ☐ ☐ ☐ · Observações:

**E13 · Não circularidade.** A eficiência é **resultado** de E10; nunca pode ser entrada para calcular combustível ou energia útil no mesmo período.
Revisor: ☐ ☐ ☐ ☐ · Observações:

**E14 · Decomposição do custo.** `custo = preço × intensidade` (R$/GJ × GJ/t de vapor). Variação por preço não pode ser chamada de perda de eficiência.
Revisor: ☐ ☐ ☐ ☐ · Observações:

**E15 · Incerteza e menor mudança detectável.** Propagação de primeira ordem (derivadas parciais) com incertezas declaradas dos instrumentos. Hipótese atual de menor mudança detectável na perda nos gases, 1 semana com leituras a cada 2 h: ≈0,8 p.p. com umidade medida por entrega e ≈1,4 p.p. sem medir umidade.
Pergunta: método aceitável para o protótipo (primeira ordem vs Monte Carlo)?
Revisor: ☐ ☐ ☐ ☐ · Observações:

---

## Registro da revisão

| Revisor | Área | Itens revisados | Data | Assinatura/e-mail |
|---|---|---|---|---|
| | | | | |

Toda correção aprovada vira: (1) ticket no backlog, (2) atualização de `tests/golden/`, feita **por uma pessoa**, com o nome do revisor no commit.
~~~~

### Arquivo 7: `docs/decisoes.md`

~~~~
# Registro de decisões (técnicas e de produto)

Formato: uma linha por decisão. Agentes podem PROPOR linhas no PR; uma pessoa aprova.

| # | Data | Decisão | Motivo | Proposta por | Aprovada por / revisor |
|---|---|---|---|---|---|
| D01 | | Unidades SI internas; pressão em bar absoluto | evitar erro de conversão | spec v0.3 | |
| D02 | | Perda nos gases em base PCI por kg seco | coerência com PCI_u | spec v0.3 | REV pendente |
| D03 | | Sem IA generativa e sem OCR no protótipo do edital | foco e confiabilidade | spec v0.3 | |
| D04 | | Extrato de energia por fornecedor entra na Fase 0 | principal argumento de valor (M1) | kit agentes | |
~~~~

### Arquivo 8: `tests/golden/casos_referencia.csv`

~~~~
caso,t_gases_c,o2_seco_pct,umidade_bu_frac,t_ar_c,C,H,O,N,S,pci_seco_mj_kg,modelo_cp,perda_gases_pct_esperada,lambda_esperado,tolerancia_pp,status_revisao
G01_referencia,180,8,0.40,25,0.50,0.06,0.43,0.003,0.0005,18.5,constante,11.773,1.611,0.01,pendente
G02_tg150,150,8,0.40,25,0.50,0.06,0.43,0.003,0.0005,18.5,constante,9.494,1.611,0.01,pendente
G03_tg210,210,8,0.40,25,0.50,0.06,0.43,0.003,0.0005,18.5,constante,14.052,1.611,0.01,pendente
G04_tg250,250,8,0.40,25,0.50,0.06,0.43,0.003,0.0005,18.5,constante,17.090,1.611,0.01,pendente
G05_o2_4,180,4,0.40,25,0.50,0.06,0.43,0.003,0.0005,18.5,constante,9.611,1.2336,0.01,pendente
G06_o2_6,180,6,0.40,25,0.50,0.06,0.43,0.003,0.0005,18.5,constante,10.548,1.3972,0.01,pendente
G07_o2_10,180,10,0.40,25,0.50,0.06,0.43,0.003,0.0005,18.5,constante,13.444,1.9027,0.01,pendente
G08_w30,180,8,0.30,25,0.50,0.06,0.43,0.003,0.0005,18.5,constante,10.979,1.611,0.01,pendente
G09_w45,180,8,0.45,25,0.50,0.06,0.43,0.003,0.0005,18.5,constante,12.307,1.611,0.01,pendente
G10_w50,180,8,0.50,25,0.50,0.06,0.43,0.003,0.0005,18.5,constante,12.981,1.611,0.01,pendente
G11_caso_a_antes,180,8,0.3104,25,0.50,0.06,0.43,0.003,0.0005,18.5,constante,11.049,1.611,0.01,pendente
G12_caso_a_depois,292.2,8,0.3104,25,0.50,0.06,0.43,0.003,0.0005,18.5,constante,19.047,1.611,0.01,pendente
~~~~

### Arquivo 9: `tests/golden/vapor_referencia.csv`

~~~~
caso,p_vapor_bar_abs,estado_vapor,t_agua_alim_c,delta_h_mj_kg_esperado,t_sat_c_esperado,tolerancia,status_revisao
V01_10bar_saturado_agua80,10,saturado_seco,80,2.4414,179.89,0.001,pendente
~~~~

### Arquivo 10: `tests/golden/pci_umido_referencia.csv`

~~~~
caso,pci_seco_mj_kg,umidade_bu_frac,pci_umido_mj_kg_esperado,tolerancia,status_revisao
P01,18.5,0.30,12.217,0.001,pendente
P02,18.5,0.35,11.170,0.001,pendente
P03,18.5,0.40,10.123,0.001,pendente
P04,18.5,0.45,9.076,0.001,pendente
P05,18.5,0.50,8.029,0.001,pendente
~~~~

### Arquivo 11: `tests/golden/test_golden.py`

~~~~
"""Testes golden da EULER.

SOMENTE LEITURA para agentes de programação: valores revisados pela equipe científica
(ver docs/fisica_para_revisao.md). Se falhar, o código está errado até prova em contrário.
Ajuste apenas os imports/assinaturas quando os módulos existirem (tickets T06, T07, T08).
"""
from pathlib import Path

import pandas as pd
import pytest

AQUI = Path(__file__).parent

indireto = pytest.importorskip("euler.indireto")
vapor = pytest.importorskip("euler.vapor")
combustivel = pytest.importorskip("euler.combustivel")


@pytest.mark.parametrize("linha", pd.read_csv(AQUI / "casos_referencia.csv").to_dict("records"))
def test_perda_gases_modo_referencia(linha):
    comp = {k: linha[k] for k in ("C", "H", "O", "N", "S")}
    res = indireto.perda_gases(
        t_gases_c=linha["t_gases_c"],
        o2_seco_pct=linha["o2_seco_pct"],
        umidade_bu_frac=linha["umidade_bu_frac"],
        t_ar_c=linha["t_ar_c"],
        composicao_seca=comp,
        pci_seco_mj_kg=linha["pci_seco_mj_kg"],
        modelo_cp=linha["modelo_cp"],
    )
    assert res.perda_pct == pytest.approx(linha["perda_gases_pct_esperada"], abs=linha["tolerancia_pp"])
    assert res.lambda_ar == pytest.approx(linha["lambda_esperado"], abs=1e-3)


@pytest.mark.parametrize("linha", pd.read_csv(AQUI / "vapor_referencia.csv").to_dict("records"))
def test_delta_h_vapor(linha):
    dh = vapor.delta_h_mj_kg(
        p_bar_abs=linha["p_vapor_bar_abs"],
        estado=linha["estado_vapor"],
        t_agua_alim_c=linha["t_agua_alim_c"],
    )
    assert dh == pytest.approx(linha["delta_h_mj_kg_esperado"], abs=linha["tolerancia"])


@pytest.mark.parametrize("linha", pd.read_csv(AQUI / "pci_umido_referencia.csv").to_dict("records"))
def test_pci_umido(linha):
    pci = combustivel.pci_umido(linha["pci_seco_mj_kg"], linha["umidade_bu_frac"])
    assert pci == pytest.approx(linha["pci_umido_mj_kg_esperado"], abs=linha["tolerancia"])
~~~~

### Arquivo 12: `lab/referencia_perda_gases.py`

~~~~
"""
EULER · calculadora de REFERÊNCIA para revisão (não é o motor nem o gerador).
Perda sensível nos gases de chaminé, base PCI, por kg de combustível seco.
Hipóteses: combustão completa; ar seco 21/79; cp constantes (1,05 gases secos; 1,90 vapor) — simplificação;
referência 25 °C; ar de combustão a 25 °C; sem umidade do ar.
"""
import numpy as np

COMP = dict(C=0.50, H=0.06, O=0.43, N=0.003, S=0.0005)   # fração mássica, base seca (cinzas 0,65%)
PCI_SECO = 18.5      # MJ/kg seco
HVAP = 2.442         # MJ/kg a 25 °C
CP_GAS, CP_H2O = 1.05e-3, 1.90e-3   # MJ/(kg·K)

def perda_gases(Tg, o2_seco, w, comp=COMP, pci_seco=PCI_SECO, Tref=25.0):
    C,H,O,N,S = (comp[k] for k in "CHONS")
    a = C/12 + H/4 + S/32 - O/32                      # kmol O2 esteq./kg seco
    y = o2_seco/100
    # (λ-1)a = y [C/12 + S/32 + (λ-1)a + 79/21 λ a + N/28]
    k = 79/21
    x = (a + y*(C/12 + S/32 + N/28) - y*a) / (1 - y - y*k)
    lam = x / a
    m_dry = (C/12)*44 + (S/32)*64 + (lam-1)*a*32 + (k*lam*a)*28 + N   # kg gás seco/kg seco
    m_h2o = 9*H + w/(1-w)
    num = (m_dry*CP_GAS + m_h2o*CP_H2O) * (Tg - Tref)
    den = pci_seco - HVAP*w/(1-w)
    return num/den, lam

if __name__ == "__main__":
    q, lam = perda_gases(180, 8, 0.40)
    print(f"referência 180 °C, O2 8%, w 40%: perda = {q*100:.2f}%  λ = {lam:.3f}")
~~~~

### Arquivo 13: `templates/amostras.csv`

~~~~
amostra_id,lote_id,data,umidade_bu_frac,pci_seco_mj_kg,C,H,O,N,S,cinzas,metodo,laboratorio,origem_dado
A-0001,L-0001,2026-10-05T11:00:00-03:00,0.38,18.5,0.50,0.06,0.43,0.003,0.0005,0.0065,estufa_ISO18134,interno,sintetico
~~~~

### Arquivo 14: `templates/combustivel.csv`

~~~~
data,tipo,fornecedor_id,lote_id,massa_kg,volume_m3,densidade_kg_m3,origem_densidade,preco_brl,origem_dado
2026-10-05T10:30:00-03:00,recebimento,F1,L-0001,30000,,,,5400.00,sintetico
~~~~

### Arquivo 15: `templates/diario.csv`

~~~~
caldeira_id,instante_observado,instante_registrado,turno,operador_id,regime,p_vapor_bar_man,t_gases_c,ponto_gases_id,o2_seco_pct,instrumento_o2_id,co_ppm,t_agua_alim_c,t_ar_c,purgas_n,purgas_s,totalizador_vapor_t,producao,ocorrencia,flag_instrumento_indisponivel,origem_dado
CALD-SINT-01,2026-10-05T08:00:00-03:00,2026-10-05T08:05:00-03:00,A,OP-01,estavel,9.0,182,CHAMINE-1,8.1,ANALIS-01,,80,28,1,20,15234.5,,,false,sintetico
~~~~

### Arquivo 16: `templates/eventos.csv`

~~~~
instante,tipo,descricao,autorizado_por,origem_dado
2026-10-12T14:00:00-03:00,limpeza,Limpeza dos tubos de fumaça,SUP-01,sintetico
~~~~

### Arquivo 17: `templates/instrumentos.csv`

~~~~
instrumento_id,tipo,ponto,unidade,resolucao,incerteza_declarada,ultima_verificacao,observacao
ANALIS-01,analisador_o2,CHAMINE-1,pct_seco,0.1,0.3,2026-09-01,sintetico
~~~~

---

## Fim do arquivo mestre

Depois de criar todos os arquivos, confirme a lista para o Adryan, rode `pytest -q` (os testes golden devem aparecer como *skipped* até a Etapa 2) e espere o "ok" dele para a Etapa 1.
