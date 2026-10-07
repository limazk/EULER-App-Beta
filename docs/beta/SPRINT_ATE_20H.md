# Sprint EULER Beta — alvo 08/10/2026 20:00 BRT

Objetivo: entregar a melhor versão **testável por usuários reais** sem arriscar o motor
científico. Não tentar finalizar desktop + Android + API nova simultaneamente.

## P0 — precisa funcionar antes do prazo

- [ ] Supabase criado e migration aplicada — **HUMANO**
- [ ] Cadastro/login/bloqueio por aprovação — **CHATGPT**
- [ ] Painel admin: aprovar, suspender, rejeitar — **CHATGPT**
- [ ] Organizações + papéis — **CHATGPT**
- [ ] Testes do software existente continuam passando — **CODEX**
- [ ] Teste manual com 2 contas reais — **HUMANO + CODEX**
- [ ] Deploy web acessível aos testers — **CODEX/HUMANO**
- [ ] Corrigir regressões descobertas — **CHATGPT/CODEX**

## P1 — fazer se P0 estiver verde

- [ ] Polimento responsivo das telas críticas — **CODEX**
- [ ] Página Conta / organização atual — **CHATGPT**
- [ ] Feedback de beta / reportar bug — **CHATGPT**
- [ ] Changelog e versão beta visível — **CHATGPT**
- [ ] Workflow de release e build desktop inicial — **CODEX**

## P2 — não sacrificar P0 para fazer

- [ ] Tauri completo
- [ ] instalador Windows assinado
- [ ] Linux AppImage
- [ ] APK/AAB
- [ ] updater nativo
- [ ] migração completa Streamlit -> React/FastAPI

Esses itens continuam sendo objetivo do produto, mas tentar terminá-los antes do beta web
estar estável aumenta muito o risco de não haver nenhuma versão funcional às 20h.

## Critério de entrega

Às 20h, um tester deve conseguir:

1. abrir uma URL;
2. criar uma conta;
3. ficar bloqueado até aprovação;
4. ser aprovado pelo administrador;
5. entrar e usar as funcionalidades existentes da EULER;
6. ter seus dados de identidade associados a uma organização;
7. ser suspenso imediatamente pelo administrador.

O motor científico deve permanecer com os testes existentes verdes.
