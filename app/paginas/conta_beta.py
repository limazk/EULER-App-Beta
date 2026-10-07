"""Conta do beta, vínculo organizacional e envio de feedback."""

import streamlit as st
from auth import contexto_atual, enviar_feedback
from componentes import cabecalho

import euler


def renderizar(ctx: dict) -> None:
    cabecalho(
        "Conta e feedback",
        "Veja seu acesso atual e envie problemas ou sugestões do beta.",
        "Beta EULER",
    )

    perfil = ctx["profile"]
    st.subheader("Sua conta")
    c1, c2, c3 = st.columns(3)
    c1.metric("Nome", perfil.get("full_name") or "Não informado")
    c2.metric("Status", perfil.get("status", "desconhecido"))
    c3.metric("Versão", euler.__version__)
    st.caption(ctx.get("email") or "E-mail indisponível")

    st.subheader("Empresa e acesso")
    memberships = ctx.get("memberships") or []
    if memberships:
        membership = memberships[0]
        org = membership.get("organizations") or {}
        st.write(f"**{org.get('name', 'Organização')}**")
        papeis = {
            "admin": "Administrador da empresa",
            "engineer": "Engenheiro",
            "operator": "Operador",
            "viewer": "Visualizador",
        }
        st.caption(f"Perfil: {papeis.get(membership.get('role'), membership.get('role', ''))}")
    elif ctx.get("is_superadmin"):
        st.info("Conta de administração global da EULER.")
    else:
        st.warning("Sua conta ainda não está vinculada a uma organização.")

    st.divider()
    st.subheader("Enviar feedback")
    st.caption("Use isto para reportar bug, dúvida ou melhoria durante o beta.")

    with st.form("feedback-beta"):
        tipo = st.selectbox(
            "Tipo",
            ["bug", "melhoria", "duvida", "outro"],
            format_func=lambda valor: {
                "bug": "Bug",
                "melhoria": "Sugestão de melhoria",
                "duvida": "Dúvida",
                "outro": "Outro",
            }[valor],
        )
        pagina = st.text_input("Tela relacionada (opcional)", placeholder="Ex.: Investigação")
        mensagem = st.text_area(
            "Descrição",
            height=160,
            placeholder="Explique o que aconteceu, o que esperava e como reproduzir, se souber.",
        )
        enviar = st.form_submit_button("Enviar feedback", type="primary")

    if enviar:
        try:
            enviar_feedback(tipo, mensagem, pagina)
            st.success("Feedback enviado. Obrigado por ajudar a testar a EULER.")
        except (RuntimeError, ValueError) as exc:
            st.error(str(exc))
        except Exception as exc:  # noqa: BLE001
            st.error(f"Não foi possível enviar o feedback: {exc}")


ctx = contexto_atual(recarregar=True)
if ctx:
    renderizar(ctx)
else:
    st.error("Não foi possível carregar sua conta.")
