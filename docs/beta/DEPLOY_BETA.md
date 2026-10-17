# Deploy do EULER Beta

Objetivo: publicar rapidamente o beta Streamlit mantendo autenticação no Supabase e
persistência das plantas por organização.

## Requisitos obrigatórios do servidor

Configure as variáveis:

```text
SUPABASE_URL=...
SUPABASE_PUBLISHABLE_KEY=...
SUPABASE_SECRET_KEY=...
EULER_DADOS_DIR=/var/data/euler
EULER_REQUIRE_PERSISTENT_STORAGE=1
```

**Nunca** configure `EULER_TEST_BYPASS_AUTH=1` no servidor público.

O container usa a variável `PORT` fornecida pelo Render (com `8501` apenas como
fallback para execução local) e inicia com o equivalente a:

```bash
streamlit run app/main.py --server.address 0.0.0.0 --server.port $PORT --server.headless true
```

## Persistência

A versão beta ainda preserva os bancos científicos em SQLite. Portanto, o diretório
apontado por `EULER_DADOS_DIR` precisa ser o **ponto de montagem existente** de um
volume/disco persistente. O runtime recusa o fallback local no Render e também recusa
caminho relativo, inexistente, sem escrita ou link simbólico quando
`EULER_REQUIRE_PERSISTENT_STORAGE=1`.

Sem volume persistente, um redeploy pode apagar os bancos locais. Em Render, por
exemplo, o filesystem padrão é efêmero; use um Persistent Disk e monte-o exatamente em
`/var/data/euler`. Um serviço com Persistent Disk fica limitado a uma instância, o que é
aceitável para este beta fechado.

Essa validação confirma somente o contrato visto pelo processo. Antes do deploy, confira
no painel do provedor que `/var/data/euler` é realmente um Persistent Disk; uma pasta
comum com o mesmo nome não oferece durabilidade.

Estrutura no volume:

```text
/var/data/euler/  # mount do Persistent Disk
└── tenants/
    ├── <organization-id-A>/
    └── <organization-id-B>/
```

## Teste de fumaça depois do deploy

1. abrir a URL em janela anônima;
2. criar uma conta tester;
3. confirmar que a conta fica bloqueada;
4. entrar como superadmin e aprovar;
5. criar/vincular organização;
6. entrar como tester;
7. criar ou abrir uma planta;
8. sair e entrar novamente;
9. confirmar que a planta permanece;
10. suspender o tester e confirmar bloqueio.

## Atualizações durante o beta web

O beta web não exige que o usuário baixe um novo instalador. Depois de um deploy da nova
versão, todos recebem o código novo ao abrir/recarregar a aplicação. O updater nativo
fica para a etapa Tauri/desktop/APK.
