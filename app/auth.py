"""Autenticação e autorização do beta EULER via Supabase.

A chave pública é usada para cadastro/login. A chave secreta só é usada em
operações administrativas executadas no servidor Streamlit.
"""

from __future__ import annotations

import os
import time
from datetime import UTC, datetime

import streamlit as st

from supabase import Client, create_client

TOKEN_ACCESS = "_euler_access_token"
TOKEN_REFRESH = "_euler_refresh_token"
CTX = "_euler_auth_context"
CTX_VALIDATED_AT = "_euler_auth_context_validated_at"
AUTH_CONTEXT_TTL_SECONDS = 45.0


def _modo_teste() -> bool:
    return os.environ.get("EULER_TEST_BYPASS_AUTH") == "1"


def _contexto_teste() -> dict:
    return {
        "user_id": "test-user",
        "email": "test@euler.local",
        "profile": {
            "full_name": "Teste automatizado",
            "status": "active",
            "is_superadmin": True,
        },
        "memberships": [],
        "is_superadmin": True,
    }


def _segredo(*nomes: str) -> str:
    for nome in nomes:
        valor = os.environ.get(nome)
        if valor:
            return valor
        try:
            valor = st.secrets.get(nome)
        except Exception:  # noqa: BLE001
            valor = None
        if valor:
            return str(valor)
    return ""


def configuracao() -> dict[str, str]:
    return {
        "url": _segredo("SUPABASE_URL"),
        "public_key": _segredo("SUPABASE_PUBLISHABLE_KEY", "SUPABASE_ANON_KEY"),
        "secret_key": _segredo("SUPABASE_SECRET_KEY", "SUPABASE_SERVICE_ROLE_KEY"),
    }


def configurado() -> bool:
    cfg = configuracao()
    return bool(cfg["url"] and cfg["public_key"])


def _cliente_usuario() -> Client:
    cfg = configuracao()
    if not cfg["url"] or not cfg["public_key"]:
        raise RuntimeError("Supabase não configurado.")
    cliente = create_client(cfg["url"], cfg["public_key"])
    access = st.session_state.get(TOKEN_ACCESS)
    refresh = st.session_state.get(TOKEN_REFRESH)
    if access and refresh:
        try:
            sessao = cliente.auth.set_session(access, refresh)
            if sessao and sessao.session:
                _guardar_sessao(sessao.session)
        except Exception:  # noqa: BLE001
            limpar_sessao()
    return cliente


def _cliente_admin() -> Client:
    cfg = configuracao()
    if not cfg["url"] or not cfg["secret_key"]:
        raise RuntimeError("SUPABASE_SECRET_KEY não configurada no servidor.")
    # Workaround para regressão do supabase-py em ClientOptions que pode lançar
    # AttributeError: 'ClientOptions' object has no attribute 'storage'.
    # O cliente administrativo roda apenas no servidor e não cria sessão de usuário,
    # então os defaults do SDK são suficientes aqui.
    return create_client(cfg["url"], cfg["secret_key"])


def _invalidar_contexto() -> None:
    """Descarta autorização derivada da sessão sem remover os tokens de login."""
    st.session_state.pop(CTX, None)
    st.session_state.pop(CTX_VALIDATED_AT, None)


def _guardar_sessao(sessao) -> None:
    st.session_state[TOKEN_ACCESS] = sessao.access_token
    st.session_state[TOKEN_REFRESH] = sessao.refresh_token
    _invalidar_contexto()


def limpar_sessao() -> None:
    for chave in (TOKEN_ACCESS, TOKEN_REFRESH, CTX, CTX_VALIDATED_AT):
        st.session_state.pop(chave, None)


def cadastrar(nome: str, email: str, senha: str) -> tuple[bool, str]:
    nome = nome.strip()
    email = email.strip().lower()
    if len(nome) < 2:
        return False, "Informe seu nome."
    if "@" not in email:
        return False, "Informe um e-mail válido."
    if len(senha) < 8:
        return False, "A senha precisa ter pelo menos 8 caracteres."
    try:
        resposta = _cliente_usuario().auth.sign_up(
            {
                "email": email,
                "password": senha,
                "options": {"data": {"full_name": nome}},
            }
        )
        if resposta.session:
            _guardar_sessao(resposta.session)
        return True, "Cadastro criado. Sua conta ficará aguardando aprovação."
    except Exception:  # noqa: BLE001
        return False, "Não foi possível criar a conta. Confira os dados ou tente novamente."


def entrar(email: str, senha: str) -> tuple[bool, str]:
    try:
        resposta = _cliente_usuario().auth.sign_in_with_password(
            {"email": email.strip().lower(), "password": senha}
        )
        if not resposta.session:
            return False, "Login não retornou uma sessão válida."
        _guardar_sessao(resposta.session)
        return True, ""
    except Exception:  # noqa: BLE001
        return False, "E-mail ou senha inválidos."


def recuperar_senha(email: str) -> tuple[bool, str]:
    """Solicita ao Supabase um link de recuperação sem revelar se a conta existe."""
    email = email.strip().lower()
    if "@" not in email:
        return False, "Informe um e-mail válido."
    try:
        opcoes = {}
        if redirecionamento := os.environ.get("EULER_PASSWORD_RESET_REDIRECT_URL"):
            opcoes["redirect_to"] = redirecionamento
        _cliente_usuario().auth.reset_password_for_email(email, opcoes or None)
        return True, "Se o e-mail estiver cadastrado, você receberá um link para redefinir a senha."
    except Exception:  # noqa: BLE001
        return False, "Não foi possível enviar o link agora. Tente novamente em alguns minutos."


def redefinir_senha(senha: str, confirmar: str) -> tuple[bool, str]:
    if len(senha) < 8:
        return False, "A nova senha precisa ter pelo menos 8 caracteres."
    if senha != confirmar:
        return False, "As senhas não coincidem."
    try:
        cliente = _cliente_usuario()
        cliente.auth.update_user({"password": senha})
        cliente.auth.sign_out()
        limpar_sessao()
        st.session_state.pop("_euler_password_recovery", None)
        return True, "Senha atualizada. Você já pode entrar."
    except Exception:  # noqa: BLE001
        return False, "O link expirou ou já foi usado. Solicite uma nova recuperação."


def _receber_recuperacao() -> bool:
    """Troca o código PKCE da URL por uma sessão apta a atualizar a senha."""
    if st.session_state.get("_euler_password_recovery"):
        return True
    token_hash = st.query_params.get("token_hash")
    codigo = st.query_params.get("code")
    if not token_hash and not codigo:
        return False
    try:
        cliente = _cliente_usuario()
        if token_hash:
            resposta = cliente.auth.verify_otp({"token_hash": token_hash, "type": "recovery"})
        else:
            resposta = cliente.auth.exchange_code_for_session({"auth_code": codigo})
        if resposta.session:
            _guardar_sessao(resposta.session)
            st.session_state["_euler_password_recovery"] = True
            st.query_params.clear()
            return True
    except Exception:  # noqa: BLE001
        st.error("O link de recuperação expirou ou é inválido. Solicite um novo link.")
    return False


def sair() -> None:
    try:
        cliente = _cliente_usuario()
        cliente.auth.sign_out()
    except Exception:  # noqa: BLE001
        st.session_state["_euler_remote_signout_failed"] = True
    limpar_sessao()


def _usuario_validado():
    access = st.session_state.get(TOKEN_ACCESS)
    if not access:
        return None
    try:
        resposta = _cliente_usuario().auth.get_user(access)
        return resposta.user
    except Exception:  # noqa: BLE001
        limpar_sessao()
        return None


def _carregar_contexto() -> dict | None:
    usuario = _usuario_validado()
    if not usuario:
        return None
    cliente = _cliente_usuario()
    perfil_resp = cliente.table("profiles").select("*").eq("id", str(usuario.id)).limit(1).execute()
    if not perfil_resp.data:
        return None
    perfil = perfil_resp.data[0]
    membros_resp = (
        cliente.table("memberships")
        .select("organization_id,role,status,organizations(id,name,slug,status)")
        .eq("user_id", str(usuario.id))
        .eq("status", "active")
        .execute()
    )
    ctx = {
        "user_id": str(usuario.id),
        "email": getattr(usuario, "email", None) or perfil.get("email"),
        "profile": perfil,
        "memberships": membros_resp.data or [],
        "is_superadmin": bool(perfil.get("is_superadmin")),
    }
    st.session_state[CTX] = ctx
    st.session_state[CTX_VALIDATED_AT] = time.monotonic()
    return ctx


def contexto_atual(*, recarregar: bool = False) -> dict | None:
    """Reutiliza por poucos segundos o contexto já validado nesta sessão."""
    if _modo_teste():
        ctx = st.session_state.get(CTX) or _contexto_teste()
        st.session_state[CTX] = ctx
        return ctx

    ctx = st.session_state.get(CTX)
    validado_em = st.session_state.get(CTX_VALIDATED_AT)
    dentro_do_ttl = (
        ctx is not None
        and validado_em is not None
        and time.monotonic() - float(validado_em) < AUTH_CONTEXT_TTL_SECONDS
    )
    if not recarregar and dentro_do_ttl:
        return ctx
    return _carregar_contexto()


def registrar_atividade(ctx: dict) -> None:
    if st.session_state.get("_euler_last_seen_registered"):
        return
    try:
        admin = _cliente_admin()
        admin.table("profiles").update({"last_seen_at": datetime.now(UTC).isoformat()}).eq(
            "id", ctx["user_id"]
        ).execute()
        st.session_state["_euler_last_seen_registered"] = True
    except Exception:  # noqa: BLE001
        st.session_state["_euler_last_seen_failed"] = True


def _tela_login() -> None:
    st.markdown("# EULER")
    st.caption("Beta · investigação física para caldeiras industriais")

    if _receber_recuperacao():
        st.subheader("Definir nova senha")
        with st.form("redefinir-senha"):
            nova = st.text_input("Nova senha", type="password")
            confirmar_nova = st.text_input("Confirmar nova senha", type="password")
            atualizar = st.form_submit_button(
                "Atualizar senha", type="primary", use_container_width=True
            )
        if atualizar:
            with st.spinner("Atualizando senha…"):
                ok, mensagem = redefinir_senha(nova, confirmar_nova)
            (st.success if ok else st.error)(mensagem)
        return

    st.markdown("## Acessar")
    st.caption("Contas novas precisam de aprovação.")

    aba_login, aba_cadastro = st.tabs(["Entrar", "Criar conta"])
    with aba_login:
        with st.form("login-euler"):
            email = st.text_input("E-mail")
            senha = st.text_input("Senha", type="password")
            enviar = st.form_submit_button("Entrar", type="primary", use_container_width=True)
        if enviar:
            with st.spinner("Entrando…"):
                ok, mensagem = entrar(email, senha)
            if ok:
                st.rerun()
            st.error(mensagem)

        with st.expander("Esqueci minha senha"):
            with st.form("recuperar-senha"):
                email_recuperacao = st.text_input("E-mail da conta")
                recuperar = st.form_submit_button("Enviar link", use_container_width=True)
            if recuperar:
                with st.spinner("Enviando link…"):
                    ok, mensagem = recuperar_senha(email_recuperacao)
                (st.success if ok else st.error)(mensagem)

    with aba_cadastro:
        with st.form("cadastro-euler"):
            nome = st.text_input("Nome completo")
            email_novo = st.text_input("E-mail", key="cadastro-email")
            senha_nova = st.text_input("Senha", type="password", key="cadastro-senha")
            confirmar = st.text_input("Confirmar senha", type="password", key="cadastro-confirmar")
            criar = st.form_submit_button("Criar conta", type="primary", use_container_width=True)
        if criar:
            if senha_nova != confirmar:
                st.error("As senhas não coincidem.")
            else:
                with st.spinner("Criando conta…"):
                    ok, mensagem = cadastrar(nome, email_novo, senha_nova)
                if ok:
                    st.success(mensagem)
                    if st.session_state.get(TOKEN_ACCESS):
                        st.rerun()
                else:
                    st.error(mensagem)


def exigir_acesso() -> dict:
    # Exclusivo para a suíte automatizada. Produção continua fail-closed sem Supabase.
    if _modo_teste():
        ctx = _contexto_teste()
        st.session_state[CTX] = ctx
        return ctx

    if not configurado():
        st.error("O login do beta ainda não foi configurado neste ambiente.")
        st.code(
            "SUPABASE_URL=...\nSUPABASE_PUBLISHABLE_KEY=...\nSUPABASE_SECRET_KEY=...",
            language="text",
        )
        st.caption("Veja docs/beta/SETUP_SUPABASE.md.")
        st.stop()

    if not st.session_state.get(TOKEN_ACCESS):
        _tela_login()
        st.stop()

    ctx = contexto_atual()
    if not ctx:
        limpar_sessao()
        st.error("Não foi possível carregar seu perfil.")
        st.stop()

    status = ctx["profile"].get("status", "pending")
    if status != "active":
        st.markdown("## Conta aguardando liberação")
        if status == "pending":
            st.info(
                "Seu cadastro foi recebido. Um administrador da EULER precisa aprovar o acesso."
            )
        elif status == "suspended":
            st.warning("Esta conta está suspensa. Fale com um administrador.")
        else:
            st.error("Este cadastro não está autorizado a acessar a EULER.")
        st.caption(f"Conta: {ctx.get('email') or 'e-mail não disponível'}")
        if st.button("Sair"):
            sair()
            st.rerun()
        st.stop()

    if not ctx.get("is_superadmin") and not ctx.get("memberships"):
        st.markdown("## Conta aprovada")
        st.info(
            "Seu acesso foi aprovado. Falta um administrador vincular sua conta "
            "a uma empresa antes de liberar os dados da EULER."
        )
        if st.button("Sair", key="sair-sem-organizacao"):
            sair()
            st.rerun()
        st.stop()

    if not ctx.get("is_superadmin") and ctx.get("memberships"):
        org = ctx["memberships"][0].get("organizations") or {}
        if org.get("status") != "active":
            st.markdown("## Empresa temporariamente suspensa")
            st.warning(
                "O acesso desta organização está suspenso. "
                "Entre em contato com a administração da EULER."
            )
            if st.button("Sair", key="sair-org-suspensa"):
                sair()
                st.rerun()
            st.stop()

    registrar_atividade(ctx)
    return ctx


def painel_conta_sidebar(ctx: dict) -> None:
    perfil = ctx["profile"]
    with st.sidebar:
        st.divider()
        st.caption("CONTA")
        st.write(perfil.get("full_name") or ctx.get("email") or "Usuário")
        if ctx["memberships"]:
            org = ctx["memberships"][0].get("organizations") or {}
            if org:
                st.caption(org.get("name", "Organização"))
        if ctx.get("is_superadmin"):
            st.caption("Administrador EULER")
        if st.button("Sair", key="logout-euler", use_container_width=True):
            sair()
            st.rerun()


def exigir_superadmin() -> dict:
    ctx = contexto_atual(recarregar=True)
    if not ctx or not ctx.get("is_superadmin") or ctx["profile"].get("status") != "active":
        st.error("Acesso restrito à administração da EULER.")
        st.stop()
    return ctx


def listar_perfis() -> list[dict]:
    if _modo_teste():
        return []
    resposta = (
        _cliente_admin().table("profiles").select("*").order("created_at", desc=True).execute()
    )
    return resposta.data or []


def atualizar_status_usuario(user_id: str, status: str) -> None:
    if status not in {"pending", "active", "suspended", "rejected"}:
        raise ValueError("Status inválido.")
    dados: dict[str, str | None] = {"status": status}
    if status == "active":
        dados["approved_at"] = datetime.now(UTC).isoformat()
    _cliente_admin().table("profiles").update(dados).eq("id", user_id).execute()
    _invalidar_contexto()


def listar_organizacoes() -> list[dict]:
    if _modo_teste():
        return []
    resposta = _cliente_admin().table("organizations").select("*").order("name").execute()
    return resposta.data or []


def criar_organizacao(nome: str, slug: str) -> None:
    nome = nome.strip()
    slug = slug.strip().lower()
    if not nome or not slug:
        raise ValueError("Nome e identificador são obrigatórios.")
    _cliente_admin().table("organizations").insert(
        {"name": nome, "slug": slug, "status": "active"}
    ).execute()


def atualizar_status_organizacao(organization_id: str, status: str) -> None:
    if status not in {"active", "suspended"}:
        raise ValueError("Status de organização inválido.")
    _cliente_admin().table("organizations").update({"status": status}).eq(
        "id", organization_id
    ).execute()
    _invalidar_contexto()


def vincular_usuario(user_id: str, organization_id: str, role: str) -> None:
    if role not in {"admin", "engineer", "operator", "viewer"}:
        raise ValueError("Perfil de acesso inválido.")
    _cliente_admin().table("memberships").upsert(
        {
            "user_id": user_id,
            "organization_id": organization_id,
            "role": role,
            "status": "active",
        },
        on_conflict="organization_id,user_id",
    ).execute()
    _invalidar_contexto()


def enviar_feedback(tipo: str, mensagem: str, pagina: str = "") -> None:
    """Registra feedback do usuário autenticado sem expor privilégios administrativos."""
    tipos = {"bug", "melhoria", "duvida", "outro"}
    if tipo not in tipos:
        raise ValueError("Tipo de feedback inválido.")
    mensagem = mensagem.strip()
    if len(mensagem) < 5 or len(mensagem) > 4000:
        raise ValueError("Descreva o feedback entre 5 e 4000 caracteres.")

    ctx = contexto_atual(recarregar=True)
    if not ctx:
        raise RuntimeError("Sessão não encontrada.")

    memberships = ctx.get("memberships") or []
    organization_id = memberships[0]["organization_id"] if memberships else None
    _cliente_usuario().table("feedback").insert(
        {
            "user_id": ctx["user_id"],
            "organization_id": organization_id,
            "type": tipo,
            "message": mensagem,
            "page": pagina.strip()[:200],
        }
    ).execute()


def listar_feedback() -> list[dict]:
    if _modo_teste():
        return []
    resposta = (
        _cliente_admin()
        .table("feedback")
        .select("*")
        .order("created_at", desc=True)
        .limit(100)
        .execute()
    )
    return resposta.data or []
