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
3. Deixar abertos, em outras abas, o **plano B**: `demo/video/rascunho_video_demo.mp4` e a
   pasta `prints/`.
4. Recarregar a página (F5) para começar sem dados: a barra lateral deve dizer
   "sem dados carregados".
5. A internet não é necessária. O PDF do relatório precisa do Chromium (ver README); se ele
   não estiver instalado, usar **Baixar HTML** e mostrar no navegador.

## Sequência exata

| # | Clique | O que deve aparecer (conferir) | O que dizer |
|---|---|---|---|
| 1 | Tela **Início** (já aberta) | Aviso "Protótipo em construção…"; quadro **Em que pé está a EULER** (implementado e verificado · em revisão científica · ainda não feito) | "Este é um caso **sintético**. Os cálculos estão implementados e testados; as hipóteses físicas estão em revisão; ainda não validamos com dados reais." |
| 2 | **Começar com o caso de demonstração** | Abre **Dados e limites**. Selo laranja **DADOS SINTÉTICOS**. Quadro **Qualidade dos registros: 0 erros · 4 avisos de atenção · 13 informações** com a lacuna de 12/09 a 13/09 e o totalizador zerado. Métricas: **10 liberadas · 0 com limites · 1 bloqueada**. | "A EULER usa os registros que a fábrica já tem e mostra os problemas sem corrigir nada." |
| 3 | Rolar até **Faixa de incerteza da eficiência (E15)** | Situação **Bloqueada**, com o que cadastrar (termômetro da água de alimentação, método de umidade, PCI seco) | "Ela diz o que **não** dá para concluir e o que medir para liberar." |
| 4 | Menu **4. Extrato por fornecedor** | Frase azul: **F3 tem o menor preço por tonelada (R$ 160,20/t), mas custa R$ 20,05 por GJ**; menor custo por energia: **F1, R$ 17,23/GJ**. Gráfico de umidade: F3 subindo de ~45% para ~55%. | "O mais barato por tonelada é o mais caro por energia. A caldeira compra energia." |
| 5 | Menu **3. Investigação** | Períodos padrão: referência **03/08 a 31/08**, comparação **31/08 a 14/09**. Faixa amarela **Não dá para concluir…** | — |
| 6 | Ler o bloco **1. O que mudou** | **Consumo subiu 10,1% (0,321 → 0,353 t por t de vapor; incerteza ±3,6%)**. Tabela: temperatura dos gases **185,8 → 217,7 °C: sim**; umidade **43,2% → 46,4%: só se o erro do mesmo instrumento se repetir (falta cadastrar a incerteza)**. Valor em jogo **R$ 26.992 (± R$ 9.624), estimado**. | "O consumo subiu 10%. A temperatura dos gases subiu 32 °C de forma detectável." |
| 7 | Rolar até **2. O que os dados sustentam** | **Mais calor saindo pela chaminé** · "Compatível com os dados (não comprovada)", efeito +3,1%. Frases: "explicam +3,1% de +10,1%… sobra cerca de +6,6%" e "Contando também umidade… explicariam +11,2%: fechariam dentro da incerteza". | "Compatível não é comprovado. A umidade fecharia a conta — mas ainda não está confirmada." |
| 8 | Rolar até **3** e **5. Próxima verificação** | Umidade em **Continua possível**. Próxima verificação: **Cadastrar em instrumentos.csv a incerteza do método de umidade (estufa)…** | "A saída nunca é uma ordem para a caldeira; é a próxima verificação." |
| 9 | Voltar ao topo; no controle **Período de comparação**, arrastar o fim até **14/09 a 21/09** | Faixa amarela: **o consumo por tonelada de vapor não pode ser calculado**; bloco 1: **Não dá para saber se o consumo… mudou** | "Quando falta o dado do vapor, ela nem tenta." |
| 10 | Arrastar o fim de volta até **07/09 a 14/09** | Volta o consumo **+10,1%** | — |
| 11 | Menu **5. Relatório** → **Gerar relatório** | Linha "Comparação em uso: 03/08… × 31/08… a 14/09…"; botões **Baixar HTML** e **Baixar PDF**; prévia com **DADOS SINTÉTICOS** e "Situação do modelo…" | "Tudo vira um relatório de cinco blocos, com o aviso de segurança." |
| 12 | Rolar a prévia até **5. Próxima verificação** e o rodapé | Rodapé de segurança: "Não emite comandos operacionais…" | Fechar com a frase do produto. |

## Se algo der errado

- **O app não abre:** usar o vídeo `demo/video/rascunho_video_demo.mp4` (sem som; narrar
  por cima com o texto de `demo/ROTEIRO_VIDEO.md`) ou os prints de `prints/`.
- **Tela esmaecida por alguns segundos:** é o recálculo depois de mudar o período; esperar.
- **Clicou em outra coisa e perdeu o caminho:** menu **Início** → **Começar com o caso de
  demonstração** recomeça do passo 2. A escolha de períodos é lembrada ao voltar para a
  Investigação.
- **"Baixar PDF" não aparece:** o Chromium não está instalado; usar "Baixar HTML" e, se
  precisar, Imprimir → Salvar como PDF no navegador.

## Perguntas prováveis
- **"Os dados são reais?"** Não, são sintéticos. Ainda não validamos com uma caldeira real.
- **"Por que ela não concluiu?"** Falta a incerteza do método de umidade. Inventar esse
  número para fechar a conclusão seria exatamente o que a EULER se recusa a fazer.
- **"Isso controla a caldeira?"** Não. A EULER não emite comandos; indica verificações.

## Legibilidade (conferido em 01/10/2026)
Prints em 1280 px de largura (`prints/`), vídeo em 1280 × 720 e PDF A4 de 4 páginas:
textos, tabelas e gráficos legíveis. Em projetor, usar zoom de 110% a 125%.
