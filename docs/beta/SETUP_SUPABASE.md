# Configurar login do EULER Beta com Supabase

Esta configuração deixa o beta web com cadastro, login, aprovação manual, suspensão,
organizações e papéis de acesso.

## 1. Criar o projeto

Crie um projeto Supabase dedicado ao beta. Em **Auth > Providers > Email**, para o beta
fechado, deixe cadastro por e-mail habilitado. Para reduzir atrito até a validação,
pode deixar **Confirm email desabilitado**: a aprovação manual da EULER continuará
bloqueando qualquer conta nova até um administrador liberar.

## 2. Criar as tabelas

Abra o SQL Editor e execute:

`supabase/migrations/20261007_001_beta_auth.sql`

Cadastre sua própria conta pelo app e depois execute a instrução no fim da migration,
substituindo `SEU_EMAIL_AQUI`. Essa será a primeira conta superadministradora.

## 3. Configurar os segredos do servidor

Nunca coloque a chave secreta no GitHub.

Configure no ambiente que executa o Streamlit:

```text
SUPABASE_URL=https://SEU-PROJETO.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_...
SUPABASE_SECRET_KEY=sb_secret_...
```

Para recuperação de senha, cadastre a URL pública do app nas Redirect URLs do Supabase e configure:

```text
EULER_PASSWORD_RESET_REDIRECT_URL=https://SEU-APP.onrender.com
```

No template **Reset Password**, use o redirecionamento com o token de uso único:

```text
{{ .RedirectTo }}?token_hash={{ .TokenHash }}&type=recovery
```

Essa configuração do template é uma pendência externa; não é feita pelo aplicativo.

Projetos antigos podem mostrar `ANON_KEY` e `SERVICE_ROLE_KEY`; o código aceita os
nomes antigos como fallback.

A chave secreta é usada somente pelo servidor para aprovar/suspender usuários,
criar organizações e vínculos. Ela não deve aparecer em frontend, APK ou navegador.

## 4. Teste mínimo

1. Entre com a conta superadmin.
2. Crie uma segunda conta.
3. Confirme que ela vê "Conta aguardando liberação".
4. No admin, aprove a conta.
5. Crie uma organização.
6. Vincule a segunda conta.
7. Entre novamente com a segunda conta e confirme acesso ao software.
8. Suspenda a conta e confirme que ela deixa de acessar.

## Nota para a migração futura

O Supabase Auth e as tabelas de identidade foram separados do Streamlit para serem
reutilizados depois pelo frontend React/Tauri e pelo APK. O motor `euler/` não foi
alterado por esta etapa.
