# EULER App Beta — Final Handoff

Data do snapshot: 07/10/2026  
Branch base: `feature/auth-beta`  
Base observada: `9a7c8f1f5847c37b916d7ff87e65da2679726ce3`

## Estado atual

A integração técnica planejada para esta fase está concluída em `feature/auth-beta`. O domínio do Adryan já faz parte da branch após o merge do PR #19.

Isso **não** significa que o Beta já foi promovido para `main`. O PR #3 continua **Draft** e a validação final integrada será executada pelo Codex após o merge do PR #20.

## PRs da etapa

| PR | Papel | Estado |
|---|---|---|
| #15 | Cache do contexto de autenticação | **MERGED** |
| #16 | Cache compatível da assinatura dos dados | **MERGED** |
| #17 | Dependências Supabase reproduzíveis | **MERGED** |
| #18 | Startup UX do Tauri | **MERGED** |
| #19 | Integração do core Adryan | **MERGED** |
| #20 | Checklist, release notes e handoff final | **EM REVISÃO** |
| #3 | `feature/auth-beta -> main` | **DRAFT** |

## Integração Adryan

O PR #19 foi mesclado em `feature/auth-beta`.

- Merge SHA: `9a7c8f1f5847c37b916d7ff87e65da2679726ce3`.
- Último head validado antes do merge: `b5a87378beac14995d2fbfcdbb6be298e8558e00`.
- Módulos integrados incluem mensal, dia a dia, condições, atendimento e dependências internas necessárias.
- A interface mensal completa continua fora do escopo dessa integração.

### Evidências finais do #19

- testes direcionados: **97 passed**;
- suíte completa: **815 passed / 34 skipped**;
- CI: **verde**;
- `ruff check .`: **verde**;
- format: **255 arquivos corretamente formatados**;
- `tests/golden/**`: **intacto**;
- tolerâncias científicas: **intactas**;
- asserts removidos: **nenhum**;
- tolerâncias aumentadas: **nenhuma**;
- conflitos: **nenhum**.

O único apontamento conhecido dessa validação são avisos não bloqueantes sobre Node.js 20 nas GitHub Actions.

## Arquitetura do Beta

O EULER Beta permanece organizado em camadas:

- **`app/`** — interface Streamlit, autenticação, navegação e administração;
- **`euler/`** — motor científico e módulos de domínio, incluindo o core integrado pelo PR #19;
- **Supabase** — autenticação, identidade, organizações e papéis do Beta;
- **SQLite por organização** — persistência científica local do Beta;
- **`apps/euler-shell/`** — shell Tauri 2 para a aplicação web hospedada;
- **Docker/Render** — empacotamento e execução do serviço;
- **GitHub Actions** — CI e builds desktop.

## Validação local de referência

Preparação:

```bash
git clone https://github.com/limazk/EULER-App-Beta.git
cd EULER-App-Beta
git fetch --all
git checkout feature/auth-beta
git pull

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Suíte e qualidade:

```bash
EULER_TEST_BYPASS_AUTH=1 pytest -q -p no:cacheprovider
ruff check .
ruff format --check .
```

Validação de ambiente Supabase:

```bash
python scripts/beta_check.py --offline
```

Com credenciais reais configuradas em ambiente seguro, a validação operacional externa pode ser executada com:

```bash
python scripts/beta_check.py
```

Nunca use `EULER_TEST_BYPASS_AUTH=1` em servidor público e nunca versione `SUPABASE_SECRET_KEY`.

## Estado de liberação

### `feature/auth-beta`

**Integração técnica concluída, aguardando validação final.**

A branch já contém os PRs #15, #16, #17, #18 e #19.

### `main`

**Ainda não promovida.**

O PR #3 continua Draft. Os checks antigos do #3 não devem ser usados como evidência da versão final integrada.

## Próximo passo obrigatório

Depois do merge do PR #20:

1. obter o novo SHA de `feature/auth-beta`;
2. executar a validação final integrada com o Codex sobre esse SHA;
3. confirmar novamente testes, lint, format, CI, golden e tolerâncias;
4. somente então reavaliar o PR #3 para sair de Draft.

Nenhuma promoção para `main` deve ocorrer antes dessa validação.

