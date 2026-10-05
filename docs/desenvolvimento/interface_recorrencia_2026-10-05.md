# Interface e proposta de recorrência - 05/10/2026

Base: 83a4f30. Trabalho solicitado por Adryan: reduzir a quantidade de abas e texto, mantendo
as análises existentes, e pesquisar entregas que possam justificar uma assinatura mensal.

## O que mudou

- `app/navegacao.py`: registro único das 17 páginas; seis entradas principais e três grupos
  complementares em “Mais ferramentas”. Todas as URLs e páginas continuam registradas.
- `app/main.py`: usa o registro e o menu compacto. Dados, autoria, persistência e rodapé mantidos.
- `app/paginas/inicio.py`: entrada curta para acompanhar planta, importar um arquivo ou explorar
  a demonstração. Dados sintéticos e públicos permanecem distinguidos. Detalhes da demonstração
  e estágios de validação ficam recolhidos; os dois casos de demonstração continuam acessíveis.
- `app/paginas/investigacao.py`: resultado e próxima verificação primeiro; as quatro antigas abas
  viraram seções recolhidas. Diagnóstico de evidências e rastreabilidade continuam disponíveis.
- `app/paginas/financeiro.py`: composição, premissas e explicação da incerteza ficam recolhidas;
  valores, faixa do desvio, parcela evitável não apurada e próxima verificação permanecem visíveis.
- `app/paginas/painel.py`: três prioridades em destaque, demais itens e pendências recolhidos.
  Não houve mudança no cálculo da prioridade nem descarte de itens.
- `tests/test_navegacao_simples.py`: preservação das rotas e links, menu curto e estado inicial
  das seções recolhidas. A verificação usa `Expander.proto.expanded`, conforme a API de testes.

Nenhuma alteração em `euler/`, dados, golden ou tolerâncias. Esta entrega não inclui login,
hospedagem, notificações externas, faturamento ou nova comprovação de economia.

## Hipótese comercial

[Pesquisa e roteiro das reuniões](../produto/assinatura_recorrente_2026-10-05.md): oferta por
planta com atualização dos registros, fechamento periódico, fila de verificações, acompanhamento
de ações e relatório. Implantação e suporte com escopo delimitado; preço e disposição a pagar
ainda precisam ser validados. Evidências externas não são resultados da EULER.

## Como conferir manualmente

Validação automatizada concluída: **59 testes passaram**, sem falhas ou testes pulados,
em `test_navegacao_simples.py`, `test_app.py` e `test_telas_acompanhamento.py`. Inclui abertura
de todas as páginas, estados inconclusivos, números da investigação, relatórios e o ciclo
persistido de acompanhamento. Ruff check e format passaram nos sete arquivos Python alterados.
A suíte científica completa não foi reexecutada; não houve alteração do motor.

1. Abrir a EULER pelo inicializador habitual; conferir seis entradas e “Mais ferramentas”.
2. Abrir a demonstração, consultar Análise e Financeiro, investigar uma mudança e abrir os
   detalhes. Conferir conclusão, limites, valores e relatório, inclusive com dados incompletos.
3. Abrir Minha planta, consultar o fechamento e uma investigação, sem alterar registros reais.
4. Testar por teclado, em tela estreita e no notebook da reunião. Conferir legibilidade e se os
   caminhos complementares são encontrados sem orientação verbal.

A prévia HTML estática publicada anteriormente não foi regenerada: esta alteração é no aplicativo
Streamlit. Após reiniciar a instalação local, a tela inicial foi aberta e conferida visualmente no
navegador integrado, incluindo os acessos à demonstração e aos dados públicos. As seis entradas do
menu foram verificadas. A revisão responsiva completa das demais telas continua pendente.
