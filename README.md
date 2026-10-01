# EULER · protótipo (Fase 0)

SaaS de **investigação física** para caldeiras industriais: usa os registros que a fábrica já
tem para dizer quanto de energia foi comprada, quanto virou vapor e onde o resto foi parar —
e diz com clareza quando os dados **não** bastam para concluir.

> **Situação:** cálculos implementados e verificados por testes automáticos; hipóteses
> físicas em revisão científica (nenhuma aprovada); sem validação com dados reais. Os dados
> do repositório são **sintéticos**. A EULER **não emite comandos para a caldeira**: indica
> verificações.

## Começar

Requer **Python 3.11+**.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
streamlit run app/main.py          # abre em http://localhost:8501
```

No app: **Início → Começar com o caso de demonstração** (passeio guiado em
`demo/PASSEIO_PELAS_TELAS.md`). O fluxo é
carregar dados → conferir qualidade e limites → investigar → consultar fornecedores →
gerar relatório.

## Verificar

```bash
pytest -q                          # ~2 min
ruff check . && ruff format --check .
```

Para rodar também a verificação independente da física (CoolProp, Cantera):
`pip install -e ".[validacao]"`. Versões exatas testadas: `requirements-lock.txt`.

## PDF do relatório, prints e vídeo

```bash
pip install -e ".[prints]"         # playwright + markdown
playwright install chromium
python scripts/prints.py           # prints/ (8 telas)
python scripts/gravar_video_demo.py  # demo/video/ (rascunho sem narração; MP4 com ffmpeg)
python scripts/gerar_pdfs_revisao.py # docs/revisao/ (PDFs para os revisores)
```

Sem o Chromium, o app oferece só **Baixar HTML**; abra no navegador e use
**Imprimir → Salvar como PDF**.

## Onde está cada coisa

| Caminho | Conteúdo |
|---|---|
| `HANDOFF.md` | **entrega aos desenvolvedores**: organização, o que funciona, limitações, prioridades |
| `PROGRESSO.md` | andamento por etapa |
| `euler/` | motor (física, importação, investigação, relatório) |
| `app/` | telas Streamlit |
| `tests/` | testes; `tests/golden/` são valores de referência **somente leitura** |
| `demo/` | caso sintético, passeio pelas telas, guia da demonstração ao vivo, roteiro do vídeo |
| `docs/` | visão de produto, física para revisão, decisões, revisão do motor, matriz de validação, perguntas aos revisores, contrato de dados, exemplos de relatório |
| `docs/revisao/` | PDFs para enviar aos revisores |
| `templates/` | modelos de CSV e planilha para o cliente preencher |
| `prints/` | prints das telas |
| `lab/` | calculadora de referência dos revisores (não é o motor) |

Regras para quem programa (pessoas ou agentes): `AGENTS.md`.
