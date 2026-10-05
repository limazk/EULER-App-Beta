# Documentação da EULER

[Voltar ao repositório](../README.md)

## Produto e demonstração

- [Visão do produto](produto/visao_produto.md): problema, escopo e limites.
- [Entenda a EULER](demonstracao/ENTENDA_A_EULER.md): explicação do fluxo de investigação.
- [Passeio pelas telas](demonstracao/PASSEIO_PELAS_TELAS.md).
- [Guia da demonstração ao vivo](demonstracao/GUIA_DEMONSTRACAO_AO_VIVO.md).
- [Roteiro de vídeo](demonstracao/ROTEIRO_VIDEO.md).

## Desenvolvimento

- [Assinatura recorrente: hipótese comercial e perguntas para o piloto](produto/assinatura_recorrente_2026-10-05.md).

- [Guia dos desenvolvedores](desenvolvimento/README.md): instalação, arquitetura e verificações.
- [Banco unificado](desenvolvimento/unificacao_banco_2026-10-04.md): plantas, registros, fechamentos, backup e passagem para o Claude.
- [Progresso](desenvolvimento/PROGRESSO.md): registro cronológico das entregas.
- [Backlog](desenvolvimento/backlog_agentes.md): tarefas e critérios de aceite.
- [Conferência da especificação](desenvolvimento/conferencia_especificacao.md).

## Dados e revisão científica

- [Contrato de dados](dados/contrato_dados.md): colunas, unidades e obrigatoriedade.
- [Modelos para preencher](../templates/README.md).
- [Revisão científica](fisica/README.md): equações, validação e perguntas aos revisores.
- [Registro de decisões](gestao/decisoes.md): propostas e situação da aprovação humana.
- [PDFs de revisão](revisao/LEIAME.md): cópias para impressão; conferir a versão antes de usar.
- [Exemplos de relatório](exemplos_relatorio/LEIAME.md): saídas do caso sintético.

## Histórico

- [Entrega de 01/10/2026](historico/ENTREGA_2026-10-01.md).
- [Plano original de construção](historico/PLANO_ORIGINAL.md).

Os documentos históricos explicam decisões e etapas anteriores. Para trabalhar na versão
atual, comece pelo guia dos desenvolvedores e consulte o progresso e o código vigente.

## Onde colocar novos arquivos

Use `produto/` para escopo; `desenvolvimento/` para guias e tarefas; `dados/` para o contrato;
`fisica/` para revisão científica; `gestao/` para decisões; `demonstracao/` para roteiros.
Materiais superados vão para `historico/`, com data e contexto. PDFs e relatórios gerados
ficam nas pastas específicas, separados das fontes editáveis.
