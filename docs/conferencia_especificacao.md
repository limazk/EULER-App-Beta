# Conferência contra a especificação detalhada (item 6, rodada de 01/10/2026)

**Situação: aguardando o arquivo.** O `EULER_ESPECIFICACAO_DETALHADA.md` ainda não está na
pasta do projeto nem no GitHub (conferido em 01/10/2026). Pedido do Adryan: listar as
diferenças e **só mudar depois de mostrar**. Nada foi mudado.

A tabela de capacidades (D30) e o formato do JSON (D28) foram propostos porque as seções
4 e 7 da spec v0.3 não estavam disponíveis. Abaixo está o estado atual, para a comparação
ser feita linha a linha quando o arquivo chegar.

## 1. Tabela de capacidades atual (`euler/capacidades.py`)

Situações possíveis: `habilitada`, `parcial` (roda com limites), `bloqueada` (com motivo e
o que fazer). Coluna "situação no ato 2" = caso de demonstração sem a incerteza de quatro
instrumentos.

| id | Nome | Pergunta | Pré-requisitos | Referências | Situação no ato 2 |
|---|---|---|---|---|---|
| registros | Qualidade dos registros | Os registros têm lacunas, duplicatas ou unidades suspeitas? | diário do operador | D13, D14 | habilitada |
| perda_gases | Perda nos gases (caminho indireto) | Quanto da energia do combustível sai pela chaminé? | temperatura dos gases, O₂, temperatura do ar, umidade, análise elementar | E1–E7 | habilitada |
| energia_vapor | Energia útil do vapor | Quanta energia virou vapor? | totalizador de vapor, pressão, altitude, água de alimentação | E8 | habilitada |
| combustivel_queimado | Combustível queimado no período | Quanto combustível foi queimado? | recebimentos pesados, estoque inicial e final | E9, D17, D18, D49 | habilitada |
| energia_combustivel | Energia do combustível | Quanta energia a fábrica comprou e queimou? | combustível queimado, umidade por lote, PCI seco | E5, E10, D22, D38 | habilitada |
| eficiencia_direta | Eficiência direta | Quanto da energia comprada virou vapor? | energia útil do vapor, energia do combustível | E10, E13, D39 | habilitada |
| incerteza | Faixa de incerteza da eficiência | Quanto o resultado pode estar errado? | eficiência direta e a incerteza de cada instrumento do balanço direto (vapor, estoque, balança, pressão, água de alimentação, umidade, PCI seco) | E15, D35 | bloqueada |
| extrato | Extrato de energia por fornecedor | Quem entrega a energia mais barata? | recebimentos com fornecedor, umidade por lote, preço | M1, E11, D19, D20 | habilitada |
| comparacao | Comparação entre períodos | O que mudou de um período para outro? | diário, três ou mais medições de estoque | D25, D37, D50 | habilitada |
| investigacao | Investigação de mudança de consumo | O consumo mudou? O que explica? O que verificar? | comparação; parcial sem eficiência direta ou sem perda nos gases | — | habilitada |
| custo_vapor | Custo do vapor e efeito do preço | O custo do vapor mudou por preço ou por consumo? | eficiência direta, preço | E14 | habilitada |

## 2. JSON de investigação atual (`euler/investigacao.py`, formato `investigacao/0.2`)

- `versao_euler`, `formato`, `caldeira_id`, `origem_dados` (lista: sintético/público/real)
- `periodos`: `referencia` e `comparacao`, cada um com início, fim, rótulo, leituras e cobertura do diário, vapor, energia útil, combustível, fração de estoque, umidade e PCI recebidos, cenários do pátio, eficiência direta, consumo por t de vapor, perda nos gases, preços, purgas, eventos e bloqueios
- `o_que_mudou`: `frase`, `consumo_especifico` (comparação com incerteza e detectabilidade
  `sim`/`condicional`/`nao`/`null`), `custo_vapor`, `fechamento` (veredito `fecha`/`sobra`/`excede`, também com as explicações condicionais),
  `indicadores` (lista de comparações)
- `hipoteses` (lista): `id`, `titulo`, `status` (`sustentada`/`oposta`/`possivel`/
  `descartada`/`nao_avaliavel`), `avaliacao`, `porque`, `efeito`, `evidencia`, `medicoes`,
  `verificacao`, `para_comprovar`
- `independencia`: `caminho_direto`, `caminho_indireto`, `compartilham`, `independentes`, `nota`
- `o_que_falta` (lista de textos)
- `proxima_verificacao`: `acao`, `separa`, `porque`
- `conclusao`: `abstencao` (verdadeiro/falso), `motivo`, `texto`
- `resumo`: `frases` (até 3), `texto` (D63)
- `valor_em_jogo`: `valor_brl`, `incerteza_brl`, `combustivel_extra_t`, `origem`, `base`
  (ou `null` com `valor_em_jogo_motivo`)
- `criterios`: relevância (D29), efeito mínimo relevante, sensibilidade, nota

Campos sem base ficam `null` (regra 5 do AGENTS.md); não há probabilidades.

## 3. O que será conferido quando o arquivo chegar

1. Lista de capacidades: nomes, quais existem lá e não aqui (e o contrário).
2. Pré-requisitos de cada uma e a regra de bloqueio/parcial.
3. Campos do JSON: nomes, tipos, valores permitidos (status, detectabilidade, abstenção).
4. Regras de abstenção e da próxima verificação.
5. O que a spec pede e o motor ainda não calcula (vira proposta, não código).

O resultado será uma lista "igual / diferente / falta aqui / falta lá", com a recomendação
de cada diferença, para o Adryan aprovar antes de qualquer mudança.
