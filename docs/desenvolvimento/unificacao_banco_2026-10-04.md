# Banco unificado — passagem para o Claude

04/10/2026. Conciliação das entregas `1d4994b` (biblioteca de arquivos e análises)
e `6e5dad9` (acompanhamento recorrente). Este documento substitui a descrição da
primeira entrega de persistência para o estado atual.

## Resultado

**Um SQLite por planta, compartilhado pelas duas APIs.** `Repositorio.armazem(id)`
abre o mesmo arquivo que contém importações, originais e investigações arquivadas.
Não foi criado outro motor físico. Equações, golden e tolerâncias foram preservados.

O banco reúne:

- arquivos originais e versões completas, com autoria, motivo, altitude e hashes;
- equipamentos, registros normalizados com revisão, conflitos e correções;
- perfis de colunas, cobertura temporal e aviso de desatualização;
- preços, referências versionadas e fechamentos;
- investigações, intervenções, avaliações posteriores e custos de acompanhamento;
- vínculo explícito entre cada lote operacional e seus arquivos originais.

Um arquivo completo salvo e uma série acumulada são duas representações diferentes
**dentro do mesmo banco**. A série pode reunir importações sucessivas e correções.
Os originais não são substituídos pelos CSVs normalizados usados no cálculo.

## Localização e migração

As duas APIs resolvem a mesma pasta: `EULER_DADOS_DIR`, quando definida; depois
`EULER_DADOS`; em instalação nova, `~/EULER-dados`. Uma biblioteca anterior em
`%LOCALAPPDATA%/EULER/dados` continua sendo usada, se for a única biblioteca existente.
Se houver bancos nas duas pastas antigas, a aplicação pede que a pasta ativa seja
definida; não escolhe nem move dados silenciosamente.

Os formatos antigos `<id>.sqlite` e `<id>/euler.sqlite` são reconhecidos. Ambos
recebem o esquema v2 **no próprio arquivo**, com cópia `.v1.bak` anterior à migração.
Dois bancos com a mesma identidade são recusados até resolução explícita.
Versões futuras são recusadas antes de qualquer alteração de esquema.

Bibliotecas antigas sem classe ficam `nao_classificado`: os arquivos continuam
acessíveis, mas o acompanhamento exige classificação explícita. Arquivos salvos
são conferidos antes de aceitar essa classificação. Cliente exige registro de
autorização. Dados de origem incompatível são recusados, inclusive em correções.
Os lotes operacionais antigos mantêm seu histórico; bytes originais que nunca
foram guardados pela versão anterior não podem ser recuperados retroativamente.

## Fluxo pela interface

1. **Importar dados:** carregar os arquivos; informar a altitude quando conhecida.
2. **Plantas e histórico:** cadastrar planta e classe; salvar os arquivos com autor
   e motivo. Reabrir versões e baixar/restaurar backup no mesmo lugar.
3. **Acompanhamento:** cadastrar equipamento com o `caldeira_id` do diário e altitude.
4. Escolher a versão salva, preparar a prévia e conferir novas, iguais, conflitos,
   recusadas, repetidas, tardias e avisos de unidades. A altitude do equipamento deve
   corresponder àquela da versão escolhida; divergências não são corrigidas em silêncio.
5. Confirmar os registros novos. Conflitos permanecem pendentes até decisão com
   responsável e motivo. Mapeamento de nomes não converte unidades.
6. **Analisar série acumulada:** materializar os registros dessa revisão e abrir
   Investigação. A versão consolidada fica identificada como tal; os originais permanecem.
7. Em **Referência e fechamentos**, escolher os períodos e justificar a referência.
   Fechar períodos disponíveis, consultar relatório e conferir sua reprodução.

Limpar a sessão não apaga o banco. Selecionar uma planta não abre automaticamente
seus arquivos. A barra lateral informa se os dados atuais estão salvos ou alterados.
Plantas de exemplo continuam identificadas como sintéticas.

## Correções importantes da conciliação

- Confirmação do lote, registro dos originais e vínculo ocorrem na mesma transação.
- Uma prévia de outra planta, revisão ou configuração é recusada: precisa ser refeita.
- Backup JSON inclui **todas as tabelas operacionais**, além dos arquivos e análises.
  Restauração pela interface cria outra identidade de planta sem substituir a original.
- Exportação de auditoria representa bytes em base64, sendo JSON serializável.
- Fechamentos novos guardam altitude/pressão atmosférica, configuração, referência
  e preços usados. Alterar a configuração ou cadastrar outro preço depois não muda
  a reprodução do fechamento antigo.
- Corrigir dados históricos que alimentam a referência exige registrar outra versão
  antes do próximo fechamento. A referência não absorve a correção silenciosamente.
- Conta, oportunidades e custo por energia do fechamento usam a mesma política de
  preço. Se ela não tiver dados suficientes, seus valores financeiros ficam ausentes.
- Fechamento legado sem essas premissas permanece consultável, mas não é declarado
  reproduzível por adivinhação da configuração antiga.
- A API histórica de reprodução com outra referência continua disponível, como
  recálculo explicitamente diferente; não sobrescreve o fechamento original.
- Mantida a correção do inicializador para não atualizar por engano o repositório pai
  quando a pasta da aplicação não tiver repositório próprio.

## Arquivos principais

| Arquivo | Responsabilidade |
|---|---|
| `euler/persistencia.py` | Esquema comum, migração, arquivos, análises e backup integral |
| `euler/armazem.py` | Registros por equipamento, revisões, perfis, conflitos e cobertura |
| `euler/fechamento.py` | Referência, custo, fechamento e reprodução com premissas históricas |
| `euler/acompanhamento.py` | Fluxo de investigações, intervenções e avaliação posterior do Claude |
| `euler/painel.py` | Fila de atenção, indicadores e proteção contra dupla contagem |
| `app/armazenamento.py` | Ligação da sessão com versões salvas e séries acumuladas |
| `app/paginas/plantas.py` | Biblioteca, classificação, backup e restauração |
| `app/paginas/acompanhamento.py` | Entrada incremental, conflitos, referência e fechamentos |

As APIs públicas do Claude foram mantidas. `Previa` passou a incluir identidade da
planta, revisão, configuração e bytes originais; obtenha-a por `a.previa(...)`.
`a.confirmar(...)` aceita `importacao_id` opcional para vincular uma versão já salva
e devolve esse identificador junto com o lote. `Repositorio` aceita classes e
autorização e disponibiliza `armazem(id)` e `classificar_planta(...)`.

## Validação e limites

Os testes originais `test_armazem.py`, `test_fechamento.py`,
`test_acompanhamento.py` e os testes do inicializador foram preservados. Novas
regressões verificam banco comum, migração dos dois esquemas, restauração integral,
isolamento, origem, prévia obsoleta e reprodução após mudança de preço/altitude.
`test_acompanhamento_ui.py` percorre o fluxo real da tela até a série acumulada.
Resultado: **102 testes distintos aprovados**, executados em grupos:

- 55 de armazenamento, unificação e fechamento na última bateria (234 s);
- 12 de acompanhamento/intervenções;
- 8 da ponte com a sessão e reabertura de análise;
- 1 do fluxo completo da nova tela;
- 9 do inicializador seguro;
- 17 de abertura das páginas e preservação do rodapé.

A última mudança da prévia, que passa a considerar a altitude cadastrada e agrupa
os avisos na tela, foi conferida novamente: 14 testes de armazém e 1 de interface
passaram (68 s). Revisão final: `ruff check .` e `ruff format --check .` aprovados,
179 arquivos formatados. Esses testes repetidos não foram somados ao total acima.
Não foi repetida a suíte científica inteira nesta conciliação: os cálculos físicos
não foram alterados. Nenhum teste original, golden ou tolerância foi removido.

Não confundir persistência com validação industrial. O protocolo EULER-MV 0.1 é
proposto, não uma certificação independente. A revisão da referência, comparabilidade
e cobertura de incerteza continua sendo necessária antes de uma alegação comercial
de economia verificada. A conciliação não acrescenta prova de causa nem dados de campo.

Ainda é uma instalação local: sem login, autorização por usuário, criptografia ou
sincronização em nuvem. A autoria é declarada. Hash detecta alteração, não autentica
o responsável. Backup é manual: até 128 MiB em JSON; importação até 20 arquivos/50 MiB.
Não publicar esta instalação como SaaS multiempresa sem controles de acesso.

Próximos trabalhos: telas completas para investigações/intervenções e cadastro de
preços (as APIs e testes já existem); revisão do protocolo de verificação econômica;
concorrência multiusuário; backup programado e autenticação. A nova tela já usa as
entidades operacionais, mas não expõe todos os campos dessas APIs.
