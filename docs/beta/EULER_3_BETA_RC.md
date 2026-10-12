# EULER 3.0 — candidato à Beta

Branch: `integration/v3-beta-release-candidate`  
Base: `42e28e8d8ee8db99430226e4a298f4b3e6e2fdd2`  
PR: [#29](https://github.com/limazk/EULER-App-Beta/pull/29) (draft)

## Conteúdo do candidato

- PR #22: fechamentos financeiros vigentes e origem legada auditável.
- PR #26: fundação visual e interface v3, incorporando #23 e #24 uma única vez.
- PR #28: ML-01, ML-02 e ML-03 experimentais, offline e desativados.
- Issue #27: seleção autorizada de organização, planta, equipamento e período; leitura
  dos registros persistidos; histórico de importações; fechamento vigente; estados vazios;
  origem e unidades explícitas.

O dashboard reutiliza `armazenamento.repositorio()`, `Armazem`, `fechamentos_vigentes` e
os controles de autenticação existentes. Não há uma segunda camada de persistência.

## Segurança e limites

- `EULER_ML_ENABLED` continua desligado; a interface não executa inferência.
- IA generativa permanece desligada.
- A troca de organização invalida dados e seletores da sessão anterior.
- A organização escolhida precisa existir nas associações ativas do usuário.
- Planta e equipamento são validados dentro do repositório do tenant selecionado.
- Recebimento e consumo de combustível permanecem campos separados.
- `Custo esperado` continua indisponível; a referência histórica não vira expectativa.
- Nenhuma fórmula, tolerância, golden test, RLS ou migração foi alterada.

Este candidato não representa homologação industrial. Os testes não validam dados reais,
instrumentação física, segurança operacional ou desempenho estatístico em produção.

## Instalação e teste

Ambiente de referência: Python 3.11.

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev,validacao]"
ruff check .
ruff format --check .
EULER_TEST_BYPASS_AUTH=1 pytest -q
```

Para inspeção local da interface:

```bash
EULER_TEST_BYPASS_AUTH=1 streamlit run app/main.py
```

O bypass é exclusivo da suíte e da inspeção local; não deve ser usado em implantação.
A configuração real de Supabase está descrita em `docs/beta/SETUP_SUPABASE.md`.

## Evidências visuais

As capturas foram produzidas com Chromium, dados sintéticos e autenticação de teste.

- [Desktop persistido 1440×1000](evidencias/dashboard-persistido-desktop-1440x1000.png)
- [Desktop com sidebar recolhida 1440×1000](evidencias/dashboard-persistido-desktop-sidebar-recolhida-1440x1000.png)
- [Mobile com menu aberto 390×844](evidencias/dashboard-persistido-mobile-menu-aberto-390x844.png)
- [Mobile com menu recolhido 390×844](evidencias/dashboard-persistido-mobile-390x844.png)
- [Dashboard vazio](evidencias/dashboard-vazio-desktop-1440x1000.png)
- [Demonstração sintética identificada](evidencias/dashboard-demonstracao-sintetica-desktop-1440x1000.png)

A validação automatizada confirmou viewport sem rolagem horizontal no mobile e nenhum erro
JavaScript capturado. A execução manual do workflow Tauri Shell gerou e publicou artefatos
de CI para Linux (AppImage/deb) e Windows (NSIS). Isso comprova o build, não a execução dos
instaladores em máquinas físicas.

## Rollback

O PR permanece draft e não altera `main`. Para descartar o candidato, feche o PR #29 e
remova somente a branch de integração. Os PRs e branches de origem permanecem intactos.

## Pendências para aceite humano

- Revisar visualmente as capturas e os textos financeiros.
- Validar login, expiração de sessão e tenant real em um ambiente Supabase autorizado.
- Revisar estatisticamente os modelos experimentais com dados independentes autorizados.
- Executar os instaladores Linux/Windows em máquinas de teste antes de distribuição.
- Autorizar explicitamente qualquer merge ou retirada do estado draft.
