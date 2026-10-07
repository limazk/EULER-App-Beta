# EULER App Beta — Release Notes

Data: 07/10/2026

Estas notas descrevem o estado técnico atual de `feature/auth-beta` após a integração do PR #19. A promoção para `main` ainda não ocorreu.

## O que está integrado em `feature/auth-beta`

### Autenticação e administração

- autenticação e cadastro via Supabase;
- aprovação manual de contas do beta fechado;
- suspensão/reativação e papéis administrativos;
- organizações e isolamento por organização;
- recuperação de senha e fluxo de conta Beta;
- cache curto do contexto de autenticação.

### Performance

- cache do contexto de autenticação com TTL e invalidação;
- cache da assinatura dos dados e da versão do motor;
- preservação do algoritmo legado de assinatura quando ocorre recálculo.

### Segurança e dependências

- família Supabase alinhada e reproduzível;
- versões sensíveis de dependências fixadas;
- Docker usando `requirements-lock.txt` como constraints;
- `pip check` no build do container;
- smoke tests offline do cliente Supabase;
- chave secreta Supabase mantida somente no servidor.

### Desktop

- shell Tauri 2 para o Beta hospedado;
- splash local imediata;
- janela principal remota oculta durante o carregamento;
- tratamento de cold start, conexão demorada e estado offline;
- retry sem reiniciar o aplicativo;
- navegação remota de topo limitada ao host oficial do Beta;
- ausência de novas permissões nativas expostas ao conteúdo remoto.

### Domínio Adryan

O PR #19 foi **mesclado** e seu conteúdo já faz parte de `feature/auth-beta`.

Inclui:

- fechamento/resumo mensal;
- dia a dia;
- condições;
- atendimento;
- ajustes internos necessários nos módulos de domínio e importação;
- testes e regressões diretamente relacionados.

A interface mensal completa permanece fora do escopo do PR #19.

## Validação final do PR #19

- último head validado: `b5a87378beac14995d2fbfcdbb6be298e8558e00`;
- merge SHA: `9a7c8f1f5847c37b916d7ff87e65da2679726ce3`;
- testes direcionados: **97 passed**;
- suíte completa: **815 passed / 34 skipped**;
- CI: **verde**;
- `ruff check .`: **verde**;
- format: **255 arquivos corretamente formatados**;
- golden: **intacto**;
- tolerâncias: **intactas**;
- asserts removidos: **nenhum**;
- tolerâncias aumentadas: **nenhuma**;
- conflitos: **nenhum**.

Aviso conhecido: apenas mensagens não bloqueantes relacionadas ao Node.js 20 nas GitHub Actions.

## Builds

O PR #18 foi validado com sucesso em:

- Linux: AppImage e pacote `.deb`;
- Windows: instalador NSIS `.exe`.

Os artifacts `euler-linux` e `euler-windows` foram publicados pelo workflow correspondente.

## Limitações conhecidas

- o EULER Desktop continua online-only e depende do serviço web hospedado;
- não existe backend científico offline no shell;
- assinatura de binários e updater nativo ainda não foram implementados;
- `navigator.onLine` detecta conectividade básica, não garante acesso efetivo ao serviço;
- testes manuais com cold start real, DNS/HTTPS e perda real de rede continuam recomendados;
- a validação integrada contra um projeto Supabase real continua sendo uma etapa operacional quando exigida;
- a interface mensal completa do Adryan ficou para etapa posterior.

## Estado de liberação

- PRs #15, #16, #17, #18 e #19: **MERGED em `feature/auth-beta`**.
- PR #20: **documentação final em revisão**.
- PR #3: **DRAFT**.
- `feature/auth-beta`: **integração técnica concluída, aguardando validação final integrada do Codex**.
- `main`: **ainda não promovida**.

Depois do merge do PR #20, a validação final deve ser executada sobre o novo SHA de `feature/auth-beta`. Somente depois disso o PR #3 poderá ser reavaliado para promoção.

