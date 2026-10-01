# Roteiro do vídeo do edital · 2 minutos (T18)

**Edital:** Fábrica de Spinoff da UnB (prazo 15/11/2026).
**O que mostrar:** o app rodando com o **caso de demonstração sintético** (`demo/caso_demo/`).
**Rascunho gravado automaticamente:** `python scripts/gravar_video_demo.py` gera um vídeo
sem narração, com legendas, seguindo exatamente estas cenas (pasta `demo/video/`).

> Antes de gravar: `streamlit run app/main.py`, janela do navegador em 1280 × 720,
> zoom 100%. Fale devagar; cada cena tem folga de alguns segundos.

| Tempo | Tela e o que clicar | O que falar (narração) |
|---|---|---|
| 0:00–0:10 | **Início** | "Uma fábrica compra cavaco por tonelada. Mas a caldeira consome **energia** — e um dia o consumo muda. Ninguém sabe dizer por quê." |
| 0:10–0:24 | **1. Importar dados** → botão **Caso de demonstração (8 semanas)** → rolar até os avisos | "A EULER usa os registros que a fábrica **já tem**: diário do operador, recebimentos e amostras. Ela aponta os problemas — lacunas, medidor zerado — **sem corrigir nada em silêncio**." |
| 0:24–0:36 | **2. Dados e limites** → rolar até *Período a período* | "Antes de concluir, ela mostra o que dá e o que **não** dá para saber. Nesta semana, o medidor de vapor estava fora: ali, não dá para fechar a conta." |
| 0:36–1:06 | **3. Investigação** (padrão: agosto × duas semanas seguintes) → rolar devagar | "Comparando agosto com as duas semanas seguintes: o consumo por tonelada de vapor subiu **10%**. A temperatura dos gases subiu 32 °C e é uma explicação compatível. O cavaco ficou mais úmido, mas a fábrica não cadastrou a incerteza do método de umidade, então a EULER **não conclui**: diz que a umidade fecharia a conta se for confirmada. A saída não é uma ordem para a caldeira: é a **próxima verificação** — cadastrar essa incerteza e conferir a amostragem de umidade." |
| 1:06–1:24 | **4. Extrato por fornecedor** → rolar até o gráfico de umidade | "O fornecedor mais barato por tonelada nem sempre é o mais barato por **energia**. O F3 cobra menos por tonelada, mas o cavaco dele ficou mais úmido semana a semana." |
| 1:24–1:40 | **5. Relatório** → botão **Gerar relatório** | "Tudo vira um relatório em linguagem simples, com cinco blocos fixos, pronto para o gestor — e sempre com o aviso de segurança." |
| 1:40–1:54 | **3. Investigação** → no período de comparação, escolher só a semana **14/09 a 21/09** | "E quando falta dado? A resposta honesta é: **não dá para concluir** — e a EULER diz exatamente o que medir." |
| 1:54–2:00 | (tela parada) | "EULER: quanto de energia a fábrica comprou, quanto virou vapor e onde o resto foi parar." |

## Frases que **não** usar
"A IA prevê", "economia garantida", "comprovado". O valor em jogo é **estimado** e
"não é promessa de economia". Os dados do vídeo são **sintéticos** — dizer isso se perguntarem.

## Checklist antes de enviar
- [ ] O selo/aviso "dados sintéticos" aparece em algum momento.
- [ ] O rodapé de segurança aparece (fim das telas e do relatório).
- [ ] Duração ≤ 2:00.
