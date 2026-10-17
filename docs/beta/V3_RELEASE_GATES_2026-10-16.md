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

## Atualização da coordenação: 16/10 — resgate de QA interrompido por cota

- PR documental de QA: https://github.com/limazk/EULER-App-Beta/pull/34, branch `qa/v3-installers-antigravity-20261016`, criado em `draft` a partir da `main`.
- Evidência original: transcrição enviada pelo usuário da sessão Antigravity. O agente relatou abertura bem-sucedida do AppImage Linux com Xvfb/xdotool; detecção de splash 620×420 e janela principal 1440×900; inspeção do .deb; execução de testes offline, mas os logs brutos não foram anexados.
- Consulta complementar ao GitHub confirma que ambos os builds do Tauri passaram e que o arquivo versionado `tauri.conf.json` prevê as dimensões relatadas. Digests dos artefatos ZIP de workflow conferidos na API GitHub, **não** hashes de instaladores individuais.
- **G3 continua PARCIAL:** Windows e instalação completa do .deb ainda não foram executados/documentados; execução de aplicação 3.0 e autenticação reais seguem pendentes. Testes relatados pelo agente não são auditoria independente sem logs.
- Nenhum merge, alteração de infraestrutura ou publicação foram efetuados.

## Atualização de QA independente — 16/10/2026

- No **PR #34** (https://github.com/limazk/EULER-App-Beta/pull/34), a documentação agora inclui execução independente do AppImage oficial em Debian 13/x86_64 usando Xvfb/Openbox, com screenshot real da splash e processo/janela EULER detectados; o .deb teve estrutura validada, 5/5 MD5 internos corretos; o instalador NSIS do Windows teve formato e SHA-256 conferidos.
- ZIPs GitHub Actions e três binários individuais tiveram os SHA-256 calculados e registrados no PR #34.
- A execução Linux com DNS inacessível resultou em tela branca de erro WebKit, em vez de fallback amigável de offline/retry; houve reprodução visual e issue https://github.com/limazk/EULER-App-Beta/issues/36 registrada.
- Os screenshots de 1s e 9s foram salvos na Library privada do solicitante em /EULER/QA/2026-10-16/.
- Faltam instalação nativa .deb, Windows, teste real de reconexão, sessão autenticada, demonstração da interface v3 no shell.
- **G3 continua PARCIAL e não autoriza merge/deploy**; o PR #29, a main e os ambientes Render/Supabase não foram alterados.

## Gates de instalação — atualização após QA nativo (16/10/2026)

- PR de workflows de QA isolados: https://github.com/limazk/EULER-App-Beta/pull/37 (draft).
- Windows Server 2025 NSIS: [run #38996138723](https://github.com/limazk/EULER-App-Beta/actions/runs/38996138723), **success**. SHA-256 verificado; instalação, lançamento do processo ainda ativo aos 10s e desinstalação **aprovados**.
- Ubuntu 22.04 .deb: [run #38996327626](https://github.com/limazk/EULER-App-Beta/actions/runs/38996327626), **success**. Instalação nativa com dependências, execução/Janela EULER 1440×900 via Xvfb, remoção **aprovados**.
- Debian 13 AppImage: evento de fechamento de janela WM_DELETE_WINDOW testado; exit code 0 e desaparecimento da janela. Instalação física via FUSE não testada.
- Relatório consolidado: https://github.com/limazk/EULER-App-Beta/pull/34.
- **G3 segue PARCIAL:** a falha offline [issue #36](https://github.com/limazk/EULER-App-Beta/issues/36), Windows GUI interativa, login real Supabase, interface 3.0 servida em ambiente adequado e teste físico permanecem pendentes. Os testes em runners nativos **não** equivalem à homologação funcional de clientes.
- Sem merge ou deploy da candidata, sem alterações em Render ou Supabase.

## Atualização — screenshot da Beta hospedada em Windows e Linux (16/10/2026)

- [Run Windows #38996524546](https://github.com/limazk/EULER-App-Beta/actions/runs/38996524546): **success**, janela Win32 `EULER` detectada e captura real do formulário de login; NSIS instalou/abriu/desinstalou.
- [Run Linux #38996524551](https://github.com/limazk/EULER-App-Beta/actions/runs/38996524551): **success**, `.deb` instalou, abriu janela Streamlit em Xvfb e desinstalou; captura real do mesmo formulário.
- PNGs preservados na Library privada em `/EULER/QA/2026-10-16/euler-windows-native-login.png` e `euler-linux-deb-native-login.png`; veja documentação PR #34.
- Issue UX #38 registrada: https://github.com/limazk/EULER-App-Beta/issues/38 — botão de login branco sem texto legível em ambos os SOs; verificar na candidata 3.0 antes da liberação.
- Os dados e telas acessados eram a Beta atual do Render (`42e28e8`), **não a EULER 3.0**; testes de autenticação real continuam bloqueados pelo Supabase `INACTIVE`.
- **G3 segue PARCIAL, porém instalação nativa, janela e login visual (sem autenticação) estão comprovados no Windows e Linux.** Sem deploy, merge ou modificação de credenciais.

## QA visual de navegação — Windows, 16/10/2026

- [Run #38996800115](https://github.com/limazk/EULER-App-Beta/actions/runs/38996800115) aprovou instalação/execução/desinstalação NSIS, detecção de janela Win32 e cliques seguros em **Claro** e **Criar conta**, gerando 3 screenshots.
- Tema Claro: **PASS** — UI alternou cores e o botão `Entrar` tornou-se legível.
- Aba Criar conta: **PASS** — campos Nome completo, E-mail e Senha visíveis; nenhum dado submetido.
- Screenshots salvos na Library `/EULER/QA/2026-10-16/euler-windows-light-theme.png` e `euler-windows-signup-tab.png`.
- A [issue #38](https://github.com/limazk/EULER-App-Beta/issues/38) foi refinada para um problema provável de **contraste do botão no tema escuro** na Beta hospedada.
- **G3 permanece PARCIAL**: sem autenticação Supabase autorizada, teste físico de usuário ou UI de produção EULER 3.0; a [issue #36](https://github.com/limazk/EULER-App-Beta/issues/36) de fallback offline continua aberta.
