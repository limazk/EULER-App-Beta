# Passeio pelas telas da EULER (para conhecer o app)

Tempo: uns 10 minutos, com calma. Tudo com o **caso de demonstração sintético** (dados
inventados para teste). Para a apresentação com cliques e números exatos, use
`demo/GUIA_DEMONSTRACAO_AO_VIVO.md`.

## Como abrir

- No seu computador: dois cliques em `ABRIR-EULER.cmd`. O navegador abre sozinho em
  http://localhost:8501 (ou 127.0.0.1:8501). A versão nova traz esse lançador dentro da
  própria pasta do projeto; para fechar a EULER, feche a janela preta.
- À esquerda fica o **menu** (faixa azul-escura com o logo EULER). As telas do fluxo são
  numeradas de 1 a 5. Em cada tela, no alto, aparece "Passo X de 5". No fim da tela, o botão
  **Próximo** leva à tela seguinte.
- A linha cinza "Dados em uso" com o selo laranja **DADOS SINTÉTICOS** mostra quais dados
  estão carregados. Recarregar a página (F5) apaga os dados e volta ao começo.
- Se abrir uma tela sem dados, ela oferece o botão **Carregar o caso de demonstração**.

## 1. Início

- O que é: a apresentação da EULER, o aviso de que é um protótipo e o quadro **Em que pé
  está a EULER** (o que está verificado, o que está em revisão e o que ainda não foi feito).
- Onde clicar: botão laranja **Começar com o caso de demonstração**. Ele carrega os dados e
  já leva para a tela 2. (O botão **Importar meus dados** vai para a tela 1.)

## 2. Importar dados (menu "1. Importar dados")

- O que é: onde a fábrica envia os registros (CSV ou planilha).
- O que dá para fazer:
  - informar a altitude do local;
  - clicar em **Escolher arquivos** (ou arrastar) e depois em **Importar os arquivos
    enviados**;
  - baixar a planilha modelo;
  - escolher um dos três exemplos sintéticos nos cartões de baixo.
- Experimente: **Exemplo com problemas (sintético)**. Aparecem os números de erros e avisos e,
  embaixo, a tabela **Avisos de qualidade** com selos (vermelho = erro, laranja = atenção,
  cinza = informação). Nada é corrigido em silêncio.
- Depois volte ao **Caso de demonstração** (cartão da esquerda) para seguir o passeio.

## 3. Dados e limites (menu "2. Dados e limites")

- O que é: o que dá e o que não dá para concluir com esses dados, e por quê.
- O que olhar, de cima para baixo:
  - os três cartões: **10 liberadas · 0 com limites · 1 bloqueada**;
  - o quadro **Qualidade dos registros**, com a lacuna no diário e o medidor zerado;
  - **Precisa de dados para concluir**: a análise bloqueada (selo vermelho), o **Por quê** e
    o que fazer para liberar;
  - **Liberadas com estes dados**;
  - a tabela **Período a período** (uma linha por semana). A semana de 14/09 tem ✕: sem o
    medidor de vapor, não dá para concluir.

## 4. Investigação (menu "3. Investigação"), a tela principal

- **Períodos comparados:** dois controles deslizantes. A faixa colorida embaixo mostra as
  semanas: cinza-azulado = referência (como era), laranja-claro = comparação (como ficou).
  Arraste as bolinhas para escolher outras semanas.
- **Resultado** (logo abaixo):
  - à esquerda, em amarelo, a conclusão: aqui "Não dá para concluir" e o porquê;
  - à direita, em azul, a **Próxima verificação**;
  - três cartões: o consumo por tonelada de vapor, o valor em jogo (estimado, com
    incerteza) e quantas explicações são compatíveis com os dados.
- **Detalhes**, em abas (clique no nome da aba):
  1. **O que mudou**: a frase do consumo, o gráfico (os botões trocam a grandeza: gases,
     O₂, CO, ar, água) e a tabela. Na tabela, a coluna **Diferença** traz a incerteza entre
     parênteses. A coluna **Mudou de forma detectável?** tem quatro selos: **Sim** (azul),
     **Condicional** (laranja: só vale com uma condição), **Não** (cinza) e **Sem incerteza
     para dizer** (cinza).
  2. **O que os dados sustentam**: a explicação compatível (não comprovada) e quanto ela
     explica da mudança.
  3. **Explicações possíveis**: o que ainda não dá para confirmar nem descartar.
  4. **O que falta saber**: em dois grupos. **Completar o cadastro de instrumentos** (as
     incertezas que a fábrica precisa informar) e **Medir, registrar ou conferir**.
- Experimente: no controle **Período de comparação**, arraste a bolinha da direita até
  **14/09 a 21/09**. O amarelo passa a dizer que o consumo não pode ser calculado, e os
  cartões mostram "—" e "não estimado": a EULER não inventa número. Arraste de volta até
  **07/09 a 14/09**. Voltar a uma comparação já vista é instantâneo: a EULER guarda o
  cálculo.

## 5. Extrato por fornecedor (menu "4. Extrato por fornecedor")

- O que é: quanto custa a **energia** de cada fornecedor, não só a tonelada.
- O que olhar:
  - a frase azul: o F3 é o mais barato por tonelada e o mais caro por energia;
  - os dois gráficos lado a lado (o mais barato fica no topo);
  - a tabela;
  - o gráfico da umidade por semana (o F3 vai ficando mais úmido).
- O campo **Período** no alto muda as datas do extrato.

## 6. Relatório (menu "5. Relatório")

- Onde clicar: **Gerar relatório**. Aparecem **Baixar HTML** e, se houver o Chromium,
  **Baixar PDF**.
- Na prévia, o botão **Imprimir ou salvar como PDF** abre a impressão do navegador: escolha
  "Salvar como PDF" e papel A4. Funciona no Windows sem instalar nada.
- O relatório usa os períodos escolhidos na Investigação. Se você trocar os dados ou os
  períodos, ele pede para gerar de novo; nunca mostra um relatório antigo.

## 7. Calculadora de referência (menu "Referência")

- O que é: simulação da perda de calor pela chaminé (em revisão científica; não use para
  decisões).
- Mexa nos três controles (temperatura dos gases, O₂ e umidade) e veja os números mudarem.

---

## Como atualizar a sua cópia no Windows

A pasta `software-euler` que o Codex preparou **não é um checkout Git**: ela não se atualiza
sozinha. Escolha um caminho:

- **Pedir ao Codex (mais simples):** "Atualize a pasta software-euler com a versão mais nova
  do branch `claude/new-session-xytynj` do GitHub, mantendo a pasta `.venv`. Se possível,
  troque a pasta por um `git clone` desse branch, para as próximas atualizações virem com
  `git pull`."
- **Pelo navegador:**
  1. No GitHub, abra o repositório e troque o branch para `claude/new-session-xytynj`.
  2. Clique em **Code → Download ZIP** e descompacte.
  3. Copie tudo por cima da pasta `software-euler`. Não apague a pasta `.venv` dela.

Depois, feche a janela preta do app (se estiver aberta), abra o `ABRIR-EULER.cmd` (o que vem
dentro da pasta `software-euler`) e aperte F5 no navegador. Esta atualização **não** traz
dependências novas: não precisa instalar nada.
