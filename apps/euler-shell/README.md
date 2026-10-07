# EULER Tauri Shell

Shell instalável do EULER Beta usando Tauri 2.

## Objetivo

Esta fase não reescreve o EULER. O aplicativo carrega a versão web hospedada em:

`https://euler-app-beta.onrender.com`

O motor científico continua no projeto Python e nenhuma credencial secreta é embutida no aplicativo.

## Desenvolvimento

Pré-requisitos: Rust, Node.js e as dependências de sistema do Tauri 2.

```bash
cd apps/euler-shell
npm install
npm run dev
```

## Build desktop

```bash
npm run build
```

Os instaladores são gerados pelo bundler do Tauri para o sistema operacional onde o build é executado.

## Segurança

- Não adicionar `SUPABASE_SECRET_KEY`, service-role ou qualquer credencial privada ao shell.
- O conteúdo remoto não recebe permissões nativas do Tauri nesta primeira versão.
- A URL pública do EULER é a única dependência remota configurada nesta fase.

## Próximos passos

1. Testar o shell no Linux.
2. Adicionar ícones oficiais do EULER.
3. Criar CI para AppImage/deb e Windows setup.
4. Inicializar o target Android e gerar APK beta.
5. Adicionar assinatura e updater somente depois da validação do shell.
