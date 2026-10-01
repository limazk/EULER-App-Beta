from pathlib import Path

from euler.textos import RODAPE_SEGURANCA

RAIZ = Path(__file__).resolve().parents[1]


def test_rodape_igual_ao_documento_de_visao():
    doc = (RAIZ / "docs" / "visao_produto.md").read_text(encoding="utf-8")
    secao = doc.split("## Rodapé de segurança", 1)[1]
    citacao = next(linha for linha in secao.splitlines() if linha.startswith("> "))
    assert RODAPE_SEGURANCA == citacao.removeprefix("> ").strip()
