# Persistência local — entrega e passagem para o Claude

Data: 04/10/2026. Base integrada: `e522b03`, na branch principal `claude/new-session-xytynj`.

## O que foi encontrado

A versão publicada pelo Claude já tinha explicação da conta de combustível, oportunidades,
avaliação da referência operacional e atualização segura pelo inicializador. Essas mudanças
foram incorporadas antes desta implementação. Não foi encontrado banco de dados publicado.
Os cálculos rodam no Python; o problema era a dependência da sessão Streamlit para guardar
os arquivos e resultados.

## O que está implementado

- **Um SQLite por planta**, fora do repositório. No Windows, o padrão é
  `%LOCALAPPDATA%\EULER\dados`. A variável `EULER_DADOS_DIR` permite escolher outro local.
  O sistema recusa uma pasta de dados dentro do repositório.
- **Versões completas dos arquivos originais**, preservando nomes e bytes, altitude,
  indicação sintética, autor declarado, motivo, data em UTC e vínculo com a versão anterior.
  Um reenvio idêntico à versão anterior não duplica o armazenamento nem altera sua autoria.
- **Correções por nova versão:** reenvia-se o conjunto completo corrigido, com responsável
  e motivo. A versão anterior continua disponível; não se atualizam células em silêncio.
- **Investigações arquivadas automaticamente** quando calculadas a partir de uma versão
  salva. O JSON completo e os períodos escolhidos de referência/comparação são preservados.
  A explicação financeira e as oportunidades presentes nesse JSON também ficam arquivadas.
- **Reabertura em outra sessão**, com arquivos, altitude e análise compatível. A assinatura
  inclui arquivos, altitude, planta, importação e código do motor. Uma análise de outro
  contexto ou versão do motor continua histórica, mas não é reutilizada como análise atual.
- **Backup e restauração pela interface.** O backup contém os originais e o histórico.
  A restauração cria outra identificação de planta e não sobrescreve o banco original.
  As análises restauradas ficam disponíveis como histórico; é necessário recalcular para
  associar um resultado ao novo contexto.
- **Verificações de integridade SHA-256 e transações.** Arquivos, metadados, análises e
  backups são verificados. Falhas de gravação são exibidas; não há mensagem de sucesso falso.
- **Separação dos exemplos:** carregar uma demonstração ou outro conjunto desvincula a
  sessão da planta anterior. Limpar a sessão não apaga versões salvas.

## Como usar

1. Em **Importar dados**, carregue a planilha/CSVs do equipamento e informe a altitude.
2. Abra **Gestão → Plantas e histórico** e cadastre a planta.
3. Em **Salvar os dados em uso nesta planta**, informe responsável e motivo e salve.
4. Abra **Investigação** para calcular e arquivar o resultado dessa versão.
5. Depois de fechar e abrir o navegador, entre em **Plantas e histórico**, selecione a
   planta e a versão e clique em **Abrir versão**.
6. Para corrigir ou acrescentar um período, envie o **conjunto completo** em Importar dados,
   mantendo marcada a opção de salvar nova versão na planta. As versões não são concatenadas.
7. Em **Cópia de segurança**, prepare e baixe o backup. Depois de novos registros, prepare-o
   novamente. A restauração fica no mesmo menu.

Selecionar uma planta na lista, sozinho, não troca os dados ativos. Dados ainda não salvos
continuam apenas na sessão, e a barra lateral informa isso. Salvar os arquivos de uma sessão
pela primeira vez pode exigir recalcular a investigação para arquivar o resultado.

## Arquitetura para continuar o trabalho

| Arquivo | Responsabilidade |
|---|---|
| `euler/persistencia.py` | Repositório SQLite, esquema v1, validação, importações, análises, backup/restauração |
| `app/armazenamento.py` | Ponte entre sessão e repositório; verificação de compatibilidade e gravação de investigações |
| `app/paginas/plantas.py` | Cadastro, versões, reabertura, histórico e backup |
| `app/estado.py` | Limpeza/desvinculação, assinatura com contexto e chamada de arquivamento |
| `app/paginas/importar.py` | Importação opcional como nova versão na planta ativa |
| `app/main.py` | Navegação e indicação do estado de salvamento |
| `tests/test_persistencia.py` | Integridade, reinício, isolamento, deduplicação, concorrência, rollback e backup |
| `tests/test_armazenamento_app.py` | Sessão, compatibilidade e fluxo completo usando a interface Streamlit e o motor real |

O banco tem tabelas `planta`, `importacoes`, `arquivos` e `analises`. As cinco tabelas do
**contrato industrial** permanecem dentro dos arquivos importados: não se confundem com
as tabelas de armazenamento. O leitor e a normalização existentes continuam sendo usados.
Esta entrega não muda equações, hipóteses físicas, valores golden ou tolerâncias.

A suíte encontrou também uma falha do inicializador no Windows: uma subpasta sem
repositório próprio era reconhecida como parte do repositório pai. Foi corrigida em
`scripts/abrir_local.py` e coberta por um teste adicional em
`tests/test_inicializador_local.py`, preservando o código do repositório pai.

API principal: `criar_planta`, `listar_plantas`, `salvar_importacao`, `listar_importacoes`,
`carregar_importacao`, `salvar_analise`, `listar_analises`, `exportar_backup`, `restaurar_backup`.
O esquema tem versão e rejeita versões desconhecidas sem alterá-las. Uma futura mudança de
esquema precisa de migração explícita e testes de recuperação.

## Limites e próximas entregas

1. **Perfis de colunas e unidades:** ainda não existe um editor persistente de mapeamento.
   A entrada usa o contrato atual. Integrar perfis ao leitor e ao hash da análise antes de
   expor essa funcionalidade; não cadastrar configurações sem efeito na análise.
2. **Correção por célula e entrada incremental:** hoje são snapshots completos, com vínculo
   anterior. Falta uma tela de diferenças por registro e uma identidade confiável para
   conciliar linhas sem duplicar medições nem misturar equipamentos.
3. **Fechamentos, verificações e intervenções:** ainda não há entidades nem fluxo específico
   persistente para isso. Arquivar um JSON de investigação não equivale a implementar
   acompanhamento de intervenção, fechamento aprovado ou economia verificada.
4. **Referências operacionais:** a seleção de períodos fica dentro da investigação arquivada.
   Uma referência nomeada, aprovada e reutilizável como entidade independente ainda falta.
5. **SaaS com clientes:** a biblioteca é local, sem autenticação, autorização por empresa,
   criptografia ou sincronização na nuvem. Quem acessa esta instalação pode acessar todas
   as plantas. Não publicar como ambiente multiempresa sem implementar esses controles.

Limites desta versão: até 20 arquivos e 50 MiB por importação; backup JSON até 128 MiB.
O backup contém dados da planta e precisa ser guardado em local protegido. Hash detecta
corrupção, mas não autentica o autor nem substitui assinatura digital. Autoria é informada
pelo usuário, não identidade verificada. Backups são manuais nesta entrega.

## Validação

Os testes específicos exercitam reinício, isolamento entre plantas, bytes originais,
nomes com espaços/acentos, revisões, reenvio sem duplicação, gravações concorrentes,
rollback, corrupção, versões incompatíveis, backup inválido, mudança de altitude,
motor diferente e limpeza da sessão. O teste da interface cria uma planta sintética,
salva a importação, executa o motor, abre outra sessão e recupera arquivos e investigação.

Resultados executados nesta entrega:

- Suíte completa: **550 passaram e 1 falhou**, em 16 minutos. A única falha estava no
  reconhecimento de repositórios pelo inicializador, descrita acima; não era um cálculo.
- Após a correção: **9 testes do inicializador passaram**, incluindo o caso que falhava e
  um novo teste de proteção da pasta pai. Não foi repetida a suíte completa depois dessa
  correção isolada. O conjunto atual tem 552 testes.
- **22 testes de persistência e integração** estão entre os aprovados: 14 do repositório
  e 8 da ponte/interface. Incluem o fluxo completo com o motor real e outra sessão.
- `ruff check .` e `ruff format --check .`: aprovados; 168 arquivos formatados.
- Verificação no navegador: planta sintética criada, dados salvos, servidor reiniciado,
  versão reaberta e investigação executada com o motor atualizado. A planta de exemplo
  permanece claramente identificada como sintética na biblioteca local.
- Três avisos preexistentes do pandas apareceram nos testes de entradas não finitas.
  Os testes correspondentes passaram; não foram escondidos nem tolerâncias alteradas.

Antes de publicar dados reais na nuvem, executar os trabalhos de isolamento e acesso
listados acima. Esta entrega é uma base local funcional, não uma certificação de SaaS.
