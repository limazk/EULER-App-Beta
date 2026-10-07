# Handoff Codex — EULER Beta até 08/10 20h

Base de trabalho: `feature/auth-beta`.

## Regra principal

Não alterar fórmulas, golden tests nem lógica científica dentro de `euler/` salvo para
corrigir um erro de integração comprovado. O objetivo do Codex é **execução, testes,
deploy e correções de ambiente**, não redesenhar a arquitetura.

## Passo 1 — preparar ambiente local

```bash
git clone https://github.com/limazk/EULER-App-Beta.git
cd EULER-App-Beta
git fetch --all
git checkout feature/auth-beta
git pull
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Rodar:

```bash
ruff check .
ruff format --check .
EULER_TEST_BYPASS_AUTH=1 pytest -q
```

Se algo falhar, corrigir somente a causa real. Não editar `tests/golden/`.

## Passo 2 — Supabase local/real

Depois que o humano criar o projeto Supabase e aplicar
`supabase/migrations/20261007_001_beta_auth.sql`, criar um arquivo local não versionado
com as três variáveis descritas em `docs/beta/SETUP_SUPABASE.md`.

Subir:

```bash
streamlit run app/main.py
```

Validar dois navegadores/sessões independentes:

1. superadmin entra;
2. tester cria conta;
3. tester fica em pending;
4. admin aprova;
5. tester entra;
6. admin cria organização e vincula tester;
7. admin suspende tester;
8. tester perde acesso.

Registrar qualquer traceback exato antes de corrigir.

## Passo 3 — responsividade crítica

Testar largura desktop e mobile nas telas:

- login/cadastro;
- início;
- minha planta;
- análise;
- importar dados;
- administração.

Corrigir apenas overflow, botões inacessíveis, tabelas ilegíveis e navegação quebrada.
Não redesenhar telas inteiras antes do P0 estar verde.

## Passo 4 — deploy beta web

Fazer deploy da branch aprovada em ambiente persistente, com os Secrets definidos no
servidor. Nunca commitar `SUPABASE_SECRET_KEY`.

Verificar por URL pública:

- login;
- cadastro;
- aprovação;
- acesso ao app;
- logout;
- suspensão.

## Passo 5 — somente se P0 estiver verde

Criar branch `codex/desktop-bootstrap` e avaliar empacotamento desktop inicial.
Não iniciar Android/Tauri completo se houver qualquer regressão de autenticação ou do
Streamlit.

## Entrega do Codex

Ao terminar, responder com:

- commit/branch;
- comandos executados;
- testes e quantidade de aprovados/falhos;
- URL de deploy, se houver;
- erros ainda abertos;
- prints ou logs dos fluxos login -> aprovação -> acesso -> suspensão.
