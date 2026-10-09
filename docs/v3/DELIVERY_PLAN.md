# Plano de entrega e isolamento — EULER v3

## Regras de integração

Uma tarefa = uma branch = um PR de escopo reduzido. `main` recebe apenas PRs
revisados, com CI verde e sem conflitos. Sempre conferir SHA do destino, base e
arquivos modificados. Não fazer merge por rotina automática.

Nenhuma mudança em `euler/**`, `tests/golden/**`, dependências científicas,
migrations, RLS ou credenciais sem um PR técnico próprio e revisão do responsável.
O PR #22 de fechamentos financeiros não faz parte da entrega inicial de UX.

## Ordem dos PRs propostos

| Ordem | Área | Arquivos principais | Aceite |
|---|---|---|---|
| 01 | Fundação | `app/design_v3/**`, `euler_intelligence/**`, `docs/v3/**` | Sem efeitos colaterais e testes novos verdes |
| 02 | Componentes visuais | `app/componentes.py`, `app/design_v3/**` | Responsivo, contraste, estados e componentes reutilizados |
| 03 | Navegação | `app/navegacao.py`, `app/main.py` | Rotas, permissões e contexto preservados |
| 04 | Dashboard | `app/paginas/inicio.py`, widgets próprios | Sem dados fictícios nem indicadores sem período |
| 05 | Análises e gráficos | `app/graficos.py`, telas de análise | Unidades, fontes, limitações e incertezas preservadas |
| 06 | Planta e rotina mensal | Telas operacionais, sem tocar no PR #22 antes do merge | Fechamento, ações e histórico íntegros |
| 07 | **ML obrigatório para Beta v3** | Modelos, avaliação e testes em `euler_intelligence/ml/**`, branch/PR separados | Detecção de anomalias, previsão de consumo e diagnóstico de resíduos físico-estatísticos demonstráveis com validação temporal; uso industrial desligado até homologação |
| 08 | Preparação da IA | Recuperação autorizada de evidências e validação | Nenhum provedor selecionado ou chamado |
| 09 | Beta e qualidade | Testes de fluxos, segurança, visual e documentação | CI verde e checklist de revisão humana |

## Escopo obrigatório de Machine Learning antes da Beta v3

Decisão de produto: a EULER 3.0 Beta **não será considerada completa** com apenas
interfaces e contratos vazios de ML. Após o PR visual do Codex, executar PR(s)
isolados de ML, sem editar o motor físico ou `tests/golden/**`:

1. **ML-01 — Anomalias:** detectar desvios relevantes em dados industriais
   temporalmente ordenados, com referência, evidência e possibilidade de
   abstenção quando a amostra for insuficiente.
2. **ML-02 — Previsão de consumo:** produzir previsão e intervalo de incerteza
   quando justificáveis, comparando desempenho com baseline simples;
   não confundir custo estimado com economia verificada.
3. **ML-03 — Resíduos físico-estatísticos:** analisar discrepâncias entre
   medições e saídas existentes do motor físico, sem ajustar equações nem
   emitir comandos operacionais.

Critérios mínimos de aceite: (a) pipelines executáveis de treinamento e
inferência offline, não somente scaffolds; (b) dados sintéticos ou públicos
com origem claramente identificada; (c) testes de dados ausentes/inválidos,
poucas amostras, divisão temporal sem vazamento e resultados reproduzíveis;
(d) comparação com baseline e documentação de métricas, limitações e
versões do modelo; (e) nenhum acesso entre organizações, telemetria externa
ou uso automático de dados reais sem autorização; (f) CI e revisão técnica.

A **disponibilidade em produção permanecerá desligada** até validação
industrial e aprovação humana, mesmo que a Beta inclua demonstrações e
experimentos funcionais. IA generativa permanece fora deste requisito.

## Divisão entre agentes

- **Coordenação (ChatGPT):** contratos, proteção do core, integração e revisão;
  não edita os arquivos que estão atribuídos simultaneamente ao Codex.
- **Codex:** PR visual isolado, preferencialmente começando por componentes após
  o merge da fundação. Não edita financeiro, core, banco ou testes golden.
- **Integração:** rebase ou atualização de branch somente depois de conferir a base;
  se houver conflito, interromper e solicitar reconciliação.

## Critérios obrigatórios por PR

1. Arquivos modificados limitados ao escopo autorizado.
2. Testes direcionados verdes, `ruff check .` e `ruff format --check .`.
3. Execução da suíte completa no CI, incluindo golden; não mexer em tolerâncias.
4. Teste sem dados, dados incompletos e dados sintéticos identificados.
5. Fluxos de autenticação, organização e permissões sem regressões.
6. Evidências visuais para mudanças de UI e revisão responsiva em navegador real.
7. Resumo do que mudou, riscos, limites, SHA, testes e rollback.

## Portões

Não aprovar mudanças científicas sem revisor técnico; não habilitar IA nem ML
sem decisão documentada, autorização, avaliação e controles de acesso.
