# EULER Tauri Shell

Shell instalável do EULER Beta usando Tauri 2.

## Objetivo

Esta fase não reescreve o EULER. O aplicativo continua carregando a versão web hospedada em:

`https://euler-app-beta.onrender.com`

O motor científico permanece no projeto Python e nenhuma credencial secreta é embutida no aplicativo.

## Startup UX

O shell usa duas janelas:

1. **`splash` local** — abre imediatamente a partir de `dist/index.html`, sem dados industriais e sem acesso a rede pela página local.
2. **`main` remota** — inicia oculta e carrega o EULER hospedado. Só aparece quando o carregamento remoto termina.

Enquanto a janela remota carrega, a tela local mostra:

- `Conectando à EULER...`;
- aviso de possível cold start depois de 12 segundos;
- estado de conexão demorada depois de 45 segundos;
- estado offline usando `navigator.onLine`;
- botão **Tentar novamente** sem precisar fechar o aplicativo.

O botão de retry navega a splash para `https://retry.euler.local/`. Essa navegação é interceptada pelo backend Tauri e cancelada; o shell apenas manda a janela remota tentar carregar novamente.

## Desenvolvimento

Pré-requisitos: Rust, Node.js e as dependências de sistema do Tauri 2.

```bash
cd apps/euler-shell
npm install
npm run dev
```

A splash local é empacotada em `apps/euler-shell/dist/`.

## Build desktop

```bash
npm run build
```

Os instaladores são gerados pelo bundler do Tauri para o sistema operacional onde o build é executado.

O workflow `Tauri Shell` valida:

- Linux: AppImage e `.deb`;
- Windows: NSIS `.exe`.

## Segurança

- Não adicionar `SUPABASE_SECRET_KEY`, service-role ou qualquer credencial privada ao shell.
- `app.security.capabilities` permanece vazio.
- Nenhuma API nativa é exposta ao conteúdo remoto.
- A página local não usa IPC do Tauri.
- A janela remota só permite navegação de topo para `https://euler-app-beta.onrender.com`.
- O retry é tratado no backend como navegação especial da janela local; não é um comando exposto ao site remoto.
- O conteúdo remoto não recebe acesso a shell, filesystem, processos ou variáveis de ambiente.
- O CSP da página local bloqueia conexões, frames, objetos, formulários e scripts fora do próprio bundle.

## Limites atuais

- O EULER Desktop continua exigindo internet.
- Não há backend científico offline.
- A detecção `navigator.onLine` distingue ausência evidente de conexão, mas não substitui diagnóstico completo de rede.
- O cold start depende do tempo de resposta do serviço hospedado.
- Assinatura de binários e updater continuam fora deste escopo.
