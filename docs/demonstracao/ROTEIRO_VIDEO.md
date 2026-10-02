# Roteiro do vídeo · 2 minutos

**Para:** demonstração à banca e a investidores em **30/10/2026** (serve também para o vídeo
do edital).
**O que mostrar:** o app real com o caso de demonstração **sintético**, em **dois atos** com
os mesmos registros de operação (D62): no **ato 1** (`demo/caso_demo_completo/`) a fábrica
cadastrou a incerteza de todos os instrumentos e a EULER **conclui**; no **ato 2**
(`demo/caso_demo/`) falta esse cadastro e a EULER **explica por que não conclui**.
**Rascunho gravado:** `demo/video/rascunho_video_demo.mp4` é da versão anterior (só o ato 2,
visual antigo, sem narração). O vídeo final é gravado pelo Adryan seguindo as cenas abaixo.

> Antes de gravar a versão final: `streamlit run app/main.py`, navegador em 1280 × 720,
> zoom 100%. Fale devagar; cada cena tem alguns segundos de folga.

## Mensagem em uma frase
A EULER usa os registros que a fábrica já tem para mostrar quanto de energia foi comprada,
quanto virou vapor e onde o resto foi parar — e diz com clareza quando os dados **não**
bastam para concluir.

## Cenas

| Tempo | Tela e o que fazer | Narração | Ponto do roteiro |
|---|---|---|---|
| 0:00–0:12 | **Início** → clicar **Ato 1 · a EULER conclui** | "Uma fábrica compra cavaco por tonelada. Um dia o consumo da caldeira sobe 10% e o gestor não sabe dizer por quê. Este é um caso **sintético**, criado para demonstração." | 1 · problema do gestor |
| 0:12–0:22 | **Saúde da caldeira** (abre sozinha) → selo **Mudou** e o gráfico semana a semana | "A EULER lê os registros que a fábrica já tem, **sem corrigir nada em silêncio**, e mostra o consumo por tonelada de vapor semana a semana: subiu 10% de 31/08 a 14/09, além da incerteza das medições." | 1 |
| 0:22–0:40 | **Extrato por fornecedor** → frase azul e os dois gráficos de barras | "O fornecedor mais barato por tonelada, o F3, é o **mais caro por energia**: R$ 20 por gigajoule, contra R$ 17 do F1. A caldeira compra energia, não toneladas." | 2 · extrato por energia |
| 0:40–1:05 | Menu **2. Saúde da caldeira** → **Investigar esta mudança** (agosto × 31/08 a 14/09) → resultado em verde no topo → aba **2. O que os dados sustentam** | "O consumo por tonelada de vapor subiu **10%**. Duas explicações são compatíveis com os dados: gases **mais quentes** na chaminé, sinal de sujeira, e o cavaco **mais úmido** do F3. O excesso de ar foi **descartado**: o oxigênio ficou estável. Juntas, as duas fecham a conta dentro da incerteza." | 3 · investigação |
| 1:05–1:18 | Atalho/controles: referência **31/08 a 14/09** × comparação **21/09 a 28/09** (antes × depois da limpeza) | "Depois da limpeza dos tubos, a EULER confirma o efeito: o consumo **caiu 4,5%**, e a queda da temperatura dos gases explica a mudança." | 3 · intervenção |
| 1:18–1:42 | **Início** → **Ato 2 · a EULER explica por que não conclui** → **Investigar esta mudança** (faixa amarela) | "Agora, a mesma caldeira sem o cadastro de quatro instrumentos. A EULER **não conclui**: a umidade fecharia a conta, mas falta a incerteza do método de umidade. E na semana em que o medidor de vapor estava fora, ela nem tenta: não dá para saber se o consumo mudou." | 4 · dados insuficientes |
| 1:42–1:56 | **Relatório** → **Gerar relatório** → rolar até **5. Próxima verificação** | "Tudo vira um relatório em linguagem simples. A saída nunca é uma ordem para a caldeira: é a **próxima verificação**." | 5 · relatório e próxima verificação |
| 1:56–2:04 | (tela parada no relatório) | "EULER: ela conclui quando os dados bastam, e diz o que falta quando não bastam." | fecho |

## O que dizer se perguntarem
- **Os dados são reais?** Não. São sintéticos, feitos para testar o fluxo. A EULER ainda não
  foi validada com dados reais de uma caldeira.
- **A física está aprovada?** Os cálculos estão implementados e verificados por testes
  automáticos; as hipóteses estão em revisão científica, ainda sem aprovação.
- **Por que ela não concluiu?** Porque falta uma informação que a fábrica pode fornecer (a
  incerteza do método de umidade). Inventar esse número para fechar a conclusão seria
  exatamente o que a EULER se recusa a fazer.
- **Então no ato 1 vocês inventaram as incertezas?** Os dois atos são sintéticos. No ato 1 as
  incertezas são as de especificação típica de cada instrumento, do lado conservador (D62),
  e nenhuma foi escolhida para produzir a conclusão. Numa fábrica real, elas vêm do
  fabricante ou da calibração.

## Frases que **não** usar
"A IA prevê", "economia garantida", "comprovado". O valor em jogo é **estimado** e
"não é promessa de economia".

## Checklist antes de apresentar ou enviar
- [ ] "Sintético" aparece no começo (fala e tela).
- [ ] A faixa amarela "Não dá para concluir" aparece e é explicada.
- [ ] O rodapé de segurança aparece (fim das telas e do relatório).
- [ ] Duração ≤ 2:05.
