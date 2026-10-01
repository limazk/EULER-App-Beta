# Guia da demonstração ao vivo (banca e investidores · 30/10/2026)

Duração: **5 a 7 minutos** com perguntas curtas; versão curta de 2 minutos em
`demo/ROTEIRO_VIDEO.md`. Tudo usa o **caso de demonstração sintético** (`demo/caso_demo/`),
sem alterar dados.

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

| # | Clique | O que deve aparecer (conferir) | O que dizer |
|---|---|---|---|
| 1 | Tela **Início** (já aberta) | Faixa azul-escura com **EULER**; aviso azul "Protótipo em construção… caldeira **sintética**"; cartões **Em que pé está a EULER** (implementado e verificado · em revisão científica · ainda não feito) | "Este é um caso **sintético**. Os cálculos estão implementados e testados; as hipóteses físicas estão em revisão; ainda não validamos com dados reais." |
| 2 | Botão laranja **Começar com o caso de demonstração** | Abre **Dados e limites** (Passo 2 de 5). Selo **DADOS SINTÉTICOS**. Cartões **10 liberadas · 0 com limites · 1 bloqueada**. Quadro **Qualidade dos registros: 0 erros · 4 avisos de atenção · 13 informações**, com a lacuna de 12/09 a 13/09 e o totalizador zerado. | "A EULER usa os registros que a fábrica já tem e mostra os problemas sem corrigir nada." |
| 3 | Rolar até **Precisa de dados para concluir** | **Faixa de incerteza da eficiência (E15)** com selo vermelho **Bloqueada**, **Por quê** e **Para liberar** | "Ela diz o que **não** dá para concluir e o que medir para liberar." |
| 4 | Menu **4. Extrato por fornecedor** | Frase azul: **F3 tem o menor preço por tonelada (R$ 160,20/t), mas custa R$ 20,05 por GJ**; menor custo por energia: **F1, R$ 17,23/GJ**. Dois gráficos lado a lado; umidade do F3 subindo de ~45% para ~55%. | "O mais barato por tonelada é o mais caro por energia. A caldeira compra energia." |
| 5 | Menu **3. Investigação** | Quadro **Períodos comparados** com a linha do tempo: **Referência · 03/08 a 31/08 · 28 dias** (cinza-azulado) e **Comparação · 31/08 a 14/09 · 14 dias** (laranja-claro). Em **Resultado**: amarelo **Não dá para concluir…** à esquerda; azul **Próxima verificação: Cadastrar em instrumentos.csv a incerteza do método de umidade (estufa)…** à direita. | "Em cima, o resultado e a próxima verificação. A saída nunca é uma ordem para a caldeira." |
| 6 | Ler os três cartões de números | **Consumo por tonelada de vapor 0,353 t/t** (↑ +10,1% sobre 0,321 t/t; detectável: **Sim**); **Valor em jogo R$ 26.992** (incerteza ± R$ 9.624; estimado, não é promessa de economia); **Explicações compatíveis 1** (2 em aberto · 2 descartadas) | "O consumo subiu 10%. Uma explicação é compatível com os dados." |
| 7 | Aba **1. O que mudou** (já aberta) | Frase **subiu 10,1% (… incerteza ±3,6%)**. Gráfico da temperatura dos gases com as faixas dos dois períodos (botões para ver O₂, CO, ar e água). Tabela: **Temperatura dos gases +31,9 °C (± 3,3) · Sim**; **Umidade +3,2 p.p. (incerteza incompleta) · Condicional**. | "A temperatura dos gases subiu 32 °C de forma detectável. A umidade subiu, mas só seria uma mudança real com uma condição." |
| 8 | Aba **2. O que os dados sustentam (1)** | **Mais calor saindo pela chaminé** · selo azul "Compatível com os dados (não comprovada)", efeito +3,1%. Frases: "explicam +3,1% de +10,1%… sobra cerca de +6,6%" e "Contando também umidade… explicariam +11,2%: fechariam dentro da incerteza". | "Compatível não é comprovado. A umidade fecharia a conta — mas ainda não está confirmada." |
| 9 | Aba **3. Explicações possíveis (2)** | **Combustível mais úmido** · selo laranja "Continua possível" | "É por isso que ela não conclui: falta um número que a fábrica precisa cadastrar." |
| 10 | Voltar ao topo; no controle **Período de comparação**, arrastar o fim até **14/09 a 21/09** | Amarelo: **o consumo por tonelada de vapor não pode ser calculado**; cartões: consumo **—** e valor em jogo **não estimado** | "Quando falta o dado do vapor, ela nem tenta — e não inventa número." |
| 11 | Arrastar o fim de volta até **07/09 a 14/09** | Volta o consumo **+10,1%** | — |
| 12 | Botão **Próximo** no fim da tela, ou menu **5. Relatório** → **Gerar relatório** | Linha "Comparação em uso: 03/08… × 31/08… a 14/09…"; botões **Baixar HTML** e **Baixar PDF** lado a lado; prévia com **DADOS SINTÉTICOS**, "Situação do modelo…" e o botão **Imprimir ou salvar como PDF** | "Tudo vira um relatório de cinco blocos, com o aviso de segurança." |
| 13 | Rolar a prévia até **5. Próxima verificação** e o rodapé | Rodapé de segurança: "Não emite comandos operacionais…" | Fechar com a frase do produto. |

## Se algo der errado

- **O app não abre:** usar os prints de `prints/` (visual anterior, mesmos números) ou o
  vídeo gravado pelo Adryan.
- **Tela esmaecida por alguns segundos:** é o recálculo depois de mudar o período; esperar.
- **Clicou em outra coisa e perdeu o caminho:** menu **Início** → **Começar com o caso de
  demonstração** recomeça do passo 2. A escolha de períodos é lembrada ao voltar para a
  Investigação.
- **"Baixar PDF" não aparece:** o Chromium não está instalado. Na prévia, clicar em
  **Imprimir ou salvar como PDF** e escolher "Salvar como PDF" (papel A4). Funciona no
  Windows sem instalar nada.

## Perguntas prováveis
- **"Os dados são reais?"** Não, são sintéticos. Ainda não validamos com uma caldeira real.
- **"Por que ela não concluiu?"** Falta a incerteza do método de umidade. Inventar esse
  número para fechar a conclusão seria exatamente o que a EULER se recusa a fazer.
- **"Isso controla a caldeira?"** Não. A EULER não emite comandos; indica verificações.

## Legibilidade (conferido em 01/10/2026)
Visual novo conferido em 1280 px de largura e PDF A4 de 4 páginas: textos, tabelas e
gráficos legíveis. Em projetor, usar zoom de 110% a 125%. Os prints de `prints/` e o
rascunho de vídeo mostram o visual anterior (mesmos números e textos).
