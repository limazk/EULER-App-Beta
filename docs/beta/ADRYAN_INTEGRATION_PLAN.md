# Plano de integração — versão Adryan → EULER App Beta

Data: 07/10/2026

## Referências auditadas

- Origem: `rodriguesadryan06-a11y/softwer-euler`
- Branch principal atual da origem: `claude/new-session-xytynj`
- Commit auditado da origem: `0c90f68f4a0e582083b362d42524bd78d3f89a0b`
- Destino: `limazk/EULER-App-Beta`
- Branch base do destino: `feature/auth-beta`
- Commit base auditado do destino: `e731267a9a2059871f1cbd97a05fa4478dd44bac`

## Regras de integração

1. Não substituir autenticação, Supabase, administração, tenant isolation, Tauri, Render ou workflows do Beta.
2. Não editar `tests/golden/` nem tolerâncias científicas.
3. Ausente continua ausente; nunca preencher com zero.
4. Não introduzir comandos operacionais para a caldeira.
5. Uma tarefa = uma branch = um PR.
6. Conflito científico ou de segurança deve ser documentado antes de qualquer escolha.
7. A interface nova só entra quando as dependências de domínio que ela usa estiverem presentes e testadas.

## Resultado da comparação de árvores

- Arquivos na origem Adryan: 340
- Arquivos no Beta: 329
- Iguais: 257
- Mesmo caminho, conteúdo diferente: 44
- Apenas na origem Adryan: 39
- Apenas no Beta: 28

## Arquivos exclusivos do Beta que devem ser preservados

Estes arquivos fazem parte da infraestrutura do Beta e não devem ser substituídos pela versão do Adryan:

- `app/auth.py`
- `app/paginas/admin.py`
- `app/paginas/conta_beta.py`
- `Dockerfile`
- `.dockerignore`
- `.github/workflows/tauri-shell.yml`
- `.github/workflows/publish-release.yml`
- `apps/euler-shell/**`
- `supabase/migrations/20261007_001_beta_auth.sql`
- `scripts/beta_check.py`
- `scripts/bootstrap_superadmin.py`
- `scripts/smoke_beta.py`
- `docs/beta/**`
- `tests/test_auth_beta.py`
- `tests/test_scripts_beta.py`
- `app/imagens/euler_app_icone.svg`

## Novos módulos da versão do Adryan

### Interface/produto

- `app/blocos/painel_principal.py`
- `app/blocos/rotina_mensal.py`
- `app/visao_mensal.py`
- `app/vocabulario_fabrica.py`

### Domínio

- `euler/atendimento.py`
- `euler/condicoes.py`
- `euler/dia_a_dia.py`
- `euler/mensal.py`

### Testes novos relevantes

- `tests/test_atendimento.py`
- `tests/test_condicoes.py`
- `tests/test_dia_a_dia.py`
- `tests/test_escala_atendimento.py`
- `tests/test_mensal.py`
- `tests/test_planilha_real.py`
- `tests/test_preco_e_ponte.py`
- `tests/test_previa_fechamento.py`
- `tests/test_revisao_inconsistencias.py`
- `tests/test_visao_mensal.py`

## Arquivos conflitantes de alto risco

Estes arquivos existem nos dois projetos e mudaram dos dois lados. Não devem ser substituídos por cópia direta:

### Infraestrutura/interface Beta

- `app/main.py`
- `app/navegacao.py`
- `app/armazenamento.py`
- `app/componentes.py`
- `app/paginas/investigacao.py`
- `requirements.txt`
- `requirements-lock.txt`
- `pyproject.toml`
- `.github/workflows/ci.yml`

Motivo: o Beta adicionou autenticação, isolamento por organização, loading profissional, dependências Supabase, deploy e integração Tauri.

### Interface nova do Adryan

- `app/paginas/painel.py`
- `app/paginas/fechamentos.py`
- `app/paginas/acompanhamento.py`
- `app/paginas/importar.py`
- `app/importacao_guiada.py`
- `app/blocos/financeiro_planta.py`

Motivo: a origem implementa a nova rotina mensal, dia a dia, cinco respostas, prévia, histórico e importação orientada a planilhas reais. Devem ser portados por adaptação, preservando autenticação e tenant isolation.

### Motor/domínio alterado na origem

- `euler/acompanhamento.py`
- `euler/armazem.py`
- `euler/conta.py`
- `euler/entrega.py`
- `euler/fechamento.py`
- `euler/io/leitura.py`
- `euler/linha_do_tempo.py`
- `euler/painel.py`
- `euler/percurso.py`

Motivo: a nova UI depende dessas mudanças. A integração deve ser feita com testes antes da interface final.

## Dependência real da nova interface

A nova experiência do Adryan não é apenas uma troca visual. O painel usa:

- fechamento mensal;
- resumo mensal;
- prévia de fechamento;
- condições comparadas;
- dia a dia;
- histórico vigente;
- autoria e revisões;
- preços variáveis;
- importação guiada ampliada.

Portanto, copiar apenas `app/paginas/painel.py` deixaria imports ausentes ou comportamento inconsistente.

## Divisão de trabalho recomendada

### Bloco A — mudanças simples/baixo risco

Podem ser executadas separadamente no Beta:

1. Cache curto do contexto de autenticação.
2. Cache da assinatura dos dados e da versão do motor.
3. Lock consistente das dependências Supabase.
4. Smoke tests do cliente Supabase.
5. Ajustes de loading/retry/offline que não alterem física.
6. Preparação da interface para receber o novo painel, sem remover telas atuais.

### Bloco B — integração profunda para Codex

Deve ser feita depois, com suíte completa:

1. Portar `euler/mensal.py`, `euler/dia_a_dia.py`, `euler/condicoes.py` e `euler/atendimento.py`.
2. Reconciliar alterações em `euler/fechamento.py`, `euler/conta.py`, `euler/armazem.py`, `euler/painel.py` e importadores.
3. Rodar todos os testes novos da origem.
4. Preservar golden/tolerâncias.
5. Só então portar a interface mensal completa.

## Ordem segura de execução

1. Performance de autenticação.
2. Performance de assinatura/cache.
3. Dependências reproduzíveis e smoke tests.
4. Integração do motor mensal pelo Codex.
5. Integração da nova interface.
6. Otimização de reruns do Streamlit.
7. Hardening de autorização e uploads.
8. Persistência durável.
9. Benchmark final.
10. Nova Release.

## Critério para liberar a nova interface

A nova interface só deve substituir o painel atual quando:

- todos os imports da origem existirem no Beta;
- os testes do módulo mensal passarem;
- isolamento por organização continuar funcionando;
- conta suspensa continuar bloqueada;
- superadmin continuar isolado;
- nenhuma chave secreta for exposta;
- a suíte existente continuar verde;
- testes novos do Adryan passarem sem alterar golden ou tolerâncias.

## Conclusão

A integração é viável, mas deve ser feita por reconciliação, não por substituição em massa. O Beta tem infraestrutura de autenticação/distribuição que a origem não possui, enquanto a origem possui a evolução mais recente do produto e do fluxo mensal. O caminho seguro é preservar a infraestrutura do Beta e portar o domínio/UX novo de forma incremental.
