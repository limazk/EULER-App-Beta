# Operação do EULER Beta

## Variáveis de ambiente

| Variável | Uso |
|---|---|
| `SUPABASE_URL` | `https://<ref>.supabase.co` |
| `SUPABASE_PUBLISHABLE_KEY` | chave pública (login/cadastro) |
| `SUPABASE_SECRET_KEY` | chave secreta (só servidor e scripts de admin) |
| `EULER_DADOS_DIR` | pasta gravável dos dados locais |

Os scripts leem **somente** variáveis de ambiente (não leem `.streamlit/secrets.toml`).
Exemplo numa sessão: `export SUPABASE_URL=...` (não grave isso em arquivo versionado).

## 1. Validar ambiente — `beta_check.py`

```bash
python scripts/beta_check.py            # variáveis + tabelas Supabase (somente leitura)
python scripts/beta_check.py --offline  # só variáveis
```

Mostra `OK`/`AUSENTE` por variável, nunca os valores. Sem `SUPABASE_SECRET_KEY`, o
teste administrativo é ignorado. Saída 0 = OK, 1 = falha.

## 2. Smoke test do Render — `smoke_beta.py`

```bash
python scripts/smoke_beta.py                     # https://euler-app-beta.onrender.com
python scripts/smoke_beta.py https://outra-url   # outro alvo
```

Verifica HTTP, 5xx, tempo, Streamlit e `/_stcore/health`. A primeira chamada pode
demorar ~1 min se o serviço estiver dormindo.

## 3. Promover o primeiro superadmin — `bootstrap_superadmin.py`

1. A pessoa se cadastra no app (isso cria o perfil `pending`).
2. Com `SUPABASE_URL` e `SUPABASE_SECRET_KEY` exportadas:

```bash
python scripts/bootstrap_superadmin.py email@exemplo.com
```

O script mostra e-mail, status e `is_superadmin` atuais e pede para **digitar o e-mail
de novo**. Só então grava `status=active`, `is_superadmin=true`, `approved_at=agora`
nesse único perfil. Nunca cria usuário nem altera outros perfis.

## ⚠️ Segredos

- **Nunca** commite `.env`, `.streamlit/secrets.toml`, `SUPABASE_SECRET_KEY`,
  chaves `service_role`, senhas, tokens ou credenciais do Render.
- Os nomes das variáveis podem aparecer em código/docs; os **valores**, nunca.
- Antes de commitar: `git grep -n "SUPABASE_SECRET_KEY"` e `git grep -n "service_role"`
  devem mostrar só nomes, nunca chaves.
