# Dependências de produção e Supabase

Data: 07/10/2026

## Objetivo

Evitar que o deploy monte combinações diferentes das bibliotecas usadas nos testes,
especialmente no cliente Supabase. Uma incompatibilidade entre o pacote principal e seus
subpacotes já causou erro em tempo de execução no caminho administrativo.

## Estratégia

- `requirements.txt` fixa as dependências diretas usadas pelo runtime.
- O stack Supabase usa a release `2.32.0` de forma explícita:
  `supabase`, `postgrest`, `realtime`, `storage3`, `supabase-auth` e
  `supabase-functions`.
- `httpx`, `pydantic` e `yarl` ficam fixados nas versões testadas porque fazem parte
  do caminho de construção e transporte do SDK.
- `requirements-lock.txt` é aplicado como arquivo de *constraints* no Docker.
- O Docker executa `pip check` depois da instalação e falha antes de iniciar o app caso
  exista conflito declarado entre pacotes.
- `tests/test_supabase_runtime.py` verifica as versões instaladas e cria clientes
  Supabase com URL/chaves fictícias, sem acessar a rede.

## Fonte da compatibilidade

A própria release `supabase==2.32.0` declara como dependências exatas os cinco
subpacotes Supabase na mesma versão `2.32.0`. A integração mantém essa família alinhada
em vez de misturar releases.

## Atualização futura

Uma atualização do Supabase deve ser tratada como mudança única:

1. atualizar a família Supabase em conjunto;
2. revisar changelog e documentação atuais;
3. atualizar constraints;
4. executar os smoke tests;
5. executar a suíte completa;
6. testar o build Docker;
7. somente então liberar o deploy.

Não atualizar apenas um subpacote isoladamente.

## Segurança

- Nenhuma chave real é usada nos smoke tests.
- `SUPABASE_SECRET_KEY` continua exclusivamente no servidor.
- Este trabalho não altera RLS, schema, migrations ou dados do projeto Supabase.
