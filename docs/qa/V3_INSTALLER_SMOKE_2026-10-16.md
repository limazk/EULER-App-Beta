# EULER 3.0 — Relatório de smoke test dos instaladores (Linux)

**Data:** 16/10/2026  
**Origem dos testes de runtime:** transcrição de execução do Antigravity disponibilizada pelo solicitante.  
**Auditoria complementar:** GitHub API (workflows, artefatos e configuração Tauri).  
**Classificação:** **VALIDAÇÃO PARCIAL — GATE G3 EM ABERTO**  
**Escopo:** documentação e consolidação das evidências já existentes. Este relatório **não representa uma nova execução dos instaladores pelo ChatGPT**.

## 1. Referências técnicas verificadas

- Repositório: https://github.com/limazk/EULER-App-Beta
- PR principal: https://github.com/limazk/EULER-App-Beta/pull/29 — aberto e draft no momento da auditoria
- Commit final da candidata PR #29: `8d89de9395f9a0fcfdc829e3b88280202982ec28`
- Run Tauri: https://github.com/limazk/EULER-App-Beta/actions/runs/38211447620 — jobs **Build Windows: success** e **Build Linux: success**
- Commit de origem do run dos artefatos: `32ed4e88314f94f2b5611a709e09458511ad2724`. O PR #29 registra que a árvore deste commit é idêntica à árvore de seu merge final. Essa afirmação de equivalência deve ser revalidada antes de publicar versões.
- Configuração verificada em `apps/euler-shell/src-tauri/tauri.conf.json`: versão `0.1.0-beta.1`; janela `splash` **620×420**; janela `main` **1440×900**; URL remota da janela principal `https://euler-app-beta.onrender.com`.

### Artefatos do workflow confirmados na API do GitHub

| Artefato de workflow | ID | Estado | SHA-256 do arquivo ZIP do artefato (informado pelo GitHub) |
|---|---:|---|---|
| `euler-linux` | `11728924078` | `expired=false` | `c494cd3a810f3f0538dc4878300949e7ae415a0aead925558cf3cf4222bcb438` |
| `euler-windows` | `11729721134` | `expired=false` | `eebf5a9474f114b0e29cfefd92925bf690ab07dc707da1312207803ef5e93ce1` |

**Atenção:** os SHA-256 acima são os *digests dos arquivos ZIP publicados como artefatos pelo GitHub*. **Não** são hashes individuais do AppImage, .deb ou .exe. A transcrição não trouxe checksums individuais dos executáveis usados pelo Antigravity, portanto a igualdade byte a byte entre cópias locais e artefatos precisa ser documentada com `sha256sum` / `certutil` em cada sistema.

## 2. Ambiente declarado pelo agente de QA

- Sistema disponível: Linux.
- Teste gráfico: `Xvfb` (display virtual headless) com `xdotool` disponíveis.
- Caminhos mencionados para os pacotes:
  - `/home/lz/EULER-App-Beta/qa-artifacts/euler-linux/appimage/EULER_0.1.0-beta.1_amd64.AppImage`
  - `/home/lz/EULER-App-Beta/qa-artifacts/euler-linux/deb/EULER_0.1.0-beta.1_amd64.deb`
- Distribuição, versão do kernel, arquitetura real da máquina, bibliotecas gráficas e versões de `Xvfb`/`xdotool`: **não informadas**.
- Nenhum teste Windows foi executado pelo agente nessa sessão.

## 3. Resultados registrados, com nível de evidência explícito

| Caso | Resultado | Evidência/limitação |
|---|---|---|
| GitHub Actions: build Linux e Windows | **CONFIRMADO** | GitHub retornou ambos os jobs como `success`; isso prova compilação/publicação, não execução nativa |
| AppImage: bit de execução | **RELATADO PASS** | Agente executou `chmod +x` e informou que o arquivo ficou executável; saída integral do terminal não compartilhada |
| AppImage: inicialização em Linux/Xvfb | **RELATADO PASS** | Agente informou que processo permaneceu em execução; não há log/screenshot bruto anexado |
| Splash `EULER` (620×420) | **RELATADO PASS + CONFIGURAÇÃO CONFIRMADA** | Agente informou detecção da janela por `xdotool`; dimensões batem com `tauri.conf.json` |
| Janela principal `EULER` (1440×900) | **RELATADO PASS + CONFIGURAÇÃO CONFIRMADA** | Janela detectada no display virtual; **não confirma conteúdo da EULER 3.0 carregado** |
| Encerramento via `SIGTERM` | **RELATADO PASS** | Saída limpa mencionada pelo agente; fechamento via botão da GUI não demonstrado |
| AppImage com `--version` | **NÃO CONCLUSIVO** | Flag não respondeu com versão; aplicativo entrou em execução até timeout; não constitui falha de empacotamento |
| Pacote `.deb` — metadados e estrutura | **RELATADO PASS** | Agente executou `dpkg -I` e inspecionou conteúdo; saída bruta não incluída na transcrição |
| Binário extraído do `.deb` | **RELATADO PASS SEM DETALHES** | Agente anunciou teste e depois resumiu “todos os testes Linux passaram”; faltam comandos, logs e critérios de saída |
| Instalação de `.deb` no sistema e desinstalação | **NÃO EXECUTADO / NÃO COMPROVADO** | Extração ou execução de binário não substitui instalação pelo gerenciador de pacotes |
| Offline, reconexão e recuperação | **RELATADO PASS SEM EVIDÊNCIA DETALHADA** | Agente relatou todos os testes Linux aprovados, mas não apresentou métricas, janelas de tempo, capturas ou verificações concretas |
| Serviço remoto Render | **CONFIGURAÇÃO CONFIRMADA** | `tauri.conf.json` aponta para o Render; monitoramento de deploy identificou `42e28e8` (main antiga), não EULER 3.0 |
| Login/expiração/suspensão/isolamento com Supabase real | **BLOQUEADO / NÃO EXECUTADO** | Supabase `EULER` reportado `INACTIVE` na auditoria de 16/10; não há contas de teste e evidências reais fornecidas |
| Instalação/execução Windows NSIS | **NÃO EXECUTADO** | Houve apenas build CI; é necessário testar em Windows real ou VM autorizada |
| Aplicativo 3.0 de ponta a ponta em desktop | **NÃO EXECUTADO** | Shell Tauri está configurado para Render, que ainda serve commit da `main` anterior à v3 |

**Critério de leitura:** “RELATADO PASS” significa *resultado declarado pelo Antigravity na transcrição do usuário*; não significa reproduzido ou auditado independentemente. Só “CONFIRMADO” identifica uma observação recuperada no GitHub.

## 4. Bloqueadores para concluir G3

1. Reproduzir/salvar logs brutos e capturas da detecção das janelas `splash` e `main` no Linux; registrar a distro/versão e os checksums individuais.
2. Testar instalação e remoção do `.deb` (ou marcar como não aplicável, com justificativa).
3. Executar ou obter evidência de teste do NSIS em Windows real/VM autorizada: instalação, abertura, encerramento, reinício e remoção.
4. Validar visualmente cold start, indisponibilidade de rede, reconexão e fluxos funcionais, com critérios de resultado claros.
5. Disponibilizar ambiente de homologação apontando à EULER 3.0 e Supabase funcional com contas autorizadas **sem trocar URL de produção nem publicar na main**.
6. Validar que a janela principal mostra a candidata 3.0, não apenas o Streamlit da versão antiga.

## 5. Recomendações para reprodução Linux

Executar **somente** no ambiente de testes autorizado:

```bash
sha256sum qa-artifacts/euler-linux/appimage/*.AppImage
sha256sum qa-artifacts/euler-linux/deb/*.deb
dpkg -I qa-artifacts/euler-linux/deb/*.deb
```

Capturar logs (sem incluir senhas, tokens ou dados empresariais); preservar a identificação da distribuição e screenshots no relatório, caso disponíveis. Para o Windows, executar os testes em computador/VM Windows autorizado, em vez de inferir sucesso do CI.

## 6. Resumo de qualidade

**Aprovado parcialmente:**

- Geração de artefatos Linux e Windows pelo CI.
- Smoke test de inicialização e detecção de janelas do AppImage Linux, **conforme relato do agente**.
- Coerência dos tamanhos das janelas com a configuração versionada.

**Não aprovado para fechar o gate G3:**

- Instalação e desinstalação completas `.deb` e `.exe` em sistemas de destino.
- Testes Windows.
- Comportamento offline/reconexão com evidência auditável.
- Autenticação com contas reais.
- Execução funcional **da versão 3.0** no shell desktop.

**Decisão:** **G3 PARCIAL / PENDENTE. Não fazer merge/deploy com base exclusivamente neste smoke test.**

## 7. Isolamento e rastreabilidade

Documento produzido em branch `qa/v3-installers-antigravity-20261016` derivada da `main` para preservar o trabalho interrompido por limite de uso. Nenhum arquivo da aplicação, shell Tauri, pipeline ou branch de integração foi alterado. Ao retomar Antigravity, sincronizar primeiro com esta branch remota para evitar commits divergentes; completar aqui as evidências faltantes em commits adicionais.

---

## 8. Validação independente de QA — ChatGPT, 16/10/2026

Esta seção **complementa** os testes relatados pelo Antigravity com execuções **novas** sobre os próprios artefatos oficiais GitHub Actions. Os testes de Windows, instalação nativa .deb, login real e interface EULER 3.0 **não** foram realizados.

### Ambiente

- Debian GNU/Linux 13 (trixie), x86_64; kernel Linux 6.18.55; container isolado.
- Xvfb 1600×1000, Openbox, WebKitGTK, sessão D-Bus e renderização GL por software.
- Sem /dev/fuse: AppImage executado via APPIMAGE_EXTRACT_AND_RUN=1 e --appimage-extract-and-run. Isto testa o conteúdo oficial, **não** a montagem FUSE em desktop físico.
- Shell Tauri configurado com https://euler-app-beta.onrender.com (verificado no arquivo versionado tauri.conf.json).
- Artefatos recuperados diretamente do run https://github.com/limazk/EULER-App-Beta/actions/runs/38211447620.

Os ZIPs oficiais tiveram SHA-256 calculado e coincidente com o digest anunciado pelo GitHub:

- Linux ZIP: c494cd3a810f3f0538dc4878300949e7ae415a0aead925558cf3cf4222bcb438.
- Windows ZIP: eebf5a9474f114b0e29cfefd92925bf690ab07dc707da1312207803ef5e93ce1.

### SHA-256 dos instaladores individuais (novo)

| Binário extraído do ZIP oficial | SHA-256 calculado |
| --- | --- |
| EULER_0.1.0-beta.1_amd64.AppImage | 666944f428c3cbe34657b080366c5f2db123d243677e9537480e66fdfecc6b78 |
| EULER_0.1.0-beta.1_amd64.deb | 1bed3e232ada0d08da48dd456857a3f992f43f175affadd2e2421cbe83c101c5 |
| EULER_0.1.0-beta.1_x64-setup.exe | 375eb281abc653b9aab5ea92a4a51fd9b2911dd8c089dde696635f20b1107cbe |

Estes são hashes individuais, **diferentes** dos ZIPs do workflow.

### Matriz de testes reproduzidos

| Teste | Resultado verificado |
| --- | --- |
| AppImage abre em display virtual | PASS — processo ELF iniciado e ativo por pelo menos 13s; janela EULER detectada por wmctrl |
| Splash local | PASS — captura de 1s mostra logo, animação de espera e texto “Conectando à EULER...” |
| Carregamento remoto | BLOQUEADO — após ~9s, o WebKit exibiu “Error resolving ‘euler-app-beta.onrender.com’: Temporary failure in name resolution” |
| Encerramento de processo | PASS limitado — SIGTERM controlado pelo executor; **não** é prova de fechamento pelo botão da janela |
| Pacote .deb: metadados | PASS — versão 0.1.0-beta.1, arquitetura amd64; depende de libwebkit2gtk-4.1-0 e libgtk-3-0 |
| Pacote .deb: integridade interna | PASS — extração via dpkg-deb e **5 checksums MD5 válidos / 0 divergências** |
| Pacote .deb: instalação e execução reais | NÃO EXECUTADO — bibliotecas libwebkit2gtk-4.1.so.0 e libjavascriptcoregtk-4.1.so.0 ausentes neste ambiente, não se alterou o sistema |
| Instalador Windows | PASS estático — executável NSIS PE, integridade hash; **execução Windows NÃO EXECUTADA** |
| Offline/retry com serviço acessível | NÃO APROVADO — indisponibilidade de DNS impediu reconexão no teste, não há teste do servidor remoto |
| Login e dashboard v3 | NÃO EXECUTADO — o shell aponta para Render na main antiga; Supabase real não validado |

### Evidências visuais

Foram produzidas novas capturas reais de tela PNG (1600×1000) da execução Linux:
- 1s — splash EULER “Conectando à EULER...” — SHA-256 b3380ce52f69e1bc6cbee39fadf2558e51e0f21dec5e2e5b30660381582e0f18.
- 9s — página WebKit branca com erro DNS — SHA-256 cf4741daede92986b2543ec7f5753473076d3bef75d942b65f3ade7e8692567e.

Essas imagens foram salvas na Library privada do solicitante, respectivamente:
- /EULER/QA/2026-10-16/euler-appimage-splash-linux.png
- /EULER/QA/2026-10-16/euler-appimage-dns-error-linux.png

As capturas NÃO foram commitadas neste PR; as imagens não são públicas no GitHub.

### Achado reproduzível: fallback de erro DNS

Issue: https://github.com/limazk/EULER-App-Beta/issues/36

No ambiente sem DNS, a splash inicial é substituída pela página de erro WebKit. A inspeção do código apps/euler-shell/src-tauri/src/lib.rs revela que PageLoadEvent::Finished exibe a janela principal e esconde a splash sem checar explicitamente sucesso da carga remota. O arquivo apps/euler-shell/dist/startup.js contém estados amigáveis offline e retry, mas não são mantidos visíveis nesse erro reproduzido.

Causa provável, **não comprovada por debugging interno**. Não alteramos o código Tauri nesta branch documental. Recomendado corrigir em PR de código separado, reconstruir artefatos e repetir o teste offline.

### Parecer G3 atualizado

**PARCIAL / PENDENTE.** O AppImage oficial abriu e exibiu splash numa execução independente; os três instaladores tiveram integridade verificada, e o .deb tem manifesto interno íntegro. Porém testes físicos, instalação .deb, Windows, reconexão amigável, autenticação e dashboard v3 continuam pendentes. **Não autoriza merge do PR #29 nem deploy.**
