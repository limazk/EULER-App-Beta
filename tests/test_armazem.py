"""Armazém da planta (D92): importação repetida sem duplicar, correções com histórico,
plantas e equipamentos separados, classe dos dados, perfis, cobertura, persistência após
reinicialização, cópia de segurança e restauração."""

from datetime import UTC, datetime

import pytest
from construtor_caso import Periodo, montar

from euler.armazem import (
    ErroArmazem,
    abrir_planta,
    cabecalho_csv,
    criar_planta,
    listar_plantas,
    restaurar_copia,
)
from euler.periodos import periodos_entre_estoques

G01 = 11.773
EQ = "CALD-T"


def arquivos_caso(*periodos):
    pacote, _ = montar(list(periodos) or [Periodo(G01), Periodo(G01)])
    return {f"{k}.csv": v for k, v in pacote._arquivos_teste.items()}


@pytest.fixture
def planta(tmp_path):
    a = criar_planta("Usina Teste", "sintetico", raiz=tmp_path)
    a.criar_equipamento(EQ, "Caldeira de teste")
    return a


def test_importacao_repetida_nao_duplica(planta):
    arqs = arquivos_caso()
    r1 = planta.confirmar(planta.previa(EQ, arqs), autor="Ana")
    n = len(planta.registros(EQ, "diario"))
    previa = planta.previa(EQ, arqs)
    contagem = previa.contagem()
    assert all(t["nova"] == 0 and t["conflito"] == 0 for t in contagem.values())
    assert contagem["diario"]["igual"] == n
    planta.confirmar(previa, autor="Ana")
    assert len(planta.registros(EQ, "diario")) == n
    assert r1["novas"] > 0


def test_valor_diferente_vira_conflito_e_correcao_guarda_o_original(planta):
    arqs = arquivos_caso()
    planta.confirmar(planta.previa(EQ, arqs), autor="Ana")
    texto = arqs["diario.csv"].decode()
    linhas = texto.splitlines()
    campos = linhas[1].split(",")
    campos[5] = "999.0"  # t_gases_c da primeira leitura
    linhas[1] = ",".join(campos)
    alterado = {"diario.csv": "\n".join(linhas).encode()}
    previa = planta.previa(EQ, alterado)
    conflitos = [x for x in previa.linhas if x.situacao == "conflito"]
    assert len(conflitos) == 1
    assert conflitos[0].diferencas["t_gases_c"]["novo"] == 999.0
    # incremental: nada é substituído em silêncio
    planta.confirmar(previa, autor="Ana")
    chave = conflitos[0].chave
    assert len(planta.historico(EQ, "diario", chave)) == 1
    pend = planta.conflitos(EQ)
    assert len(pend) == 1 and pend[0]["atual"]["t_gases_c"] != 999.0
    with pytest.raises(ErroArmazem):
        planta.resolver_conflito(pend[0]["id"], True, "Ana", "")
    planta.resolver_conflito(
        pend[0]["id"], True, "Ana", "Termopar recalibrado; valor do supervisório"
    )
    hist = planta.historico(EQ, "diario", chave)
    assert [h["versao"] for h in hist] == [1, 2]
    assert hist[0]["conteudo"]["t_gases_c"] != 999.0 and hist[0]["revisao_ate"] is not None
    assert hist[1]["conteudo"]["t_gases_c"] == 999.0 and hist[1]["motivo"]
    corr = [e for e in planta.eventos(EQ) if e["tipo"] == "correcao"]
    assert corr and corr[0]["dados"]["campos"]["t_gases_c"]["novo"] == 999.0
    assert planta.conflitos(EQ) == []


def test_importacao_de_correcao_exige_motivo(planta):
    arqs = arquivos_caso()
    planta.confirmar(planta.previa(EQ, arqs), autor="Ana")
    with pytest.raises(ErroArmazem):
        planta.confirmar(planta.previa(EQ, arqs), autor="Ana", modo="correcao")


def test_revisao_antiga_reconstroi_os_dados_de_antes_da_correcao(planta):
    arqs = arquivos_caso()
    r = planta.confirmar(planta.previa(EQ, arqs), autor="Ana")
    chave = next(iter(planta._ativos(EQ, "diario")))
    planta.corrigir(EQ, "diario", chave, {"t_gases_c": 300.0}, "teste de correção", "Ana")
    antes = {
        c["instante_observado"]: c["t_gases_c"]
        for c in planta.registros(EQ, "diario", r["revisao"])
    }
    agora = {c["instante_observado"]: c["t_gases_c"] for c in planta.registros(EQ, "diario")}
    assert antes != agora and 300.0 in agora.values() and 300.0 not in antes.values()
    assert planta.conjunto_sha(EQ, r["revisao"]) != planta.conjunto_sha(EQ)


def test_dados_de_outro_equipamento_e_de_outra_classe_sao_recusados(planta, tmp_path):
    arqs = arquivos_caso()
    planta.criar_equipamento("CALD-2", "Outra caldeira")
    previa = planta.previa("CALD-2", arqs)
    diario = [x for x in previa.linhas if x.tabela == "diario"]
    assert diario and all(x.situacao == "rejeitada" for x in diario)
    assert "não se misturam" in diario[0].motivo
    # planta de cliente não aceita linhas marcadas como sintéticas
    fora = tmp_path.parent / "dados_cliente"
    cliente = criar_planta(
        "Cliente X", "cliente_autorizado", raiz=fora, autorizacao="Contrato 12/2026"
    )
    cliente.criar_equipamento(EQ, "Caldeira")
    linhas = cliente.previa(EQ, arqs).linhas
    assert all(x.situacao == "rejeitada" for x in linhas)
    assert "nunca se misturam" in linhas[0].motivo


def test_plantas_ficam_em_arquivos_separados(tmp_path):
    a = criar_planta("Planta A", "sintetico", raiz=tmp_path)
    b = criar_planta("Planta B", "sintetico", raiz=tmp_path)
    for p in (a, b):
        p.criar_equipamento(EQ, "Caldeira")
    a.confirmar(a.previa(EQ, arquivos_caso()), autor="Ana")
    assert a.arquivo != b.arquivo
    assert a.registros(EQ, "diario") and not b.registros(EQ, "diario")
    assert {p["planta_id"] for p in listar_plantas(tmp_path)} == {"planta-a", "planta-b"}


def test_dados_de_cliente_exigem_autorizacao_e_ficam_fora_do_codigo(tmp_path):
    with pytest.raises(ErroArmazem, match="autorizou"):
        criar_planta("Cliente", "cliente_autorizado", raiz=tmp_path)
    from euler.armazem import RAIZ_CODIGO

    with pytest.raises(ErroArmazem, match="fora do repositório"):
        criar_planta("Cliente", "cliente_autorizado", raiz=RAIZ_CODIGO / "dados", autorizacao="x")


def test_perfil_de_importacao_mapeia_colunas_e_e_reutilizado(planta):
    arqs = arquivos_caso()
    texto = (
        arqs["diario.csv"]
        .decode()
        .replace("t_gases_c", "TempChamine")
        .replace("o2_seco_pct", "O2_analisador")
    )
    fonte = {"diario.csv": texto.encode()}
    assert "TempChamine" in cabecalho_csv(fonte["diario.csv"])
    mapa = {"TempChamine": "t_gases_c", "O2_analisador": "o2_seco_pct"}
    previa = planta.previa(EQ, fonte, fonte="supervisorio", mapeamento=mapa)
    planta.confirmar(previa, autor="Ana", salvar_perfil=True)
    assert planta.perfil(EQ, "supervisorio") == mapa
    gravado = planta.registros(EQ, "diario")[0]
    assert gravado["t_gases_c"] is not None and gravado["o2_seco_pct"] is not None
    # segunda vez: o perfil salvo é usado sem informar o mapeamento
    segunda = planta.previa(EQ, fonte, fonte="supervisorio")
    assert segunda.contagem()["diario"]["igual"] == len(planta.registros(EQ, "diario"))
    planta.confirmar(segunda, autor="Ana")
    assert planta.perfis(EQ)[0]["usos"] == 2


def test_mesma_chave_com_valores_diferentes_no_arquivo_nao_escolhe_nenhuma(planta):
    arqs = arquivos_caso()
    linhas = arqs["diario.csv"].decode().splitlines()
    copia = linhas[1].split(",")
    copia[5] = "250.0"
    alterado = "\n".join([*linhas[:2], ",".join(copia), *linhas[2:]])
    previa = planta.previa(EQ, {"diario.csv": alterado.encode()})
    rejeitadas = [x for x in previa.linhas if x.situacao == "rejeitada"]
    assert len(rejeitadas) == 2 and "nenhuma foi escolhida" in rejeitadas[0].motivo


def test_unidade_incompativel_e_registro_tardio_sao_avisados(planta):
    arqs = arquivos_caso()
    planta.confirmar(planta.previa(EQ, arqs), autor="Ana")
    linhas = arqs["diario.csv"].decode().splitlines()
    cab = linhas[0].split(",")
    i = cab.index("p_vapor_bar_man")
    novas = [linhas[0]]
    for linha in linhas[1:40]:
        c = linha.split(",")
        c[i] = str(float(c[i]) * 100)  # kPa em vez de bar
        novas.append(",".join(c))
    previa = planta.previa(EQ, {"diario.csv": "\n".join(novas).encode()})
    assert any(a.tipo == "unidade_incompativel" for a in previa.avisos)
    # registro novo dentro de um período já importado: marcado como tardio
    j = linhas[1].split(",")
    j[cab.index("instante_observado")] = "2026-01-05T09:31:00-03:00"
    tardia = planta.previa(EQ, {"diario.csv": "\n".join([linhas[0], ",".join(j)]).encode()})
    assert tardia.linhas[0].situacao == "nova" and tardia.linhas[0].tardia


def test_cobertura_indica_desatualizado_sem_reapresentar_analise_antiga(planta):
    assert planta.cobertura(EQ)["estado"] == "sem_dados"
    planta.confirmar(planta.previa(EQ, arquivos_caso()), autor="Ana")
    perto = planta.cobertura(EQ, agora=datetime(2026, 2, 5, tzinfo=UTC))
    longe = planta.cobertura(EQ, agora=datetime(2026, 6, 1, tzinfo=UTC))
    assert perto["estado"] == "atualizado"
    assert longe["estado"] == "desatualizado" and "não o momento atual" in longe["frase"]


def test_dados_persistem_depois_de_reiniciar(tmp_path):
    a = criar_planta("Persistente", "sintetico", raiz=tmp_path)
    a.criar_equipamento(EQ, "Caldeira")
    a.confirmar(a.previa(EQ, arquivos_caso()), autor="Ana")
    n, rev = len(a.registros(EQ, "diario")), a.revisao
    a.fechar()
    b = abrir_planta("persistente", raiz=tmp_path)
    assert len(b.registros(EQ, "diario")) == n and b.revisao == rev
    assert b.importacoes(EQ)[0]["autor"] == "Ana"


def test_pacote_reconstruido_da_os_mesmos_periodos(planta):
    arqs = arquivos_caso()
    planta.confirmar(planta.previa(EQ, arqs), autor="Ana")
    pacote, _ = montar([Periodo(G01), Periodo(G01)])
    assert periodos_entre_estoques(planta.pacote(EQ)) == periodos_entre_estoques(pacote)


def test_copia_de_seguranca_e_restauracao(planta, tmp_path):
    planta.confirmar(planta.previa(EQ, arquivos_caso()), autor="Ana")
    copia = planta.copia_seguranca(tmp_path / "copias")
    outra_raiz = tmp_path / "outro_pc"
    restaurada = restaurar_copia(copia, raiz=outra_raiz)
    assert restaurada.registros(EQ, "diario") == planta.registros(EQ, "diario")
    with pytest.raises(ErroArmazem, match="já existe"):
        restaurar_copia(copia, raiz=outra_raiz)
    restaurar_copia(copia, raiz=outra_raiz, substituir=True)
    assert list((outra_raiz / "usina-teste" / "copias").glob("*.euler.sqlite"))
    exportado = planta.exportar()
    assert exportado["planta"]["classe"] == "sintetico" and exportado["tabelas"]["registro"]
