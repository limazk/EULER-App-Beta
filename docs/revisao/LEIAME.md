# Material para os revisores científicos

Para enviar a professores e doutorandos (termodinâmica, combustão, química, metrologia).
Gerado por `python scripts/gerar_pdfs_revisao.py` a partir dos arquivos `.md` de `docs/`
(fonte única; o PDF só formata para imprimir e anotar).

| Arquivo | Conteúdo | Páginas |
|---|---|---|
| `fisica_para_revisao.pdf` | Equações e valores de referência E1–E15, com campo para o parecer de cada item | 5 |
| `perguntas_revisores.pdf` | **Três decisões prioritárias** (com exemplo numérico e efeito no relatório) + perguntas Q1–Q17 | 7 |

Material de apoio (no repositório, se o revisor quiser aprofundar):
`docs/revisao_motor_fisico.md` (diagnóstico e correções), `docs/matriz_validacao_fisica.md`
(o que cada teste demonstra e o que não demonstra), `docs/decisoes.md` (D01–D57).

## Situação

**Nenhum item está aprovado.** Os cálculos estão implementados e verificados por testes
automáticos (parte deles contra referências externas: tabelas IAPWS, IAPWS-95, CODATA/NIST);
as hipóteses aguardam revisão humana; não houve validação com dados reais de caldeira.

## As três decisões prioritárias (começar por elas)

| # | Decisão | Hoje no protótipo | Situação |
|---|---|---|---|
| 1 | Qual combustível foi realmente queimado (estoque do pátio) | cenário "o que entra é o que queima" + FIFO + limites contábeis; lotes sem amostra com a média dos medidos (D22, D38, D51) | aguardando resposta |
| 2 | Como amostrar a umidade e tratar o estado do vapor | sem a incerteza do método de umidade, a mudança de umidade é só "condicional"; título x = 1 assumido (D21, D52, D09) | aguardando resposta |
| 3 | Como interpretar incertezas, correlações e o critério D29 | incerteza sem tipo lida como limite ±a; r = 0 e r = 1 entre períodos; fator 0,5 (D35, D37, D29) | aguardando resposta |

## Como devolver
Para cada item: aprovado · aprovado com ressalva · corrigir · fora do escopo, com a forma
correta e a referência bibliográfica quando houver correção. Cada resposta vira uma decisão
"aprovada por <nome>" em `docs/decisoes.md`; mudanças em `tests/golden/` só por uma pessoa,
com o nome do revisor no commit.
