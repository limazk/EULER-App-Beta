"""Contratos preliminares de IA explicativa; sem conexão com provedores.

Somente identificadores de escopo e pergunta; a recuperação de evidências
dependerá de autenticação, autorização e avaliação técnica numa entrega futura.
"""

from dataclasses import dataclass
from typing import Literal

Situacao = Literal["desativado", "indisponivel", "pronto"]


@dataclass(frozen=True)
class PedidoExplicacao:
    """Referências da análise; sem dados brutos ou segredos no contrato inicial."""

    organizacao_id: str
    planta_id: str
    analise_id: str
    pergunta: str

    def __post_init__(self) -> None:
        for nome in ("organizacao_id", "planta_id", "analise_id", "pergunta"):
            valor = getattr(self, nome)
            if not isinstance(valor, str) or not valor.strip():
                raise ValueError(f"Campo obrigatório: {nome}")


@dataclass(frozen=True)
class RespostaExplicacao:
    """Resposta versionável, que não confunde indisponibilidade com análise."""

    situacao: Situacao
    provedor: str | None
    texto: str | None
    ids_evidencias: tuple[str, ...]
    mensagem: str
