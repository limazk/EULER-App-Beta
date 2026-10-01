"""Tipos comuns do motor EULER."""

from typing import Literal

Origem = Literal["medido", "estimado", "assumido"]
"""Origem de um número mostrado ao usuário (AGENTS.md, estilo de texto)."""


class AnaliseBloqueada(Exception):
    """A análise não pode ser feita com os dados disponíveis (AGENTS.md, regra 4).

    Atributos:
        motivo: frase legível para o usuário final explicando o bloqueio.
        falta: o que precisaria ser medido ou informado para desbloquear.
    """

    def __init__(self, motivo: str, falta: list[str] | None = None):
        super().__init__(motivo)
        self.motivo = motivo
        self.falta = list(falta or [])
