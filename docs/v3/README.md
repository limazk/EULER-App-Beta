# EULER 3.0 — Fundação de interface e inteligência opcional

**Estado:** implementação incremental; não é uma nova versão já lançada.

## Identidade visual aprovada

A fonte de direção visual é a captura de dashboard escolhida pela equipe:
fundo quase preto, barra lateral escura, cartões em grafite, tipografia branca,
verde e vermelho apenas quando comunicarem informação e âmbar para atenção.
**Sem roxo.** Os tokens iniciais ficam em `app/design_v3/tokens.py`.

A captura é uma **referência visual**, não uma fonte de medições. Os números,
percentuais, metas, alertas, datas, séries, conversas de IA e dados de unidades
presentes em mockups não podem entrar no produto como dados reais.

### Composição alvo

1. Sidebar e cabeçalho contextual: organização/planta, período e conta autenticada.
2. Linha de KPIs: valores somente quando houver fonte, unidade e período válidos.
3. Gráfico principal: consumo, custos e comparação apenas entre grandezas compatíveis.
4. Painel lateral Intelligence: **indisponível**, sem campo de envio funcional.
5. Fechamento mensal, insights com evidência, próximas verificações e registros recentes.
6. Rodapé com aviso de segurança existente, acessibilidade e estados de erro explícitos.

A navegação deve aproveitar as rotas atuais. Não remover funções para reproduzir o mockup.

## Limites arquiteturais

- O pacote `euler/` e os testes `tests/golden/` não serão alterados na fundação.
- Proibição de comandos operacionais da caldeira.
- Dado ausente não vira zero, preço presumido ou economia verificada.
- `euler_intelligence/` é independente do motor e NÃO está habilitado.
- `euler_intelligence/ml/` não possui modelos ou previsões; avaliação é etapa futura.
- Nenhuma dependência nova ou alteração de banco foi exigida neste PR.

A implantação visual das páginas e a integração real com a autenticação e o
repositório ocorrerão em PRs separados, com testes de não regressão.
