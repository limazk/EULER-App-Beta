# EULER App Beta — Final Handoff

Data do snapshot: 07/10/2026  
Branch base: `feature/auth-beta`  
Commit observado: `7c6e8ac6ba523a0ae07e23dafccd9c3e3f168122`

## Arquitetura do Beta

O EULER Beta permanece organizado em camadas:

- **`app/`** — interface Streamlit, autenticação, navegação, administração e integração da experiência de usuário;
- **`euler/`** — motor científico e módulos de domínio;
- **Supabase** — autenticação, identidade, organizações e papéis do Beta; a chave secreta permanece somente no servidor;
- **SQLite por organização** — persistência científica local no Beta, usando diretório persistente configurado por `EULER_DADOS_DIR`;
- **`apps/euler-shell/`** — shell Tauri 2 que carrega a aplicação web hospedada sem expor permissões nativas ao conteúdo remoto;
- **Docker/Render** — empacotamento e execução do serviço Streamlit;
- **GitHub Actions** — CI e builds desktop Linux/Windows.

O shell desktop não reimplementa o motor. Ele continua sendo um cliente do Beta web hospedado.

## PRs que formaram esta etapa

| PR | Papel | Estado no snapshot |
|---|---|---|
| #15 | Cache do contexto de autenticação | Mesclado |
| #16 | Cache compatível da assinatura dos dados | Mesclado |
| #17 | Dependências Supabase reproduzíveis | Mesclado |
| #18 | Startup UX do Tauri | Mesclado |
| #19 | Integração do core Adryan | Aberto; ainda não integrado |
| #3 | Integração geral do Beta em `main` | Draft |

## Integração Adryan

O PR #19 integra os módulos de domínio mensal, dia a dia, condições e atendimento, além das dependências internas e testes diretamente relacionados.

No estado deste documento:

- o PR #19 está aberto e mergeável;
- os testes locais reportados no PR passaram (`799 passed, 34 skipped`);
- o CI do PR passou na base anterior;
- `tests/golden/**` e tolerâncias foram declarados intactos;
- a interface mensal completa ficou fora do escopo;
- o PR ainda precisa ser atualizado/revalidado sobre a base que já contém o #18 antes do merge final.

Não considerar a integração Adryan como parte do Beta publicado antes desse fechamento.

## Como validar localmente

### 1. Preparar o ambiente Python

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

No Windows, ative o ambiente virtual com o caminho equivalente em `.venv\\Scripts`.

### 2. Rodar testes

Para a suíte usada durante a integração Beta:

```bash
EULER_TEST_BYPASS_AUTH=1 pytest -q -p no:cacheprovider
```

Também é possível executar:

```bash
pytest -q
ruff format --check .
```

### 3. Lint

O comando oficial do projeto é:

```bash
ruff check .
```

Há uma dívida técnica conhecida: no estado auditado, esse comando encontra `I001` de ordenação de imports em `app/auth.py`. Não mascarar a falha nem alterar golden/tolerâncias para obter verde; corrigir `app/auth.py` somente em tarefa autorizada.

### 4. Validar Supabase

Sem acesso à rede, valide o ambiente/configuração:

```bash
python scripts/beta_check.py --offline
```

Com as variáveis reais configuradas em ambiente seguro:

```bash
python scripts/beta_check.py
```

Nunca use `EULER_TEST_BYPASS_AUTH=1` em servidor público e nunca versione `SUPABASE_SECRET_KEY`.

### 5. Rodar o app web

```bash
streamlit run app/main.py
```

O fluxo operacional de validação deve cobrir, quando houver Supabase real disponível:

1. cadastro de tester;
2. conta pendente;
3. aprovação por superadmin;
4. vínculo a organização;
5. acesso ao software;
6. persistência da planta;
7. suspensão e bloqueio do usuário.

## Como gerar e verificar builds

### Docker / web

Gerar a imagem:

```bash
docker build -t euler-beta .
```

O deploy deve fornecer `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, `SUPABASE_SECRET_KEY` e `EULER_DADOS_DIR` em ambiente seguro.

### Tauri local

Pré-requisitos: Node.js, Rust e dependências de sistema do Tauri 2.

```bash
cd apps/euler-shell
npm install
npm run build
```

O bundler gera os instaladores do sistema operacional em que o build é executado.

### GitHub Actions

O workflow **Tauri Shell** valida:

- Linux: AppImage + `.deb`;
- Windows: NSIS `.exe`.

No PR #18, ambos passaram e publicaram os artifacts `euler-linux` e `euler-windows`.

Após o merge do #18, uma nova execução de CI/Tauri da base `feature/auth-beta` estava em andamento no momento deste snapshot. Verificar que essa execução e a execução posterior ao merge do #19 terminem verdes antes da promoção final.

## Auditoria de coerência documental

Foram encontradas as seguintes diferenças entre documentação histórica e o estado atual:

1. **`apps/euler-shell/STARTUP_UX_REPORT.md`** ainda diz que o próximo passo é revisar/mesclar o PR #18. Esse passo já ocorreu; o PR #18 está mesclado.
2. **`docs/beta/CODEX_HANDOFF.md`** representa uma etapa anterior e instrui o Codex a não alterar `euler/`; isso não descreve o escopo atual do PR #19, que é justamente uma integração controlada do domínio. Tratar esse arquivo como handoff histórico, não como instrução atual.
3. **`docs/beta/ADRYAN_INTEGRATION_PLAN.md`** usa commits-base antigos e descreve uma sequência planejada. A estratégia continua útil, mas o estado de execução deve ser lido pelos PRs #15–#19.
4. **`docs/beta/CHANGELOG.md`** ainda resume apenas a fundação inicial do Beta e não inclui as melhorias dos PRs #15–#18 nem o estado pendente do #19.
5. **`README.md`** contém uma seção de deploy via Streamlit Community Cloud apontando para o repositório/branch de origem do Adryan, o que não representa a branch Beta atual. Não foi alterado nesta tarefa porque o escopo autorizado é somente documentação final em `docs/beta/`.

Nenhuma dessas inconsistências foi corrigida fora dos três arquivos autorizados nesta tarefa.

## Itens para versões ou tarefas futuras

- concluir, atualizar e mesclar o PR #19;
- portar a interface mensal completa somente depois da integração segura do domínio;
- corrigir a ordenação de imports em `app/auth.py` em tarefa isolada;
- concluir/registrar teste integrado com Supabase real antes da liberação que exigir essa garantia;
- assinatura de binários;
- updater nativo;
- backend científico offline para desktop, se virar requisito de produto;
- validação manual adicional de cold start, perda real de rede e diferenças entre WebView2/WebKitGTK;
- rever a estratégia de persistência quando o Beta precisar escalar além do modelo atual de uma instância com disco persistente.

## Condição de saída

Antes de promover `feature/auth-beta` para `main`:

- PR #19 integrado e revalidado;
- CI final verde;
- builds Linux/Windows finais verdes;
- golden/tolerâncias sem mudança;
- dívida de lint tratada ou explicitamente aceita;
- PR #3 revisado e retirado de Draft somente quando o estado integrado estiver pronto.
