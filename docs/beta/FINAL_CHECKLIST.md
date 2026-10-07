# EULER App Beta — Checklist Final

Data do snapshot: 07/10/2026  
Base da documentação: `feature/auth-beta` em `9a7c8f1f5847c37b916d7ff87e65da2679726ce3`.

> Estado desta etapa: a integração técnica em `feature/auth-beta` está concluída. A promoção para `main` ainda não ocorreu e depende da validação final integrada do Codex após o merge do PR #20.

## Status

| Área | Status | Evidência / observação |
|---|---|---|
| Autenticação | **Integrado na branch Beta** | Cadastro/login, recuperação, aprovação, suspensão, organizações e papéis fazem parte da `feature/auth-beta`. O PR #3 permanece **Draft** contra `main`. |
| Performance | **Concluído** | PRs #15 e #16 mesclados: cache do contexto de autenticação e cache compatível da assinatura dos dados. |
| Dependências | **Concluído** | PR #17 mesclado, com stack Supabase reproduzível, constraints no Docker, `pip check` e smoke tests offline. |
| Tauri / Startup UX | **Concluído** | PR #18 mesclado. Builds Linux e Windows passaram no escopo do PR. |
| Integração Adryan | **Concluída** | PR #19 mesclado. Merge SHA: `9a7c8f1f5847c37b916d7ff87e65da2679726ce3`. Último head validado antes do merge: `b5a87378beac14995d2fbfcdbb6be298e8558e00`. |
| Testes do #19 | **Verdes** | 97 testes direcionados passaram. Suíte completa: **815 passed / 34 skipped**. |
| CI do #19 | **Verde** | O CI do head final validado do PR #19 concluiu com sucesso. |
| Lint | **Verde** | `ruff check .` passou no estado validado do PR #19. |
| Format | **Verde** | 255 arquivos verificados como corretamente formatados. |
| Golden / tolerâncias | **Intactos** | Nenhuma alteração em `tests/golden/**`; nenhuma tolerância aumentada; nenhum assert removido. |
| Conflitos do #19 | **Nenhum** | A integração final do #19 foi revalidada sem conflitos. |
| Avisos conhecidos | **Não bloqueantes** | Apenas avisos sobre Node.js 20 nas GitHub Actions. |
| PR #20 | **Em atualização documental** | Somente os três arquivos finais em `docs/beta/**`. Não deve ser mesclado automaticamente por esta tarefa. |
| PR #3 | **DRAFT** | `feature/auth-beta -> main` continua aguardando a validação final integrada do Codex. |

## PRs que compõem esta etapa

- **#15** — Performance: cache curto do contexto de autenticação — **MERGED**.
- **#16** — Performance: cache compatível da assinatura dos dados — **MERGED**.
- **#17** — Segurança: dependências Supabase reproduzíveis no runtime — **MERGED**.
- **#18** — Tauri: startup profissional, cold start e retry — **MERGED**.
- **#19** — Core: integrar domínio atual do Adryan — **MERGED**.
- **#20** — Documentação final do Beta — **EM REVISÃO**.
- **#3** — Beta v0.1: `feature/auth-beta -> main` — **DRAFT**.

## Evidência final do PR #19

- Head validado: `b5a87378beac14995d2fbfcdbb6be298e8558e00`.
- Merge SHA: `9a7c8f1f5847c37b916d7ff87e65da2679726ce3`.
- Testes direcionados: **97 passed**.
- Suíte completa: **815 passed / 34 skipped**.
- CI: **verde**.
- `ruff check .`: **verde**.
- Format: **255 arquivos corretamente formatados**.
- Golden: **intacto**.
- Tolerâncias: **intactas**.
- Asserts removidos: **nenhum**.
- Conflitos: **nenhum**.

## Condição para promoção para `main`

A `feature/auth-beta` está tecnicamente integrada, mas ainda não deve ser promovida para `main`. Depois do merge do PR #20, o Codex deve executar a validação final integrada sobre o novo SHA da branch. Somente após essa validação o PR #3 poderá ser reavaliado para sair de Draft.

