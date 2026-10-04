# Guia dos desenvolvedores

[Início](../../README.md) · [Documentação](../README.md)

## Primeiro acesso

```bash
git clone https://github.com/rodriguesadryan06-a11y/softwer-euler.git
cd softwer-euler
```

A branch padrão contém a versão integrada. Siga a [instalação](../../README.md#rodar-o-software)
e use um ambiente `.venv` próprio. Não é necessário ter Codex ou Claude Code para rodar o produto.
Existe uma única versão: a branch padrão. Trabalhe nela ou em branches curtas que voltam para
ela; não mantenha versões paralelas. O `ABRIR-EULER.cmd` atualiza a cópia local sozinho, só por
avanço rápido (D91); manualmente, use `git pull --ff-only` e preserve alterações próprias antes.

## O que está implementado

- Importação CSV/Excel, qualidade dos dados e pré-requisitos de cada análise.
- Balanço direto, estados de vapor, perda nos gases e orçamento de incerteza.
- Investigação de mudanças, extrato por fornecedor e relatório.
- Comparação complementar por carga e bloqueios para regimes transitórios.
- Energia de purga e UA aparente do economizador, com medições próprias e limites explícitos.

As extensões físicas continuam em revisão. O software deve se abster quando faltarem
dados; um teste aprovado não equivale a aprovação científica ou validação em campo.

## Onde alterar

| Trabalho | Local |
|---|---|
| Telas, navegação e apresentação | `app/` |
| Leitura, normalização e contrato dos arquivos | `euler/io/` |
| Física, incerteza e regras de investigação | `euler/` |
| Verificação de comportamento | `tests/` |
| Dados sintéticos | `demo/` |
| Documentação e decisões | [Índice](../README.md) |

Leia [AGENTS.md](../../AGENTS.md) antes de editar. Não altere `tests/golden/` nem tolerâncias
dos testes. Registre hipóteses propostas em [decisões](../gestao/decisoes.md).

## Verificar uma alteração

Com o ambiente virtual ativado:

```bash
python -m pip install -e ".[dev,validacao]"
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
```

O extra `validacao` instala CoolProp e Cantera para verificações independentes. Sem ele,
essa parte da suíte pode ser pulada. Dependências e extras:
[`pyproject.toml`](../../pyproject.toml). Versões registradas:
[`requirements-lock.txt`](../../requirements-lock.txt).

## Ferramentas opcionais

Para exportar PDF pelo aplicativo e gerar capturas, instale `.[prints]` e execute
`python -m playwright install chromium` no ambiente virtual. Sem Chromium, use a
exportação HTML e a impressão do navegador para PDF.

Consulte [scripts de apoio](../../scripts/README.md) para gerar modelos, relatórios,
capturas, PDFs de revisão e vídeo. O vídeo exige FFmpeg para conversão para MP4.

## Próximos passos

Consulte o [progresso](PROGRESSO.md), o [backlog](backlog_agentes.md) e as
[decisões pendentes](../fisica/resumo_decisoes_pendentes.md). O plano inicial e a entrega
antiga estão no [histórico](../README.md#histórico), não são a descrição atual do código.
