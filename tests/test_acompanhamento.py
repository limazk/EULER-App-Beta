"""Investigações acompanhadas, intervenções e verificação posterior (D94), painel (D95).

Casos: intervenção sem dados, resultados positivo, negativo e inconclusivo, mudança
concomitante, ausência de dupla contagem, persistência dos ganhos e agrupamento."""

import pytest
from construtor_caso import Periodo, montar

from euler.acompanhamento import (
    abrir_do_fechamento,
    adicionar_evidencia,
    adotar_referencia_pos_intervencao,
    avaliar_intervencao,
    encerrar,
    investigacao,
    mudar_estado,
    registrar_intervencao,
)
from euler.armazem import ErroArmazem, criar_planta
from euler.fechamento import criar_referencia, produzir_fechamento
from euler.painel import fila_de_atencao, painel
from euler.periodos import periodos_entre_estoques
from euler.relatorio import comandos_operacionais

G11, G12 = 11.049, 19.047
EQ = "CALD-T"


def quente(carga=10.0):
    return Periodo(G12, t_gases_c=292.2, umidade=0.3104, vapor_t_h=carga)


def frio(carga=10.0):
    return Periodo(G11, t_gases_c=180, umidade=0.3104, vapor_t_h=carga)


def planta_com(tmp_path, periodos, n_ref):
    pacote, _ = montar(periodos)
    a = criar_planta("Usina", "sintetico", raiz=tmp_path)
    a.criar_equipamento(EQ, "Caldeira", config={"altitude_m": 0})
    a.confirmar(
        a.previa(EQ, {f"{k}.csv": v for k, v in pacote._arquivos_teste.items()}), autor="Ana"
    )
    s = periodos_entre_estoques(a.pacote(EQ))
    criar_referencia(a, EQ, s[0][0], s[n_ref - 1][1], "inicial", "Base", "Ana")
    return a, s


def textos(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from textos(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from textos(v)


@pytest.fixture
def melhora(tmp_path):
    """Gases quentes na referência (3 períodos, carga variando um pouco), limpeza, gases
    frios depois (2 períodos, carga dentro da faixa da referência)."""
    a, s = planta_com(
        tmp_path, [quente(9.5), quente(10.5), quente(10.0), frio(10.0), frio(10.2)], 3
    )
    return a, s


def test_intervencao_sem_dados_depois_nao_preenche_economia(tmp_path):
    a, s = planta_com(tmp_path, [frio(), frio()], 2)
    it = registrar_intervencao(
        a,
        EQ,
        s[1][1],
        "limpeza",
        "Limpeza do economizador",
        "Ana",
        custo_brl=3000,
        custo_origem="nota fiscal",
    )
    av = avaliar_intervencao(a, it["id"], "Ana")["resultado"]
    assert av["resultado"] == "nao_avaliavel"
    assert av["economia_verificada"] is None and av["melhoria_associada"] is None
    assert av["diferenca_observada"] is None and "faltam" in av["frase"]


def test_resultado_positivo_separa_diferenca_melhoria_e_economia(melhora):
    a, s = melhora
    it = registrar_intervencao(
        a,
        EQ,
        s[3][0],
        "limpeza",
        "Limpeza das superfícies de troca",
        "Ana",
        custo_brl=5000,
        custo_origem="nota fiscal",
    )
    av = avaliar_intervencao(a, it["id"], "Ana")["resultado"]
    assert av["resultado"] == "positivo"
    assert av["diferenca_observada"]["desvio_estado"] == "abaixo"
    m = av["melhoria_associada"]
    assert m["custo_brl"] > 0 and m["faixa_brl"][0] > 0 and "não prova" in m["nota"]
    ev = av["economia_verificada"]
    assert ev["valor_brl"] == pytest.approx(m["custo_brl"])
    assert ev["beneficio_liquido_brl"] == pytest.approx(m["custo_brl"] - 5000)
    assert "proposto" in ev["protocolo"]
    assert not comandos_operacionais(" ".join(textos(av)))


def test_resultado_negativo_e_inconclusivo_sao_preservados(tmp_path):
    a, s = planta_com(tmp_path, [frio(9.5), frio(10.5), frio(10.0), quente(10.0), quente(10.2)], 3)
    it = registrar_intervencao(a, EQ, s[3][0], "calibracao", "Troca do analisador", "Ana")
    neg = avaliar_intervencao(a, it["id"], "Ana")["resultado"]
    assert neg["resultado"] == "negativo" and neg["economia_verificada"] is None

    b, t = planta_com(
        tmp_path / "b", [frio(9.5), frio(10.5), frio(10.0), frio(10.0), frio(10.2)], 3
    )
    it2 = registrar_intervencao(b, EQ, t[3][0], "calibracao", "Calibração do termopar", "Ana")
    inc = avaliar_intervencao(b, it2["id"], "Ana")["resultado"]
    assert inc["resultado"] == "inconclusivo" and inc["melhoria_associada"] is None


def test_outra_intervencao_na_janela_impede_associacao(melhora):
    a, s = melhora
    it = registrar_intervencao(a, EQ, s[3][0], "limpeza", "Limpeza", "Ana")
    registrar_intervencao(a, EQ, s[4][0], "mudanca_combustivel", "Novo fornecedor", "Ana")
    av = avaliar_intervencao(a, it["id"], "Ana")["resultado"]
    assert av["resultado"] == "inconclusivo"
    assert av["melhoria_associada"] is None and av["economia_verificada"] is None
    assert any("outra intervenção" in m for m in av["comparabilidade"]["motivos"])


def test_mudanca_concomitante_declarada_impede_associacao(melhora):
    a, s = melhora
    it = registrar_intervencao(
        a, EQ, s[3][0], "limpeza", "Limpeza", "Ana", concomitantes=["troca do queimador"]
    )
    av = avaliar_intervencao(a, it["id"], "Ana")["resultado"]
    assert av["resultado"] == "inconclusivo" and av["economia_verificada"] is None


def test_painel_nao_conta_duas_vezes(melhora):
    a, s = melhora
    it = registrar_intervencao(
        a, EQ, s[3][0], "limpeza", "Limpeza", "Ana", custo_brl=5000, custo_origem="nota"
    )
    v1 = avaliar_intervencao(a, it["id"], "Ana")["resultado"]["economia_verificada"]["valor_brl"]
    avaliar_intervencao(a, it["id"], "Ana")  # reavaliar não soma de novo
    p = painel(a, EQ)
    assert len(p["verificado"]["itens"]) == 1
    assert p["verificado"]["total_brl"] == pytest.approx(v1)
    assert p["verificado"]["beneficio_liquido_brl"] == pytest.approx(v1 - 5000)
    assert "não um valor atribuído à EULER" in p["verificado"]["nota"]


def test_janelas_sobrepostas_nao_somam():
    from euler.painel import _janelas_sobrepostas

    itens = [
        {"intervencao_id": 1, "periodo": {"inicio": "2026-01-01", "fim": "2026-02-01"}},
        {"intervencao_id": 2, "periodo": {"inicio": "2026-01-15", "fim": "2026-03-01"}},
        {"intervencao_id": 3, "periodo": {"inicio": "2026-04-01", "fim": "2026-05-01"}},
    ]
    assert _janelas_sobrepostas(itens) == {1, 2}


def test_persistencia_detecta_nova_deterioracao_sem_inventar_economia(tmp_path):
    a, s = planta_com(
        tmp_path,
        [quente(9.5), quente(10.5), quente(10.0), frio(10.0), frio(10.2), frio(10.1), quente(10.0)],
        3,
    )
    it = registrar_intervencao(a, EQ, s[3][0], "limpeza", "Limpeza", "Ana")
    av = avaliar_intervencao(a, it["id"], "Ana")["resultado"]
    assert av["resultado"] == "positivo"
    per = av["diferenca_observada"]["periodo_depois"]
    assert per["fim"] == s[6][1].isoformat()  # usou todos os períodos válidos depois
    # adota a referência depois da limpeza só com os dois primeiros períodos frios
    ref = criar_referencia(
        a,
        EQ,
        s[3][0],
        s[4][1],
        "estrutural",
        "Depois da limpeza #1",
        "Ana",
        intervencao_id=it["id"],
    )
    assert ref["versao"] == 2
    mantido = produzir_fechamento(a, EQ, "Ana", s[5][0], s[5][1])
    assert "compatível" in mantido["resultado"]["contexto"]["persistencia"]
    assert "não é 'economia preservada'" in mantido["resultado"]["contexto"]["persistencia"]
    piora = produzir_fechamento(a, EQ, "Ana", s[6][0], s[6][1])
    assert "Nova deterioração detectável" in piora["resultado"]["contexto"]["persistencia"]


def test_adotar_referencia_exige_avaliacao(melhora):
    a, s = melhora
    it = registrar_intervencao(a, EQ, s[3][0], "limpeza", "Limpeza", "Ana")
    with pytest.raises(ErroArmazem, match="Avalie"):
        adotar_referencia_pos_intervencao(a, it["id"], "Ana", "nova condição")
    avaliar_intervencao(a, it["id"], "Ana")
    ref = adotar_referencia_pos_intervencao(a, it["id"], "Ana", "nova condição")
    assert ref["tipo"] == "estrutural" and ref["intervencao_id"] == it["id"]


def test_fluxo_da_investigacao_com_estados_e_agrupamento(tmp_path):
    a, s = planta_com(tmp_path, [frio(9.5), frio(10.5), quente(10.0), quente(10.1)], 2)
    f1 = produzir_fechamento(a, EQ, "Ana", s[2][0], s[2][1])
    assert f1["resultado"]["situacao"] == "acima"
    inv = abrir_do_fechamento(a, f1["id"], "Ana", responsavel="Bruno")
    assert inv["estado"] == "em_investigacao" and inv["responsavel"] == "Bruno"
    assert inv["dados"]["hipoteses"] and inv["dados"]["proxima_verificacao"]["acao"]
    f2 = produzir_fechamento(a, EQ, "Ana")
    mesma = abrir_do_fechamento(a, f2["id"], "Ana")
    assert mesma["id"] == inv["id"]  # mesma hipótese: ocorrência agrupada
    assert sum(e["tipo"] in ("criada", "ocorrencia") for e in mesma["eventos"]) == 2
    with pytest.raises(ErroArmazem, match="Não é possível"):
        mudar_estado(a, inv["id"], "em_verificacao", "Ana", "pular etapa")
    adicionar_evidencia(
        a, inv["id"], "Termômetro de referência confirmou 290 °C", "Bruno", "OS 4512"
    )
    it = registrar_intervencao(
        a, EQ, s[3][1], "limpeza", "Limpeza", "Bruno", investigacao_id=inv["id"]
    )
    assert investigacao(a, inv["id"])["estado"] == "acao_registrada"
    avaliar_intervencao(a, it["id"], "Bruno")  # sem dados depois: não muda para verificação
    assert investigacao(a, inv["id"])["estado"] == "acao_registrada"
    with pytest.raises(ErroArmazem):
        encerrar(a, inv["id"], "inconclusiva", "", "Bruno")
    fim = encerrar(a, inv["id"], "inconclusiva", "Sem período depois da limpeza ainda", "Bruno")
    assert fim["estado"] == "encerrada" and fim["dados"]["resultado"] == "inconclusiva"
    reaberta = mudar_estado(a, inv["id"], "em_investigacao", "Bruno", "novos dados chegaram")
    assert reaberta["estado"] == "em_investigacao"
    tipos = [e["tipo"] for e in reaberta["eventos"]]
    assert tipos.count("estado") >= 2 and "evidencia" in tipos and "acao" in tipos


def test_fila_de_atencao_explica_criterios_e_nao_esconde_ocorrencias(tmp_path):
    a, s = planta_com(tmp_path, [frio(9.5), frio(10.5), quente(10.0), quente(10.1)], 2)
    produzir_fechamento(a, EQ, "Ana", s[2][0], s[2][1])
    f2 = produzir_fechamento(a, EQ, "Ana")
    fila = fila_de_atencao(a, EQ)
    assert fila[0]["categoria"] == "desvio_persistente"
    assert fila[0]["criterios"]["persistencia_fechamentos"] == 2
    abrir_do_fechamento(a, f2["id"], "Ana")
    fila = fila_de_atencao(a, EQ)
    cats = [i["categoria"] for i in fila]
    assert "investigacao_aberta" in cats
    # a oportunidade que virou investigação aparece agrupada lá, não duplicada
    assert not any(i["categoria"] == "oportunidade" and "chaminé" in i["titulo"] for i in fila)
    assert [i["ordem"] for i in fila] == list(range(1, len(fila) + 1))


def test_nao_abre_investigacao_sem_desvio_nem_hipotese(tmp_path):
    a, _ = planta_com(tmp_path, [frio(9.5), frio(10.5), frio(10.0)], 2)
    f = produzir_fechamento(a, EQ, "Ana")
    assert f["resultado"]["situacao"] == "nao_estabelecido"
    assert not [
        o for o in f["resultado"]["nucleo"]["oportunidades"] if o["prioridade"] in ("alta", "media")
    ]
    with pytest.raises(ErroArmazem, match="não há o que investigar"):
        abrir_do_fechamento(a, f["id"], "Ana")
