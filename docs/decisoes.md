# Registro de decisões (técnicas e de produto)

Formato: uma linha por decisão. Agentes podem PROPOR linhas no PR; uma pessoa aprova.

| # | Data | Decisão | Motivo | Proposta por | Aprovada por / revisor |
|---|---|---|---|---|---|
| D01 | | Unidades SI internas; pressão em bar absoluto | evitar erro de conversão | spec v0.3 | |
| D02 | | Perda nos gases em base PCI por kg seco | coerência com PCI_u | spec v0.3 | REV pendente |
| D03 | | Sem IA generativa e sem OCR no protótipo do edital | foco e confiabilidade | spec v0.3 | |
| D04 | | Extrato de energia por fornecedor entra na Fase 0 | principal argumento de valor (M1) | kit agentes | |
| D05 | 2026-10-01 | Sem barômetro, `p_atm` é estimada pela altitude do local (atmosfera padrão ISA) e marcada como `estimado`; sem altitude nem barômetro, a conversão manométrica → absoluta fica bloqueada | responde provisoriamente à pergunta do E8 sem inventar valor fixo | Claude (Etapa 2) | pendente (AD + REV) |
| D06 | 2026-10-01 | Orvalho (E7) = saturação da água na pressão parcial do vapor nos gases; pressão dos gases = 1,01325 bar por padrão; sem umidade do ar e sem orvalho ácido (SO₃). Abaixo do orvalho, a perda nos gases é bloqueada | E7 pede "ponto de orvalho estimado" sem definir o método | Claude (Etapa 2) | pendente (REV) |
| D07 | 2026-10-01 | Alerta de plausibilidade T_g × T_sat (E7) implementado, mas sem valor padrão de aproximação mínima: sem valor definido pelo revisor, o alerta não é emitido | regra 5: não inventar números | Claude (Etapa 2) | pendente (REV) |
| D08 | 2026-10-01 | `modelo_cp="variavel"` fica bloqueado com motivo até o revisor definir a fonte de cp(T) (E6) | T07 na Etapa 2 pede só o modo constante | Claude (Etapa 2) | pendente (REV) |
| D09 | 2026-10-01 | Vapor "umido" exige título medido; sem medição, quem chama usa "saturado_seco" (x = 1) e marca como `assumido` | prática atual descrita no E8 | Claude (Etapa 2) | pendente (REV) |
| D10 | 2026-10-01 | CO acima de 200 ppm gera **aviso** (não bloqueio) de que o λ pode ter erro | pergunta aberta no E2 | Claude (Etapa 2) | pendente (REV) |
| D11 | 2026-10-01 | Entalpia da água de alimentação avaliada na pressão da caldeira (líquido comprimido), como `h_a(p, T_a)` no E8 | coincide com o golden V01 (2,4414 MJ/kg) | Claude (Etapa 2) | pendente (REV) |
