# EULER App Beta — Release Notes

Data: 07/10/2026

Estas notas distinguem o que já está incorporado em `feature/auth-beta` do que ainda depende do PR #19.

## O que já está no Beta

### Autenticação e administração

- autenticação e cadastro via Supabase;
- aprovação manual de contas do beta fechado;
- suspensão/reativação e papéis administrativos;
- organizações e isolamento dos dados por organização;
- recuperação de senha e fluxo de conta Beta;
- cache curto do contexto de autenticação para reduzir chamadas Supabase em reruns comuns.

### Performance

- cache do contexto de autenticação com TTL e invalidação nos fluxos sensíveis;
- cache da assinatura dos dados e da versão do motor;
- preservação do algoritmo legado de assinatura quando ocorre recálculo, evitando invalidar histórico apenas pela otimização.

### Segurança e dependências

- família Supabase alinhada na versão 2.32.0;
- versões sensíveis de `httpx`, `pydantic` e `yarl` fixadas;
- instalação Docker usando `requirements-lock.txt` como constraints;
- `pip check` no build do container;
- smoke tests offline do cliente Supabase sem uso de credenciais reais;
- chave secreta Supabase mantida apenas no servidor.

### Desktop

- shell Tauri 2 para o Beta hospedado;
- splash local imediata;
- janela principal remota oculta até terminar o carregamento;
- tratamento visual de cold start, conexão demorada e estado offline;
- botão de nova tentativa sem reiniciar o aplicativo;
- navegação remota de topo limitada ao host oficial do Beta;
- sem novas permissões nativas expostas ao conteúdo remoto.

### Builds

O PR #18 foi validado com sucesso em:

- Linux: AppImage e pacote `.deb`;
- Windows: instalador NSIS `.exe`.

Os artifacts `euler-linux` e `euler-windows` foram publicados pelo workflow do PR #18.

## Integração do domínio Adryan

O PR #19 prepara a integração de:

- fechamento/resumo mensal;
- dia a dia;
- condições;
- atendimento;
- ajustes internos necessários nos módulos de domínio e importação;
- testes e regressões diretamente relacionados.

**Importante:** no momento deste documento, o PR #19 ainda está aberto e não faz parte da base final. Portanto essas mudanças não devem ser apresentadas como já liberadas no Beta até o merge e a revalidação final.

A interface mensal completa continua fora do escopo do PR #19.

## Melhorias de segurança relevantes

- credenciais privadas não são embutidas no shell desktop;
- o conteúdo remoto não recebe acesso a shell, filesystem, processos, variáveis de ambiente ou comandos IPC customizados;
- o CSP da splash local é restritivo;
- o stack Supabase passou a ter versões reproduzíveis e smoke tests de compatibilidade;
- golden tests e tolerâncias científicas permanecem protegidos pela política do projeto.

## Limitações conhecidas

- o EULER Desktop continua online-only e depende do serviço web hospedado;
- não existe backend científico offline no shell;
- assinatura de binários e updater nativo ainda não foram implementados;
- `navigator.onLine` detecta conectividade básica, não garante acesso efetivo à internet;
- testes manuais com cold start real, DNS/HTTPS e perda real de rede continuam recomendados;
- a validação integrada contra um projeto Supabase real permanece um passo operacional externo;
- a interface mensal completa do Adryan ficou para uma etapa posterior;
- existe uma pequena dívida de lint em `app/auth.py` (`I001`, ordenação de imports);
- o PR #3 ainda está Draft e a promoção para `main` não foi concluída.

## Estado de liberação

PRs #15, #16, #17 e #18 estão mesclados em `feature/auth-beta`.  
PR #19 está pendente.  
PR #3 continua Draft contra `main`.

Estas release notes devem ser revisitadas antes da promoção final para retirar qualquer item que ainda esteja marcado como pendente.
