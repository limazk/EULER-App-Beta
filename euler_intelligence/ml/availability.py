"""Estado público do ML da EULER v3: sem previsões até validação independente."""

from dataclasses import dataclass


@dataclass(frozen=True)
class EstadoML:
    """Disponibilidade do módulo, sem probabilidade ou resultado inventado."""

    habilitado: bool
    modelo: str | None
    mensagem: str


def disponibilidade() -> EstadoML:
    """ML permanece inativo até aprovação e testes com dados adequados."""
    return EstadoML(
        habilitado=False,
        modelo=None,
        mensagem="Machine Learning experimental ainda não validado nem habilitado.",
    )
