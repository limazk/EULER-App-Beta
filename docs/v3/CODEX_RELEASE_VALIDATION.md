# Homologação técnica — EULER 3.0 Beta

Data da execução: 16/10/2026. Responsável: Codex. Escopo: autenticação,
autorização, isolamento de tenant, persistência, backup, restauração e
recuperação operacional. Este documento não aprova deploy nem substitui a auditoria
do PR #33 ou os testes físicos de instaladores.

## Identidade da candidata

- Repositório: `limazk/EULER-App-Beta`.
- Base de trabalho: `integration/v3-beta-release-candidate`.
- SHA recebido e confirmado após `git fetch origin --prune`:
  `8d89de9395f9a0fcfdc829e3b88280202982ec28`.
- `origin/main` observado no preflight:
  `42e28e8d8ee8db99430226e4a298f4b3e6e2fdd2`.
- Branch de homologação: `hardening/v3-release-validation-codex`.
- O checkout estava limpo antes da criação da branch. A candidata, `main` e o PR
  draft #29 não foram modificados diretamente.

## Resultado executivo

A validação offline confirma comportamento fail-closed para perda de sessão ou de
contexto de autorização, limpeza do contexto operacional em troca de identidade ou
empresa, isolamento dos bancos SQLite por tenant e backup/restauração local sem
sobrescrever a planta de origem. Foi corrigido um escape de diretório por link simbólico
no caminho do tenant.

A Beta **não está aprovada para persistência em nuvem no Render gratuito**. O estado
persistente é gravado em SQLite local; sem disco persistente, reinício, spin-down ou
redeploy removem esses arquivos. A documentação oficial do Render confirma que o
filesystem do serviço gratuito é efêmero e que esse plano não aceita persistent disk:

- <https://render.com/docs/free#local-files-lost-on-redeploy>
- <https://render.com/docs/disks>

O Supabase EULER foi informado como `INACTIVE` em 16/10/2026 e este ambiente não
possui configuração nem contas autorizadas. Por isso, cadastro, login, renovação,
expiração e revogação reais permanecem **BLOQUEADOS**. Os resultados abaixo são
offline e não devem ser apresentados como evidência do serviço real.

## Armazenamento encontrado

`euler.persistencia.raiz_padrao()` resolve a raiz nesta ordem:

1. `EULER_DADOS_DIR`;
2. `EULER_DADOS`;
3. `~/EULER-dados`, salvo reconhecimento de instalação legada.

Na aplicação autenticada, `app/armazenamento.py` acrescenta
`tenants/<organization_id>`. Cada planta é um SQLite em
`<planta_id>.sqlite` ou `<planta_id>/euler.sqlite`. Arquivos originais, importações,
análises e entidades operacionais ficam nesse banco. A restauração cria outra planta
e não sobrescreve a original.

O backup existente é JSON, limitado a 128 MiB, com bytes em base64 e SHA-256 sobre o
conteúdo canônico. O hash detecta corrupção acidental; não é assinatura digital, não
autentica o autor e não oferece confidencialidade. O arquivo contém dados sensíveis e
deve ser guardado cifrado, fora do serviço e com acesso restrito.

## Cobertura reproduzível

Os testes offline exercitam:

- cadastro e login simulados, normalização de identidade e rejeição de login sem
  sessão válida;
- carregamento de perfil ativo e associação autorizada;
- token expirado ou revogado, falha do Supabase, perfil removido, usuário suspenso,
  organização suspensa e usuário sem organização;
- renovação legítima do mesmo usuário sem perder o trabalho e troca de identidade com
  limpeza do contexto anterior;
- troca de organização, isolamento entre empresas A e B, tenant malformado e escape
  por link simbólico;
- bloqueio de `EULER_TEST_BYPASS_AUTH=1` fora do pytest, no Render, em ambientes
  protegidos ou quando qualquer configuração Supabase estiver presente;
- persistência após recriar o repositório local, integridade, concorrência, rollback de
  transação, backup completo e restauração como nova planta.

Comandos obrigatórios de aceite:

```bash
python -m ruff check .
python -m ruff format --check .
EULER_TEST_BYPASS_AUTH=1 python -m pytest -q
```

Resultado local sob Python 3.14:

- `python -m ruff check .`: aprovado;
- `python -m ruff format --check .`: aprovado, 286 arquivos formatados;
- suíte integral: `903 passed, 34 skipped, 105 warnings` em 567,80 s;
- teste focado de autenticação/persistência: `90 passed, 2 warnings` em 9,41 s.

Os 34 skips são validações opcionais impedidas pela ausência local de `xlrd` (1),
`CoolProp` (32) e `cantera` (1). Os 105 warnings incluem 100 ocorrências da depreciação
de `importlib.metadata`, um `FutureWarning` do pandas e quatro depreciações do cliente
Supabase; nenhum foi ocultado. O SHA do PR e os checks oficiais devem ser consultados na
descrição e no CI do PR de homologação.

## Gates técnicos

| Gate | Situação | Evidência ou limitação |
|---|---|---|
| SHA e árvore inicial | APROVADO | Candidata exatamente em `8d89de9`; checkout limpo. |
| Autenticação offline | APROVADO | Testes isolados de sessão, falha e autorização. |
| Autenticação Supabase real | BLOQUEADO | Projeto informado `INACTIVE`; sem conta autorizada/configuração. |
| Isolamento entre tenants | APROVADO OFFLINE | Raízes A/B distintas, acesso cruzado rejeitado e troca limpa a sessão. |
| Escape de diretório | APROVADO | IDs malformados e links simbólicos de tenant/raiz recusados. |
| Persistência local | APROVADO | Reabertura de SQLite em nova instância e fluxo Streamlit testados. |
| Backup/restauração local | APROVADO | Integridade validada antes/depois; original não sobrescrito. |
| Persistência no Render gratuito | REPROVADO | Filesystem efêmero; o plano gratuito não suporta persistent disk. |
| Recuperação em produção | BLOQUEADO | Procedimento definido, mas nenhum deploy/rollback real foi autorizado. |
| Motor científico | APROVADO LOCALMENTE | Suíte integral sem falhas; nenhum arquivo `euler/**` ou `tests/golden/**` foi alterado. |

## Procedimento de publicação e recuperação

### 1. Verificar a versão implantada

1. No Render, abra o serviço e registre o deploy ativo, o commit, a data e o status.
2. Confirme no GitHub que o SHA existe e que os checks pertencem exatamente a ele:
   `git show --no-patch --format=fuller <sha>` e `gh run list --commit <sha>`.
3. Compare o SHA com o commit aprovado no registro de liberação. A aplicação ainda
   não expõe um endpoint de versão; portanto, o painel do Render é a fonte operacional.

### 2. Preservar os dados antes da publicação

1. Bloqueie novas gravações por procedimento operacional e registre o horário.
2. Para cada tenant e planta, use **Plantas e histórico → Cópia de segurança**,
   prepare um backup novo e transfira-o imediatamente para armazenamento externo cifrado.
3. Em ambiente isolado de teste, restaure cada backup como nova planta e confirme
   listagem, arquivos, versões, análises e entidades operacionais.
4. Registre SHA-256, tamanho, planta, tenant, data, responsável e local externo. Não
   coloque o backup em logs, Git ou no filesystem efêmero como única cópia.
5. Se não for possível obter e validar todos os backups, cancele a publicação.

### 3. Publicar uma versão previamente aprovada

1. Fixe o SHA aprovado; não use apenas o nome de uma branch mutável.
2. Confirme novamente CI, aprovação humana, backups e ausência de alteração em
   `euler/**`/`tests/golden/**` não revisada.
3. Integre o SHA em `main` somente por PR revisado. Como o Render faz auto-deploy da
   `main`, o merge é o ato de publicação e deve ocorrer apenas na janela aprovada.
4. Acompanhe build, inicialização e smoke tests sem inserir dados reais de cliente.

### 4. Detectar falha após o deploy

Considere o deploy falho se houver health/startup failure, exceção repetida, login real
inválido para conta autorizada, acesso cruzado entre tenants, banco ausente/corrompido,
divergência do SHA, impossibilidade de abrir uma versão salva ou falha no smoke test de
cadastro/login/consulta. Pare novas gravações e preserve logs sem dados ou credenciais.

### 5. Retornar ao último commit validado

O caminho mais rápido é **Render → Deploys → Rollback** para um deploy bem-sucedido
recente. Segundo a documentação oficial, o rollback pelo painel reutiliza o artefato e
desabilita auto-deploy; discos não são revertidos junto com o código:
<https://render.com/docs/rollbacks>. Não execute restauração de dados automaticamente.

Depois da contenção, reconcilie `main` por um PR de rollback que produza a árvore do
commit validado. Não use force-push nem reset remoto. Reative auto-deploy somente após o
PR corretivo, CI e aceite humano.

### 6. Verificar depois da reversão

1. Confirme no Render o deploy ativo e seu SHA.
2. Execute smoke de inicialização e login com conta de teste autorizada.
3. Confira tenant A e B separadamente, sem copiar identificadores entre sessões.
4. Abra uma versão histórica e valide integridade sem recalcular como se fosse evidência
   nova. Faça um backup novo e teste a restauração fora da produção.
5. Compare inventário e hashes com o registro pré-deploy. Escale qualquer divergência;
   rollback de código não reverte dados.

## Recomendação de persistência

Para manter a arquitetura SQLite na Beta, a opção mínima é migrar o serviço para um
plano pago com persistent disk montado, por exemplo, em `/var/data/euler`, definir
`EULER_DADOS_DIR` exatamente para esse caminho e manter backups externos testados. Isso
exige mudança de infraestrutura e não foi aplicado.

Para escala multi-instância e recuperação mais forte, planejar migração para banco
gerenciado com backups e isolamento por tenant. Essa alternativa exige desenho de
schema, migração, RLS, testes e plano de retorno; está deliberadamente fora desta
homologação. Render Postgres gratuito não é substituto de produção: a documentação
atual informa expiração e ausência de backups no plano gratuito.

## Riscos remanescentes

- Nenhuma evidência real de cadastro, login, refresh, expiração, revogação ou RLS no
  Supabase inativo.
- Nenhuma garantia de retenção dos SQLite no Render gratuito; perda pode ocorrer em
  restart, spin-down ou redeploy.
- Backup é manual, por planta, sem criptografia ou assinatura digital no formato.
- Não houve ensaio de rollback no Render nem restauração sobre dados reais, conforme a
  restrição de segurança.
- O cache de autorização tem TTL de 45 segundos; revogações são observadas na próxima
  revalidação, não de forma instantânea.
- Hashes locais detectam alteração acidental, mas não impedem adulterador com acesso ao
  filesystem de recalcular hashes.

Conclusão: a candidata pode avançar nos gates **offline**, mas a aprovação técnica final
continua condicionada a Supabase real autorizado, armazenamento persistente configurado,
ensaio controlado de backup/restore/rollback e aprovação humana.

## Atualização de integração final — 17/10/2026

- O commit do PR #35 (`939569d28c44bed54d9496f62441a508503a9336`) foi incorporado
  por merge explícito, sem duplicação, na branch
  `integration/v3-final-homologation-codex`, baseada na candidata `8d89de9`.
- O runtime agora recusa armazenamento no Render se
  `EULER_REQUIRE_PERSISTENT_STORAGE=1` não estiver configurado. Quando exigida, a raiz
  precisa ser absoluta, existir, permitir escrita e não ser link simbólico.
- `scripts/beta_check.py` aplica o mesmo contrato sem imprimir valores de segredos. A
  validação local não prova que o caminho é um disco do provedor; o mount ainda deve ser
  confirmado no painel do Render.
- O endpoint público do Render respondeu HTTP 200, Streamlit e health `OK` em smoke
  somente leitura. A aplicação não expõe versão, portanto esse teste não comprova o SHA
  implantado nem persistência.
- Não havia configuração Supabase no ambiente, secrets/variables do repositório ou CLI
  autenticada disponível. O status `INACTIVE` informado anteriormente não pôde ser
  revalidado diretamente no provedor; a homologação real segue bloqueada.
- Os artefatos Tauri do run `38211447620` foram construídos em `32ed4e8`, cuja árvore é
  idêntica à candidata `8d89de9`. PR #37 comprovou instalação/inicialização/desinstalação
  do `.deb` no Ubuntu 22.04 e do NSIS no Windows Server 2025, com hashes individuais.
  AppImage abriu e tratou fechamento em ambiente gráfico virtual. Isso não equivale a
  teste físico humano, login real ou execução do dashboard 3.0.
- Permanecem abertas a UX offline/retry do shell (issue #36) e a revisão de contraste da
  Beta hospedada antiga (issue #38). Nenhuma correção Tauri concorrente foi incorporada.

### Checklist antes de publicação

- [ ] CI Python 3.11 verde no SHA final desta integração.
- [ ] Builds Linux/Windows vinculados ao mesmo SHA final ou equivalência de árvore
      registrada.
- [ ] Projeto Supabase autorizado ativo e matriz real A/B aprovada.
- [ ] Persistent Disk visível no Render, montado exatamente no `EULER_DADOS_DIR`.
- [ ] Backup externo íntegro de cada planta e restauração ensaiada fora da produção.
- [ ] SHA do deploy registrado; smoke de autenticação e persistência pós-deploy aprovado.
- [ ] Procedimento de rollback revisado; auto-deploy controlado durante a janela.
- [ ] Aprovação humana explícita. Nenhum item bloqueado pode ser presumido como aprovado.
