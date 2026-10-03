# Trocar os dados da EULER

## Começar uma nova análise

Na barra lateral, abra **Trocar ou limpar dados**. Em **Importar dados**, clique em
**Limpar dados e começar de novo**. Isso remove os arquivos carregados, a altitude,
as seleções de períodos, a investigação e o relatório da sessão atual. Seus arquivos
originais no computador permanecem intactos. Outras abas/sessões não são limpas.

O botão limpa a sessão, não representa exclusão segura de todas as cópias em memória:
o servidor mantém caches de processamento. Encerrar o servidor elimina sua memória de
processo. Relatórios já baixados e arquivos originais continuam onde foram salvos.

## Importar uma empresa

1. Baixe **a planilha modelo (.xlsx)** na tela Importar dados.
2. Apague a linha sintética de exemplo de cada aba. Preserve cabeçalhos, nomes de abas
   e unidades. Não misture exemplos e registros reais.
3. Preencha somente o que existe: diário, combustível, amostras, eventos e instrumentos.
   Use uma caldeira por análise, identificadores consistentes e datas/horários corretos.
   Declare `origem_dado=real` nos registros da empresa. Esse campo indica a origem,
   não certifica precisão nem transforma estimativa em medição. Preserve também os
   campos próprios de origem/metodologia quando disponíveis. Ausente fica vazio, não zero.
4. Informe a altitude do local dos novos arquivos, se conhecida. Ela não vem da demonstração.
5. Selecione a planilha ou todos os CSVs que compõem o conjunto e clique em
   **Importar os arquivos enviados**. A importação substitui o conjunto anterior por
   inteiro: para acrescentar uma tabela depois, reenvie o conjunto completo desejado.
6. Confira erros e avisos. Abra **Saúde da caldeira** para consumo histórico e
   **Dados e limites** para saber quais análises os registros permitem.

Não é necessário carregar todos os campos para começar. Cada análise tem requisitos
próprios. A Saúde por estoques exige períodos entre inventários; outros sinais podem
habilitar rotas diferentes em Dados e limites. Exportações com nomes ou unidades
não reconhecidos precisam de mapeamento antes do uso.

Os arquivos enviados nesta instalação são processados pelo aplicativo local. Não os
adicione ao repositório do GitHub. Salve os originais e os relatórios necessários:
o protótipo não é um banco permanente de registros de clientes.

## Ler a Saúde da caldeira

- O gráfico mostra **kg de combustível por tonelada de vapor**, convertidos dos mesmos
  resultados do motor. Uma lacuna continua ausente; não vira zero nem interpolação.
- A referência é a primeira metade dos períodos entre inventários, não uma eficiência ideal.
- O destaque é a primeira sequência com mudança detectada, não necessariamente o período mais recente.
- **Sem mudança detectável** significa diferença dentro da incerteza declarada.
  Não demonstra ausência de perdas nem certifica eficiência ou segurança.
- Carga, qualidade do combustível e condições do vapor podem alterar kg/t. A diferença
  sozinha não prova causa ou economia recuperável. As verificações físicas continuam na Investigação.

Revisão de interface em 03/10/2026: fórmulas físicas e tolerâncias preservadas.
