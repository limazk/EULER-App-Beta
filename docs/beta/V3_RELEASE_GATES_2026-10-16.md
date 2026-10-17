# EULER 3.0 — Auditoria de gates de liberação (2026-10-16)

> Documento de coordenação, **não é aprovação de merge nem de deploy**.
> Coleta inicial via conectores GitHub, Render e Supabase em 2026-10-16.
> Este relatório é baseado em metadados e evidências de CI; não substitui teste end-to-end com contas reais ou em máquinas físicas.

## Referências imutáveis

- Repositório: https://github.com/limazk/EULER-App-Beta
- PR candidato: https://github.com/limazk/EULER-App-Beta/pull/29 — `open`, `draft=true`, mergeável, sem aprovação humana registrada
- Base `main`: `42e28e8d8ee8db99430226e4a298f4b3e6e2fdd2`
- Head candidato: `8d89de9395f9a0fcfdc829e3b88280202982ec28`
- Comparação: 26 commits à frente, 0 atrás, 41 arquivos afetados
- CI no head: https://github.com/limazk/EULER-App-Beta/actions/runs/38212494187 — `success` (929 passed, 0 failed, 0 skipped, 7 warnings conforme descrição do PR)
- Builds Tauri: https://github.com/limazk/EULER-App-Beta/actions/runs/38211447620 — jobs Windows e Linux `success`; conteúdo do commit de build igual à árvore integrada segundo registro do PR #29

## Estado da infraestrutura — somente leitura

- Render `EULER-App-Beta`: serviço Docker `not_suspended`, plano `free`, branch `main`, `autoDeploy=yes` com gatilho por commit.
- Último deploy no Render: `live` no commit `42e28e8` (07/10/2026); **EULER 3.0 não foi publicada**.
- URL de serviço: https://euler-app-beta.onrender.com
- Supabase: projeto nomeado `EULER` consta `INACTIVE` em 16/10; sua disponibilidade precisa ser restabelecida/confirmada antes de testes reais. **Não foram feitas mutações** no projeto.
- Advisors Supabase (security/performance) retornaram listas vazias; isso **não comprova** ausência de problemas enquanto o projeto permanece inativo.
- Persistência/backup SQLite no Render gratuito e restauração ainda **não comprovados**.

## Gates obrigatórios (manter bloqueados até evidência)

| Gate | Dono | Estado em 16/10 | Evidência necessária |
| --- | --- | --- | --- |
| G1: testes Auth/Supabase com identidades reais autorizadas, suspensão, revogação, expiração e isolamento A/B | Codex | **BLOQUEADO** (Supabase `INACTIVE`; nenhum teste real atestado) | Logs e matriz de casos com contas de teste, sem credenciais, incluindo negações cruzadas |
| G2: persistência, backup e restauração | Codex | **PENDENTE** | Teste de reinício/redeploy e de restauração com dados de teste, RPO/RTO medidos, sem modificar dados reais |
| G3: instaladores Windows NSIS e Linux AppImage/deb em sistemas reais | Antigravity | **PARCIAL** (CI gerou artefatos; execução em SOs reais não comprovada) | SO/versão, arquitetura, hashes, screenshots/logs, instalação-abertura-login-fechamento-desinstalação |
| G4: aprovação do PR #29 por responsável humano após revisão | ChatGPT coordena, responsável humano aprova | **PENDENTE** | Aprovação explícita e registro no PR; retirar draft só após G1-G3 e revisão |
| G5: deploy controlado e rollback | ChatGPT + Codex | **BLOQUEADO** | Plano de janela, proteção contra auto-deploy, referência exata de versão anterior, checklist de verificação e restauração/rollback ensaiado |

## Divisão rígida dos trabalhos

### ChatGPT — auditoria/release gates (somente documentação)
- Registra fatos conferidos nos conectores e as evidências/pendências; não aprova o próprio PR #29.
- Branch exclusiva: `docs/v3-release-gates-20261016`.
- Arquivo exclusivo: `docs/beta/V3_RELEASE_GATES_2026-10-16.md`.
- Não altera `main`, `integration/v3-beta-release-candidate`, configurações Render/Supabase ou branches de outros agentes.

### Codex — validações profundas e engenharia reversível
- Criar branch própria **a partir** de `integration/v3-beta-release-candidate` no SHA `8d89de9`; não fazer push na branch da candidata.
- Testes da matriz de autenticação, tenant isolation e sessão usando ambientes e usuários autorizados. Não coletar/expor senhas, tokens ou chaves.
- Investigar perda de SQLite efêmero e produzir proposta/implementação reversível, isolada e testada de persistência/backup quando possível, sem mexer em produção.
- Produzir runbook técnico de rollback; PR separado e **draft** com base na branch de integração.
- Não tocar neste arquivo de auditoria nem nas evidências de desktop do Antigravity.
- Caso Supabase inativo ou credenciais de teste ausentes: **marcar testes reais como BLOQUEADOS, não simular aprovação**.
- Proibido `force-push`, merge, deploy, alteração de RLS/migrações/dados reais ou desativação de segurança sem aprovação específica.

### Antigravity — smoke tests desktop (rápidos e sem código de produção)
- Usar artefatos associados à árvore validada `8d89de9` (run Tauri acima) e verificar hashes/origem.
- Rodar apenas nos SOs efetivamente acessíveis. Em SO inacessível, marcar explicitamente **NÃO EXECUTADO**.
- Testar abertura, startup/cold start, ausência de rede, recuperação, login com credenciais de teste autorizadas se Supabase ativo, fechamento e desinstalação.
- Branch documental própria, derivada da `main`, com arquivo exclusivo `docs/qa/V3_INSTALLER_SMOKE_2026-10-16.md`; PR separado draft.
- Nunca alterar `apps/euler-shell/**`, workflow, `main` ou branch de integração; registrar problemas para o Codex em vez de corrigi-los nesta frente.

## Condições de liberação

1. Não realizar merge do PR #29 enquanto G1, G2 ou G3 estiverem sem evidência aprovada.
2. Antes de qualquer merge na `main`, confirmar que o Render continua com auto-deploy habilitado; **merge pode causar publicação automática**. Preparar controle de deploy e reversão **antes** de mudar `main`.
3. Revisar as mudanças dos três agentes em PRs isolados, confirmar CI/artefatos e o head SHA final. Qualquer mudança no código reinicia os testes afetados.
4. Não classificar a candidata como homologada para operação industrial com base em CI ou testes sintéticos.
5. Não fechar issues #25/#27 sem verificar os critérios de aceite efetivos.

## Critério de saída

**APROVADO PARA LIBERAÇÃO** somente se os cinco gates tiverem evidência linkável, a revisão de segurança final passar, o responsável humano consentir com a publicação e existir rollback ensaiado. Até lá: **PRONTO PARA REVISÃO / NÃO LIBERADO**.
