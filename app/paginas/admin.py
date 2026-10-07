"""Painel administrativo do beta EULER."""

import re

import streamlit as st

from auth import (
    atualizar_status_usuario,
    criar_organizacao,
    exigir_superadmin,
    listar_organizacoes,
    listar_perfis,
    vincular_usuario,
)
from componentes import cabecalho

exigir_superadmin()

cabecalho(
    "Administração",
    "Aprove cadastros, suspenda acessos e organize usuários por empresa.",
    "Beta EULER",
)

perfis = listar_perfis()
pendentes = [p for p in perfis if p.get("status") == "pending"]
ativos = [p for p in perfis if p.get("status") == "active"]

c1, c2, c3 = st.columns(3)
c1.metric("Cadastros", len(perfis))
c2.metric("Pendentes", len(pendentes))
c3.metric("Ativos", len(ativos))

st.subheader("Cadastros pendentes")
if not pendentes:
    st.caption("Nenhum cadastro aguardando aprovação.")
for perfil in pendentes:
    with st.container(border=True):
        st.write(f"**{perfil.get('full_name') or 'Sem nome'}**")
        st.caption(perfil.get("email") or perfil["id"])
        aprovar, rejeitar = st.columns(2)
        if aprovar.button("Aprovar", key=f"aprovar-{perfil['id']}", type="primary"):
            atualizar_status_usuario(perfil["id"], "active")
            st.rerun()
        if rejeitar.button("Rejeitar", key=f"rejeitar-{perfil['id']}"):
            atualizar_status_usuario(perfil["id"], "rejected")
            st.rerun()

st.subheader("Usuários")
for perfil in perfis:
    if perfil.get("status") == "pending":
        continue
    with st.expander(
        f"{perfil.get('full_name') or perfil.get('email') or perfil['id']} · {perfil.get('status')}"
    ):
        st.caption(perfil.get("email") or perfil["id"])
        st.write(f"Último acesso: {perfil.get('last_seen_at') or 'ainda não registrado'}")
        cols = st.columns(3)
        if cols[0].button("Ativar", key=f"ativar-{perfil['id']}"):
            atualizar_status_usuario(perfil["id"], "active")
            st.rerun()
        if cols[1].button("Suspender", key=f"suspender-{perfil['id']}"):
            atualizar_status_usuario(perfil["id"], "suspended")
            st.rerun()
        if cols[2].button("Rejeitar", key=f"rej2-{perfil['id']}"):
            atualizar_status_usuario(perfil["id"], "rejected")
            st.rerun()

st.divider()
st.subheader("Empresas / organizações")
organizacoes = listar_organizacoes()

with st.form("nova-organizacao"):
    nome = st.text_input("Nome da organização")
    slug = st.text_input("Identificador", help="Ex.: fabrica-abc")
    criar = st.form_submit_button("Criar organização")
if criar:
    slug_limpo = re.sub(r"[^a-z0-9-]+", "-", slug.lower()).strip("-")
    try:
        criar_organizacao(nome, slug_limpo)
        st.success("Organização criada.")
        st.rerun()
    except Exception as exc:
        st.error(f"Não foi possível criar: {exc}")

if organizacoes and perfis:
    st.subheader("Vincular usuário")
    perfis_opcoes = {
        f"{p.get('full_name') or p.get('email') or p['id']} · {p.get('email') or ''}": p["id"]
        for p in perfis
        if p.get("status") == "active"
    }
    org_opcoes = {o["name"]: o["id"] for o in organizacoes if o.get("status") == "active"}
    if perfis_opcoes and org_opcoes:
        with st.form("vincular-usuario"):
            usuario_label = st.selectbox("Usuário", list(perfis_opcoes))
            org_label = st.selectbox("Organização", list(org_opcoes))
            role = st.selectbox(
                "Perfil",
                ["viewer", "operator", "engineer", "admin"],
                format_func=lambda r: {
                    "viewer": "Visualizador",
                    "operator": "Operador",
                    "engineer": "Engenheiro",
                    "admin": "Administrador da empresa",
                }[r],
            )
            vincular = st.form_submit_button("Vincular")
        if vincular:
            try:
                vincular_usuario(
                    perfis_opcoes[usuario_label],
                    org_opcoes[org_label],
                    role,
                )
                st.success("Usuário vinculado.")
            except Exception as exc:
                st.error(f"Não foi possível vincular: {exc}")
