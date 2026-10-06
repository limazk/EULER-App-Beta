"""Percurso financeiro com dados carregados: conclusão e próximo passo legíveis."""

from test_app import abrir_com_demo


def test_financeiro_expoe_ponte_e_separa_compras_do_periodo():
    at = abrir_com_demo("financeiro.py")
    assert not at.exception, at.exception
    assert at.radio(key="fin_origem").value == "Dados desta sessão"
    textos = " ".join(m.value for m in at.markdown)
    assert "Por que o custo mudou" in textos
    assert "Oportunidade fundamentada" in textos
    assert "Economia verificada" in textos
    assert "Compras e estoque no período" in textos
    assert any("não é pagamento" in c.value for c in at.caption)
    assert any(e.label == "Todos os recebimentos carregados" for e in at.expander)
    metricas = {m.label: m.value for m in at.metric}
    assert "Preço do combustível" in metricas
    assert "Produção e ajustes disponíveis" in metricas
    assert metricas["Pagamento confirmado"] == "Não informado"


def test_financeiro_sem_preco_nao_apresenta_zero_ou_economia():
    import io

    import pandas as pd

    at = abrir_com_demo("financeiro.py")
    arquivos = dict(at.session_state["arquivos"])
    df = pd.read_csv(io.BytesIO(arquivos["combustivel.csv"]))
    df["preco_brl"] = None
    arquivos["combustivel.csv"] = df.to_csv(index=False).encode()
    at.session_state["arquivos"] = tuple(sorted(arquivos.items()))
    at.run()
    assert not at.exception, at.exception
    assert any(
        "Valor dos recebimentos" == m.label and m.value == "Não informado" for m in at.metric
    )
    assert any("Preço do combustível" in c.value for c in at.caption)
