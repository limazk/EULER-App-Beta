# CLAUDE.md

As regras do projeto ficam num arquivo só, compartilhado com outros agentes (ex.: Codex):

@AGENTS.md

## Como trabalhar com o Adryan (fundador, não programador)
- Português simples; explique antes e depois de agir; uma etapa por vez, com plano curto e "ok" dele.
- Deixe o app rodando (`streamlit run app/main.py`), informe o endereço e onde clicar para ver o que mudou; salve prints em `prints/`.
- Ao fim de cada etapa: `pytest -q`, `ruff check .`, commit e atualização do `PROGRESSO.md`.
- Quando ele disser "continue": leia `PROGRESSO.md` e siga o plano em `EULER_CONSTRUCAO_COMPLETA.md` (Parte 2).
- Decisões de produto ou de física não especificadas: pergunte com opções e recomendação.
- **Modo automático (pedido do Adryan em 01/10/2026):** siga as etapas em sequência sem esperar "ok". Nas decisões não especificadas, escolha a opção mais conservadora, registre em `docs/decisoes.md` como proposta pendente de aprovação e liste para ele ao final. As regras invioláveis do `AGENTS.md` continuam valendo.
