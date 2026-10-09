"""Gateway fail-closed: IA generativa deliberadamente indisponível na EULER v3.

Não consulta ambiente, banco, modelo, rede ou arquivos do cliente. A escolha
entre IA local/online depende de uma decisão explícita e um PR independente.
"""

from euler_intelligence.contracts import PedidoExplicacao, RespostaExplicacao

VERSAO_CONTRATO = "euler-intelligence/0.1"


def explicar(_pedido: PedidoExplicacao) -> RespostaExplicacao:
    """Retorna indisponibilidade determinística sem executar inferência."""
    return RespostaExplicacao(
        situacao="desativado",
        provedor=None,
        texto=None,
        ids_evidencias=(),
        mensagem="EULER Intelligence não está habilitado. Nenhuma IA foi consultada.",
    )
