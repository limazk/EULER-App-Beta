# EULER

Software de investigação do consumo de combustível em caldeiras industriais. Reúne os
registros da operação para mostrar o que mudou, quais explicações são compatíveis com
os dados e qual verificação pode esclarecer a mudança.

**Protótipo em desenvolvimento.** A demonstração usa dados sintéticos. Os cálculos têm
testes automáticos; as hipóteses físicas dependem de revisão humana e não houve validação
em planta. A EULER indica verificações e não emite comandos para a caldeira.

## Comece por aqui

| Quero… | Acesse |
|---|---|
| Entender o produto | [Visão do produto](docs/produto/visao_produto.md) |
| Instalar e desenvolver | [Guia dos desenvolvedores](docs/desenvolvimento/README.md) |
| Conhecer as telas | [Passeio pela demonstração](docs/demonstracao/PASSEIO_PELAS_TELAS.md) |
| Preparar arquivos para importar | [Modelos de dados](templates/README.md) |
| Salvar plantas, versões e acompanhamento | [Banco unificado e backup](docs/desenvolvimento/unificacao_banco_2026-10-04.md) |
| Revisar os cálculos | [Documentação científica](docs/fisica/README.md) |
| Entender a evidência e os limites | [Diagnóstico e avaliação da referência](docs/desenvolvimento/evolucao_evidencias_2026-10-04.md) |
| Encontrar um documento | [Índice da documentação](docs/README.md) |

## Rodar o software

Requer **Python 3.11+**. Execute dentro da pasta do repositório.

**Windows — Prompt de Comando:**

```bat
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[dev]"
.venv\Scripts\python.exe -m streamlit run app/main.py
```

**Linux ou macOS:**

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -m streamlit run app/main.py
```

Abra **http://localhost:8501** e escolha **Ato 1 · a EULER conclui** para percorrer o caso
completo, ou **Ato 2** para ver como o software informa que faltam dados.

Na instalação Windows já preparada, use [ABRIR-EULER.cmd](ABRIR-EULER.cmd). O inicializador
evita servidores duplicados e, a cada abertura, traz a versão principal do GitHub quando isso
é seguro: só avança, nunca descarta alteração local não salva nem commits próprios. A barra
lateral mostra se a versão foi atualizada ou por que não foi (D91).

### Pela internet (Streamlit Community Cloud, gratuito)

1. Em **share.streamlit.io**, entre com a conta do GitHub dona deste repositório.
2. **Create app** → implantar a partir do GitHub: repositório `rodriguesadryan06-a11y/softwer-euler`,
   branch `claude/new-session-xytynj`, arquivo principal `app/main.py`.
3. Em **Advanced settings**, Python **3.11**. Depois, **Deploy**.

O servidor instala o [requirements.txt](requirements.txt) e publica um endereço
`….streamlit.app`. Cada envio para esse branch atualiza o app sozinho (uma versão só).
Cuidados: com o repositório público, **qualquer pessoa com o link abre o app**; use só
**dados sintéticos** (nunca dados de cliente); o que for gravado lá (plantas, fechamentos)
**some quando o app reinicia**. Depois de um tempo sem uso, o app "dorme" e leva alguns
segundos para acordar.

## Mapa do repositório

| Pasta | Conteúdo |
|---|---|
| [app/](app/) | Interface e telas |
| [euler/](euler/) | Motor físico, importação e investigação |
| [tests/](tests/) | Testes e valores de referência protegidos |
| [docs/](docs/README.md) | Produto, desenvolvimento, física, dados, decisões e histórico |
| [templates/](templates/README.md) | CSVs e planilha para preencher |
| [demo/](demo/README.md) | Dados sintéticos e gerador da demonstração |
| [scripts/](scripts/README.md) | Ferramentas de apoio e geração de arquivos |
| [prints/](prints/README.md) | Capturas de referência das telas |
| [lab/](lab/) | Calculadora de referência, separada do motor do produto |

Quem altera o projeto deve seguir [AGENTS.md](AGENTS.md). Entregas e próximos passos:
[progresso](docs/desenvolvimento/PROGRESSO.md) e [backlog](docs/desenvolvimento/backlog_agentes.md).
