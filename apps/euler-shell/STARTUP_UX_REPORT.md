# EULER Desktop — Startup UX

## Status

PARCIALMENTE CONCLUÍDO

A implementação está concluída dentro do escopo. A validação automática passou no CI geral e no build Windows. O build Linux não chegou à compilação do projeto porque o runner do GitHub Actions permaneceu preso na etapa **Linux dependencies** (`apt-get`), antes de Node, Rust e Tauri serem executados.

## Branch

`tauri/startup-ux`

## Base utilizada

`feature/auth-beta` em `32382560a1f58d069deeea02bfe6947dc06e64bc`.

## O que foi implementado

- Splash local que aparece imediatamente ao abrir o EULER.
- Janela principal remota inicia oculta e carrega `https://euler-app-beta.onrender.com`.
- A janela principal só é exibida quando o carregamento remoto termina.
- Estado inicial **Conectando à EULER...**.
- Aviso de cold start após 12 segundos.
- Estado de conexão demorada após 45 segundos.
- Detecção básica de offline com `navigator.onLine` e eventos `online/offline`.
- Botão **Tentar novamente** sem fechar o aplicativo.
- Retry tratado no backend Tauri por interceptação de navegação, sem expor comandos nativos ao site remoto.
- Navegação de topo da janela remota limitada ao host oficial do beta.
- Fechamento coordenado das duas janelas para evitar processo invisível sobrando.
- CSP restritivo para a splash local.
- Documentação do novo fluxo no README.

## Arquivos alterados

- `apps/euler-shell/dist/index.html`
- `apps/euler-shell/dist/startup.css`
- `apps/euler-shell/dist/startup.js`
- `apps/euler-shell/src-tauri/tauri.conf.json`
- `apps/euler-shell/src-tauri/src/lib.rs`
- `apps/euler-shell/README.md`
- `apps/euler-shell/STARTUP_UX_REPORT.md`

Nenhum arquivo de `app/**`, `euler/**`, Supabase, Render ou release foi alterado.

## Segurança

**Nenhuma nova permissão nativa adicionada.**

`app.security.capabilities` continua vazio.

O conteúdo remoto não recebe:

- shell;
- filesystem;
- execução de comandos;
- processos;
- variáveis de ambiente;
- secrets;
- service role;
- `SUPABASE_SECRET_KEY`;
- comandos IPC customizados.

A splash também não usa IPC. O botão de retry aponta para um endereço sentinela (`https://retry.euler.local/`), cuja navegação é interceptada e cancelada pelo backend do shell. O backend apenas manda a janela `main` navegar novamente para a URL oficial.

A janela remota aceita navegação de topo somente em HTTPS para `euler-app-beta.onrender.com`.

A página local usa CSP com conexões, frames, objetos e formulários bloqueados.

## Testes realizados

### CI geral

Workflow: `CI`  
Run: `37672411896`  
Resultado: **SUCCESS**

O lint passou antes da suíte de testes e o job completo terminou com sucesso.

### Tauri Windows

Workflow: `Tauri Shell`  
Job: `Build Windows`  
Resultado: **SUCCESS**

Etapas confirmadas:

- checkout;
- Node;
- Rust;
- npm install;
- geração de ícones;
- build NSIS;
- upload do instalador.

Uma execução anterior do mesmo código funcional também concluiu Windows com sucesso.

### Fluxos cobertos pela implementação

- conexão normal;
- servidor demorando;
- ausência evidente de internet;
- conexão restaurada;
- retry manual;
- janela remota oculta durante inicialização;
- ausência de permissões nativas novas.

Os cenários de rede são tratados pela splash. Não há teste automatizado end-to-end simulando uma queda real de rede no WebView nesta etapa.

## Linux

**Validação pendente por infraestrutura do runner.**

Workflow: `Tauri Shell`  
Job: `Build Linux`

O runner permaneceu em:

`Linux dependencies`

antes de chegar a:

- Setup Node;
- Setup Rust;
- npm install;
- Tauri build.

Portanto, não há evidência de erro Linux no código nesta execução; a compilação Linux simplesmente não foi alcançada.

O build Linux deve ser reexecutado quando o runner/apt estiver saudável.

## Windows

**Validado com sucesso.**

O NSIS foi compilado e enviado como artifact pelo workflow.

## Pendências

1. Reexecutar o job Linux até ele ultrapassar a instalação de dependências e validar AppImage + `.deb`.
2. Fazer teste manual em desktop com Render realmente em cold start.
3. Fazer teste manual sem internet para verificar a mensagem do WebView em cada plataforma.

Não há pendência conhecida de implementação dentro do escopo do startup UX.

## Riscos conhecidos

- `navigator.onLine` detecta conectividade básica, não garante acesso à internet.
- Um erro de rede específico do WebView pode variar entre WebView2 e WebKitGTK.
- O evento de page load do Tauri é usado para decidir quando mostrar a janela remota; um teste manual com falha real de DNS/HTTPS continua recomendado.
- Links de navegação de topo para domínios externos são bloqueados intencionalmente na janela remota. Se a EULER futuramente precisar abrir um domínio externo no mesmo WebView, isso deve ser revisado explicitamente em vez de ampliar a regra genericamente.
- O app continua online-only.

## Próximo passo recomendado

Reexecutar somente a validação Linux. Se AppImage e `.deb` forem gerados, marcar este trabalho como concluído e liberar o PR para revisão do coordenador.

## Prompt de continuação

Continue a tarefa **EULER Desktop — Startup UX**.

- Repositório: `limazk/EULER-App-Beta`
- Branch existente: `tauri/startup-ux`
- Último commit funcional antes deste relatório: `907a4fab917190a70665b0337663f2ec208404fe`
- PR: `#18`
- Implementação já concluída: splash local, cold-start UX, offline, retry, janela remota oculta, navegação restrita e segurança sem novas permissões.
- CI geral: sucesso.
- Windows NSIS: sucesso.
- Única validação pendente: Linux.
- O workflow Linux ficou preso em `Linux dependencies` antes de compilar.

Próximo passo:

1. verifique o estado mais recente do PR #18;
2. reexecute o job/workflow Linux quando possível;
3. confirme AppImage e `.deb`;
4. se Linux passar, atualize este relatório de PARCIALMENTE CONCLUÍDO para CONCLUÍDO;
5. não faça merge.
