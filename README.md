# EULER · protótipo (Fase 0)

SaaS de **investigação física** para caldeiras industriais: usa os registros que a fábrica já tem
para dizer quanto de energia foi comprada, quanto virou vapor e onde o resto foi parar.

> Protótipo com dados **sintéticos**. Ver `docs/visao_produto.md` e `AGENTS.md`.

## Rodar no seu computador
Requer Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
streamlit run app/main.py          # abre em http://localhost:8501
```

## Verificar
```bash
pytest -q
ruff check . && ruff format --check .
```

## Onde está cada coisa
| Pasta | Conteúdo |
|---|---|
| `euler/` | motor (física, importação, investigação) |
| `app/` | telas Streamlit |
| `tests/` | testes; `tests/golden/` são valores de referência **somente leitura** |
| `docs/` | visão de produto, backlog, física para revisão, decisões |
| `templates/` | modelos de CSV para o cliente preencher |
| `lab/` | calculadora de referência para os revisores (não é o motor) |
| `prints/` | prints das telas (`python scripts/prints.py`, requer `pip install -e ".[prints]"`) |

Andamento da construção: `PROGRESSO.md`.
