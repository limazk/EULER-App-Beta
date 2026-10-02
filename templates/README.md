# Modelos para importar dados

[Início](../README.md) · [Contrato de dados](../docs/dados/contrato_dados.md)

Use a [planilha Excel](planilha_modelo_euler.xlsx) ou os cinco arquivos CSV:

| Arquivo | Registros |
|---|---|
| [diario.csv](diario.csv) | Leituras e condições da operação |
| [combustivel.csv](combustivel.csv) | Recebimentos e estoques de combustível |
| [amostras.csv](amostras.csv) | Características e amostras do combustível |
| [eventos.csv](eventos.csv) | Ocorrências, intervenções e verificações |
| [instrumentos.csv](instrumentos.csv) | Instrumentos e incertezas declaradas |

As linhas de exemplo são sintéticas. Confira unidades e campos obrigatórios no contrato.
Ausência de informação não deve ser preenchida com zero. Arquivos de clientes não devem
ser enviados ao repositório.

Para desenvolver o contrato, altere `euler/io/esquemas.py` e execute
`python scripts/gerar_modelos.py`. O contrato e a planilha são gerados a partir dessa fonte.
