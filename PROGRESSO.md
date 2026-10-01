# PROGRESSO da construção

| Etapa | Status | Data | O que funciona | Pendências |
|---|---|---|---|---|
| 0 · Preparar | concluída | 2026-10-01 | 17 arquivos da Parte 3 criados idênticos ao arquivo mestre (conferido por script); `.venv` com Python 3.11; dependências instaladas (`pip install -e ".[dev]"`); `pytest -q` → testes golden *skipped*; `ruff check .` sem erros. Checagem extra: `lab/referencia_perda_gases.py` e IAPWS reproduzem todos os valores golden (G01–G12, V01, P01–P05). | Spec v0.3 não está no repositório (citada por T02, T11, T12, T13): pedir ao Adryan antes da Etapa 3. |
| 1 · Fundação | concluída | 2026-10-01 | App abre com a tela inicial e o rodapé de segurança (texto único em `euler/textos.py`, testado contra `docs/visao_produto.md`). CI no GitHub Actions (ruff + pytest), modelo de PR, README, script de prints (`scripts/prints.py`). | — |
| 2 · Física | concluída | 2026-10-01 | `euler/vapor.py` (IF97, E8), `euler/indireto.py` (E1–E7, modo constante), `euler/combustivel.py` (E5, E9, E10). **18 testes golden passando** (G01–G12, V01, P01–P05). Página "Calculadora de referência" com perda, λ, PCI úmido, sensibilidades e aviso de simulação; bloqueia com motivo fora do domínio (ex.: abaixo do orvalho). | Modo cp variável aguarda fonte de cp(T) do revisor (D08). Decisões D05–D11 aguardam aprovação. |
| 3 · Entrada de dados | concluída | 2026-10-01 | Contrato de dados em `euler/io/esquemas.py`, que gera `docs/contrato_dados.md` e `templates/planilha_modelo_euler.xlsx` (`python scripts/gerar_modelos.py`). Importadores de todas as tabelas (CSV com `,` ou `;`, vírgula decimal, codificação Windows, planilha .xlsx). Avisos com linha e motivo: lacunas, duplicatas, totalizador reiniciado, registro tardio, unidades suspeitas, volume sem densidade, relações entre tabelas. Tela "Importar dados" com exemplo de problemas em `demo/qualidade/`. | Registro de correções manuais (original, novo valor, motivo, autor, data) ainda não existe: hoje nada é corrigido. Decisões D12–D18 aguardam aprovação. |
| 4 · Extrato por fornecedor | concluída | 2026-10-01 | `extrato_por_fornecedor` (E11): energia e R$/GJ por lote e fornecedor, origem de cada dado, ranking por energia × por tonelada, alerta neutro de umidade fora da faixa histórica, "energia não determinada" sem umidade medida. Reproduz a tabela F1–F3 do documento. Tela "Extrato por fornecedor" com gráficos (preço/t × custo/GJ; umidade por semana). **Dados do caso de demonstração (T18) adiantados:** `demo/caso_demo/` + `demo/gerar_caso_demo.py`, botão "Caso de demonstração" na importação. | Decisões D19–D21 aguardam aprovação. Roteiro do vídeo fica para a Etapa 7. |
| 5 · Investigação | concluída | 2026-10-01 | `periodos.py` (resumo entre medições de estoque), `direto.py` (T10: eficiência com intervalo, E13 testado), `deteccao.py` (mudança detectável), `investigacao.py` (T13: JSON com o que mudou, hipóteses, independência E12, o que falta, próxima verificação, abstenção, valor em jogo só com base, custo E14), `capacidades.py` (T11, 11 análises). Testes: casos A, B, C, contraexemplo da purga e semana sem vapor. Telas "Dados e limites" (com período a período) e "Investigação" (5 blocos, gráfico e JSON). | T12 (detecção de degrau) não feito (extra). Decisões D22–D32 aguardam aprovação; formato do JSON e tabela de capacidades a conferir com a spec v0.3. |
| 6 · Relatório | concluída | 2026-10-01 | `euler/relatorio.py`: JSON → HTML com os 5 blocos fixos, rodapé de segurança, selo "dados sintéticos", pronto para A4; PDF pelo Chromium quando disponível. Teste com lista de verbos proibidos (e trava no app). Tela "Relatório" com botão "Gerar relatório", prévia e downloads. **3 exemplos em `docs/exemplos_relatorio/`** (HTML + PDF) com guia de revisão. | **Adryan: revisar o texto dos 3 exemplos.** Decisões D33–D34. |
| 7 · Demonstração | concluída (falta só o ensaio e a narração, que dependem de pessoas) | 2026-10-01 | Caso sintético completo (`demo/caso_demo/`, D53: dados **mantidos**, abstenção preservada); fluxo inteiro no app em menos de 5 minutos; revisão de uso como usuário novo com 5 falhas reais corrigidas e testadas (resultado antigo nunca aparece com dados novos); 8 prints (`prints/`); vídeo **rascunho sem narração** de 2 min (`demo/video/rascunho_video_demo.mp4`) com o texto da narração em `demo/ROTEIRO_VIDEO.md`; guia de cliques da apresentação ao vivo (`demo/GUIA_DEMONSTRACAO_AO_VIVO.md`). | Adryan: gravar a narração; ensaiar no notebook da apresentação (ver seção abaixo). |
| 8 · Entrega aos devs | concluída (falta o repositório privado e a autoria, que são decisões do Adryan) | 2026-10-01 | `HANDOFF.md` (instalação, organização, o que funciona, experimental, limitações, revisão crítica do código, decisões pendentes, casos, prioridades até 30/10); README reescrito; `requirements-lock.txt`; instalação do zero conferida; PDFs para os revisores em `docs/revisao/` (física E1–E15 e as três decisões prioritárias + Q1–Q17). | **Repositório ainda público** → Adryan torna privado. T19 (tag e autoria para o INPI) → Adryan. T17 fica fora deste repositório. |

## Fase R · Revisão e validação do motor físico (pedido do Adryan em 01/10/2026)

| Item | Implementação | Aprovação científica | Onde ver |
|---|---|---|---|
| Diagnóstico (matriz de 28 cálculos, erros ER-1 a ER-9) | **concluída** | não se aplica | `docs/revisao_motor_fisico.md` §1 |
| Correções dos erros demonstráveis | **concluída** (ER-1 a ER-9) | **pendente** (revisor) | §4 do mesmo documento |
| Novas funções experimentais (cp(T) NASA, umidade do ar, CO, O₂ úmido) | **concluída**, marcada como experimental | **pendente** (Q2–Q4, Q10) | `euler/indireto.py`, `euler/propriedades_gases.py` |
| Incerteza por componentes (GUM) e correlação entre períodos | **concluída** | **pendente** (Q8, Q11, Q12, Q16) | `euler/incerteza.py` |
| Recebido × queimado (cenários do pátio) | **concluída** | **pendente** (Q7) | `euler/periodos.py` |
| Regras da investigação (vocabulário, `oposta`, fechamento) | **concluída** | **pendente** (Q9, Q17) | `euler/investigacao.py` |
| Verificação | **concluída**, mas a auditoria mostrou que "53 verificações independentes" era um resumo errado; reclassificada em categorias (ver revisão de confiabilidade) | não se aplica: verificar ≠ aprovar | `docs/matriz_validacao_fisica.md` |
| Comparação com caldeira real | **não feita** (sem dados reais no repositório) | — | matriz, P-4 |
| Perguntas aos revisores | **prontas** (Q1–Q17) | aguardando respostas | `docs/perguntas_revisores.md` |
| Decisões | D35–D50 propostas; D08, D24 e D26 substituídas | **todas pendentes** | `docs/decisoes.md` |

**Situação:** a implementação da Fase R está concluída e verificada; **nenhum item tem
aprovação científica**. Testes passando mostram que o código faz o que foi especificado, não
que a especificação esteja certa.

- Versão examinada no diagnóstico: `97ad0c6`. Versão final da fase: `01c2a4b`.
- `pytest -q`: 243 testes passando; `ruff check .` e `ruff format --check .` sem erros;
  `tests/golden/` e tolerâncias sem alteração.
- Sites bloqueados na sessão (para liberar na rede do ambiente, se quiser que a próxima
  sessão confira as fontes originais): `www.iapws.org`, `webbook.nist.gov`, `janaf.nist.gov`,
  `www.bipm.org`.
- Print `05_dados_e_limites` refeito (tabela com as colunas do pátio).

## Revisão de confiabilidade (auditoria externa de 01/10/2026)

Auditoria técnica externa da versão `2cd4dc3` (não é aprovação científica). Escopo fechado:
corrigir A1–A5, reclassificar as verificações e corrigir as referências, sem mexer nos
golden nem nos dados do demo.

| Item | Implementação | Aprovação científica | Onde ver |
|---|---|---|---|
| A1 · FIFO com massa sem qualidade conhecida | **corrigido**: FIFO indisponível com motivo; hipóteses dos cenários declaradas | **pendente** (decisão 1) | D51; V-C10, V-C11 |
| A2 · umidade duas vezes no resíduo | **corrigido**: cada fonte uma vez, conferido perturbando os dados pela cadeia inteira | **pendente** (decisão 3) | D54; V-D7, V-D8 |
| A3 · incerteza ausente virando zero | **corrigido**: orçamento completo / parcial / indisponível; nunca "sim" com orçamento incompleto | **pendente** (decisão 3) | D52; V-D9, V-D10, V-E6 |
| A4 · divisão por zero (consumo ou vapor zero) | **corrigido**: bloqueio com motivo | não se aplica | D56; V-C12, V-C13 |
| A5 · O₂ úmido fora do domínio | **corrigido**: recusa com motivo | não se aplica | D56; V-B16, V-B17 |
| Relatório: quatro estados da detecção | **corrigido** (relatório e tela) | não se aplica | V-E7 |
| Tela sem as hipóteses `oposta` (achado desta revisão) | **corrigido** | não se aplica | V-E8 |
| PCI seco e dispersão de Δh no orçamento | **implementado** | **pendente** | D55, D57 |
| Matriz reclassificada (57 linhas, 4 categorias + consistência, regressão, golden); 18 pontos reservados IF97 × IAPWS-95 | **concluída** | não se aplica | `docs/matriz_validacao_fisica.md` |
| Referências corrigidas (GUM 4.3.7 como hipótese do projeto; CODATA × JANAF; IAPWS conferido pela auditoria) | **concluída** | — | `docs/revisao_motor_fisico.md` §2 e §7 |
| Pauta de revisão humana: três decisões prioritárias + Q1–Q17 | **pronta** | aguardando reunião | `docs/perguntas_revisores.md` |
| Demo: história mudou (umidade só condicional, abstenção) sem alterar dados | **feito**; gabarito, exemplos de relatório, roteiro e prints 05/06 atualizados | — | D53 (**decisão do Adryan**) |
| Comparação externa e piloto com dados autorizados | **não feita** | — | matriz, P-4 e P-7 |

- Versão examinada pela auditoria: `2cd4dc3`. Versão desta revisão: `b124c76`.
- `pytest -q`: 299 testes passando; `ruff check .` e `ruff format --check .` sem erros;
  `tests/golden/` e `lab/` sem alteração.

**Próximo passo:** reunião com os revisores começando pelas três decisões prioritárias
(`docs/perguntas_revisores.md`); decisão do Adryan sobre o demo (D53). Depois: casos
reservados montados fora da lógica do motor e piloto com dados autorizados de uma caldeira.
Vídeo e prints 04 e 07 da Etapa 7 são apresentação do fluxo sintético, não evidência de
validação.

## Etapas 7 e 8 · demonstração de 30/10/2026 e entrega aos desenvolvedores

**Escopo fechado:** carregar dados → conferir qualidade e limites → investigar → consultar
fornecedores → gerar relatório. Login, várias empresas, OCR, API e novas funções físicas
ficam para fases posteriores. Dados do demo **não** foram alterados e nenhuma incerteza foi
acrescentada: o caso continua mostrando a EULER explicando por que não conclui (D53, decisão
do Adryan).

**Falhas de uso encontradas e corrigidas:** relatório usando a investigação dos dados
anteriores; escolha de períodos voltando ao padrão ao trocar de tela; relatório sumindo
depois de baixar; barra lateral com a origem errada dos dados (estas quatro com teste em
`tests/test_app.py`); PDF do relatório com páginas quase vazias (conferido à mão: 4
páginas). Textos: plural, unidades, nome do arquivo
nos avisos, motivo quando o valor em jogo não é estimado, selo **DADOS SINTÉTICOS** em todas
as telas e no relatório, quadro "Em que pé está a EULER" (verificado · em revisão · não feito).

| Tipo de evidência | O que foi feito | Resultado |
|---|---|---|
| **Testes automáticos** | `pytest -q` (inclui telas pelo AppTest, fluxo completo do demo, verbos proibidos, golden) e `ruff check .` / `ruff format --check .` | 308 passando; lint sem erros; `tests/golden/` e tolerâncias sem alteração |
| **Instalação do zero** | ambiente novo, só `pip install -e ".[dev]"` | 275 passando, 33 pulados (CoolProp/Cantera, extra `validacao`) |
| **Conferência manual (navegador real)** | fluxo inteiro como usuário novo: demonstração, avisos, análises bloqueadas, troca de períodos, extrato, relatório, baixar HTML e PDF, trocar os arquivos depois, ir e voltar entre telas | sem resultado antigo nos dados novos; PDF baixado (4 páginas A4) |
| **Conferência manual (materiais)** | 8 prints, quadros do vídeo em cada cena, PDF do relatório, PDFs dos revisores (5 e 7 páginas) | legíveis em 1280 px, 1280 × 720 e A4 |
| **Depende do notebook da apresentação** | ensaio com o guia ao vivo; Chromium para o botão "Baixar PDF" (ou plano B com HTML); zoom no projetor; Windows não testado | **a fazer** (Adryan + 1 dev) |
| **Depende de pessoas** | narração do vídeo (rascunho atual não tem som); revisão do texto dos exemplos de relatório | **a fazer** (Adryan) |
| **Revisão humana e validação externa** | três decisões prioritárias + Q1–Q17 (`docs/revisao/`); golden; piloto com dados reais autorizados; T17 em repositório separado | **pendentes**: nenhuma proposta foi marcada como aprovada sem resposta humana |

- Versão examinada nesta etapa: `e49338d` (a mesma da capa dos PDFs de
  `docs/revisao/` e do `HANDOFF.md`).
- **Repositório ainda público** (a API do GitHub responde sem login em 01/10/2026).

**Próximo passo até 30/10:** (1) Adryan torna o repositório privado; (2) ensaio no notebook
da apresentação seguindo `demo/GUIA_DEMONSTRACAO_AO_VIVO.md`, duas vezes seguidas sem ajuda;
(3) narração gravada sobre o rascunho do vídeo; (4) enviar `docs/revisao/` aos revisores.
Detalhes e responsáveis: `HANDOFF.md` §9.

## Visual do app (pedido do Adryan em 01/10/2026, depois da conferência no Windows)

O Codex abriu a EULER no computador do Adryan (cópia sem Git; PDF direto indisponível por
falta do Chromium). Pedido: conhecer o app e deixá-lo mais profissional, organizado e com
cara de aplicativo, **sem mexer em cálculos, demo, incertezas nem resultados inconclusivos**.

| Item | O que mudou | Situação |
|---|---|---|
| Identidade EULER | logo e marca (um "E" de barras sobre ferrugem), barra lateral azul-marinho, tema e cartões; faixa de abertura na tela inicial | **feito**; D58 **proposta pendente (Adryan)** |
| Organização | "Passo X de 5" e resumo no alto de cada tela; botão **Próximo** no fim; exemplos sintéticos em cartões; bloqueado antes do liberado em Dados e limites | **feito** |
| Investigação | resultado no topo (conclusão + próxima verificação lado a lado; consumo, valor em jogo e explicações em cartões); blocos 1–4 em abas; linha do tempo dos períodos; gráfico com escolha da grandeza; coluna **Diferença (± incerteza)**; selos para os quatro estados da detecção | **feito**; D59 **proposta pendente (Adryan)** |
| Relatório | botões lado a lado; **Imprimir ou salvar como PDF** na prévia (funciona sem Chromium) | **feito**; D60 **proposta pendente (Adryan)** |
| Falha encontrada | um texto interno aparecia na tela do Relatório (Streamlit mostra texto solto da página) | **corrigida**, com teste |
| Passeio escrito | `demo/PASSEIO_PELAS_TELAS.md` (onde clicar em cada tela + como atualizar a cópia do Windows) | **feito** |
| Guia ao vivo | `demo/GUIA_DEMONSTRACAO_AO_VIVO.md` refeito para o visual novo | **feito** |
| Prints e vídeo | não refeitos (pedido do Adryan: ele mesmo faz o vídeo); `prints/` mostra o visual anterior | — |

- Cálculos, JSON da investigação, relatório baixado, demo e `tests/golden/` **sem
  alteração**. Os números da tela continuam vindo do JSON.
- Evidências: testes de tela novos (resumo da Investigação, semana sem vapor sem número
  inventado, nenhum texto solto nas telas); conferência visual em navegador real de todas as
  telas; botão de impressão conferido (abre a impressão, some do papel).
- `pytest -q`: 311 passando; `ruff check .` e `ruff format --check .` sem erros.

## Acabamentos e tema escuro (pedidos do Adryan em 01/10/2026)

| Item | O que mudou | Situação |
|---|---|---|
| Visual D58–D60 | aprovado pelo Adryan | **aprovado** |
| Tema escuro e marca | fundo grafite, barra lateral mais escura, interface monocromática; marca "E" de traço fino, sem fundo cobre; relatório com a marca em tinta escura | **feito**; D61 **aprovada** (pedido do Adryan) |
| O que falta saber | dois grupos na tela: incertezas a cadastrar em instrumentos.csv e o que medir/registrar | **feito**, com teste |
| Envio de arquivos | "Escolher arquivos" em português | **feito** |
| Telas mais rápidas | investigação e período a período guardadas pela assinatura dos dados; mudar dados refaz a conta | **feito**, com teste |
| Telas sem dados | botão "Carregar o caso de demonstração" | **feito**, com teste |
| Extrato | tabela inteira, sem rolagem lateral; gráficos sem caixa a mais | **feito** |
| Windows | `ABRIR-EULER.cmd` dentro do projeto | **feito**, com teste |
| Código | formatação das telas em `app/formatacao.py` (sem Streamlit), usada também pela prévia | **feito** |

- Cálculos, demo, incertezas e `tests/golden/` **sem alteração**.

**Modo de trabalho:** automático (pedido do Adryan em 01/10/2026): seguir as etapas sem esperar "ok"; decisões não especificadas vão para `docs/decisoes.md` como propostas pendentes.

## Notas da Etapa 0
- O arquivo mestre foi copiado para a raiz (`EULER_CONSTRUCAO_COMPLETA.md`) para que "continue" funcione em sessões novas.
- `pyproject.toml` mínimo criado já na Etapa 0 (necessário para instalar dependências). A Etapa 1 (T01) completa com CI e modelo de PR.
- Ruff ignora `lab/` (calculadora de referência copiada como veio, não é código do produto); `ruff format` não toca em `tests/golden/`.
- Ambiente na nuvem: o endereço `localhost:8501` não abre no computador do Adryan. Nas etapas com tela, mostrar prints (Playwright) enviados na conversa.
