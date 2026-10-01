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
| 7 · Demonstração | em andamento (pausada para a fase de revisão física) | 2026-10-01 | Tela inicial com "Começar com o caso de demonstração" e passos 1–5; menu na ordem do T15; teste do fluxo completo (`tests/test_fluxo_demo.py`); roteiro de 2 min (`demo/ROTEIRO_VIDEO.md`); script de rascunho do vídeo (`scripts/gravar_video_demo.py`). | Regravar o rascunho do vídeo e refazer os prints 04, 06 e 07 (os dados do demo mudaram). Parâmetro de cenário alterado: umidade do F3 de 42→54% para 44→56% (escolha de narrativa da demonstração, **não** é correção nem validação). |
| 8 · Entrega aos devs | a fazer | | | |

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

**Modo de trabalho:** automático (pedido do Adryan em 01/10/2026): seguir as etapas sem esperar "ok"; decisões não especificadas vão para `docs/decisoes.md` como propostas pendentes.

## Notas da Etapa 0
- O arquivo mestre foi copiado para a raiz (`EULER_CONSTRUCAO_COMPLETA.md`) para que "continue" funcione em sessões novas.
- `pyproject.toml` mínimo criado já na Etapa 0 (necessário para instalar dependências). A Etapa 1 (T01) completa com CI e modelo de PR.
- Ruff ignora `lab/` (calculadora de referência copiada como veio, não é código do produto); `ruff format` não toca em `tests/golden/`.
- Ambiente na nuvem: o endereço `localhost:8501` não abre no computador do Adryan. Nas etapas com tela, mostrar prints (Playwright) enviados na conversa.
