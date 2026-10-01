# Arquivos sintéticos com problemas de propósito

Dados **sintéticos**. Cada arquivo tem um exemplo de cada problema que o importador
deve detectar (T03, T05). Usados em `tests/test_importacao.py` e no botão
"Exemplo com problemas" da tela **Importar dados**.

| Arquivo | Linha | Problema plantado |
|---|---|---|
| diario.csv | 5 | duplicata exata da linha 4 |
| diario.csv | 6 | t_gases_c = 455 (parece kelvin) |
| diario.csv | 7 | o2_seco_pct = 0,081 (fração em vez de %) |
| diario.csv | 8 | anotada 8 h depois da observação (registro tardio) |
| diario.csv | 9 | 14 h sem leituras antes desta linha (lacuna); instrumento ANALIS-02 sem cadastro |
| diario.csv | 10 | totalizador volta de 15.511,3 t para 12,4 t (reiniciado) |
| diario.csv | 11 | p_vapor_bar_man = 900 (parece kPa) |
| diario.csv | 12 | t_gases_c = "abc" (ilegível) |
| diario.csv | 13–14 | mesmo instante com valores diferentes (conflito) |
| diario.csv | 15 | instrumento indisponível, t_gases_c vazio |
| diario.csv | 16 | data dia/mês/ano sem fuso |
| combustivel.csv | 4 | volume sem densidade |
| combustivel.csv | 5 | massa estimada por volume × densidade |
| combustivel.csv | 6 | sem fornecedor; 28 kg (parece toneladas) |
| combustivel.csv | 7 | lote L-0001 repetido |
| combustivel.csv | 8 | sem preço |
| amostras.csv | 3 | umidade 38 (parece %) |
| amostras.csv | 4 | lote L-0009 não existe em combustivel.csv |
| amostras.csv | 5 | composição incompleta |
