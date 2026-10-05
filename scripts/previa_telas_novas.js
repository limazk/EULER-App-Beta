/* ---------------------------------------------- Financeiro e Oportunidades (análise de um período) */
const md = (s) => e(s).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>");
const rs = (v) => (v === null || v === undefined ? "—" : (v < 0 ? "−" : "") + "R$ " + nf(Math.abs(v), 0));
const link = (tela, rotulo, ic = "seta") => `<button class="link" data-ir="${tela}">${icone(ic)} ${e(rotulo)}</button>`;

function telaFinanceiro() {
  const topo = cabecalho("Analisar um período", "Financeiro", "Quanto o consumo pesa no caixa — e o que vale investigar.");
  const c = combo();
  if (!c) return topo + periodosHtml() + foraDaPrevia();
  const f = c.fin;
  let h = `${topo}<p class="legenda">${e(f.cab)}</p><div>${link("investigacao", "Escolher períodos e ver investigação", "busca")}</div>`;
  if (f.motivo) {
    h += `<div class="alerta info">${icone("busca")}<div>${e(f.motivo)}</div></div>`;
  } else {
    const classe = { total: "fin-total", alerta: "fin-alerta" };
    h += `<h3>${e(f.frase)}</h3>
      <div class="grade g3">${f.cartoes.map(([r, v, l, cl]) => `<div class="cartao metrica ${classe[cl] || ""}"><div class="rotulo">${e(r)}</div><div class="valor">${e(v)}</div><p class="legenda">${e(l)}</p></div>`).join("")}</div>
      <div class="cartao"><b>Parcela evitável: não apurada</b><p class="legenda">${e(f.evitavel)}</p>
        ${f.verificacao ? `<p>${md("**Próxima verificação:** " + f.verificacao)}</p><p class="legenda">${e(f.porque)}</p>` : ""}
        <div>${link("oportunidades", "Ver as oportunidades em ordem de prioridade", "oportunidades")}</div></div>
      <h3>Por que a conta mudou em relação à referência</h3><p class="legenda">${e(f.variacao)}</p>
      ${tabela(["Parcela", "Pergunta", "Combustível", "Valor"], f.parcelas.map((l) => l.map(e)), [2, 3])}
      ${f.separacao ? `<p class="legenda">${e(f.separacao)}</p>` : ""}
      <details><summary>Premissas, faixas e cenários</summary><div class="grade" style="gap:8px">${f.premissas.map((x) => `<p>${md(x)}</p>`).join("")}${f.notas.map((x) => `<p class="legenda">${md(x)}</p>`).join("")}<p class="legenda">Economia comprovada: ainda não apurada. Depende de intervenção registrada e comparação posterior com a referência ajustada.</p></div></details>`;
  }
  const cp = A().compras;
  if (cp) {
    const max = Math.max(...cp.grupos.map((g) => g[1])) * 1.25;
    h += `<h3>Compras registradas</h3><p class="legenda">Todos os recebimentos carregados: ${e(cp.periodo)}. Este período pode ser diferente da comparação acima.</p>
      <div class="grade g2"><div class="cartao metrica"><div class="rotulo">${e(cp.rotulo)}</div><div class="valor">${e(cp.total)}</div><p class="legenda">${e(cp.contagem)} Compra não equivale a consumo nem a pagamento confirmado.</p></div>
      <div class="cartao"><b style="font-size:15px">Compras por fornecedor (R$)</b><div class="barras">${cp.grupos.map(([forn, v, rot]) => `<div class="barra"><span>${e(forn)}</span><div class="trilho"><div class="cheia" style="width:${(100 * v) / max}%;background:#7f9ab4" data-dica="${e(forn)} · ${e(rot)}"></div><span>${e(rot)}</span></div></div>`).join("")}</div></div></div>
      <div>${link("extrato", "Comparar fornecedores por custo da energia", "extrato")}</div>`;
  }
  return h;
}

function telaOportunidades() {
  const topo = cabecalho("Analisar um período", "Oportunidades", "Onde vale colocar tempo e dinheiro primeiro — sem passar do que os dados sustentam.");
  const c = combo();
  if (!c) return topo + periodosHtml() + foraDaPrevia();
  const o = c.op;
  if (o.vazio) return `${topo}<div class="alerta info">${icone("busca")}<div>${e(o.vazio)}</div></div>`;
  const ano = estado.diasAno;
  const proj = (v) => (ano && v !== null && v !== undefined && o.dias ? (v / o.dias) * ano : null);
  const cartao = (x) => {
    const legenda = [...x.legenda];
    if (ano && x.custo !== null) {
      const par = x.faixa ? x.faixa.map(proj) : null;
      legenda.push(`${rs(proj(x.custo))}/ano` + (par ? ` (${rs(par[0])} a ${rs(par[1])})` : "") + " na projeção informada");
    }
    if (x.motivo) legenda.push(x.motivo);
    return `<div class="cartao"><b>${x.ordem}. ${e(x.titulo)}</b><div>${selo(x.prioridade[1], x.prioridade[0])}</div>
      <div class="grade g3">
        <div class="metrica"><div class="rotulo">Impacto potencial associado</div><div class="valor">${e(x.impacto)}</div><p class="legenda">${e(legenda.join(" · "))}</p></div>
        <div class="metrica"><div class="rotulo">Evidência</div><div class="valor">${e(x.evidencia[0])}</div><p class="legenda">${e(x.evidencia[1])}</p></div>
        <div class="metrica"><div class="rotulo">Complexidade da verificação</div><div class="valor">${e(x.complexidade[0])}</div><p class="legenda">${e(x.complexidade[1])}</p></div>
      </div>
      <p>${md("**Próxima verificação:** " + x.acao)}</p>${x.detalhes.map((d) => `<p class="legenda">${md(d)}</p>`).join("")}</div>`;
  };
  const pAno = proj(o.assoc.custo);
  return `${topo}<p class="legenda">${e(o.cab)}</p><div>${link("investigacao", "Escolher períodos e ver investigação", "busca")}</div>
    <h3>${e(o.frase)}</h3>
    <div class="grade g2">
      <div class="cartao metrica"><div class="rotulo">${e(o.assoc.rotulo)}</div><div class="valor">${e(o.assoc.valor)}</div><p class="legenda">${md(o.assoc.legenda)}</p></div>
      <div class="cartao"><label class="campo" for="dias-ano">Dias de operação por ano (informado pela fábrica, opcional)<input type="number" id="dias-ano" min="1" max="366" step="1" value="${ano || ""}"></label>
        <p class="legenda">${pAno !== null ? e(`Projeção linear: ${rs(pAno)}/ano, dadas as premissas informadas. Não é economia recuperável confirmada.`) : "Só para projetar o valor do período para um ano, supondo o mesmo regime, carga e preço. Sem esse dado, a EULER não projeta."}</p></div>
    </div>
    ${o.primeira ? `<div class="cartao"><b>Verificar primeiro: ${e(o.primeira.titulo)}</b><p>${e(o.primeira.acao)}</p></div>` : ""}
    ${o.sobreposicao.map((x) => `<div class="alerta aviso">${icone("busca")}<div>${md(x)}</div></div>`).join("")}
    ${o.ativos.length ? `<h3>Em investigação</h3>${o.ativos.map(cartao).join("")}` : ""}
    ${o.outros.length ? `<details><summary>Não priorizadas agora (${o.outros.length})</summary>${tabela(["Hipótese", "Situação", "Por quê"], o.outros.map((l) => l.map(e)))}</details>` : ""}
    <h3>Intervenção</h3><div class="alerta info">${icone("busca")}<div>${e(o.intervencao)}</div></div><p class="legenda">${e(o.cadeia)}</p>
    <details><summary>Como a priorização funciona</summary><div class="grade" style="gap:8px">
      <b>Critérios objetivos (calculados pelo motor)</b><ul>${o.objetivos.map((x) => `<li>${e(x)}</li>`).join("")}</ul>
      <b>Regras de triagem propostas (pendentes de revisão, D90)</b><ul>${o.propostos.map((x) => `<li>${e(x)}</li>`).join("")}</ul>
      <b>Termos que não são sinônimos</b><ul><li>Desvio monetizado: diferença de consumo em reais (Financeiro).</li><li>Impacto potencial associado: o efeito de uma hipótese em reais, se ela se confirmar.</li><li>Parcela evitável: o que uma ação concreta evitaria; ainda não apurada.</li><li>Economia estimada: depende de intervenção definida; ainda não disponível.</li><li>Economia verificada: medida depois da intervenção; ainda não disponível.</li></ul></div></details>`;
}

/* ---------------------------------------------- Acompanhar a planta (registros guardados nesta página) */
const AC = D.acomp;
const GUARDA = "euler-previa-acompanhamento-v1";
const ACOMP = ["atualizar", "fechamentos", "acoes"]; // telas que pedem o nome de quem registra
const TIPOS_EVENTO = { criada: "Aberta", ocorrencia: "Nova ocorrência", evidencia: "Evidência", estado: "Situação", acao: "Ação registrada", verificacao: "Verificação", responsavel: "Responsável", encerrada: "Encerrada" };
const RESULTADO_ACAO = { positivo: ["Melhoria associada à ação", "green"], negativo: ["Piora detectável depois da ação", "red"], inconclusivo: ["Inconclusivo", "gray"], nao_avaliavel: ["Ainda não avaliável", "gray"] };
const CORES_FILA = { desvio_persistente: "red", acao_sem_verificacao: "orange", desvio_novo: "orange", investigacao_aberta: "blue", oportunidade: "violet", dados: "gray" };
const SITUACAO_CURTA = { acima: "desvio estabelecido", nao_estabelecido: "desvio não estabelecido", abaixo: "abaixo da referência", sem_faixa: "sem faixa de incerteza" };
const ROTULO_CRITERIO = { persistencia_fechamentos: "fechamentos seguidos acima", magnitude_pct: "% do esperado", faixa_brl: "faixa", avaliacao: "avaliação", ocorrencias: "ocorrências", responsavel: "responsável", estado: "situação", evidencia: "evidência", prioridade_investigacao: "prioridade da investigação", complexidade_verificacao: "complexidade da verificação" };
const ORDEM_FILA = Object.keys(AC.categorias);

function novoAcomp() {
  return { versao: D.versao, criada: false, autor: "", criadaEm: null, nFech: 0, fechInfo: {}, fechSel: null, invs: [], acoes: [], custos: [], precos: [], eventos: [], erro: null, abaAtualizar: 0, abaAcoes: 0, abaInv: {}, invSel: null, abriu: null };
}
let ac = (() => {
  try {
    const salvo = JSON.parse(localStorage.getItem(GUARDA) || "null");
    if (salvo && salvo.versao === D.versao) return salvo;
  } catch (_) { /* sem armazenamento: começa do zero */ }
  return novoAcomp();
})();
function guardar() { try { localStorage.setItem(GUARDA, JSON.stringify(ac)); } catch (_) { /* segue sem guardar */ } }

const pad = (n) => String(n).padStart(2, "0");
const quando = (x) => {
  if (!x) return "—";
  const d = x.length === 10 ? new Date(x + "T00:00") : new Date(x);
  return `${pad(d.getDate())}/${pad(d.getMonth() + 1)}/${d.getFullYear()}`;
};
const nome = () => (ac.autor || "").trim();
const autorDe = (x) => (x === "__AUTOR__" ? nome() || "—" : x || "—");
const agora = () => new Date().toISOString();
const fechs = () => AC.fechamentos.slice(0, ac.nFech);
const proxId = (lista) => lista.reduce((m, x) => Math.max(m, x.id), 0) + 1;

function toast(texto) {
  const el = document.getElementById("toast");
  el.textContent = texto;
  el.hidden = false;
  clearTimeout(toast.t);
  toast.t = setTimeout(() => { el.hidden = true; }, 4000);
}
function evento(oque, acao) { ac.eventos.push({ quando: agora(), o_que: oque, acao, autor: nome() }); }
// erro de um formulário: aparece junto dele, como no app
function erroEm(onde, texto, tipo = "erro") { ac.erro = { onde, texto, tipo }; mostrar(); }
const erroDe = (onde) => (ac.erro && ac.erro.onde === onde ? `<div class="alerta ${ac.erro.tipo}">${icone(ac.erro.tipo === "aviso" ? "mao" : "bloqueio")}<div>${e(ac.erro.texto)}</div></div>` : "");
function exigirNome(onde) {
  if (nome()) return true;
  erroEm(onde, "Informe seu nome na barra lateral para registrar alterações.", "aviso");
  return false;
}
function gravou(texto) { ac.erro = null; guardar(); mostrar(); if (texto) toast(texto); }

function cobertura() {
  const dias = Math.floor((Date.now() - new Date(AC.diario[1])) / 864e5);
  return dias > AC.limite_dias
    ? { ok: false, frase: `Acompanhamento desatualizado: a última leitura do diário tem ${dias} dias (limite configurado: ${AC.limite_dias}). As análises descrevem o passado, não o momento atual.` }
    : { ok: true, frase: `Dados atualizados: última leitura do diário há ${dias} dias.` };
}

function semPlanta() {
  return `<div class="alerta info">${icone("busca")}<div>Nenhuma planta cadastrada nesta instalação. Comece em <b>Atualizar dados</b> (cadastro e primeira importação) ou crie a planta de demonstração lá.</div></div><div>${link("atualizar", "Ir para Atualizar dados", "atualizar")}</div>`;
}
function seletores() {
  return `<div class="grade g2"><label class="campo">Planta<select disabled><option>${e(AC.planta)}</option></select></label>
    <label class="campo">Equipamento<select disabled><option>${e(AC.equipamento.nome)} · ${e(AC.equipamento.caldeira_id)}</option></select></label></div>
    <p class="legenda"><span style="color:var(--t-orange)">DADOS SINTÉTICOS</span> · não representam uma planta real.</p>`;
}
function faixaSituacao(sit, frase) {
  const tipo = sit === "acima" ? "aviso" : sit === "abaixo" ? "ok" : "info";
  return `<div class="alerta ${tipo}">${icone(sit === "acima" ? "cima" : sit === "abaixo" ? "ok" : "busca")}<div>${md(frase)}</div></div>`;
}
const abas = (lista, atual, acao, extra = "") => `<div class="abas" role="tablist">${lista.map((t, i) => `<button class="aba" role="tab" data-acao="${acao}" data-i="${i}" ${extra} aria-selected="${i === atual}">${e(t)}</button>`).join("")}</div>`;

/* criar a planta de demonstração: o mesmo que o botão do app, já calculado pelo motor */
function criarDemo() {
  if (!exigirNome("demo")) return;
  ac.criada = true;
  ac.criadaEm = agora();
  ac.nFech = 1;
  ac.fechInfo = { 1: { autor: nome(), em: agora(), acoes: [] } };
  ac.fechSel = 1;
  ac.eventos = AC.eventos.map((x) => ({ ...x, quando: agora(), autor: nome() }));
  gravou("Planta de demonstração criada, com referência e primeiro fechamento. Veja o resultado em Painel e Fechamentos.");
}

function telaAtualizar() {
  const topo = cabecalho("Acompanhar a planta", "Atualizar dados", "Acrescente os dados novos da planta: nada se duplica e nada é substituído em silêncio.", false);
  const cadastro = `<details ${ac.criada ? "" : "open"}><summary>Cadastrar uma planta</summary><div class="grade">
      <p class="legenda">Na prévia, o cadastro de plantas da fábrica fica desligado: use a planta de demonstração. No app, aqui entram o nome da planta, a origem dos dados (sintéticos, públicos ou de cliente, com o registro da autorização) e depois o equipamento.</p>
      <p class="legenda">Para conhecer o fluxo sem dados reais:</p>
      <div>${ac.criada ? `<span class="legenda">Planta de demonstração já criada nesta página.</span>` : `<button class="botao" data-acao="criar-demo">${icone("ciencia")} Criar planta de demonstração (sintética)</button>`}</div>${erroDe("demo")}</div></details>`;
  if (!ac.criada) return topo + cadastro;
  const cob = cobertura();
  const i = AC.importacao;
  let aba = "";
  if (ac.abaAtualizar === 0) {
    aba = `<div class="campo">Origem dos arquivos<div class="lado-a-lado"><span>◉ Enviar arquivos novos</span><span class="legenda">○ Usar versão já salva em Plantas e histórico</span></div></div>
      <div class="cartao"><div class="linha-botoes"><button class="botao" disabled>${icone("importar")} Escolher arquivos</button><span class="legenda">ou arraste para cá · CSV ou planilha .xlsx</span></div>
      <p class="legenda">Na prévia, o envio fica desligado. No app, os arquivos passam por uma prévia antes de gravar: novos, já gravados (ignorados), conflitos, recusados e tardios. Nada é gravado antes da sua confirmação.</p></div>
      <h3>Como foi a importação da demonstração</h3>${tabela(i.colunas, i.contagem.map((l) => l.map((v) => e(v))), [1, 2, 3, 4, 5, 6])}
      <p class="legenda">Registros já gravados não se duplicam. Valores diferentes ficam pendentes de decisão.</p>`;
  } else if (ac.abaAtualizar === 1) {
    aba = `<p class="legenda">Nenhum conflito pendente.</p>`;
  } else if (ac.abaAtualizar === 2) {
    aba = `${tabela(["Configuração", "Valor"], AC.config.map((l) => l.map(e)))}
      <p class="legenda">Configuração por equipamento, sem mudar código. Fechamentos antigos guardam a que usaram. Na prévia, só leitura.</p>
      <h3>Tabela de preços</h3>
      ${ac.precos.length ? tabela(["Combustível", "Fornecedor", "R$/t", "Adicional R$/t", "Adicional", "De", "Até", "Origem"], ac.precos.map((p) => [p.combustivel, p.fornecedor || "—", nf(p.preco, 2), p.adicional === null ? "—" : nf(p.adicional, 2), p.desc || "—", quando(p.de), quando(p.ate), p.origem].map(e)), [2, 3]) : ""}
      <form class="form" data-form="preco">
        <div class="grade g3"><label class="campo">Combustível<input type="text" id="preco-comb"></label><label class="campo">Fornecedor (opcional)<input type="text" id="preco-forn"></label><label class="campo">Preço (R$/t)<input type="number" id="preco-valor" min="0" step="0.01"></label></div>
        <div class="grade g3"><label class="campo">Válido de<input type="date" id="preco-de"></label><label class="campo">Válido até (opcional)<input type="date" id="preco-ate"></label><label class="campo">Origem (contrato, nota, cotação)<input type="text" id="preco-origem"></label></div>
        <div class="grade g2"><label class="campo">Custo adicional (R$/t, opcional)<input type="number" id="preco-adic" min="0" step="0.01"></label><label class="campo">Descrição do adicional (ex.: frete)<input type="text" id="preco-desc"></label></div>
        <div><button class="botao" type="submit">Registrar preço</button></div>${erroDe("preco")}</form>
      <p class="legenda">Usada só com a política "tabela de preços". Mais de um preço vigente no mesmo período deixa o custo ausente até haver regra de rateio; nada é escolhido em silêncio.</p>`;
  } else {
    aba = `${tabela(["Quando", "Quem", "Fonte", "Modo", "Novos", "Corrigidos", "Conflitos"], [[quando(ac.criadaEm), nome() || "—", "Importação de arquivos", "incremental", String(i.novas), String(i.corrigidas ?? 0), String(i.conflitos)]].map((l) => l.map(e)), [4, 5, 6])}
      <details><summary>Todas as alterações (auditoria)</summary>${tabela(["Quando", "O quê", "Ação", "Quem"], [...ac.eventos].reverse().map((x) => [quando(x.quando), x.o_que, x.acao, autorDe(x.autor)].map(e)))}</details>`;
  }
  return `${topo}${cadastro}${seletores()}
    <details><summary>Cadastrar equipamento</summary><p class="legenda">Na prévia, o equipamento é o da demonstração. No app: identificador, nome, código da caldeira no diário e altitude do local.</p></details>
    <p class="legenda">${cob.ok ? "✓ " : ""}${e(cob.frase)}</p>
    <div class="grade g3">${metrica("Diário desde", quando(AC.diario[0]))}${metrica("até", quando(AC.diario[1]))}${metrica("Última importação", quando(ac.criadaEm))}</div>
    ${abas(["Novos dados", "Conflitos", "Configuração e preços", "Histórico"], ac.abaAtualizar, "aba-atualizar")}
    <div class="grade">${aba}</div>
    <div class="grade g2" style="border-top:1px solid var(--linha);padding-top:16px">
      <div class="grade" style="gap:4px">${link("fechamentos", "Fechar o período", "fechamentos")}<p class="legenda">Próximo passo do acompanhamento: custo, desvio e o que mudou.</p></div>
      <div class="grade" style="gap:4px"><div><button class="botao" data-acao="serie">${icone("investigacao")} Analisar série acumulada</button></div><p class="legenda">Leva os registros desta revisão para as telas de análise de um período.</p></div>
    </div>`;
}

/* Fechamentos */
function telaFechamentos() {
  const topo = cabecalho("Acompanhar a planta", "Fechamentos", "Quanto custou, quanto seria esperado e o que mudou — a cada período, com histórico.", false);
  if (!ac.criada) return topo + semPlanta();
  const r = AC.referencia;
  const pend = AC.pendentes[ac.nFech - 1] || [];
  const validos = pend.filter((p) => p.valido).length;
  const lista = fechs();
  const sel = lista.find((f) => f.id === ac.fechSel) || lista[lista.length - 1];
  const info = ac.fechInfo[sel.id] || {};
  const abriu = ac.abriu && ac.abriu.fech === sel.id ? ac.abriu : null;
  const inv = abriu ? ac.invs.find((x) => x.id === abriu.inv) : null;
  const acoesAntes = info.acoes || [];
  return `${topo}${seletores()}
    <p>${md(`**Referência v${r.versao}** · ${r.periodo} · ${r.tipo} · ${r.consumo} t de combustível por t de vapor`)}</p>
    <details><summary>Definir nova versão da referência</summary><div class="grade"><p class="legenda">Na prévia, a referência fica em agosto. No app: escolher os períodos, o tipo (mudança estrutural ou correção de dados) e o motivo. Uma referência pior que a anterior só entra como mudança estrutural confirmada.</p>
      <p class="legenda">Versões anteriores nunca mudam; fechamentos antigos continuam reproduzíveis.</p>
      ${tabela(["Versão", "Período", "Tipo", "Motivo", "Por", "Em"], [[String(r.versao), r.periodo, "inicial", r.motivo, nome() || "—", quando(ac.criadaEm)].map(e)])}</div></details>
    ${pend.length ? `<p>${md(`**${pend.length} período(s) novo(s) para fechar** (${validos} com vapor e combustível conhecidos).`)}</p>
      ${pend.filter((p) => !p.valido).map((p) => `<p class="legenda">${e(p.rotulo)}: ${e(p.motivo)}</p>`).join("")}
      <div><button class="botao primario" data-acao="produzir">Produzir fechamento</button></div>${erroDe("produzir")}`
      : `<p class="legenda">Nenhum período novo desde o último fechamento: importe dados novos para continuar.</p>`}
    <h2>Fechamento #${sel.id} · ${e(sel.periodo)}</h2>
    ${faixaSituacao(sel.situacao, sel.frase)}
    ${sel.metricas ? `<div class="grade g3">${metrica("Custo do consumo observado", sel.metricas[0])}${metrica("Custo esperado (referência ajustada)", sel.metricas[1])}${metrica("Desvio monetizado", sel.metricas[2])}</div><p class="legenda">${e(sel.politica)}</p>` : ""}
    <p>${md("**O que mudou desde o fechamento anterior:** " + sel.mudanca)}</p>
    ${sel.persistencia ? `<p>${md("**Persistência:** " + sel.persistencia)}</p>` : ""}
    <p>${md("**Próxima verificação:** " + sel.proxima)}</p>
    <p class="legenda">${e(sel.forca)}</p>
    <div><button class="botao" data-acao="abrir" data-fech="${sel.id}">Abrir investigação deste desvio</button></div>${erroDe("abrir-" + sel.id)}
    ${inv ? `<div class="alerta ok">${icone("ok")}<div>Investigação #${inv.id}: ${e(inv.titulo)} (${e(AC.estados[inv.estado])}).</div></div><div>${link("acoes", "Abrir em Investigações e ações", "acoes")}</div>` : ""}
    <details><summary>Conta do período: compra, estoque, consumo e custo</summary>${tabela(["Item", "Quantidade", "Valor"], sel.conta_periodo.map((l) => l.map(e)), [1, 2])}<p class="legenda">${e(sel.nota_pagamento)}</p><p class="legenda">${e(sel.energia)}</p></details>
    ${sel.variacao ? `<details><summary>Por que a conta mudou: produção, condição do vapor, qualidade, preço</summary>${tabela(["Parcela", "Pergunta", "Valor"], sel.variacao.map((l) => l.map(e)), [2])}${sel.nao_ajustado.map((x) => `<p class="legenda">${e(x)}</p>`).join("")}</details>` : ""}
    <details><summary>O que investigar e ações anteriores</summary><div class="grade" style="gap:6px">
      ${sel.oportunidades.length ? `<ul>${sel.oportunidades.map((x) => `<li>${md(x)}</li>`).join("")}</ul>` : ""}
      ${sel.sobreposicao.map((x) => `<p class="legenda">${e(x)}</p>`).join("")}
      ${acoesAntes.length ? `<ul>${acoesAntes.map((x) => `<li>Ação #${x.id} (${quando(x.data)}) ${e(x.descricao)}: ${e(x.frase)}</li>`).join("")}</ul>` : '<p class="legenda">Nenhuma ação registrada até este fechamento.</p>'}</div></details>
    <details><summary>Rastreabilidade e reprodução</summary><p class="legenda">${e(sel.rastro)} · por ${e(info.autor || nome() || "—")} em ${quando(info.em)}</p><p class="legenda">Reproduzir o cálculo, baixar o relatório e os dados (JSON): disponíveis no app.</p></details>
    <h3>Histórico de fechamentos</h3><p class="legenda">Todos os períodos ficam: favoráveis, desfavoráveis e inconclusivos.</p>
    ${tabela(["#", "Período", "Situação", "Desvio", "Referência", "Em"], [...lista].reverse().map((f) => [String(f.id), f.periodo, f.situacao_frase, rs(f.desvio_brl), "v" + f.ref_versao, quando((ac.fechInfo[f.id] || {}).em)].map(e)), [0, 3])}
    ${lista.length > 1 ? `<label class="campo" style="max-width:320px">Ver outro fechamento<select id="ver-fech">${[...lista].reverse().map((f) => `<option value="${f.id}" ${f.id === sel.id ? "selected" : ""}>#${f.id}</option>`).join("")}</select></label>` : ""}`;
}

function produzir() {
  if (!exigirNome("produzir")) return;
  ac.nFech += 1;
  const id = ac.nFech;
  ac.fechInfo[id] = { autor: nome(), em: agora(), acoes: ac.acoes.map((x) => ({ id: x.id, data: x.data, descricao: x.descricao, frase: x.avaliacao ? x.avaliacao.frase : "Ainda não avaliada." })) };
  ac.fechSel = id;
  evento(`fechamento ${id}`, "produzido");
  gravou(`Fechamento #${id} gravado.`);
}

function abrirInvestigacao(fid) {
  if (!exigirNome("abrir-" + fid)) return;
  const r = AC.abrir[fid - 1];
  if (!r.ok) return erroEm("abrir-" + fid, r.erro);
  const aberta = ac.invs.find((x) => x.chave === r.chave && x.estado !== "encerrada");
  let inv;
  if (aberta) {
    inv = aberta;
    inv.eventos.push({ quando: agora(), tipo: "ocorrencia", autor: nome(), texto: r.desvio.frase });
    inv.atualizada = agora();
  } else {
    inv = { id: proxId(ac.invs), chave: r.chave, titulo: r.titulo, estado: r.estado, responsavel: null, criada: agora(), atualizada: agora(), desvio: r.desvio, proxima: r.proxima_verificacao, hipoteses: r.hipoteses, limitacoes: r.limitacoes, resultado: null, motivoEnc: null, eventos: [{ quando: agora(), tipo: "criada", autor: nome(), texto: r.desvio.frase }] };
    ac.invs.push(inv);
  }
  evento(`investigacao ${inv.id}`, "ocorrencia");
  ac.abriu = { fech: fid, inv: inv.id };
  ac.invSel = inv.id;
  gravou("Investigação atualizada.");
}

/* Investigações e ações */
function telaAcoes() {
  const topo = cabecalho("Acompanhar a planta", "Investigações e ações", "Do desvio à verificação: o que a equipe investigou, decidiu e qual foi o resultado.", false);
  if (!ac.criada) return topo + semPlanta();
  const abertas = ac.invs.filter((x) => x.estado !== "encerrada").length;
  return `${topo}${seletores()}
    <div class="grade g2">${metrica("Investigações abertas", String(abertas))}${metrica("Ações registradas", String(ac.acoes.length))}</div>
    ${abas(["Investigações", "Ações e resultados"], ac.abaAcoes, "aba-acoes")}
    <div class="grade">${ac.abaAcoes === 0 ? abaInvestigacoes() : abaAcoesResultados()}</div>`;
}

function formAcao(chave, invId = null) {
  return `<form class="form" data-form="acao" data-chave="${chave}" ${invId ? `data-inv="${invId}"` : ""}>
    <div class="grade g2"><label class="campo">Data da ação<input type="date" id="${chave}-data" min="2026-07-01" max="2026-12-31"></label>
      <label class="campo">Tipo<select id="${chave}-tipo">${Object.entries(AC.tipos).map(([k, v]) => `<option value="${k}">${e(v)}</option>`).join("")}</select></label></div>
    <label class="campo">O que foi feito<input type="text" id="${chave}-desc"></label>
    <div class="grade g3"><label class="campo">Responsável (opcional)<input type="text" id="${chave}-resp"></label><label class="campo">Custo da ação (R$, opcional)<input type="number" id="${chave}-custo" min="0" step="0.01"></label><label class="campo">Origem do custo (nota, orçamento)<input type="text" id="${chave}-origem"></label></div>
    <label class="campo">Outras mudanças no mesmo período (uma por linha)<textarea id="${chave}-conc" title="Ex.: troca de fornecedor, mudança de carga. Elas impedem associar o resultado só a esta ação."></textarea></label>
    <div><button class="botao" type="submit">Registrar ação</button></div>${erroDe(chave)}</form>`;
}

function abaInvestigacoes() {
  if (!ac.invs.length) return `<div class="alerta info">${icone("busca")}<div>Nenhuma investigação ainda. Elas são abertas a partir de um fechamento com desvio ou hipótese a verificar.</div></div><div>${link("fechamentos", "Ir para Fechamentos", "fechamentos")}</div>`;
  const ordem = [...ac.invs].sort((a, b) => (a.estado === "encerrada") - (b.estado === "encerrada") || b.id - a.id);
  const inv = ac.invs.find((x) => x.id === ac.invSel) || ordem[0];
  const tabelaInv = tabela(["#", "Investigação", "Situação", "Ocorrências", "Responsável", "Atualizada"], ordem.map((x) => [String(x.id), x.titulo, AC.estados[x.estado], String(x.eventos.filter((v) => v.tipo === "criada" || v.tipo === "ocorrencia").length), x.responsavel || "—", quando(x.atualizada)].map(e)), [0, 3]);
  const seletor = `<label class="campo">Abrir investigação<select id="inv-sel">${ordem.map((x) => `<option value="${x.id}" ${x.id === inv.id ? "selected" : ""}>#${x.id} · ${e(x.titulo)}</option>`).join("")}</select></label>`;
  const hist = tabela(["Quando", "O quê", "Quem", "Detalhe"], inv.eventos.map((v) => [quando(v.quando), TIPOS_EVENTO[v.tipo] || v.tipo, autorDe(v.autor), v.texto || ""].map(e)));
  let corpo = `<h3>#${inv.id} · ${e(inv.titulo)}</h3><div>${selo(inv.estado === "encerrada" ? "gray" : "blue", AC.estados[inv.estado])}</div>
    ${inv.estado === "encerrada" ? `<div class="alerta info">${icone("busca")}<div>${md(`Encerrada como **${AC.resultados[inv.resultado] || inv.resultado}**: ${inv.motivoEnc}. Encerrar não significa causa confirmada.`)}</div></div>` : ""}
    ${inv.desvio && inv.desvio.frase ? `<p>${md("**Desvio que motivou:** " + inv.desvio.frase)}</p>` : ""}
    ${inv.proxima && inv.proxima.acao ? `<div class="cartao"><p>${md("**Próxima verificação:** " + inv.proxima.acao)}</p>${inv.proxima.porque ? `<p class="legenda">${e(inv.proxima.porque)}</p>` : ""}</div>` : ""}
    <p class="legenda">Responsável: ${e(inv.responsavel || "não informado")} · aberta em ${quando(inv.criada)}</p>
    <details><summary>Hipóteses, evidências e limitações</summary><ul>${inv.hipoteses.map((h) => `<li>${md(`**${h.titulo}** · evidência ${h.evidencia.toLowerCase()} · ${rs(h.impacto_brl)} associado (não somar) · ${h.verificacao}`)}</li>`).join("")}</ul>${inv.limitacoes.map((x) => `<p class="legenda">${e(x)}</p>`).join("")}</details>
    <details><summary>Histórico (${inv.eventos.length})</summary>${hist}</details>`;
  if (inv.estado === "encerrada") {
    corpo += `<form class="form" data-form="reabrir" data-inv="${inv.id}"><label class="campo">Motivo da reabertura<input type="text" id="reabrir-motivo"></label><div><button class="botao" type="submit">Reabrir investigação</button></div>${erroDe("reabrir")}</form>`;
    return tabelaInv + seletor + corpo;
  }
  const a = ac.abaInv[inv.id] || 0;
  const opcoes = AC.transicoes[inv.estado].filter((s) => s !== "encerrada");
  let sub = "";
  if (a === 0) sub = `<form class="form" data-form="evidencia" data-inv="${inv.id}"><label class="campo">O que foi verificado ou medido<textarea id="evid-texto"></textarea></label><label class="campo">Onde está o documento ou a medição (opcional)<input type="text" id="evid-ref"></label><div><button class="botao" type="submit">Adicionar evidência</button></div>${erroDe("evidencia")}</form>`;
  else if (a === 1) sub = `<form class="form" data-form="estado" data-inv="${inv.id}"><label class="campo">Nova situação<select id="estado-novo">${opcoes.map((s) => `<option value="${s}">${e(AC.estados[s])}</option>`).join("")}</select></label><label class="campo">Motivo<input type="text" id="estado-motivo"></label><div><button class="botao" type="submit">Mudar situação</button></div>${erroDe("estado")}</form>
      <form class="form" data-form="responsavel" data-inv="${inv.id}"><label class="campo">Responsável<input type="text" id="resp-nome" value="${e(inv.responsavel || "")}"></label><div><button class="botao" type="submit">Definir responsável</button></div>${erroDe("responsavel")}</form>`;
  else if (a === 2) sub = `<p class="legenda">A ação fica ligada a esta investigação; o resultado vem da avaliação posterior.</p>${formAcao("acao-inv", inv.id)}`;
  else sub = `<form class="form" data-form="encerrar" data-inv="${inv.id}"><label class="campo">Resultado<select id="enc-resultado">${Object.entries(AC.resultados).map(([k, v]) => `<option value="${k}">${e(v)}</option>`).join("")}</select></label><label class="campo">Motivo do encerramento<input type="text" id="enc-motivo"></label><p class="legenda">Inconclusiva é um resultado válido. Encerrar não significa causa confirmada.</p><div><button class="botao" type="submit">Encerrar investigação</button></div>${erroDe("encerrar")}</form>`;
  return tabelaInv + seletor + corpo + abas(["Evidência", "Situação e responsável", "Registrar ação", "Encerrar"], a, "aba-inv", `data-inv="${inv.id}"`) + `<div class="grade">${sub}</div>`;
}

function avaliacaoHtml(it) {
  const r = it.avaliacao;
  if (!r) return '<p class="legenda">Ainda não avaliada.</p>';
  const [rot, cor] = RESULTADO_ACAO[r.resultado];
  const m = r.melhoria;
  const ev = r.economia;
  let econ;
  if (ev && ev.valor_brl !== null && ev.valor_brl !== undefined) econ = md(`**Economia verificada (${ev.protocolo}):** ${rs(ev.valor_brl)} no período avaliado. ${ev.nota_custos || ""}`);
  else if (ev) econ = md("**Economia verificada:** critérios do protocolo não atendidos.") + (ev.criterios_nao_atendidos || []).map((x) => `<br><span class="legenda">• ${e(x)}</span>`).join("");
  else econ = md("**Economia verificada:** não se aplica sem melhoria associada.");
  const detalhes = [...r.motivos, ...r.excluidos, ...r.faltam];
  return `<div>${selo(cor, rot)}</div><p>${e(r.frase)}</p>
    ${r.dif ? `<p>${md(`**Diferença observada** (${r.dif.periodo}): consumo por tonelada de vapor ${r.dif.antes} → ${r.dif.depois} t/t; desvio da referência ajustada ${r.dif.desvio}.`)}</p>` : ""}
    <p>${m && m.custo_brl !== null ? md(`**Melhoria associada à ação:** ${rs(m.custo_brl)} (faixa ${rs(m.faixa_brl[0])} a ${rs(m.faixa_brl[1])}). ${m.nota}`) : md("**Melhoria associada à ação:** não estabelecida.")}</p>
    <p>${econ}</p>
    ${detalhes.length ? `<details><summary>Por que não foi possível associar ou verificar</summary>${detalhes.map((x) => `<p class="legenda">• ${e(x)}</p>`).join("")}</details>` : ""}`;
}

function abaAcoesResultados() {
  const cards = [...ac.acoes].reverse().map((it) => `<div class="cartao">
    <p>${md(`**#${it.id} · ${quando(it.data)} · ${AC.tipos[it.tipo]}** · ${it.descricao}`)}</p>
    <p class="legenda">Responsável: ${e(it.responsavel || "não informado")} · custo ${it.custo !== null ? `${e(rs(it.custo))} (${e(it.origem)})` : "não informado"}${it.inv ? ` · investigação #${it.inv}` : ""}</p>
    ${it.concomitantes.length ? `<p class="legenda">Mudanças no mesmo período: ${e(it.concomitantes.join("; "))}</p>` : ""}
    <div class="linha-botoes"><button class="botao" data-acao="avaliar" data-id="${it.id}">Avaliar agora</button>${it.avaliacao && it.avaliacao.dif ? `<button class="botao" disabled title="Disponível no app">Adotar a referência depois desta ação</button>` : ""}</div>${erroDe("avaliar-" + it.id)}
    ${avaliacaoHtml(it)}</div>`).join("");
  return `<details><summary>Registrar uma ação</summary>${formAcao("acao")}</details>
    ${cards || '<p class="legenda">Nenhuma ação registrada.</p>'}
    <details><summary>Custos de medição e acompanhamento</summary><div class="grade">
      <p class="legenda">Entram no benefício líquido das ações verificadas na mesma janela. Horas de equipe não viram dinheiro aqui.</p>
      ${ac.custos.length ? tabela(["Data", "Tipo", "Descrição", "Valor", "Origem"], ac.custos.map((c) => [quando(c.data), c.tipoRot, c.descricao, rs(c.valor), c.origem].map(e)), [3]) : ""}
      <form class="form" data-form="custo"><div class="grade g3"><label class="campo">Data<input type="date" id="custo-data"></label><label class="campo">Tipo<select id="custo-tipo"><option value="medicao">Medição</option><option value="acompanhamento">Acompanhamento</option><option value="outro">Outro</option></select></label><label class="campo">Valor (R$)<input type="number" id="custo-valor" min="0" step="0.01"></label></div>
        <label class="campo">Descrição<input type="text" id="custo-desc"></label><label class="campo">Origem (nota, contrato)<input type="text" id="custo-origem"></label>
        <div><button class="botao" type="submit">Registrar custo</button></div>${erroDe("custo")}</form></div></details>`;
}

/* avaliação: o resultado do motor para a data da ação (a página só aplica as regras de
   outras ações na mesma janela e de mudanças declaradas, como euler/acompanhamento.py) */
function avaliar(id) {
  if (!exigirNome("avaliar-" + id)) return;
  const it = ac.acoes.find((x) => x.id === id);
  const datas = Object.keys(AC.avaliacoes).sort();
  let chave = it.data, troca = null;
  if (chave < datas[0]) chave = datas[0];
  if (chave > datas[datas.length - 1]) { chave = datas[datas.length - 1]; troca = quando(it.data); }
  const r = JSON.parse(JSON.stringify(AC.avaliacoes[chave]));
  if (troca) {
    const de = quando(chave);
    r.frase = r.frase.split(de).join(troca);
    r.faltam = r.faltam.map((x) => x.split(de).join(troca));
  }
  if (r.dif && r.ref_fim) {
    const dataDe = (x) => new Date(x + "T00:00");
    const outras = ac.acoes.filter((x) => x.id !== id && new Date(r.ref_fim) < dataDe(x.data) && dataDe(x.data) <= new Date(r.dif.fim));
    const bloqueios = [];
    if (outras.length) bloqueios.push("outra intervenção registrada na mesma janela: " + outras.map((x) => `#${x.id} ${x.descricao} (${quando(x.data).slice(0, 5)})`).join(", "));
    if (it.concomitantes.length) bloqueios.push("mudanças concomitantes declaradas: " + it.concomitantes.join("; "));
    r.motivos = [...bloqueios, ...r.motivos];
    if (r.resultado === "positivo" && bloqueios.length) {
      r.resultado = "inconclusivo";
      r.frase = "Consumo abaixo da referência ajustada, mas não é possível associar à ação: " + r.motivos.join("; ") + ".";
      r.melhoria = null;
      r.economia = null;
    }
  }
  it.avaliacao = r;
  evento(`avaliacao ${id}`, r.resultado);
  const inv = it.inv ? ac.invs.find((x) => x.id === it.inv) : null;
  if (inv) {
    inv.eventos.push({ quando: agora(), tipo: "verificacao", autor: nome(), texto: r.frase });
    if (inv.estado === "acao_registrada" && r.resultado !== "nao_avaliavel") {
      inv.estado = "em_verificacao";
      inv.eventos.push({ quando: agora(), tipo: "estado", autor: nome(), texto: "Avaliação posterior registrada." });
    }
    inv.atualizada = agora();
  }
  gravou("Avaliação registrada.");
}

/* Painel: mesmas regras de euler/painel.py, lidas dos registros desta página */
function filaDeAtencao() {
  const itens = [];
  const fs = fechs();
  const ultimo = fs[fs.length - 1];
  const abertas = ac.invs.filter((x) => x.estado !== "encerrada");
  const chaves = new Set(abertas.map((x) => x.chave));
  let persist = 0;
  for (let k = fs.length - 1; k >= 0 && fs[k].situacao === "acima" && fs[k].ref_id === ultimo.ref_id; k--) persist++;
  if (ultimo && ultimo.situacao === "acima") itens.push({ categoria: persist >= 2 ? "desvio_persistente" : "desvio_novo", titulo: `Consumo acima da referência ajustada (${nf(ultimo.desvio_pct, 1)}%)`, valor: ultimo.desvio_brl, criterios: { persistencia_fechamentos: persist, magnitude_pct: ultimo.desvio_pct, faixa_brl: ultimo.desvio_faixa }, proxima: ultimo.proxima });
  for (const it of ac.acoes) {
    const av = it.avaliacao;
    if (!av || av.resultado === "nao_avaliavel") itens.push({ categoria: "acao_sem_verificacao", titulo: `Verificar o resultado: ${it.descricao} (${quando(it.data)})`, valor: null, criterios: { avaliacao: av ? av.frase : "nenhuma" }, proxima: av ? "Completar os dados que faltam e avaliar de novo." : "Avaliar a ação quando houver período completo depois dela." });
  }
  for (const x of abertas) itens.push({ categoria: "investigacao_aberta", titulo: `${x.titulo} · ${AC.estados[x.estado]}`, valor: (x.desvio || {}).custo_brl ?? null, criterios: { ocorrencias: x.eventos.filter((v) => v.tipo === "criada" || v.tipo === "ocorrencia").length, situacao_do_desvio: (x.desvio || {}).situacao, responsavel: x.responsavel || "não informado", estado: AC.estados[x.estado] }, proxima: (x.proxima || {}).acao });
  if (ultimo) for (const o of ultimo.ops) if (!chaves.has(`${AC.equipamento.id}:${o.id}`)) itens.push({ categoria: "oportunidade", titulo: o.titulo, valor: o.impacto_brl, criterios: { evidencia: o.evidencia, prioridade_investigacao: o.prioridade, complexidade_verificacao: o.complexidade, faixa_brl: o.faixa_brl }, proxima: o.verificacao });
  const cob = cobertura();
  if (!cob.ok) itens.push({ categoria: "dados", titulo: cob.frase, valor: null, criterios: {}, proxima: "Importar os dados mais recentes da planta." });
  itens.sort((a, b) => ORDEM_FILA.indexOf(a.categoria) - ORDEM_FILA.indexOf(b.categoria) || (a.valor === null) - (b.valor === null) || (b.valor ?? 0) - (a.valor ?? 0) || a.titulo.localeCompare(b.titulo));
  itens.forEach((x, i) => { x.ordem = i + 1; });
  return itens;
}

function itemFila(i) {
  const c = i.criterios || {};
  let extra = "";
  if (i.valor !== null && i.categoria === "oportunidade") extra = ` · ${rs(i.valor)} associado (não somar)`;
  else if (i.valor !== null) extra = ` · desvio de ${rs(i.valor)}` + (SITUACAO_CURTA[c.situacao_do_desvio] ? ` (${SITUACAO_CURTA[c.situacao_do_desvio]})` : "");
  const val = (v) => (Array.isArray(v) ? `${rs(v[0])} a ${rs(v[1])}` : typeof v === "number" && !Number.isInteger(v) ? nf(v, 1) : String(v) === String(v).toUpperCase() ? String(v).toLowerCase() : String(v));
  const crit = Object.entries(c).filter(([k, v]) => v !== null && v !== undefined && v !== "" && k !== "situacao_do_desvio").map(([k, v]) => `${ROTULO_CRITERIO[k] || k.replace(/_/g, " ")}: ${val(v)}`);
  return `<div class="cartao"><div>${selo(CORES_FILA[i.categoria], AC.categorias[i.categoria])}</div><p>${md(`**${i.ordem}. ${i.titulo}**`)}${e(extra)}</p>
    ${i.proxima ? `<p class="legenda">Próximo passo: ${e(i.proxima)}</p>` : ""}${crit.length ? `<p class="legenda">${e(crit.join(" · "))}</p>` : ""}</div>`;
}

function telaPainel() {
  const topo = cabecalho("Acompanhar a planta", "Painel", "O que mudou, o que olhar primeiro e o que já foi verificado.", false);
  if (!ac.criada) return topo + semPlanta();
  const fs = fechs();
  const u = fs[fs.length - 1];
  const fila = filaDeAtencao();
  const abertas = ac.invs.filter((x) => x.estado !== "encerrada");
  const encerradas = ac.invs.filter((x) => x.estado === "encerrada");
  const cob = cobertura();
  const outras = u.ops.filter((o) => !fila.some((i) => i.titulo === o.titulo));
  const pend = [];
  if (!cob.ok) pend.push(cob.frase);
  abertas.filter((x) => x.estado === "aguardando_dados").forEach((x) => pend.push(`Investigação aguardando dados: ${x.titulo}`));
  ac.acoes.filter((x) => !x.avaliacao).forEach((x) => pend.push(`Ação sem avaliação: ${x.descricao}`));
  return `${topo}${seletores()}
    ${cob.ok ? "" : `<div class="alerta aviso">${icone("mao")}<div>${e(cob.frase)}</div></div>`}
    <h3>Último fechamento · ${e(u.periodo)} · referência v${u.ref_versao}</h3>
    ${faixaSituacao(u.situacao, u.frase)}
    <p>${md("**O que mudou:** " + u.mudanca)}</p>${u.persistencia ? `<p>${md("**Persistência:** " + u.persistencia)}</p>` : ""}
    <div class="grade g4">${metrica("Investigações abertas", String(abertas.length))}${metrica("Encerradas", String(encerradas.length))}${metrica("Ações acompanhadas", String(ac.acoes.length))}${metrica("Economia verificada", "nenhuma", '<p class="legenda">Só entra aqui o resultado de ação avaliada pelo protocolo de verificação.</p>')}</div>
    <div class="lado-a-lado">${link("atualizar", "Atualizar dados", "atualizar")}${link("fechamentos", "Fechamentos", "fechamentos")}${link("acoes", "Investigações e ações", "acoes")}</div>
    <h2>O que olhar primeiro</h2>
    ${fila.length ? fila.slice(0, 5).map(itemFila).join("") : '<p class="legenda">Nada pendente: sem desvio estabelecido, ação sem verificação ou dado faltando.</p>'}
    ${fila.length > 5 ? `<details><summary>Ver todos (${fila.length})</summary><div class="grade">${fila.slice(5).map(itemFila).join("")}</div></details>` : ""}
    ${fila.some((i) => i.categoria === "oportunidade") ? '<p class="legenda">Oportunidades aparecem uma a uma, sem soma: podem representar a mesma perda e nenhuma é ganho antes de verificada.</p>' : ""}
    <details><summary>Como a ordem é definida</summary><p class="legenda">${e(AC.criterios)}</p></details>
    ${outras.length ? `<details><summary>Outras oportunidades ainda não confirmadas (${outras.length})</summary><p class="legenda">Uma a uma, sem soma: podem representar a mesma perda.</p><ul>${outras.map((o) => `<li>${md(`**${o.titulo}** · evidência ${o.evidencia.toLowerCase()} · ${rs(o.impacto_brl)} associado`)}</li>`).join("")}</ul></details>` : ""}
    ${ac.acoes.length ? `<details><summary>Ações acompanhadas (${ac.acoes.length})</summary><ul>${ac.acoes.map((x) => `<li>${quando(x.data)} · ${e(x.descricao)}: ${e(x.avaliacao ? x.avaliacao.frase : "Ainda não avaliada.")}</li>`).join("")}</ul></details>` : ""}
    ${pend.length ? `<h3>Pendências</h3><ul>${pend.map((x) => `<li>${e(x)}</li>`).join("")}</ul>` : ""}
    <p class="legenda">Desvio monetizado não é economia; oportunidade não confirmada não é ganho; só a economia verificada pelo protocolo entra como resultado. O benefício é das ações da planta.</p>`;
}

function telaPlantas() {
  const topo = cabecalho("Acompanhar a planta", "Plantas e histórico", "Guarde os dados no computador e retome a análise em outra sessão.", false);
  if (!ac.criada) return topo + semPlanta();
  return `${topo}${tabela(["Planta", "Origem dos dados", "Equipamentos", "Criada em"], [[AC.planta, "Dados sintéticos", "1", quando(ac.criadaEm)].map(e)], [2])}
    <p class="legenda">Cada planta tem um banco próprio, fora da pasta do código: arquivos originais, versões com autor e motivo, e todo o acompanhamento. Salvar versões, reabrir dados, cópia de segurança e restauração: disponíveis no app.</p>
    <div class="linha-botoes"><button class="botao" data-acao="recomecar">Apagar a demonstração desta página</button></div>${erroDe("recomecar")}`;
}

/* formulários do acompanhamento */
const val = (id) => (document.getElementById(id)?.value ?? "").trim();
const numero = (id) => (val(id) === "" ? null : Number(val(id)));
const FORMS = {
  preco() {
    if (!exigirNome("preco")) return;
    const p = { combustivel: val("preco-comb"), fornecedor: val("preco-forn") || null, preco: numero("preco-valor"), de: val("preco-de"), ate: val("preco-ate") || null, origem: val("preco-origem"), adicional: numero("preco-adic"), desc: val("preco-desc") || null };
    if (p.preco === null || !p.combustivel || !p.origem) return erroEm("preco", "Informe preço, combustível, origem e autor.");
    if (p.preco < 0 || (p.adicional !== null && p.adicional < 0)) return erroEm("preco", "Preço e custo adicional devem ser finitos e não negativos.");
    if (p.adicional && !p.desc) return erroEm("preco", "Descreva o custo adicional (ex.: frete).");
    if (!p.de) return erroEm("preco", "Informe a data de início da validade.");
    if (p.ate && p.ate <= p.de) return erroEm("preco", "O fim da validade precisa ser depois do início.");
    ac.precos.push(p);
    evento("preco " + ac.precos.length, "registrado");
    gravou("Preço registrado.");
  },
  acao(form) {
    const chave = form.dataset.chave;
    if (!exigirNome(chave)) return;
    const invId = form.dataset.inv ? Number(form.dataset.inv) : null;
    const it = { id: proxId(ac.acoes), data: val(chave + "-data"), tipo: val(chave + "-tipo"), descricao: val(chave + "-desc"), responsavel: val(chave + "-resp") || null, custo: numero(chave + "-custo"), origem: val(chave + "-origem") || null, concomitantes: val(chave + "-conc").split("\n").map((x) => x.trim()).filter(Boolean), inv: invId, avaliacao: null };
    if (!it.data) return erroEm(chave, "Informe a data da ação.");
    if (!it.descricao) return erroEm(chave, "Campo obrigatório: descricao.");
    if (it.custo !== null && (it.custo < 0 || !it.origem)) return erroEm(chave, "Custo da intervenção precisa ser não negativo e ter origem declarada.");
    ac.acoes.push(it);
    evento(`intervencao ${it.id}`, "registrada");
    const inv = invId ? ac.invs.find((x) => x.id === invId) : null;
    if (inv) {
      inv.eventos.push({ quando: agora(), tipo: "acao", autor: nome(), texto: it.descricao });
      if (AC.transicoes[inv.estado].includes("acao_registrada")) {
        inv.estado = "acao_registrada";
        inv.eventos.push({ quando: agora(), tipo: "estado", autor: nome(), texto: "Ação registrada." });
      }
      inv.atualizada = agora();
    }
    gravou("Ação registrada. Avalie quando houver períodos completos depois dela.");
  },
  evidencia(form) {
    if (!exigirNome("evidencia")) return;
    const inv = ac.invs.find((x) => x.id === Number(form.dataset.inv));
    const texto = val("evid-texto");
    if (!texto) return erroEm("evidencia", "Campo obrigatório: texto.");
    inv.eventos.push({ quando: agora(), tipo: "evidencia", autor: nome(), texto: texto + (val("evid-ref") ? ` (${val("evid-ref")})` : "") });
    inv.atualizada = agora();
    evento(`investigacao ${inv.id}`, "evidencia");
    gravou("Evidência registrada.");
  },
  estado(form) {
    if (!exigirNome("estado")) return;
    const inv = ac.invs.find((x) => x.id === Number(form.dataset.inv));
    const novo = val("estado-novo"), motivo = val("estado-motivo");
    if (!motivo) return erroEm("estado", "Campo obrigatório: motivo.");
    inv.eventos.push({ quando: agora(), tipo: "estado", autor: nome(), texto: motivo });
    inv.estado = novo;
    inv.atualizada = agora();
    evento(`investigacao ${inv.id}`, "estado:" + novo);
    gravou("Situação atualizada.");
  },
  responsavel(form) {
    if (!exigirNome("responsavel")) return;
    const inv = ac.invs.find((x) => x.id === Number(form.dataset.inv));
    const resp = val("resp-nome");
    if (!resp) return erroEm("responsavel", "Campo obrigatório: responsavel.");
    inv.eventos.push({ quando: agora(), tipo: "responsavel", autor: nome(), texto: resp });
    inv.responsavel = resp;
    inv.atualizada = agora();
    gravou("Responsável definido.");
  },
  encerrar(form) {
    if (!exigirNome("encerrar")) return;
    const inv = ac.invs.find((x) => x.id === Number(form.dataset.inv));
    const motivo = val("enc-motivo");
    if (!motivo) return erroEm("encerrar", "Campo obrigatório: motivo.");
    inv.resultado = val("enc-resultado");
    inv.motivoEnc = motivo;
    inv.estado = "encerrada";
    inv.eventos.push({ quando: agora(), tipo: "encerrada", autor: nome(), texto: motivo });
    inv.atualizada = agora();
    evento(`investigacao ${inv.id}`, "encerrada");
    gravou("Investigação encerrada.");
  },
  reabrir(form) {
    if (!exigirNome("reabrir")) return;
    const inv = ac.invs.find((x) => x.id === Number(form.dataset.inv));
    const motivo = val("reabrir-motivo");
    if (!motivo) return erroEm("reabrir", "Campo obrigatório: motivo.");
    inv.eventos.push({ quando: agora(), tipo: "estado", autor: nome(), texto: motivo });
    inv.estado = "em_investigacao";
    inv.atualizada = agora();
    evento(`investigacao ${inv.id}`, "estado:em_investigacao");
    gravou("Reaberta.");
  },
  custo() {
    if (!exigirNome("custo")) return;
    const c = { data: val("custo-data"), tipo: val("custo-tipo"), valor: numero("custo-valor"), descricao: val("custo-desc"), origem: val("custo-origem") };
    if (!c.data || c.valor === null) return erroEm("custo", "Informe data e valor.");
    if (!c.descricao || !c.origem) return erroEm("custo", `Campo obrigatório: ${[!c.descricao && "descricao", !c.origem && "origem"].filter(Boolean).join(", ")}.`);
    if (c.valor < 0) return erroEm("custo", "Tipo de custo desconhecido ou valor negativo.");
    c.tipoRot = { medicao: "medicao", acompanhamento: "acompanhamento", outro: "outro" }[c.tipo];
    ac.custos.push(c);
    evento("custo " + ac.custos.length, "registrado");
    gravou("Custo registrado.");
  },
};
const ACOES = {
  "criar-demo": criarDemo,
  produzir,
  abrir: (el) => abrirInvestigacao(Number(el.dataset.fech)),
  avaliar: (el) => avaliar(Number(el.dataset.id)),
  "aba-atualizar": (el) => { ac.abaAtualizar = Number(el.dataset.i); ac.erro = null; guardar(); mostrar(); },
  "aba-acoes": (el) => { ac.abaAcoes = Number(el.dataset.i); ac.erro = null; guardar(); mostrar(); },
  "aba-inv": (el) => { ac.abaInv[el.dataset.inv] = Number(el.dataset.i); ac.erro = null; guardar(); mostrar(); },
  serie: () => { estado.ato = "1"; toast("Série carregada: abra Investigação, Saúde ou Financeiro para analisar."); ir("saude"); },
  recomecar: () => { const autor = ac.autor; ac = novoAcomp(); ac.autor = autor; gravou("Demonstração apagada desta página."); },
};
