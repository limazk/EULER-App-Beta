"""Textos fixos mostrados ao usuário final (app e relatórios).

O rodapé de segurança é obrigatório em todas as telas e relatórios
(docs/visao_produto.md, seção "Rodapé de segurança"). O teste
tests/test_textos.py garante que o texto daqui é idêntico ao do documento.
"""

RODAPE_SEGURANCA = (
    "Ferramenta de registro e apoio à investigação. Não emite comandos operacionais "
    "nem substitui procedimentos da instalação, alarmes, intertravamentos ou a "
    "avaliação do responsável técnico. Não é um Registro de Segurança conforme a NR-13."
)

FRASE_PRODUTO = "Quanto de energia a fábrica comprou, quanto virou vapor e onde o resto foi parar."

PERGUNTA_CENTRAL = (
    "O consumo de combustível mudou. O que os registros sustentam, quais explicações "
    "continuam possíveis e qual verificação separa essas explicações?"
)

AVISO_PROTOTIPO = (
    "Protótipo em construção (Fase 0). Todos os dados usados aqui são sintéticos ou públicos."
)
