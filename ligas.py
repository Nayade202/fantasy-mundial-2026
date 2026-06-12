"""
ligas.py — Sistema de login por liga con contraseña
"""
import streamlit as st
from database import get_db

def get_liga_por_password(nombre: str, password: str):
    """Verifica si el nombre y contraseña coinciden con una liga."""
    db = get_db()
    res = db.table("ligas").select("*").eq("nombre", nombre).eq("password", password).execute()
    return res.data[0] if res.data else None

def get_todas_ligas():
    """Devuelve lista de nombres de ligas."""
    db = get_db()
    res = db.table("ligas").select("id, nombre, descripcion").execute()
    return res.data or []

def crear_liga(nombre: str, password: str, descripcion: str = "") -> int:
    """Crea una nueva liga."""
    db = get_db()
    res = db.table("ligas").insert({
        "nombre": nombre,
        "password": password,
        "descripcion": descripcion
    }).execute()
    return res.data[0]["id"] if res.data else None

def pagina_login():
    """Muestra la pantalla de login para seleccionar liga."""
    st.markdown("""
    <div style="max-width:420px;margin:3rem auto;padding:0 1rem;">
        <div style="text-align:center;margin-bottom:2rem;">
            <div style="font-size:56px;margin-bottom:12px;">🏆</div>
            <h1 style="font-size:24px;font-weight:600;margin:0;">Fantasy Mundial 2026</h1>
            <p style="color:#888;font-size:14px;margin:6px 0 0;">Introduce los datos de tu liga</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        ligas = get_todas_ligas()
        nombres_ligas = [l["nombre"] for l in ligas]

        st.markdown("**Selecciona tu liga**")
        liga_sel = st.selectbox("", nombres_ligas, label_visibility="collapsed")

        st.markdown("**Contraseña**")
        password = st.text_input("", type="password", placeholder="Contraseña de la liga", label_visibility="collapsed")

        if st.button("Entrar →", type="primary", use_container_width=True):
            liga = get_liga_por_password(liga_sel, password)
            if liga:
                st.session_state["liga_activa"] = liga
                st.rerun()
            else:
                st.error("❌ Contraseña incorrecta")

        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("➕ Crear nueva liga"):
            nuevo_nombre = st.text_input("Nombre de la liga", key="nueva_liga_nombre")
            nueva_password = st.text_input("Contraseña", type="password", key="nueva_liga_pass")
            nueva_desc = st.text_input("Descripción (opcional)", key="nueva_liga_desc")
            if st.button("Crear liga", key="btn_crear_liga"):
                if nuevo_nombre.strip() and nueva_password.strip():
                    liga_id = crear_liga(nuevo_nombre.strip(), nueva_password.strip(), nueva_desc.strip())
                    if liga_id:
                        st.success(f"✅ Liga **{nuevo_nombre}** creada. ¡Ya puedes entrar!")
                    else:
                        st.error("❌ Error al crear la liga. ¿Ya existe ese nombre?")
                else:
                    st.error("Escribe un nombre y contraseña.")
