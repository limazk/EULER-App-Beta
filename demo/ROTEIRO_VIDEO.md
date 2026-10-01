# Roteiro do vídeo · 2 minutos

**Para:** demonstração à banca e a investidores em **30/10/2026** (serve também para o vídeo
do edital).
**O que mostrar:** o app real rodando com o **caso de demonstração sintético**
(`demo/caso_demo/`), sem alterar dados.
**Rascunho gravado:** `python scripts/gravar_video_demo.py` grava o app seguindo estas
cenas, **com legendas e sem narração** (`demo/video/rascunho_video_demo.webm`). A narração
abaixo deve ser gravada por cima (ou falada ao vivo).

> Antes de gravar a versão final: `streamlit run app/main.py`, navegador em 1280 × 720,
> zoom 100%. Fale devagar; cada cena tem alguns segundos de folga.

## Mensagem em uma frase
A EULER usa os registros que a fábrica já tem para mostrar quanto de energia foi comprada,
quanto virou vapor e onde o resto foi parar — e diz com clareza quando os dados **não**
bastam para concluir.

## Cenas

| Tempo | Tela e o que fazer | Narração | Ponto do roteiro |
|---|---|---|---|
| 0:00–0:16 | **Início** (mostrar o aviso de protótipo e o quadro "Em que pé está a EULER") → clicar **Começar com o caso de demonstração** | "Uma fábrica compra cavaco por tonelada. Um dia o consumo da caldeira sobe e o gestor não sabe dizer por quê. Este é um caso **sintético**, criado para demonstração." | 1 · problema do gestor |
| 0:16–0:28 | **Dados e limites** (abre sozinha) → mostrar o quadro "Qualidade dos registros" | "A EULER lê os registros que a fábrica já tem e aponta os problemas — uma lacuna no diário, o medidor de vapor zerado — **sem corrigir nada em silêncio**." | 1 |
| 0:28–0:52 | **4. Extrato por fornecedor** → mostrar a frase azul e os dois gráficos de barras → rolar até "Umidade do cavaco por semana" | "O fornecedor mais barato por tonelada, o F3, é o **mais caro por energia**: R$ 20 por gigajoule, contra R$ 17 do F1. O cavaco dele ficou mais úmido semana a semana. A caldeira compra energia, não toneladas." | 2 · extrato por energia |
| 0:52–1:18 | **3. Investigação** (padrão: agosto × duas semanas seguintes) → rolar devagar pela tabela e pelo bloco 2 | "Comparando agosto com as duas semanas seguintes, o consumo por tonelada de vapor subiu **10%**. A temperatura dos gases subiu 32 °C: é uma explicação **compatível** com os dados — não uma causa comprovada. A umidade também subiu, mas…" | 3 · investigação |
| 1:18–1:38 | Voltar ao topo (faixa amarela "Não dá para concluir") → arrastar o **fim** do período de comparação até **21/09** (inclui a semana sem medidor de vapor) → voltar para **14/09** | "…a fábrica não informou a incerteza do método de umidade. Por isso a EULER **não conclui**: mostra que a umidade fecharia a conta *se* fosse confirmada. E se a comparação inclui a semana em que o medidor de vapor estava fora, ela nem tenta: não dá para saber se o consumo mudou." | 4 · dados insuficientes |
| 1:38–1:56 | **5. Relatório** → **Gerar relatório** → rolar até **5. Próxima verificação** | "Tudo vira um relatório em linguagem simples, com cinco blocos. A saída nunca é uma ordem para a caldeira: é a **próxima verificação** — aqui, cadastrar a incerteza da umidade e conferir a amostragem." | 5 · relatório e próxima verificação |
| 1:56–2:02 | (tela parada no relatório) | "EULER: quanto de energia a fábrica comprou, quanto virou vapor e onde o resto foi parar." | fecho |

## O que dizer se perguntarem
- **Os dados são reais?** Não. São sintéticos, feitos para testar o fluxo. A EULER ainda não
  foi validada com dados reais de uma caldeira.
- **A física está aprovada?** Os cálculos estão implementados e verificados por testes
  automáticos; as hipóteses estão em revisão científica, ainda sem aprovação.
- **Por que ela não concluiu?** Porque falta uma informação que a fábrica pode fornecer (a
  incerteza do método de umidade). Inventar esse número para fechar a conclusão seria
  exatamente o que a EULER se recusa a fazer.

## Frases que **não** usar
"A IA prevê", "economia garantida", "comprovado". O valor em jogo é **estimado** e
"não é promessa de economia".

## Checklist antes de apresentar ou enviar
- [ ] "Sintético" aparece no começo (fala e tela).
- [ ] A faixa amarela "Não dá para concluir" aparece e é explicada.
- [ ] O rodapé de segurança aparece (fim das telas e do relatório).
- [ ] Duração ≤ 2:05.
