"""Tokens da identidade visual EULER v3, escolhida para a interface escura.

A cor é somente apoio visual; status operacionais exigem texto e evidência.
Nenhuma cor transforma uma medição em diagnóstico.
"""

from dataclasses import dataclass
from typing import Literal

StatusVisual = Literal["normal", "alerta", "atencao", "indisponivel"]


@dataclass(frozen=True)
class Paleta:
    """Cores visuais estáticas; não são limiares científicos."""

    fundo: str = "#080C0E"
    lateral: str = "#090D0F"
    cartao: str = "#141A1C"
    hover: str = "#1D2528"
    borda: str = "#293136"
    texto: str = "#F2F5F3"
    secundario: str = "#9AA6A1"
    verde: str = "#31D877"
    vermelho: str = "#EB4B56"
    ambar: str = "#E8B33D"


ESCURO = Paleta()


def cor_do_estado(estado: StatusVisual) -> str:
    """Retorna a cor semântica de um estado previamente determinado pelos dados.

    Esta função não classifica sensores, valores, eficiência nem condição de segurança.
    """
    cores = {
        "normal": ESCURO.verde,
        "alerta": ESCURO.vermelho,
        "atencao": ESCURO.ambar,
        "indisponivel": ESCURO.secundario,
    }
    try:
        return cores[estado]
    except KeyError as exc:
        raise ValueError(f"Estado visual desconhecido: {estado}") from exc
