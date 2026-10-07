# EULER App Beta — Checklist Final

Data do snapshot: 07/10/2026  
Base da documentação: `feature/auth-beta` em `7c6e8ac6ba523a0ae07e23dafccd9c3e3f168122`.

> Regra de leitura: **Concluído** significa incorporado e validado no escopo descrito. **Pendente** ou **Parcial** não deve ser tratado como liberado no Beta final.

## Status

| Área | Status | Evidência / observação |
|---|---|---|
| Autenticação | **Concluído no código Beta** | Cadastro/login, recuperação, aprovação, suspensão, organizações e papéis fazem parte do PR #3. O cache curto do contexto de autenticação foi incorporado pelo PR #15. O PR #3 ainda está **Draft** contra `main`, portanto a promoção final do Beta ainda não ocorreu. |
| Performance | **Concluído no escopo dos PRs #15 e #16** | PR #15 adicionou cache de 45 s do contexto de autenticação com invalidação/revalidação; PR #16 adicionou cache compatível da assinatura dos dados preservando o algoritmo legado. Ambos estão mesclados. |
| Dependências | **Concluído** | PR #17 mesclado. Família Supabase 2.32.0 alinhada, `httpx`, `pydantic` e `yarl` fixados, Docker usando `requirements-lock.txt` como constraints, `pip check` e smoke tests offline. |
| Supabase | **Parcial / validação externa pendente** | Configuração, migration, scripts e smoke tests offline estão documentados. A validação integrada contra um projeto Supabase real continua sendo passo operacional externo e não há evidência neste snapshot de que o fluxo completo remoto tenha sido concluído. |
| Tauri / Startup UX | **Concluído** | PR #18 mesclado. Splash local, janela remota oculta durante carga, cold start, offline/retry, restrição de navegação e ausência de novas permissões nativas. |
| Linux | **Concluído no PR #18; revalidação da base em andamento** | Build Linux do PR #18 passou e publicou artifact `euler-linux` com AppImage e `.deb`. Após o merge do #18, o workflow da base `feature/auth-beta` foi disparado novamente e estava em execução neste snapshot. |
| Windows | **Concluído no PR #18; revalidação da base em andamento** | Build Windows do PR #18 passou e publicou artifact `euler-windows` com instalador NSIS. Após o merge do #18, o workflow da base também estava em execução neste snapshot. |
| Integração Adryan | **Pendente** | PR #19 está aberto e mergeável, mas **não mesclado**. Integra `mensal`, `dia_a_dia`, `condicoes`, `atendimento` e dependências internas. Deve ser atualizado/revalidado sobre a base que já contém o PR #18 antes da integração final. |
| Testes | **Parcial até o merge/reteste do #19** | CI do PR #18 passou. O PR #19 reporta `799 passed, 34 skipped` localmente com bypass oficial de auth e CI verde na base anterior; a validação final precisa ser repetida após atualização sobre a base atual. |
| Golden / tolerâncias | **Preservados no PR #19, aguardando fechamento final** | O relatório do Codex declara que `tests/golden/**` e tolerâncias não foram alterados. Confirmar novamente no diff final antes do merge do #19. |
| PRs finais | **Em andamento** | #15, #16, #17 e #18: mesclados. #19: aberto. #3 (`feature/auth-beta -> main`): aberto, mergeável e Draft. |

## PRs que compõem esta etapa

- **#15** — Performance: cache curto do contexto de autenticação — **MERGED**.
- **#16** — Performance: cache compatível da assinatura dos dados — **MERGED**.
- **#17** — Segurança: dependências Supabase reproduzíveis no runtime — **MERGED**.
- **#18** — Tauri: startup profissional, cold start e retry — **MERGED**.
- **#19** — Core: integrar domínio atual do Adryan — **ABERTO / PENDENTE**.
- **#3** — Beta v0.1: autenticação, aprovação e administração — **DRAFT / PENDENTE DE FECHAMENTO FINAL**.

## Critério para considerar o Beta pronto para promoção

O Beta só deve ser tratado como final quando, no mínimo:

1. o PR #19 estiver atualizado sobre a base atual, revisado e mesclado;
2. a suíte completa e o lint aplicável tiverem sido reexecutados no estado integrado;
3. os workflows CI e Tauri da base final estiverem verdes;
4. `tests/golden/**` e tolerâncias continuarem sem alterações;
5. o PR #3 tiver sido revalidado com os commits finais e estiver pronto para sair de Draft;
6. a validação operacional necessária do Supabase real estiver registrada, caso seja requisito de liberação.

## Dívida técnica conhecida

- `app/auth.py` possui uma falha de ordenação de imports (`ruff I001`) já registrada pelo PR #19. O arquivo não foi alterado nesta tarefa e deve ser corrigido separadamente com autorização explícita.
