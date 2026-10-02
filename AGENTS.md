# AGENTS.md · EULER (lido por Codex, Claude Code e outros agentes)

## O que é este projeto
EULER é um SaaS de **investigação física** para caldeiras industriais. Ele **soma** aos registros que a fábrica já tem (diário do operador, recebimentos de combustível, amostras, eventos) e responde:

> "O consumo de combustível mudou. O que os registros sustentam, quais explicações continuam possíveis e qual verificação separa essas explicações?"

Às vezes a resposta certa é **"não dá para concluir"** + a próxima medição. Essa abstenção é uma funcionalidade, não uma falha.

## Regras invioláveis
1. **Nunca** gerar comando operacional para a caldeira (abrir válvula, mudar setpoint, ajustar queimador). O software investiga e recomenda **verificações**. Ver rodapé de segurança em `docs/produto/visao_produto.md`.
2. **Ausente ≠ zero.** Nada é preenchido, interpolado ou corrigido em silêncio. Toda correção guarda original, novo valor, motivo, autor e data.
3. **Unidades SI internamente:** kg, MJ, °C/K, bar **absoluto**. Converter na entrada; nomear colunas com a unidade (`t_gases_c`, `p_vapor_bar_abs`).
4. **Toda análise tem pré-requisitos** (`euler/capacidades.py`). Se faltar dado, a análise é **bloqueada** com motivo legível. Nunca usar porcentagem arbitrária para "completar" perdas.
5. **Não inventar números:** sem probabilidades fictícias, sem economia estimada sem base. Campos sem base ficam `null`.
6. **Não editar `tests/golden/`** nem tolerâncias de teste. Esses valores são revisados por doutorandos (física/química). Se um teste golden falhar, o código está errado até prova em contrário: pare e descreva a divergência no PR.
7. **Separação do benchmark:** o repositório `euler-bench` (gerador de dados "verdade" e gabaritos) **não** pode ser lido nem importado pelo `euler-core`. Não compartilhar a rotina de perda nos gases entre os dois.
8. Sem dados reais de clientes no repositório. Só dados sintéticos ou públicos, marcados como tal.

## Stack e comandos
- Python 3.11 · pandas · numpy · `iapws` (IF97) · pytest · ruff · streamlit
- Instalar: `pip install -e ".[dev]"`
- Testes: `pytest -q`  · Lint: `ruff check . && ruff format --check .`
- App: `streamlit run app/main.py`

## Estrutura
```
euler/
  io/             adaptadores CSV → tabelas normalizadas (preserva original)
  qualidade.py    lacunas, duplicatas, unidades, totalizador reiniciado, registro tardio
  capacidades.py  quais análises estão habilitadas/bloqueadas e por quê
  vapor.py        entalpias IF97
  combustivel.py  combustível queimado no período, energia, extrato por fornecedor
  direto.py       balanço direto
  indireto.py     perda nos gases (base PCI)
  deteccao.py     linha de base, degrau, comparação entre períodos
  investigacao.py regras → JSON de investigação
  relatorio.py    JSON → relatório em linguagem simples (HTML/PDF)
app/              Streamlit
tests/            unidade + golden (somente leitura para agentes)
docs/             contrato de dados, física, decisões
```

## Como trabalhar
- **Uma tarefa = um branch = um PR pequeno.** Siga o ticket em `docs/desenvolvimento/backlog_agentes.md`.
- Antes de codar, escreva/atualize os testes do ticket. Depois implemente até passarem.
- Funções puras e com docstring: entrada, saída, unidades, hipóteses, referência da equação (ex.: "E7 em docs/fisica/fisica_para_revisao.md").
- Toda hipótese física nova vai para `docs/gestao/decisoes.md` (data, decisão, motivo, quem revisa).
- No PR, descreva: o que mudou, como testar, o que ficou fora, dúvidas para revisão humana.
- Se a tarefa exigir decisão de produto ou de física não especificada, **não decida sozinho**: liste as opções no PR.

## Estilo de texto para o usuário final (telas e relatórios)
Português claro, frases curtas, sem jargão desnecessário. Números sempre com unidade e origem (`medido`, `estimado`, `assumido`). Nunca "IA prevê", "economia garantida" ou "comprovado" sem evidência.
