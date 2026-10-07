# EULER Desktop — Startup UX

## Status

CONCLUÍDO

A implementação e a validação automática estão concluídas dentro do escopo. O CI geral, o build Linux e o build Windows passaram com sucesso. O Linux gerou AppImage e `.deb`, e o Windows gerou o instalador NSIS. O PR está pronto para revisão do coordenador e merge após a revisão.

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
Run: `37674105351`  
Resultado: **SUCCESS**

O lint e a suíte de testes terminaram com sucesso no commit validado.

### Tauri Windows

Workflow: `Tauri Shell`  
Run: `37674105361`  
Job: `Build Windows`  
Resultado: **SUCCESS**

Etapas confirmadas:

- checkout;
- Node;
- Rust;
- geração de ícones;
- build NSIS;
- upload do instalador.

Artifact publicado pelo workflow: `euler-windows`.

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

**Validado com sucesso.**

Workflow: `Tauri Shell`  
Run: `37674105361`  
Job: `Build Linux`  
Resultado: **SUCCESS**

A etapa `Linux dependencies`, que havia travado em uma execução anterior, concluiu normalmente. Node, Rust e Tauri foram executados e os bundles foram gerados com sucesso:

- `EULER_0.1.0-beta.1_amd64.AppImage`;
- `EULER_0.1.0-beta.1_amd64.deb`.

Artifact publicado pelo workflow: `euler-linux`.

## Windows

**Validado com sucesso.**

O NSIS foi compilado e enviado como artifact pelo workflow.

## Pendências

**Nenhuma pendência bloqueante dentro do escopo do Startup UX.**

Testes manuais adicionais com cold start real do Render e perda real de rede continuam recomendados como validação complementar, mas não há falha conhecida de implementação ou de build impedindo revisão/merge.

## Riscos conhecidos

- `navigator.onLine` detecta conectividade básica, não garante acesso à internet.
- Um erro de rede específico do WebView pode variar entre WebView2 e WebKitGTK.
- O evento de page load do Tauri é usado para decidir quando mostrar a janela remota; um teste manual com falha real de DNS/HTTPS continua recomendado.
- Links de navegação de topo para domínios externos são bloqueados intencionalmente na janela remota. Se a EULER futuramente precisar abrir um domínio externo no mesmo WebView, isso deve ser revisado explicitamente em vez de ampliar a regra genericamente.
- O app continua online-only.

## Próximo passo recomendado

Revisão final do coordenador e merge do PR #18 em `feature/auth-beta`. O Chat 3 não deve fazer o merge por conta própria.

## Handoff final

Status final do **EULER Desktop — Startup UX**:

- Repositório: `limazk/EULER-App-Beta`;
- Branch: `tauri/startup-ux`;
- PR: `#18`;
- implementação: concluída;
- CI geral: verde;
- Linux AppImage + `.deb`: verde;
- Windows NSIS: verde;
- artifacts Linux e Windows: publicados;
- pendências bloqueantes: nenhuma;
- ação seguinte: revisão do coordenador e merge.