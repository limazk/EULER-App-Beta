# HANDOFF · EULER (protótipo Fase 0) → equipe de desenvolvimento

**Versão examinada:** commit `e49338d`, branch `claude/new-session-xytynj`, 01/10/2026.
**Atualização posterior:** visual do app (identidade EULER, D58–D60), sem mudança nos
cálculos; ver `PROGRESSO.md`.
**Escrito por:** agente de programação (Claude), a pedido do Adryan (fundador). Este documento
é sincero sobre o que está pronto, o que é provisório e o que falta. **Nada da física tem
aprovação científica**, e **nada foi validado com dados reais de caldeira**.

> ⚠ **Repositório público.** A API do GitHub responde sem login para
> `rodriguesadryan06-a11y/softwer-euler`. O plano (Etapa 8) pede repositório **privado**,
> e o T19 prevê registro no INPI. Responsável: Adryan, nas configurações do GitHub.

---

## 1. Em uma frase

A EULER lê os registros que a fábrica já tem (diário do operador, recebimentos e estoques de
combustível, amostras, eventos, instrumentos) e responde: *"o consumo de combustível mudou;
o que os registros sustentam, quais explicações continuam possíveis e qual verificação separa
essas explicações?"* — inclusive dizendo **"não dá para concluir"** quando os dados não bastam.

## 2. Instalar, executar e testar num ambiente novo

Requisitos: **Python 3.11+**, Git. Testado em Linux com Python 3.11.15 (CI: GitHub Actions,
Ubuntu, Python 3.11). Uma instalação do zero seguindo os passos abaixo foi refeita em
01/10/2026 e passou em todos os testes (ver `PROGRESSO.md`).

```bash
git clone https://github.com/rodriguesadryan06-a11y/softwer-euler.git
cd softwer-euler
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -e ".[dev]"                # motor + app + pytest/ruff
streamlit run app/main.py              # http://localhost:8501
pytest -q                              # ~2 min; testes com CoolProp/Cantera são pulados
ruff check . && ruff format --check .
```

Extras opcionais (`pyproject.toml`):

| Extra | Para quê | Instala |
|---|---|---|
| `dev` | testes e lint | pytest, ruff (fixo em 0.16.x: versões novas trazem regras novas) |
| `prints` | PDF do relatório, prints, vídeo, PDFs dos revisores | playwright, markdown |
| `validacao` | verificação independente da física (`tests/test_validacao_*.py`) | CoolProp, Cantera (o motor **não** importa essas bibliotecas) |

Versões exatas que passaram nos testes: `requirements-lock.txt`
(`pip install -r requirements-lock.txt && pip install -e . --no-deps`).

### PDF do relatório
O botão **Baixar PDF** usa o Chromium pelo Playwright:
```bash
pip install -e ".[prints]"
playwright install chromium            # baixa o navegador (uma vez só; download grande)
```
Sem isso, o app mostra só **Baixar HTML** e explica a alternativa: abrir o HTML no navegador
e usar **Imprimir → Salvar como PDF** (A4). O HTML é autossuficiente (D33).

## 3. Organização

```
app/                 telas Streamlit (só apresentação; nenhuma conta física aqui)
  main.py            navegação, logo, barra lateral e rodapé de segurança
  componentes.py     identidade visual (D58): estilo, cabeçalho, cartões, botão "Próximo"
  imagens/           logo e marca EULER (SVG)
  estado.py          dados da sessão + "assinatura" dos dados (ver 3.2)
  graficos.py        gráficos Altair (paleta validada, números em pt-BR)
  paginas/           inicio · importar · limites · investigacao · extrato · relatorio · calculadora
.streamlit/config.toml  tema (cores, fontes, raio, cores dos gráficos)
euler/               motor (funções puras, testáveis sem o app)
  io/                leitura de CSV/XLSX → tabelas normalizadas (preserva o original)
  qualidade.py       lacunas, duplicatas, unidades suspeitas, totalizador reiniciado, registro tardio
  capacidades.py     quais análises estão liberadas/bloqueadas e por quê (T11)
  vapor.py           entalpias IAPWS-IF97 (pacote iapws)
  combustivel.py     PCI úmido, combustível queimado (E9), extrato por fornecedor (E11)
  periodos.py        resumo de um período entre medições de estoque + cenários do pátio
  direto.py          balanço direto: energia útil, eficiência, consumo específico
  indireto.py        perda nos gases (E1–E7); cp(T), umidade do ar, CO e O₂ úmido: experimentais
  incerteza.py       orçamento de incerteza por componente (GUM), correlação entre períodos
  deteccao.py        mudança detectável: sim · condicional · não · sem incerteza
  investigacao.py    regras → JSON da investigação (hipóteses, fechamento, próxima verificação)
  relatorio.py       JSON → HTML/PDF em linguagem simples (5 blocos + rodapé de segurança)
tests/               unidade, integração, telas (AppTest); tests/golden/ é SOMENTE LEITURA
demo/                caso sintético, gerador, roteiro do vídeo, guia ao vivo, vídeo (MP4)
docs/                física, decisões, revisão do motor, matriz de validação, perguntas, contrato
scripts/             prints, vídeo, exemplos de relatório, modelos, PDFs para revisores
lab/                 calculadora de referência dos revisores (não é o motor; não alterar)
```

### 3.1 Fluxo de dados
`arquivos` → `euler.io.importar_pacote` → `Pacote` (tabelas + avisos) →
`periodos.resumir_periodo` (por período entre medições de estoque) →
`direto.balanco_direto` e `investigacao.indireto_periodo` → `investigacao.investigar`
(JSON `investigacao/0.2`) → `relatorio.gerar_html` / `gerar_pdf`.

### 3.2 Estado nas telas
Investigação, relatório gerado e escolha de períodos ficam na sessão com a **assinatura**
dos dados (hash dos arquivos + altitude, `app/estado.py`). Trocar arquivos ou altitude nunca
mostra um resultado antigo como se fosse dos dados novos (teste em `tests/test_app.py`).

## 4. O que funciona, o que é experimental, o que falta

| Situação | O quê |
|---|---|
| **Funciona e é testado** | importação com avisos de qualidade (nada é corrigido em silêncio); capacidades; extrato por fornecedor (R$/GJ); balanço direto com orçamento de incerteza completo/parcial/indisponível; perda nos gases (cp constante, modo de referência = golden); investigação com quatro estados de detecção, fechamento, abstenção e próxima verificação; relatório HTML/PDF; fluxo completo do demo no app |
| **Implementado, hipótese em revisão** | tudo o que está em `docs/decisoes.md` como "pendente" (D05–D57, exceto D53): leitura das incertezas sem tipo (D35), correlação entre períodos (D37), cenários do pátio (D38, D51), critério de relevância D29, fronteira do balanço direto (D39) |
| **Experimental (não usado nas conclusões)** | cp(T) pelos polinômios NASA (D40), umidade do ar (D41), perda por CO (D42), conversão O₂ úmido → seco (D43) |
| **Não feito** | validação com dados reais; T12 (detecção de degrau), T04 (mapeamento automático de colunas), T16 (registro de horas); login, várias empresas/caldeiras, OCR, API, persistência (Fase 1); T17 (benchmark cego, ver 8) |

## 5. Limitações conhecidas e riscos (revisão crítica do código)

**Ciência e produto**
- Nenhuma equação ou critério tem aprovação de revisor; os golden (`tests/golden/`) também
  estão pendentes de revisão. Ver as **três decisões prioritárias** (seção 6).
- Sem dados reais: o comportamento em registros de verdade (formatos, ruído, lacunas
  longas) é desconhecido.
- O caso de demonstração **se abstém** nas semanas 5–6 e 8 porque não cadastra a incerteza
  do método de umidade: é a decisão D53 (aprovada pelo Adryan para 30/10), não um erro.
- Eficiência absoluta depende do título do vapor (x = 1 assumido), do uso do pátio e da
  amostragem de umidade: usar faixas, nunca para garantia contratual.

**Código**
- `euler/investigacao.py` tem ~1.400 linhas numa função principal longa. Funciona e é bem
  coberto por testes, mas é o primeiro candidato a refatoração (separar hipóteses,
  fechamento e textos).
- Desempenho: cada mudança de período recalcula a investigação (~3 s no demo, 8 semanas).
  Sem cache por período nas telas; aceitável para a demonstração, não para muitos meses.
- Estado só na sessão do navegador: recarregar a página apaga os dados. Sem banco, sem
  usuários, sem autenticação (escopo da Fase 1).
- Textos para o usuário estão espalhados entre `euler/investigacao.py`, `euler/relatorio.py`
  e as telas. Mudança de texto exige rodar os testes de tela e o de verbos proibidos.
- O PDF depende do Chromium (Playwright). Sem ele, só HTML (alternativa documentada).
- Componentes do Streamlit em inglês (ex.: botão "Upload" do envio de arquivos).
- O visual (D58–D60) usa o tema do `config.toml` e um pouco de CSS em `app/componentes.py`
  que se apoia nas classes `st-key-<chave>` e em alguns `data-testid` do Streamlit 1.64.
  Ao subir a versão do Streamlit, conferir as telas (cartões com a mesma altura, faixa da
  tela inicial, botão "Próximo"). Os cálculos não dependem disso.
- `prints/` e o rascunho de vídeo mostram o visual anterior (mesmos números e textos);
  `python scripts/prints.py` refaz os prints quando for preciso.
- Testes de tela (AppTest) levam ~1 min; a suíte inteira, ~2 min.

## 6. Decisões pendentes · três prioritárias para os revisores

Material para enviar: `docs/revisao/` (PDFs + LEIAME). Nenhuma está aprovada.

1. **Combustível efetivamente queimado** (D22, D38, D51; Q7). Hoje: cenário "o que entra é o
   que queima" + FIFO + limites contábeis. Decidir se mede a umidade do pátio, se aceita a
   média dos medidos para lotes sem amostra e qual modelo de pilha usar.
2. **Amostragem de umidade e estado do vapor** (D21, D52, D09; Q1, Q14). Hoje: sem a
   incerteza do método de umidade, a mudança de umidade é só "condicional"; título x = 1.
3. **Interpretação das incertezas** (D35, D37, D29; Q8, Q9, Q11, Q16). Hoje: incerteza sem
   tipo lida como limite ±a (u = a/√3); r = 0 e r = 1 entre períodos; fator D29 = 0,5.

As demais (Q1–Q17, D05–D57) estão em `docs/perguntas_revisores.md` e `docs/decisoes.md`.

## 7. Reproduzir os casos importantes

| Caso | Como |
|---|---|
| Demonstração completa | app → **Começar com o caso de demonstração**; roteiro em `demo/GUIA_DEMONSTRACAO_AO_VIVO.md`; passeio por todas as telas em `demo/PASSEIO_PELAS_TELAS.md` |
| Demo no código | `euler.io.importar_pasta("demo/caso_demo", p_atm_bar=p_atm_por_altitude_bar(1000))`; períodos por `periodos_entre_estoques`; `investigar(pacote, ref, comp)` |
| Regenerar o demo | `python demo/gerar_caso_demo.py` (determinístico; o teste confere que os arquivos batem) |
| Exemplos de relatório | `python scripts/gerar_exemplos_relatorio.py` → `docs/exemplos_relatorio/` |
| Casos A, B, C e contraexemplos | `tests/test_investigacao.py` (construtor em `tests/construtor_caso.py`) |
| Achados da auditoria (A1–A5) | `tests/test_confiabilidade.py` |
| Verificação independente da física | `pip install -e ".[validacao]"` e `pytest -q tests/test_validacao_*.py`; matriz em `docs/matriz_validacao_fisica.md` |
| Prints, vídeo, PDFs | `python scripts/prints.py` · `python scripts/gravar_video_demo.py` · `python scripts/gerar_pdfs_revisao.py` (extra `prints`) |

## 8. Fora deste repositório

- **T17 · benchmark cego:** deve ser feito depois, por outra pessoa, num repositório separado
  (`euler-bench`), com gabarito publicado antes da rodada. O `euler-core` não pode ler nem
  importar esse repositório (AGENTS.md, regra 7).
- **T19 · versão para o INPI:** tag de versão, hash e lista de autores com nome real. Hoje os
  commits são do agente ("Claude"); a autoria para registro é decisão do Adryan.

## 9. Prioridades sugeridas até 30/10/2026

1. **Ensaio da demonstração** no notebook da apresentação, seguindo
   `demo/GUIA_DEMONSTRACAO_AO_VIVO.md` (instalação limpa, `pytest -q`, PDF funcionando ou
   plano B com HTML). Responsável: Adryan + 1 dev. Concluído quando o roteiro roda duas
   vezes seguidas sem ajuda.
2. **Narração do vídeo** sobre `demo/video/rascunho_video_demo.mp4` com o texto de
   `demo/ROTEIRO_VIDEO.md`. Responsável: Adryan.
3. **Repositório privado** e decisão de autoria (T19). Responsável: Adryan.
4. **Enviar `docs/revisao/` aos revisores** e marcar a reunião começando pelas três
   decisões. Responsável: Adryan. (A resposta não precisa chegar antes de 30/10: a
   apresentação diz que a física está em revisão.)
5. Só depois, e sem tocar no demo: refatorar `investigacao.py` e acrescentar cache por
   período nas telas.

Regras do projeto: `AGENTS.md` (nunca comando operacional para a caldeira; ausente ≠ zero;
não inventar números; não editar `tests/golden/`).
