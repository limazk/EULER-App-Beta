# Relatório Codex — integração Adryan Core

## Status

PARCIALMENTE CONCLUÍDO

## Branch

`codex/adryan-core-integration`

## Base utilizada

`f0e924050cfa0038af24174582dfc9cba5899230` (`feature/auth-beta` no início)

## Origem utilizada

`0c90f68f4a0e582083b362d42524bd78d3f89a0b`

## Concluído

- Integrados os domínios mensal, dia a dia, condições e atendimento.
- Reconciliadas somente as dependências exigidas pelos novos módulos e testes.
- Integradas as regressões D107 e D110 da origem.
- Preservadas autenticação, infraestrutura Beta e separação por organização.
- Todos os testes diretamente relevantes e a suíte completa passaram.

## Arquivos adicionados

- `app/vocabulario_fabrica.py`
- `euler/atendimento.py`
- `euler/condicoes.py`
- `euler/dia_a_dia.py`
- `euler/mensal.py`
- `scripts/medir_escala.py`
- `tests/test_atendimento.py`
- `tests/test_condicoes.py`
- `tests/test_dia_a_dia.py`
- `tests/test_escala_atendimento.py`
- `tests/test_mensal.py`
- `tests/test_planilha_real.py`
- `tests/test_preco_e_ponte.py`
- `tests/test_previa_fechamento.py`
- `tests/test_revisao_inconsistencias.py`

## Arquivos alterados

- `app/importacao_guiada.py`
- `euler/acompanhamento.py`
- `euler/armazem.py`
- `euler/conta.py`
- `euler/entrega.py`
- `euler/fechamento.py`
- `euler/io/leitura.py`
- `euler/linha_do_tempo.py`
- `euler/painel.py`
- `euler/percurso.py`
- `tests/test_conclusao_financeira.py`
- `tests/test_importacao_guiada.py`

## Commits realizados

- `91f5ff9` — core: integrar domínio mensal e atendimento
- `ee88905` — test: integrar regressões do domínio atual
- `9b56366` — test: atualizar requisitos de importação e incerteza

## Testes executados

`pytest -q -p no:cacheprovider tests/test_atendimento.py tests/test_condicoes.py tests/test_dia_a_dia.py tests/test_escala_atendimento.py tests/test_mensal.py tests/test_planilha_real.py tests/test_preco_e_ponte.py tests/test_previa_fechamento.py tests/test_revisao_inconsistencias.py`

`97 passed`

`pytest -q -p no:cacheprovider tests/test_importacao_guiada.py tests/test_conclusao_financeira.py`

`24 passed`

`EULER_TEST_BYPASS_AUTH=1 pytest -q -p no:cacheprovider`

`799 passed, 34 skipped`

`ruff format --check .`

`250 files already formatted`

`ruff check` nos arquivos Python alterados

`All checks passed!`

## Testes que falharam

`ruff check .` encontra `I001` preexistente em `app/auth.py:7`. Esse arquivo é proibido pela tarefa e não foi alterado. A suíte inicialmente executada sem `EULER_TEST_BYPASS_AUTH=1` também bloqueou as telas por ausência de credenciais Supabase; com o bypass oficial de testes, a suíte passou integralmente.

## Golden/tolerâncias

`tests/golden` não foi alterado.
Tolerâncias não foram alteradas.

## Pendências

- Corrigir em tarefa separada a ordenação de imports preexistente em `app/auth.py`, com autorização para alterar esse arquivo, para que o comando literal `ruff check .` passe.
- A nova interface mensal completa permanece fora do escopo desta integração de motor.

## Bloqueios

- `app/auth.py` é explicitamente proibido nesta tarefa, mas contém a única falha do comando global `ruff check .`.

## Próxima ação recomendada

Autorizar uma correção isolada de formatação em `app/auth.py`, executar `ruff check .` e então revisar o PR sem fazer merge automático.

## Prompt de continuação

Continue na branch `codex/adryan-core-integration`, a partir do último commit registrado no relatório. O motor Adryan e os testes relevantes estão prontos; a suíte completa passou com `EULER_TEST_BYPASS_AUTH=1`. Obtenha autorização explícita para corrigir somente a ordenação de imports em `app/auth.py`, rode `ruff check .`, atualize este relatório e faça um commit final. Não altere golden, tolerâncias, Supabase, deploy ou interface mensal completa.
