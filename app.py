"""
Fantasy Mundial 2026 🏆 — Interfaz Web con Streamlit + Supabase
Ejecutar: streamlit run app.py
"""

import os
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import json
from database import get_db
from database import (
    crear_usuario, get_usuarios, crear_equipo, get_equipos,
    get_presupuesto, añadir_jugador, get_jugadores_equipo,
    jugador_ya_en_equipo, contar_jugadores, cambiar_capitan,
    get_clasificacion, get_puntos_jornada
)
from fantasy import actualizar_puntos_jornada, _api_get, LEAGUE_ID, SEASON
from alineacion import pagina_alineacion

from historial import pagina_historial
from draft import pagina_draft
from como_funciona import pagina_como_funciona

st.set_page_config(
    page_title="Fantasy Mundial 2026",
    page_icon="🏆",
    layout="wide"
)

from ligas import pagina_login as _pagina_login

# ── LOGIN CHECK ──────────────────────────
if "liga_activa" not in st.session_state:
    _pagina_login()
    st.stop()

liga_activa = st.session_state["liga_activa"]
liga_id = liga_activa["id"]
liga_nombre = liga_activa["nombre"]

# ── CSS GLOBAL ────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.fifa-header {
    background: #1a7a4a;
    border-radius: 14px;
    padding: 18px 22px;
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 1.5rem;
}
.fifa-header-logo {
    width: 48px; height: 48px;
    background: #c9a84c;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 22px;
}
.fifa-header-title { color: white; font-size: 20px; font-weight: 600; margin: 0; }
.fifa-header-sub { color: rgba(255,255,255,0.7); font-size: 12px; margin: 0; }

.stat-box {
    background: #e8f5ee;
    border-radius: 10px;
    padding: 14px;
    text-align: center;
}
.stat-box-label { font-size: 11px; color: #0f6e56; margin: 0 0 4px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.04em; }
.stat-box-value { font-size: 26px; font-weight: 600; color: #085041; margin: 0; }

.podium-card {
    background: white;
    border: 0.5px solid #e0e0e0;
    border-radius: 12px;
    padding: 14px 18px;
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 8px;
}
.podium-card.leader { border: 2px solid #1a7a4a; }
.podium-avatar {
    width: 42px; height: 42px;
    border-radius: 50%;
    background: #e8f5ee;
    display: flex; align-items: center; justify-content: center;
    font-weight: 600; font-size: 14px; color: #0f6e56;
    flex-shrink: 0;
}
.podium-name { font-size: 15px; font-weight: 500; margin: 0; }
.podium-team { font-size: 12px; color: #666; margin: 0; }
.podium-pts { font-size: 24px; font-weight: 600; color: #1a7a4a; margin: 0; }
.podium-delta { font-size: 11px; color: #1a7a4a; margin: 0; }
.badge-lider {
    display: inline-block;
    background: #e8f5ee; color: #085041;
    font-size: 10px; padding: 2px 8px;
    border-radius: 6px; margin-left: 6px;
    font-weight: 500;
}

.player-card {
    background: white;
    border: 0.5px solid #e8e8e8;
    border-radius: 10px;
    padding: 10px 12px;
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 6px;
}
.player-foto {
    width: 42px; height: 42px;
    border-radius: 50%;
    object-fit: cover; object-position: top;
    border: 2px solid #e8f5ee;
    flex-shrink: 0;
}
.player-avatar {
    width: 42px; height: 42px;
    border-radius: 50%;
    background: #e8f5ee;
    display: flex; align-items: center; justify-content: center;
    font-weight: 600; font-size: 13px; color: #0f6e56;
    flex-shrink: 0;
}
.player-nombre { font-size: 14px; font-weight: 500; margin: 0; }
.player-info { font-size: 11px; color: #888; margin: 0; }
.player-pts { font-size: 16px; font-weight: 600; color: #1a7a4a; margin-left: auto; white-space: nowrap; }
.player-cap { background: #fff8e1; color: #856404; font-size: 10px; padding: 2px 7px; border-radius: 6px; font-weight: 500; }

.seccion-titulo {
    font-size: 11px; font-weight: 600;
    color: #888; text-transform: uppercase;
    letter-spacing: 0.06em; margin: 0 0 12px;
}

div[data-testid="stSidebar"] { background: #f8fdf9; }
div[data-testid="stSidebar"] .stRadio label { font-size: 14px; }
</style>
""", unsafe_allow_html=True)

# ── SIDEBAR ───────────────────────────────
st.sidebar.markdown(f"""
<div style="background:#1a7a4a;border-radius:10px;padding:12px 14px;margin-bottom:1rem;">
  <div style="color:white;font-weight:600;font-size:16px;">🏆 Fantasy Mundial</div>
  <div style="color:rgba(255,255,255,0.7);font-size:11px;">{liga_nombre}</div>
</div>
""", unsafe_allow_html=True)
if st.sidebar.button("🚪 Cambiar liga"):
    del st.session_state["liga_activa"]
    st.rerun()

pagina = st.sidebar.radio("", [
    "🏅 Clasificación",
    "👤 Mi equipo",
    "⚽ Mi alineación",
    "📊 Historial",
    "📖 Cómo funciona",
    "🎲 Crear equipos (draft)",
    "➕ Crear usuario/equipo",
    "🔍 Buscar jugadores",
    "🔄 Actualizar puntos",
    "⚙️ Configuración API"
])

api_key = os.getenv("API_FOOTBALL_KEY", "")
if not api_key or api_key == "TU_API_KEY_AQUI":
    st.sidebar.warning("⚠️ Sin API key")
else:
    st.sidebar.markdown("""
    <div style="background:#e8f5ee;border-radius:8px;padding:8px 12px;font-size:12px;color:#085041;font-weight:500;">
    ✅ API conectada
    </div>""", unsafe_allow_html=True)

# ── CLASIFICACIÓN ─────────────────────────
if pagina == "🏅 Clasificación":
    st.markdown("""
    <div class="fifa-header">
      <div class="fifa-header-logo">🏆</div>
      <div>
        <p class="fifa-header-title">Fantasy Mundial 2026</p>
        <p class="fifa-header-sub">Liga privada · Clasificación general</p>
      </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="stat-box"><p class="stat-box-label">Jornada</p><p class="stat-box-value">1</p></div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="stat-box"><p class="stat-box-label">Equipos</p><p class="stat-box-value">3</p></div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="stat-box"><p class="stat-box-label">Días restantes</p><p class="stat-box-value">39</p></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<p class="seccion-titulo">Clasificación</p>', unsafe_allow_html=True)

    clasificacion = get_clasificacion(liga_id=liga_id)
    if not clasificacion:
        st.info("Aún no hay equipos. Ve a **Crear usuario/equipo** para empezar.")
    else:
        medallas = {1: "🥇", 2: "🥈", 3: "🥉"}
        for i, (usuario, equipo, equipo_id, pts) in enumerate(clasificacion, 1):
            medal = medallas.get(i, f"{i}.")
            iniciales = usuario[:2].upper()
            badge = '<span class="badge-lider">Líder</span>' if i == 1 else ""
            pts_color = "#1a7a4a" if i == 1 else "#333"
            card_class = "podium-card leader" if i == 1 else "podium-card"
            st.markdown(f"""
            <div class="{card_class}">
              <span style="font-size:24px;min-width:32px;">{medal}</span>
              <div class="podium-avatar">{iniciales}</div>
              <div style="flex:1;">
                <p class="podium-name">{usuario}{badge}</p>
                <p class="podium-team">{equipo}</p>
              </div>
              <div style="text-align:right;">
                <p class="podium-pts" style="color:{pts_color};">{pts:.0f} pts</p>
              </div>
            </div>
            """, unsafe_allow_html=True)

        if len(clasificacion) > 1:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<p class="seccion-titulo">Comparativa de puntos</p>', unsafe_allow_html=True)
            import pandas as pd
            df = pd.DataFrame(clasificacion, columns=["Usuario", "Equipo", "ID", "Puntos"])
            st.bar_chart(df.set_index("Usuario")["Puntos"], color="#1a7a4a")

# ── MI EQUIPO ─────────────────────────────
elif pagina == "👤 Mi equipo":
    st.markdown("""
    <div class="fifa-header">
      <div class="fifa-header-logo">👤</div>
      <div><p class="fifa-header-title">Mi equipo</p>
      <p class="fifa-header-sub">Jugadores y puntos</p></div>
    </div>""", unsafe_allow_html=True)

    usuarios = get_usuarios(liga_id=liga_id)
    if not usuarios:
        st.warning("No hay usuarios creados.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            sel = st.selectbox("Usuario", [u[1] for u in usuarios])
        uid = next(u[0] for u in usuarios if u[1] == sel)
        equipos = get_equipos(uid, liga_id=liga_id)
        if not equipos:
            st.warning("Este usuario no tiene equipo.")
        else:
            with col2:
                eq_sel = st.selectbox("Equipo", [e[1] for e in equipos])
            equipo_id = next(e[0] for e in equipos if e[1] == eq_sel)
            presupuesto = get_presupuesto(equipo_id)

            st.markdown(f"""
            <div style="background:#e8f5ee;border-radius:10px;padding:10px 16px;margin:1rem 0;display:flex;align-items:center;gap:8px;">
              <span style="font-size:18px;">💰</span>
              <span style="color:#085041;font-weight:500;">Presupuesto restante: <strong>${presupuesto:.1f}M</strong></span>
            </div>""", unsafe_allow_html=True)

            jugadores = get_jugadores_equipo(equipo_id)
            if not jugadores:
                st.info("El equipo está vacío.")
            else:
                pos_labels = {"G": "Portero", "D": "Defensa", "M": "Centrocampista", "F": "Delantero"}
                pos_order = {"G": 1, "D": 2, "M": 3, "F": 4}
                total = 0

                for pos_key in ["G", "D", "M", "F"]:
                    jugadores_pos = [j for j in jugadores if j[2] == pos_key]
                    if not jugadores_pos:
                        continue
                    st.markdown(f'<p class="seccion-titulo">{pos_labels[pos_key]}s</p>', unsafe_allow_html=True)
                    for jug_id, nombre, pos, precio, capitan, pts, foto_url in jugadores_pos:
                        cap_badge = '<span class="player-cap">👑 Capitán</span>' if capitan else ""
                        if foto_url:
                            foto_html = f'<img class="player-foto" src="{foto_url}">'
                        else:
                            iniciales = nombre[:2].upper()
                            foto_html = f'<div class="player-avatar">{iniciales}</div>'
                        st.markdown(f"""
                        <div class="player-card">
                          {foto_html}
                          <div style="flex:1;min-width:0;">
                            <p class="player-nombre">{nombre} {cap_badge}</p>
                            <p class="player-info">${precio}M</p>
                          </div>
                          <span class="player-pts">{pts:.0f} pts</span>
                        </div>""", unsafe_allow_html=True)
                        total += pts

                    # Botón capitán
                    opts = {j[1]: j[0] for j in jugadores_pos if not j[4]}
                    if opts:
                        c1, c2 = st.columns([3, 1])
                        with c1:
                            nuevo_cap = st.selectbox(f"Cambiar capitán ({pos_labels[pos_key]})", ["— sin cambios —"] + list(opts.keys()), key=f"cap_sel_{pos_key}")
                        with c2:
                            st.write("")
                            if st.button("👑 Asignar", key=f"cap_btn_{pos_key}") and nuevo_cap != "— sin cambios —":
                                cambiar_capitan(equipo_id, opts[nuevo_cap])
                                st.success(f"👑 {nuevo_cap} es el nuevo capitán")
                                st.rerun()

                st.markdown(f"""
                <div style="background:#1a7a4a;border-radius:10px;padding:12px 18px;margin-top:1rem;display:flex;justify-content:space-between;align-items:center;">
                  <span style="color:white;font-weight:500;">Total del equipo</span>
                  <span style="color:white;font-size:22px;font-weight:600;">{total:.0f} pts</span>
                </div>""", unsafe_allow_html=True)

                historial = get_puntos_jornada(equipo_id)
                if historial:
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown('<p class="seccion-titulo">Evolución por jornada</p>', unsafe_allow_html=True)
                    import pandas as pd
                    df = pd.DataFrame(historial, columns=["Jornada", "Puntos"])
                    st.line_chart(df.set_index("Jornada"), color="#1a7a4a")

# ── MI ALINEACIÓN ─────────────────────────
elif pagina == "⚽ Mi alineación":
    st.markdown("""
    <div class="fifa-header">
      <div class="fifa-header-logo">⚽</div>
      <div><p class="fifa-header-title">Mi alineación</p>
      <p class="fifa-header-sub">Selecciona tu once titular</p></div>
    </div>""", unsafe_allow_html=True)

    usuarios = get_usuarios(liga_id=liga_id)
    if not usuarios:
        st.warning("No hay usuarios creados.")
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            sel = st.selectbox("Usuario", [u[1] for u in usuarios], key="alin_user")
        uid = next(u[0] for u in usuarios if u[1] == sel)
        equipos = get_equipos(uid, liga_id=liga_id)
        if not equipos:
            st.warning("Este usuario no tiene equipo.")
        else:
            with col2:
                eq_sel = st.selectbox("Equipo", [e[1] for e in equipos], key="alin_eq")
            equipo_id = next(e[0] for e in equipos if e[1] == eq_sel)
            with col3:
                jornada = st.number_input("Jornada", min_value=1, max_value=7, value=1, key="alin_jornada")
            pagina_alineacion(equipo_id, int(jornada))

# ── HISTORIAL ─────────────────────────────
elif pagina == "📊 Historial":
    pagina_historial()

# ── CÓMO FUNCIONA ────────────────────────
elif pagina == "📖 Cómo funciona":
    pagina_como_funciona()

# ── DRAFT ────────────────────────────────
elif pagina == "🎲 Crear equipos (draft)":
    pagina_draft(liga_id)

# ── CREAR USUARIO / EQUIPO ────────────────
elif pagina == "➕ Crear usuario/equipo":
    st.markdown("""
    <div class="fifa-header">
      <div class="fifa-header-logo">➕</div>
      <div><p class="fifa-header-title">Crear usuario y equipo</p>
      <p class="fifa-header-sub">Añade participantes a la liga</p></div>
    </div>""", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["👤 Nuevo usuario", "🏟️ Nuevo equipo"])
    with tab1:
        nombre_usuario = st.text_input("Tu nombre")
        if st.button("Crear usuario", type="primary"):
            if nombre_usuario.strip():
                crear_usuario(nombre_usuario.strip())
                st.success(f"✅ Usuario **{nombre_usuario}** creado.")
            else:
                st.error("Escribe un nombre.")
    with tab2:
        usuarios = get_usuarios(liga_id=liga_id)
        if not usuarios:
            st.warning("Primero crea un usuario.")
        else:
            sel_u = st.selectbox("Usuario", [u[1] for u in usuarios], key="crear_eq_user")
            uid = next(u[0] for u in usuarios if u[1] == sel_u)
            nombre_equipo = st.text_input("Nombre del equipo")
            if st.button("Crear equipo", type="primary"):
                if nombre_equipo.strip():
                    crear_equipo(uid, nombre_equipo.strip(), liga_id=liga_id)
                    st.success(f"✅ Equipo **{nombre_equipo}** creado con $100M.")
                else:
                    st.error("Escribe un nombre.")

# ── BUSCAR JUGADORES ──────────────────────
elif pagina == "🔍 Buscar jugadores":
    st.markdown("""
    <div class="fifa-header">
      <div class="fifa-header-logo">🔍</div>
      <div><p class="fifa-header-title">Buscar jugadores</p>
      <p class="fifa-header-sub">Añade jugadores a tu equipo</p></div>
    </div>""", unsafe_allow_html=True)

    if not api_key or api_key == "TU_API_KEY_AQUI":
        st.error("⚠️ Configura tu API key en ⚙️ Configuración API.")
    else:
        col1, col2 = st.columns([3, 1])
        with col1:
            nombre_busqueda = st.text_input("Nombre del jugador", placeholder="ej: Pedri, Mbappé, Yamal...")
        with col2:
            st.write("")
            buscar = st.button("🔍 Buscar", type="primary")

        if buscar and nombre_busqueda:
            with st.spinner("Buscando..."):
                data = _api_get("players/profiles", {"search": nombre_busqueda.replace(" ", "%20")})
                resultados = data.get("response", [])

            if not resultados:
                st.warning("No encontrado. Prueba con otro nombre.")
            else:
                equipos = get_equipos(liga_id=liga_id)
                if equipos:
                    eq_opciones = {f"{e[2]} — {e[1]}": e[0] for e in equipos}
                    eq_sel = st.selectbox("Añadir al equipo:", list(eq_opciones.keys()))
                    equipo_destino = eq_opciones[eq_sel]
                    presupuesto = get_presupuesto(equipo_destino)
                    st.markdown(f'<div style="background:#e8f5ee;border-radius:8px;padding:8px 12px;color:#085041;font-size:13px;margin-bottom:1rem;">💰 Presupuesto: <strong>${presupuesto:.1f}M</strong></div>', unsafe_allow_html=True)

                    for item in resultados[:8]:
                        p = item["player"]
                        c1, c2, c3, c4, c5 = st.columns([1, 3, 1, 2, 2])
                        with c1:
                            st.write("⚽")
                        with c2:
                            st.write(f"**{p['name']}**")
                            st.caption(p.get('nationality',''))
                        with c3:
                            st.write("M")
                        with c4:
                            precio = st.number_input("$M", min_value=0.0, max_value=20.0, value=7.0, step=0.5, key=f"precio_{p['id']}")
                        with c5:
                            es_cap = st.checkbox("Cap", key=f"cap_{p['id']}")
                            if st.button("➕", key=f"add_{p['id']}"):
                                if jugador_ya_en_equipo(equipo_destino, p['id']):
                                    st.warning("Ya está en tu equipo.")
                                elif precio > presupuesto:
                                    st.error("Sin presupuesto.")
                                elif contar_jugadores(equipo_destino) >= 15:
                                    st.error("Equipo lleno.")
                                else:
                                    añadir_jugador(equipo_destino, p['id'], p['name'], "M", precio, es_cap)
                                    st.success(f"✅ {p['name']} añadido.")
                                    st.rerun()
                        st.divider()

# ── ACTUALIZAR PUNTOS ─────────────────────
elif pagina == "🔄 Actualizar puntos":
    st.markdown("""
    <div class="fifa-header">
      <div class="fifa-header-logo">🔄</div>
      <div><p class="fifa-header-title">Actualizar puntos</p>
      <p class="fifa-header-sub">Tras cada jornada del Mundial</p></div>
    </div>""", unsafe_allow_html=True)

    if not api_key or api_key == "TU_API_KEY_AQUI":
        st.error("⚠️ Configura tu API key.")
    else:
        col1, col2 = st.columns([2, 1])
        with col1:
            jornada = st.number_input("Número de jornada", min_value=1, max_value=7, value=1)
        with col2:
            st.write("")
            if st.button("🔄 Actualizar ahora", type="primary"):
                with st.spinner(f"Calculando jornada {jornada}..."):
                    actualizar_puntos_jornada(int(jornada))
                st.success(f"✅ Jornada {jornada} actualizada.")
                st.balloons()

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<p class="seccion-titulo">Calendario del Mundial 2026</p>', unsafe_allow_html=True)
        st.markdown("""
        | Fase | Fechas |
        |---|---|
        | Fase de grupos (Jornada 1) | 11–17 junio 2026 |
        | Fase de grupos (Jornada 2) | 18–23 junio 2026 |
        | Fase de grupos (Jornada 3) | 24–27 junio 2026 |
        | Octavos de final | 29 jun – 3 jul 2026 |
        | Cuartos de final | 7–9 julio 2026 |
        | Semifinales | 14–15 julio 2026 |
        | Final | 19 julio 2026 |
        """)

# ── CONFIGURACIÓN API ─────────────────────
elif pagina == "⚙️ Configuración API":
    st.markdown("""
    <div class="fifa-header">
      <div class="fifa-header-logo">⚙️</div>
      <div><p class="fifa-header-title">Configuración API</p>
      <p class="fifa-header-sub">Estado de la conexión</p></div>
    </div>""", unsafe_allow_html=True)

    if api_key and api_key != "TU_API_KEY_AQUI":
        st.success("✅ API key detectada y activa")
        if st.button("🧪 Probar conexión"):
            with st.spinner("Conectando..."):
                data = _api_get("status", {})
            if data and data.get("response"):
                subs = data.get("response", {}).get("subscription", {})
                reqs = data.get("response", {}).get("requests", {})
                st.success("✅ Conexión exitosa")
                col1, col2, col3 = st.columns(3)
                col1.metric("Plan", subs.get("plan", "—"))
                col2.metric("Requests hoy", reqs.get("current", 0))
                col3.metric("Límite diario", reqs.get("limit_day", "—"))

    st.divider()

    # ── GESTIÓN DE EQUIPOS ─────────────────
    st.markdown("### 🏟️ Eliminar equipo")
    db = get_db()
    equipos_liga = db.table("equipos").select("id, nombre, usuarios(nombre)").eq("liga_id", liga_id).execute()
    equipos_lista = equipos_liga.data or []

    if not equipos_lista:
        st.info("No hay equipos en esta liga.")
    else:
        eq_opciones = {f"{e['usuarios']['nombre']} — {e['nombre']}": e['id'] for e in equipos_lista}
        eq_sel = st.selectbox("Selecciona el equipo a eliminar", list(eq_opciones.keys()))
        equipo_borrar_id = eq_opciones[eq_sel]

        with st.expander("⚠️ Confirmar eliminación del equipo"):
            st.error(f"Se eliminarán todos los jugadores, alineaciones y puntos de **{eq_sel}**.")
            if st.button("🗑️ Eliminar este equipo", key="btn_del_equipo"):
                with st.spinner("Eliminando equipo..."):
                    try:
                        db.table("puntos_historico").delete().eq("equipo_id", equipo_borrar_id).execute()
                        db.table("alineaciones").delete().eq("equipo_id", equipo_borrar_id).execute()
                        db.table("jugadores_equipo").delete().eq("equipo_id", equipo_borrar_id).execute()
                        db.table("equipos").delete().eq("id", equipo_borrar_id).execute()
                        st.success(f"✅ Equipo eliminado.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")

    st.divider()

    # ── ELIMINAR LIGA ──────────────────────
    st.markdown("### 🗑️ Eliminar liga")
    st.warning(f"Liga activa: **{liga_nombre}**")

    with st.expander("⚠️ Zona de peligro — Eliminar esta liga"):
        st.error("Esto eliminará permanentemente la liga, sus equipos, alineaciones y puntos. **No se puede deshacer.**")
        confirmar = st.text_input("Escribe el nombre de la liga para confirmar:", placeholder=liga_nombre)
        if st.button("🗑️ Eliminar liga definitivamente", type="primary"):
            if confirmar == liga_nombre:
                db = get_db()
                with st.spinner("Eliminando..."):
                    try:
                        # Borrar en orden por dependencias
                        equipos_liga = db.table("equipos").select("id").eq("liga_id", liga_id).execute()
                        ids = [e["id"] for e in (equipos_liga.data or [])]
                        for eid in ids:
                            db.table("puntos_historico").delete().eq("equipo_id", eid).execute()
                            db.table("alineaciones").delete().eq("equipo_id", eid).execute()
                            db.table("jugadores_equipo").delete().eq("equipo_id", eid).execute()
                        db.table("equipos").delete().eq("liga_id", liga_id).execute()
                        db.table("ligas").delete().eq("id", liga_id).execute()
                        del st.session_state["liga_activa"]
                        st.success("✅ Liga eliminada.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
            else:
                st.error("El nombre no coincide. Escribe exactamente el nombre de la liga.")
