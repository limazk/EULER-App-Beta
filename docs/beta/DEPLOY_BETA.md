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
```

**Nunca** configure `EULER_TEST_BYPASS_AUTH=1` no servidor público.

O container escuta a porta `8501` e inicia com:

```bash
streamlit run app/main.py --server.address=0.0.0.0 --server.port=8501
```

## Persistência

A versão beta ainda preserva os bancos científicos em SQLite. Portanto, o diretório
apontado por `EULER_DADOS_DIR` precisa estar em um **volume/disco persistente**.

Sem volume persistente, um redeploy pode apagar os bancos locais. Em Render, por
exemplo, o filesystem padrão é efêmero; use um Persistent Disk e monte-o em
`/var/data`. Um serviço com Persistent Disk fica limitado a uma instância, o que é
aceitável para este beta fechado.

Estrutura no volume:

```text
/var/data/euler/
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
