# Guia da demonstração ao vivo (banca e investidores · 30/10/2026)

Duração: **5 a 7 minutos** com perguntas curtas; versão curta de 2 minutos em
`docs/demonstracao/ROTEIRO_VIDEO.md`. Tudo usa o **caso de demonstração sintético** em dois atos, com os
mesmos registros de operação (`demo/caso_demo_completo/` e `demo/caso_demo/`), sem alterar
dados.

## Antes de começar (no dia, 30 minutos antes)

1. No notebook da apresentação, na pasta do projeto:
   ```bash
   source .venv/bin/activate          # Windows: .venv\Scripts\activate
   pytest -q                          # deve terminar com "passed", sem "failed"
   streamlit run app/main.py          # abre http://localhost:8501
   ```
2. Navegador em tela cheia, **zoom 110% a 125%** se for projetar (Ctrl/Cmd e +). Conferir
   que a tabela "Período a período" ainda cabe na largura.
3. Deixar abertos, em outras abas, o **plano B**: o vídeo da apresentação e a pasta
   `prints/`.
4. Recarregar a página (F5) para começar sem dados: a barra lateral deve dizer
   "sem dados carregados".
5. A internet não é necessária. O botão **Baixar PDF** precisa do Chromium (ver README); sem
   ele, usar **Imprimir ou salvar como PDF** em cima da prévia do relatório.

## Sequência exata

**Ato 1 · a EULER conclui**

| # | Clique | O que deve aparecer (conferir) | O que dizer |
|---|---|---|---|
| 1 | Tela **Início** (já aberta) | **EULER** em destaque; o parágrafo "A demonstração tem dois atos"; aviso azul "Protótipo em construção… caldeira **sintética**"; **Duas formas de usar** | "Esta é a EULER. Os dados são sintéticos, criados para demonstração." |
| 2 | Botão **Ato 1 · a EULER conclui** | Abre **Saúde da caldeira**. Selo laranja **Mudou** e a frase "O consumo por tonelada de vapor subiu 10,1% de 31/08 a 14/09 em relação à referência (03/08 a 31/08), além da incerteza das medições". Números: **0,321 t/t** e **0,353 t/t (+10,1%)**. Gráfico com faixas **Referência** e **Mudança** e eventos numerados 1, 2, 3 · 4 | "Primeiro, a saúde da caldeira: o consumo por tonelada de vapor mudou além da incerteza. A semana sem medidor de vapor fica vazia: a EULER não inventa número." |
| 3 | Botão **Investigar esta mudança** | Abre **Investigação** já com **Referência · 03/08 a 31/08 · 28 dias** e **Comparação · 31/08 a 14/09 · 14 dias**. Em **Resultado**, verde: "O consumo por tonelada de vapor subiu 10,1%. Explicações compatíveis com os dados: combustível mais úmido (+7,8%) e mais calor saindo pela chaminé (+3,1%); descartado: mais excesso de ar e vapor mais exigente. Próxima verificação: Conferir a amostragem de umidade dos lotes do fornecedor F3 e medir a umidade do pátio." | "Três frases: quanto mudou, o que explica, o que foi descartado e o que verificar. Compatível não é comprovado: a verificação comprova." |
| 4 | Ler os três cartões | **Consumo 0,353 t/t** (↑ +10,1% sobre 0,321 t/t; detectável: **Sim**); **Valor em jogo R$ 26.992** (± R$ 9.624; estimado, não é promessa de economia); **Explicações compatíveis 2** (0 em aberto · 3 descartadas) | "O valor em jogo é estimado, com a incerteza ao lado." |
| 5 | Aba **2. O que os dados sustentam (2)** | Combustível mais úmido e mais calor saindo pela chaminé, com selo azul; frase "As mudanças detectadas explicam +11,2% de +10,1% observados: fecham dentro da incerteza (±6,72%)" | "As duas explicações fecham a conta, dentro da incerteza." |
| 6 | (opcional, forte para a banca) **Antes × depois da limpeza:** referência de **31/08 a 07/09** até **07/09 a 14/09**; comparação **21/09 a 28/09** (se aparecer "se sobrepõem" no meio, continuar) | Verde: "O consumo por tonelada de vapor caiu 4,5%. Explicações compatíveis com os dados: menos calor saindo pela chaminé (-2,9%)…" | "Depois da limpeza, os gases esfriaram e o consumo caiu: compatível com sujeira nos tubos." |

**Ato 2 · a EULER explica por que não conclui**

| # | Clique | O que deve aparecer (conferir) | O que dizer |
|---|---|---|---|
| 7 | Menu **Início** → **Ato 2 · a EULER explica por que não conclui** | A mesma **Saúde da caldeira** (os registros de operação são os mesmos) | "Agora a mesma caldeira, mas a fábrica não cadastrou a incerteza de quatro instrumentos." |
| 8 | **Investigar esta mudança** | Amarelo: "O consumo por tonelada de vapor subiu 10,1%. Não dá para concluir: mais calor saindo pela chaminé (+3,1%) é compatível com os dados, mas combustível mais úmido (+7,8%) ainda não está confirmado; descartado: mais excesso de ar e vapor mais exigente. Próxima verificação: Registrar no cadastro de instrumentos a incerteza do método de umidade, informando o tipo da incerteza." | "'Não dá para concluir' é uma resposta: ela diz exatamente qual cadastro resolve a dúvida." |
| 9 | (opcional) Aba **4. O que falta saber (10)** | Dois grupos: **Completar o cadastro de instrumentos** (4 incertezas) e **Medir, registrar ou conferir** (6 itens) | "A lista de tarefas para a fábrica sair do 'não dá para concluir'." |
| 10 | Menu **Dados e limites** | Cartões **10 liberadas · 0 com limites · 1 bloqueada**; **Faixa de incerteza da eficiência** com selo vermelho **Bloqueada**; tabela **Período a período** com **Com limites** nas semanas e **Não dá para concluir** em 14/09 a 21/09 | "Ela diz o que não dá para concluir e o que medir para liberar." |
| 11 | Menu **Extrato por fornecedor** | Frase azul: **F3 tem o menor preço por tonelada (R$ 160,20/t), mas custa R$ 20,05 por GJ**; menor custo por energia: **F1, R$ 17,23/GJ** | "O mais barato por tonelada é o mais caro por energia. A caldeira compra energia." |
| 12 | Menu **Relatório** → **Gerar relatório** | No topo do relatório, as mesmas três frases; botões **Baixar HTML** e **Baixar PDF**; selo **DADOS SINTÉTICOS** | "Tudo vira um relatório de cinco blocos, com o aviso de segurança." |
| 13 | Rolar a prévia até o rodapé | Rodapé de segurança: "Não emite comandos operacionais…" | Fechar com a frase do produto. |

## Se algo der errado

- **O app não abre:** usar os prints de `prints/` ou o vídeo gravado pelo Adryan.
- **Tela esmaecida por alguns segundos:** é o cálculo de uma comparação nova (1 a 2 s) ou da
  tabela período a período na primeira visita (cerca de 4 s); esperar. Na segunda vez é
  instantâneo.
- **Clicou em outra coisa e perdeu o caminho:** menu **Início** → **Ato 1** ou **Ato 2**
  recomeça da Saúde da caldeira; **Investigar esta mudança** volta à comparação padrão.
- **"Baixar PDF" não aparece:** o Chromium não está instalado. Na prévia, clicar em
  **Imprimir ou salvar como PDF** e escolher "Salvar como PDF" (papel A4). Funciona no
  Windows sem instalar nada.

## Perguntas prováveis
- **"Os dados são reais?"** Não, são sintéticos. Ainda não validamos com uma caldeira real.
- **"Por que ela não concluiu?"** Falta a incerteza do método de umidade. Inventar esse
  número para fechar a conclusão seria exatamente o que a EULER se recusa a fazer.
- **"Isso controla a caldeira?"** Não. A EULER não emite comandos; indica verificações.

## Legibilidade (conferido em 01/10/2026)
Visual aprovado conferido em 1280 px de largura e PDF A4 de 4 páginas: textos, tabelas e
gráficos legíveis. Em projetor, usar zoom de 110% a 125%. Os prints de `prints/` mostram o
visual aprovado; o rascunho de vídeo mostra o visual anterior (mesmos números e textos).
