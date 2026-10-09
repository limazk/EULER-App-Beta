# Inteligência e Machine Learning — decisões pendentes

**Decisão vigente:** nenhuma IA generativa local/online escolhida. A fundação
não executa inferência, treinamento ou previsão. **ML funcional e testado tornou-se
entrega obrigatória da EULER 3.0 Beta**, em PR posterior ao PR visual do Codex.
Modelos não validados continuam indisponíveis para uso industrial.

## Preparado agora

- Contrato versionável de pergunta e resposta da IA, sem dados brutos.
- Gateway que retorna **desativado** e nunca consulta rede ou provedor.
- Consulta de disponibilidade de ML que declara ausência de modelo e previsão.
- Tokens visuais e documentação dos próximos pontos de integração.

## A decidir antes de ativar IA generativa

- Local, remoto ou híbrido; modelo, licença, custo e recursos de infraestrutura.
- Política por cliente para compartilhamento/retencão de dados industriais.
- Fonte e permissão das evidências utilizadas em cada resposta.
- Autenticação e isolamento entre organizações, auditoria e prevenção de injeção.
- Avaliação de fidelidade, alucinação, latência e tratamento de falha de provedor.

## Machine Learning — entrega obrigatória da Beta v3

O pacote `euler_intelligence/ml/` deverá conter implementação executável
e testes de: detecção de anomalias, previsão de consumo e avaliação de resíduos
entre medições e resultados físicos existentes. O fluxo experimental funcionará
offline com dados sintéticos ou públicos claramente identificados, somente
depois de implementado em PR próprio e aprovado. ML **não depende** de
ativação da IA generativa.

Comparar modelos com baselines claros, separar treino/validação/teste no tempo,
documentar métricas de erro, falsos alertas, incertezas, drift e condições de
abstenção. Não prometer economia, causalidade nem segurança operacional.

Este requisito não autoriza automaticamente ML com dados de clientes em produção.
O default deve continuar fail-closed até validação e decisão explícita.

## A decidir antes de ativar modelos de ML

- Conjunto autorizado e versionado de treinamento/validação; nenhuma base de
  clientes deverá ser publicada no repositório.
- Objetivo medível e métrica específica por caso de uso.
- Baseline físico/estatístico e validação temporal sem vazamento de futuro.
- Erro, falsos alertas, cobertura, deriva e condições de abstenção.
- Revisão do responsável técnico e trilha de explicação e evidências.

O motor físico existente continua responsável por cálculos e conclusões.
Modelos futuros não podem mudar valores científicos, emitir comandos de
caldeira ou converter hipóteses em causas confirmadas.
