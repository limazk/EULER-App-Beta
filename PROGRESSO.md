# PROGRESSO da construção

| Etapa | Status | Data | O que funciona | Pendências |
|---|---|---|---|---|
| 0 · Preparar | concluída | 2026-10-01 | 17 arquivos da Parte 3 criados idênticos ao arquivo mestre (conferido por script); `.venv` com Python 3.11; dependências instaladas (`pip install -e ".[dev]"`); `pytest -q` → testes golden *skipped*; `ruff check .` sem erros. Checagem extra: `lab/referencia_perda_gases.py` e IAPWS reproduzem todos os valores golden (G01–G12, V01, P01–P05). | Spec v0.3 não está no repositório (citada por T02, T11, T12, T13): pedir ao Adryan antes da Etapa 3. |
| 1 · Fundação | a fazer | | | |
| 2 · Física | a fazer | | | |
| 3 · Entrada de dados | a fazer | | | |
| 4 · Extrato por fornecedor | a fazer | | | |
| 5 · Investigação | a fazer | | | |
| 6 · Relatório | a fazer | | | |
| 7 · Demonstração | a fazer | | | |
| 8 · Entrega aos devs | a fazer | | | |

**Próximo passo:** Etapa 1 (Fundação, T01), depois do "ok" do Adryan.

## Notas da Etapa 0
- O arquivo mestre foi copiado para a raiz (`EULER_CONSTRUCAO_COMPLETA.md`) para que "continue" funcione em sessões novas.
- `pyproject.toml` mínimo criado já na Etapa 0 (necessário para instalar dependências). A Etapa 1 (T01) completa com CI e modelo de PR.
- Ruff ignora `lab/` (calculadora de referência copiada como veio, não é código do produto); `ruff format` não toca em `tests/golden/`.
- Ambiente na nuvem: o endereço `localhost:8501` não abre no computador do Adryan. Nas etapas com tela, mostrar prints (Playwright) enviados na conversa.
