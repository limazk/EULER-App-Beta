"""Fechamento recorrente (D93): referência versionada sem absorver piora, política de custo
explícita, compra ≠ consumo, preço sem mudança de desempenho, produção sem falso
desperdício, reprodução e comparação com o fechamento anterior."""

import pandas as pd
import pytest
from construtor_caso import Periodo, montar

from euler.armazem import ErroArmazem, criar_planta
from euler.fechamento import (
    criar_referencia,
    fechamentos,
    periodos_pendentes,
    preco_do_periodo,
    produzir_fechamento,
    referencias,
    registrar_preco,
    reproduzir,
)
from euler.periodos import periodos_entre_estoques
from euler.relatorio import comandos_operacionais

G01, G11, G12 = 11.773, 11.049, 19.047
EQ = "CALD-T"


def planta_com(tmp_path, periodos, nome="Usina", arquivos_extra=None):
    pacote, _ = montar(periodos)
    arqs = {f"{k}.csv": v for k, v in pacote._arquivos_teste.items()}
    arqs.update(arquivos_extra or {})
    a = criar_planta(nome, "sintetico", raiz=tmp_path)
    a.criar_equipamento(EQ, "Caldeira", config={"altitude_m": 0})
    a.confirmar(a.previa(EQ, arqs), autor="Ana")
    return a, periodos_entre_estoques(a.pacote(EQ))


def componente(f, ident):
    v = f["resultado"]["nucleo"]["explicacao_conta"]["variacao"]
    return next(x for x in v["componentes"] if x["id"] == ident)


def test_referencia_versionada_e_regras_de_tipo(tmp_path):
    a, s = planta_com(tmp_path, [Periodo(G01), Periodo(G01), Periodo(G01)])
    with pytest.raises(ErroArmazem, match="inicial"):
        criar_referencia(a, EQ, s[0][0], s[0][1], "estrutural", "x", "Ana")
    with pytest.raises(ErroArmazem, match="medições de estoque"):
        criar_referencia(a, EQ, s[0][0] + pd.Timedelta(hours=1), s[0][1], "inicial", "x", "Ana")
    v1 = criar_referencia(a, EQ, s[0][0], s[0][1], "inicial", "Janeiro", "Ana")
    with pytest.raises(ErroArmazem, match="Já existe"):
        criar_referencia(a, EQ, s[1][0], s[1][1], "inicial", "x", "Ana")
    v2 = criar_referencia(a, EQ, s[1][0], s[1][1], "correcao_de_dados", "estoque corrigido", "Ana")
    assert (v1["versao"], v2["versao"]) == (1, 2)
    assert [r["versao"] for r in referencias(a, EQ)] == [1, 2]
    assert referencias(a, EQ)[0]["dados"] == v1["dados"]  # versão anterior intocada


def test_nova_referencia_nao_absorve_piora_em_silencio(tmp_path):
    a, s = planta_com(tmp_path, [Periodo(G11, t_gases_c=180), Periodo(G12, t_gases_c=292.2)])
    criar_referencia(a, EQ, s[0][0], s[0][1], "inicial", "Base", "Ana")
    with pytest.raises(ErroArmazem, match="esconderia essa piora"):
        criar_referencia(a, EQ, s[1][0], s[1][1], "correcao_de_dados", "x", "Ana")
    with pytest.raises(ErroArmazem, match="esconderia essa piora"):
        criar_referencia(a, EQ, s[1][0], s[1][1], "estrutural", "troca do economizador", "Ana")
    v2 = criar_referencia(
        a,
        EQ,
        s[1][0],
        s[1][1],
        "estrutural",
        "troca do economizador",
        "Ana",
        confirmar_absorcao=True,
    )
    assert v2["dados"]["absorve_piora_pct"] > 5


def test_mudanca_de_preco_sem_mudanca_de_desempenho(tmp_path):
    a, s = planta_com(tmp_path, [Periodo(G01, preco_brl_t=180), Periodo(G01, preco_brl_t=220)])
    criar_referencia(a, EQ, s[0][0], s[0][1], "inicial", "Base", "Ana")
    f = produzir_fechamento(a, EQ, "Ana")
    assert f["resultado"]["situacao"] == "nao_estabelecido"
    preco = componente(f, "preco")["custo_brl"]
    desvio = componente(f, "nao_explicado")["custo_brl"]
    assert preco > 0 and abs(desvio) < 0.05 * preco


def test_mudanca_de_producao_sem_falso_desperdicio(tmp_path):
    a, s = planta_com(tmp_path, [Periodo(G01, vapor_t_h=10), Periodo(G01, vapor_t_h=14)])
    criar_referencia(a, EQ, s[0][0], s[0][1], "inicial", "Base", "Ana")
    f = produzir_fechamento(a, EQ, "Ana")
    producao = componente(f, "producao")["custo_brl"]
    desvio = componente(f, "nao_explicado")["custo_brl"]
    assert f["resultado"]["situacao"] == "nao_estabelecido"
    assert producao > 0 and abs(desvio) < 0.05 * producao


def test_compra_diferente_de_consumo(tmp_path):
    """Um lote extra chega no período e fica no pátio: recebido > consumido; o custo
    atribuído segue o consumo, não a compra."""
    pacote, lim = montar([Periodo(G01), Periodo(G01)])
    texto = pacote._arquivos_teste["combustivel"].decode().splitlines()
    fim = lim[1][1]
    extra = f"{(lim[1][0] + (fim - lim[1][0]) / 2).isoformat()},recebimento,F1,EXTRA,50000,9000.00,sintetico"
    ultimo = texto[-1].split(",")
    ultimo[4] = str(float(ultimo[4]) + 50000)  # estoque final cresce com o lote extra
    texto = [*texto[:-1], extra, ",".join(ultimo)]
    a, s = planta_com(
        tmp_path,
        [Periodo(G01), Periodo(G01)],
        arquivos_extra={"combustivel.csv": "\n".join(texto).encode()},
    )
    criar_referencia(a, EQ, s[0][0], s[0][1], "inicial", "Base", "Ana")
    f = produzir_fechamento(a, EQ, "Ana")
    cp = f["resultado"]["nucleo"]["conta_do_periodo"]
    assert cp["recebido_t"] == pytest.approx(cp["consumido_t"] + 50, rel=1e-6)
    assert cp["estoque_final_t"] - cp["estoque_inicial_t"] == pytest.approx(50)
    preco = f["resultado"]["nucleo"]["politica_custo"]["preco_brl_t"]
    assert cp["custo_atribuido_brl"] == pytest.approx(cp["consumido_t"] * preco)
    assert (
        cp["despesa_ou_pagamento"] is None and "não é o que saiu do caixa" in cp["nota_pagamento"]
    )
    assert f["resultado"]["situacao"] == "nao_estabelecido"


def test_politica_de_custo_explicita_sem_troca_silenciosa(tmp_path):
    a, s = planta_com(tmp_path, [Periodo(G01, preco_brl_t=180), Periodo(G01, preco_brl_t=200)])
    pacote = a.pacote(EQ)
    sem_tabela = preco_do_periodo(a, EQ, pacote, s[1][0], s[1][1], "tabela_de_precos")
    assert sem_tabela["preco_brl_t"] is None and "Nenhum preço" in sem_tabela["motivo"]
    registrar_preco(
        a,
        EQ,
        "cavaco",
        190.0,
        s[0][0],
        "contrato 2026",
        "Ana",
        custo_adicional_brl_t=15.0,
        custo_adicional_desc="frete",
    )
    tabela = preco_do_periodo(a, EQ, pacote, s[1][0], s[1][1], "tabela_de_precos")
    assert (
        tabela["preco_brl_t"] == pytest.approx(205.0) and tabela["custo_adicional_desc"] == "frete"
    )
    registrar_preco(a, EQ, "serragem", 120.0, s[0][0], "cotação", "Ana")
    duas = preco_do_periodo(a, EQ, pacote, s[1][0], s[1][1], "tabela_de_precos")
    assert duas["preco_brl_t"] is None and "rateio" in duas["motivo"]
    # FIFO: o 1º período não tem lotes anteriores para o estoque inicial; o 2º tem
    assert preco_do_periodo(a, EQ, pacote, s[0][0], s[0][1], "fifo")["preco_brl_t"] is None
    fifo = preco_do_periodo(a, EQ, pacote, s[1][0], s[1][1], "fifo")["preco_brl_t"]
    media = preco_do_periodo(a, EQ, pacote, s[1][0], s[1][1], "recebimentos_do_periodo")[
        "preco_brl_t"
    ]
    assert 180 < fifo < 200 and media == pytest.approx(200, rel=1e-3)
    a.configurar(EQ, {"politica_custo": "tabela_de_precos"}, autor="Ana")
    criar_referencia(a, EQ, s[0][0], s[0][1], "inicial", "Base", "Ana")
    f = produzir_fechamento(a, EQ, "Ana")
    assert f["resultado"]["nucleo"]["politica_custo"]["preco_brl_t"] is None
    assert f["resultado"]["nucleo"]["conta_do_periodo"]["custo_atribuido_brl"] is None
    assert f["resultado"]["nucleo"]["custo_por_energia"]["periodo_brl_gj"] is None
    assert all(
        o["impacto_brl"] is None and o["faixa_brl"] is None
        for o in f["resultado"]["nucleo"]["oportunidades"]
    )


def test_fechamento_reproduzivel_mesmo_depois_de_correcao(tmp_path):
    a, s = planta_com(tmp_path, [Periodo(G01), Periodo(G01), Periodo(G01)])
    criar_referencia(a, EQ, s[0][0], s[0][1], "inicial", "Base", "Ana")
    f = produzir_fechamento(a, EQ, "Ana", s[1][0], s[1][1])
    chave = next(iter(a._ativos(EQ, "diario")))
    a.corrigir(EQ, "diario", chave, {"t_gases_c": 400.0}, "teste", "Ana")
    r = reproduzir(a, f["id"])
    assert r["identico"] and r["dados_identicos"] and r["mesmo_codigo"]
    v2 = criar_referencia(a, EQ, s[2][0], s[2][1], "correcao_de_dados", "teste", "Ana")
    outra = reproduzir(a, f["id"], referencia_id=v2["id"])
    assert not outra["mesma_referencia"] and "v2" in outra["frase"]


def test_comparacao_com_o_anterior_e_sem_dados_novos(tmp_path):
    a, s = planta_com(tmp_path, [Periodo(G01), Periodo(G01), Periodo(G01)])
    criar_referencia(a, EQ, s[0][0], s[0][1], "inicial", "Base", "Ana")
    f1 = produzir_fechamento(a, EQ, "Ana", s[1][0], s[1][1])
    assert f1["resultado"]["comparacao_anterior"]["existe"] is False
    f2 = produzir_fechamento(a, EQ, "Ana")
    assert (f2["inicio"], f2["fim"]) == (s[2][0].isoformat(), s[2][1].isoformat())
    comp = f2["resultado"]["comparacao_anterior"]
    assert comp["comparavel"] and comp["fechamento_id"] == f1["id"]
    assert "Situação mantida" in comp["frase"]
    with pytest.raises(ErroArmazem, match="não tem dados novos"):
        produzir_fechamento(a, EQ, "Ana")
    assert len(fechamentos(a, EQ)) == 2


def test_periodo_sem_vapor_e_fechado_sozinho_com_o_motivo(tmp_path):
    a, s = planta_com(tmp_path, [Periodo(G01), Periodo(G01, totalizador=False), Periodo(G01)])
    criar_referencia(a, EQ, s[0][0], s[0][1], "inicial", "Base", "Ana")
    pend = periodos_pendentes(a, EQ)
    assert [p["valido"] for p in pend] == [False, True]
    f = produzir_fechamento(a, EQ, "Ana")
    assert (f["inicio"], f["fim"]) == (s[1][0].isoformat(), s[1][1].isoformat())
    assert f["resultado"]["situacao"] is None
    assert "totalizador" in f["resultado"]["nucleo"]["explicacao_conta"]["motivo"]
    f2 = produzir_fechamento(a, EQ, "Ana")
    assert f2["resultado"]["situacao"] == "nao_estabelecido"
    assert "não pôde ser calculada" in f2["resultado"]["comparacao_anterior"]["frase"]


def test_relatorio_do_fechamento_vem_do_mesmo_objeto(tmp_path):
    from euler.painel import texto_fechamento

    a, s = planta_com(tmp_path, [Periodo(G01), Periodo(G01)])
    criar_referencia(a, EQ, s[0][0], s[0][1], "inicial", "Base", "Ana")
    f = produzir_fechamento(a, EQ, "Ana")
    texto = texto_fechamento(f)
    assert "Conta do período" in texto and "Desvio monetizado" in texto
    assert f["resultado"]["nucleo_sha"][:16] in texto
    assert "não é economia recuperável" in texto
    assert not comandos_operacionais(texto)


def test_relatorio_identifica_soma_parcial_de_notas(tmp_path):
    from euler.painel import texto_fechamento

    a, s = planta_com(tmp_path, [Periodo(G01), Periodo(G01)])
    criar_referencia(a, EQ, s[0][0], s[0][1], "inicial", "Base", "Ana")
    f = produzir_fechamento(a, EQ, "Ana")
    # O relatório deve respeitar a cobertura gravada, sem inferir o valor das notas ausentes.
    f["resultado"]["nucleo"]["conta_do_periodo"]["lotes_sem_valor"] = 1
    texto = texto_fechamento(f)
    assert "notas, valor parcial" in texto
    assert "1 lote(s) sem valor informado" in texto
    a.fechar()


def test_reproducao_congela_altitude_e_precos_do_fechamento(tmp_path):
    a, s = planta_com(tmp_path, [Periodo(G01), Periodo(G01)])
    a.configurar(EQ, {"politica_custo": "tabela_de_precos"}, autor="Ana")
    registrar_preco(a, EQ, "cavaco", 190.0, s[0][0], "Contrato original", "Ana")
    criar_referencia(a, EQ, s[0][0], s[0][1], "inicial", "Base", "Ana")
    f = produzir_fechamento(a, EQ, "Ana")
    conta = f["resultado"]["nucleo"]["explicacao_conta"]
    assert conta["entradas"]["politica_custo"] == "tabela_de_precos"
    assert conta["entradas"]["preco_ref_brl_gj"] is None
    assert conta["entradas"]["preco_brl_gj"] is None
    assert "tabela de preços" in conta["desvio"]["frase"]
    assert "média ponderada dos recebimentos" not in " ".join(conta["premissas"])
    assert f["resultado"]["nucleo"]["custo_por_energia"]["periodo_brl_gj"] is not None
    a.configurar(EQ, {"altitude_m": 1500.0}, autor="Ana")
    registrar_preco(a, EQ, "cavaco", 220.0, s[0][0], "Nova cotação", "Ana")
    r = reproduzir(a, f["id"])
    assert r["identico"] and r["dados_identicos"]
    assert r["nucleo"]["politica_custo"]["preco_brl_t"] == 190.0


def test_reproducao_antiga_sem_premissas_nao_adivinha_configuracao(tmp_path):
    from euler.armazem import jdump

    a, s = planta_com(tmp_path, [Periodo(G01), Periodo(G01)])
    criar_referencia(a, EQ, s[0][0], s[0][1], "inicial", "Base", "Ana")
    f = produzir_fechamento(a, EQ, "Ana")
    resultado = f["resultado"]
    resultado.pop("premissas_reproducao", None)
    with a._transacao() as cur:
        cur.execute("UPDATE fechamento SET resultado=? WHERE id=?", (jdump(resultado), f["id"]))
    r = reproduzir(a, f["id"])
    assert not r["identico"] and r["nucleo"] is None
    assert "configuração" in r["frase"]


@pytest.mark.parametrize("valor", [float("inf"), float("nan"), -1])
def test_preco_nao_finito_ou_negativo_nao_entra_no_banco(tmp_path, valor):
    a = criar_planta("Preço", "sintetico", raiz=tmp_path)
    a.criar_equipamento(EQ, "Caldeira")
    with pytest.raises(ErroArmazem):
        registrar_preco(a, EQ, "cavaco", valor, "2026-01-01", "Contrato", "Ana")
    assert a.con.execute("SELECT count(*) FROM preco").fetchone()[0] == 0
    a.fechar()


def test_referencia_nao_absorve_correcao_sem_nova_versao(tmp_path):
    a, s = planta_com(tmp_path, [Periodo(G01), Periodo(G01)])
    criar_referencia(a, EQ, s[0][0], s[0][1], "inicial", "Base", "Ana")
    chave = next(iter(a._ativos(EQ, "diario")))
    a.corrigir(EQ, "diario", chave, {"t_gases_c": 400}, "Calibração", "Ana")
    with pytest.raises(ErroArmazem, match="nova versão da referência"):
        produzir_fechamento(a, EQ, "Ana")
    assert not fechamentos(a, EQ)
    a.fechar()
