# Relatório Codex — integração Adryan Core

## Nova base

`7c6e8ac6ba523a0ae07e23dafccd9c3e3f168122`

## Novo SHA

Atualização da base: `271062560d4c1224ba01b0aaea8ac1e53031508d`.

## Conflitos encontrados

Nenhum conflito de conteúdo.

## Resolução

A branch `codex/adryan-core-integration` recebeu a nova `feature/auth-beta` por merge, preservando integralmente autenticação, caches, dependências/Supabase, Tauri/startup UX e isolamento por organização. Nenhum arquivo protegido foi editado voluntariamente.

## Testes

- Direcionados do domínio: `97 passed`.
- Suíte completa aplicável: `815 passed, 34 skipped`, executada com `EULER_TEST_BYPASS_AUTH=1`.

## Lint/format

- Lint dos arquivos Python alterados pelo PR: passou.
- `ruff check .`: passou.
- `ruff format --check .`: `255 files already formatted`.

## Golden

`tests/golden/**` permanece intacto.

## Tolerâncias

Nenhuma tolerância científica foi alterada ou aumentada durante a atualização da base. Nenhum assert foi removido durante a atualização.
