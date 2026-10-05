# Planta brasileira real: cervejaria em Viamão (RS), 660 dias

Registros diários públicos de duas caldeiras a biomassa (Bremer HBFR-4, 19 t/h cada) da
filial Águas Claras do Sul da AmBev, de 05/11/2007 a 25/08/2009, publicados pela ONU
(UNFCCC) no projeto 1202 do Mecanismo de Desenvolvimento Limpo (MDL). **Não é dado de
cliente e não implica participação, revisão ou validação da AmBev.**

## Arquivos

| Arquivo | O que é |
|---|---|
| `1202_CER_Calc_Sheet_Rev1.xls` | Planilha original publicada no pedido de emissão, **sem nenhuma alteração** (SHA-256 em `fontes.json`). |
| `diario.csv` | Extração das colunas diárias da aba "Emission Reduction Calculation", feita por `scripts/extrair_cervejaria.py`. Mesmos valores (o teste compara célula a célula), célula vazia continua vazia, número da linha original em cada registro. |
| `fontes.json` | URLs, SHA-256, termos de uso e os fatos documentados usados no caso, com página do PDF. |

Termos da UNFCCC: textos, dados e documentos oficiais são de domínio público e podem ser
copiados sem alteração do conteúdo, com a fonte citada. Por isso a planilha está aqui intacta
e a fonte aparece em cada tela.

## O que há por dia

Casca de arroz e de carvalho (t); para cada caldeira: horas de operação, pressão do vapor
(kgf/cm²), vapor (t, pela leitura diária do totalizador), entalpia e energia; óleo pesado e
sebo da caldeira reserva (t). **Não há:** estoque de casca, umidade ou PCI, temperatura da
água de alimentação, O₂ ou temperatura dos gases, preço da casca.

## O que a EULER faz (`app/ensaio_cervejaria.py`, aba "Planta brasileira · RS")

1. **Confere a planilha** sem corrigir nada: 660 dias seguidos, sem data repetida; as somas
   reproduzem os totais do relatório de verificação (218.123 t de vapor, 49.566 t de casca,
   1.530 t de óleo equivalente). Achados: 3 dias com o total diário em branco (805,79 t que
   somem se só essa coluna for somada), 1 dia com energia em branco, 7 registros acima de
   19 t/h × horas (até 165%), 31 dias sem vapor registrado (27 em fins de semana, 79 t de
   casca registradas neles).
2. **Classifica a coluna de casca:** num dia, a razão vapor/casca vai de 1,9 a 14,2 (90% dos
   dias); em 30 dias, de 4,1 a 4,8. A casca do dia não é a queimada no dia, e os documentos
   divergem sobre a origem dela (volume no galpão × densidade, no PDD; notas fiscais e
   balança, na verificação). Só somas longas são usadas, como **consumo aparente**.
3. **Física:** a entalpia do vapor saturado da planilha difere da IF97 da EULER em no máximo
   0,04%, com a pressão referida a 1 kgf/cm² absoluto (convenção da tabela da planilha). A
   planilha conta a energia desde 0 °C; a energia útil depende da água de alimentação, que
   não foi publicada, então a eficiência fica bloqueada.
4. **Pergunta:** a casca por tonelada de vapor mudou? Mesmo trecho do calendário nos dois
   anos (05/11 a 25/08): 0,2385 → 0,2182 t/t (−8,5%). Incerteza pelo orçamento GUM do motor:
   balança 2% sem tipo, lida como limite (u = 2%/√3, D35), por época de calibração (a época
   iniciada em 28/03/2008 vale nos dois períodos e é o mesmo erro, D37); estoque nas pontas e
   medidores de vapor entram como incertezas que **faltam**. Resultado: a diferença é maior
   que a parte conhecida (±0,0045 t/t, k = 2), mas **não fica estabelecida**.
5. **Explicações que continuam possíveis**, cada uma com a verificação que a separa: estoque
   (seria preciso ~1.700 t a mais no 1º período ou ~2.200 t a menos no 2º, 25 a 27 dias de
   consumo; o projeto descreve área para no mínimo 5 dias), umidade/PCI, carga (+26% no 2º
   período), medidores de vapor (+9,3% de leitura), balança e casca de carvalho.
6. **Sensibilidade:** metades do registro e trechos entre calibrações mostram o mesmo sentido.
   Isso tira a dependência da escolha do período, não mostra causa.

## O que este caso valida e o que não valida

- **Valida:** leitura de um registro industrial brasileiro real e longo; preservação de
  lacunas; conferência contra totais publicados por terceiro; detecção de registros
  impossíveis; distinção entre casca registrada e queimada; entalpia IF97 contra a tabela da
  planta; abstenção com a medição que separa as explicações.
- **Não valida:** eficiência, perda nos gases, valor em dinheiro nem causa. Faltam estoque,
  umidade/PCI, água de alimentação e preço. A validação completa continua dependendo de uma
  planta piloto autorizada.

## Como refazer

```
pip install -e ".[validacao]"          # xlrd, para ler a planilha .xls
python scripts/extrair_cervejaria.py   # regenera diario.csv (mesmo SHA-256)
pytest -q tests/test_ensaio_cervejaria.py
```

Os documentos do MDL estão atrás de uma checagem anti-robô: abra os links de `fontes.json`
num navegador.
