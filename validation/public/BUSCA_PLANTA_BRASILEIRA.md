# Busca de dados públicos de uma planta brasileira (05/10/2026)

Pedido do Adryan: encontrar dados completos de uma caldeira brasileira para validar a EULER.

**Situação:** a busca na web funciona, mas a rede deste ambiente bloqueia o acesso aos sites
onde os arquivos estão (repositórios de universidades, SciELO, Springer, Zenodo, Mendeley
Data, Figshare, dados.gov.br, ONS, IBAMA). Nada abaixo foi aberto ainda: as descrições vêm
dos resumos públicos. Nenhum dado foi baixado nem colocado no repositório.

O que a EULER precisa para a cadeia inteira, no mesmo período: combustível queimado (massa e
estoque), vapor produzido, umidade/PCI do combustível, condições do vapor e da água de
alimentação e, de preferência, O₂ e temperatura dos gases e algum evento (intervenção).

## Candidatos, do mais promissor ao menos

| # | Fonte | O que os resumos indicam | O que poderia validar | Onde está |
|---|---|---|---|---|
| 1 | *Influência da secagem da biomassa na eficiência de caldeira de cogeração energética* (Revista Energia na Agricultura, UNESP/FCA) | **registros históricos de 2012 a 2015** de duas caldeiras a biomassa (CF8 e CF9) de uma indústria de celulose e papel: consumo de biomassa, óleo BPF e piche, produção de vapor e umidade da biomassa; instalação de um **secador** no meio do período | consumo específico (t/t) ao longo do tempo, efeito da umidade, **antes × depois de uma intervenção** (o fluxo de avaliação de ações) | revistas.fca.unesp.br/index.php/energia/article/view/2606 |
| 2 | Diniz, I. S. (2014), *Estudo da influência da umidade no consumo específico do cavaco…* (UTFPR Ponta Grossa) | **banco de dados histórico** de uma empresa de papel jornal: consumo específico e umidade do cavaco ao longo de anos | relação umidade × consumo específico com dados de operação | repositorio.roca.utfpr.edu.br/jspui/handle/1/5928 |
| 3 | Resende, E. F. R. (2019), *O efeito da umidade do cavaco na geração de vapor* (UFU) | caldeira aquatubular de **180 t/h** a cavaco; desempenho em função da umidade | balanço direto e efeito da umidade | repositorio.ufu.br/bitstream/123456789/28572 |
| 4 | Cortes-Rodríguez, Nebra e Sosa-Arnao (2016), *Experimental efficiency analysis of sugarcane bagasse boilers…* (JBSMS) | **ensaios de seis caldeiras a bagaço** em usinas de SP pelo método indireto (ASME PTC 4); umidade 52–55%; perda nos gases 4,6–7,3% | **perda nos gases e método indireto (E1–E7)** contra resultados publicados | link.springer.com/article/10.1007/s40430-016-0590-y |
| 5 | Sosa-Arnao e Nebra, *A method for exergy analysis of sugarcane bagasse boilers* (Braz. J. Chem. Eng.) | caldeira **Zanini/Foster-Wheeler de 80 t/h** perto de Campinas, com medições do ensaio | entalpias, combustão e balanço de um ensaio | scielo.br (BJCE) |
| 6 | *Wet scrubbers coupled to bagasse-fired boilers: a case study in the Brazilian sugarcane industry* (Clean Technol. Environ. Policy, 2021) | indicadores da caldeira **ao longo de uma safra**; média de 114,8 t/h de bagaço com 46,8% de umidade | consumo e umidade numa safra (depende das tabelas) | link.springer.com/article/10.1007/s10098-021-02139-3 |
| 7 | Arnoni, K., dissertação (UNESP Ilha Solteira, NUPLEN) | tabelas de moagem, produção e consumo de bagaço na safra e na entressafra | consumo de bagaço × produção | feis.unesp.br (PDF) |
| 8 | Silva, R. M. (2016), caldeira de recuperação química (UNESP Guaratinguetá) | dados de operação de **2015 e 2016** | vapor e combustível de uma caldeira de recuperação (fora do foco biomassa) | repositorio.unesp.br |
| 9 | Outros trabalhos de usinas e agroindústrias: IFMG (histórico de operação com consumo de combustível), UFPB (Agroval), UFAL (várias caldeiras), UTFPR (aumento de geração de vapor), UNISC (lenha num frigorífico) | médias ou históricos curtos | conferências pontuais | ver links na conversa de 05/10 |

## Dados abertos do governo (reais, mas parciais)

- **ONS — Geração por usina em base horária** (dados.ons.org.br): geração elétrica hora a
  hora de cada usina, inclusive termelétricas a bagaço. Real e completo no tempo, mas **só a
  energia elétrica**: sem combustível nem vapor.
- **IBAMA — RAPP** (dadosabertos.ibama.gov.br): relatórios anuais por empresa, com consumo
  de lenha e cavaco. Real, mas **anual**.

Servem como conferência de ordem de grandeza, não como validação da cadeia combustível → vapor.

## Para continuar

Liberar o acesso de rede do ambiente (nível de acesso completo, ou personalizado com os
domínios abaixo) e repetir a conferência, na ordem da tabela:

```
revistas.fca.unesp.br  repositorio.roca.utfpr.edu.br  repositorio.utfpr.edu.br
repositorio.ufu.br  link.springer.com  www.scielo.br  www.feis.unesp.br
repositorio.unesp.br  dados.ons.org.br  dadosabertos.ibama.gov.br  doi.org
www.researchgate.net  www.academia.edu
```

Para cada fonte: confirmar se há **série** (não só médias), as variáveis e unidades, o
período e a **licença**. Só entra no repositório o que a licença permite, marcado como dado
público real; o resto fica como roteiro de download, com os resultados derivados.

Mesmo o melhor caso público dificilmente terá estoque do pátio, incerteza dos instrumentos
e eventos registrados. O piloto com uma planta autorizada continua sendo a validação completa.
