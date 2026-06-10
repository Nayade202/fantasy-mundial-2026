"""
Fantasy Mundial 2026 🏆 — Interfaz Web con Streamlit + Supabase
Ejecutar: streamlit run app.py
"""

import os
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import json
from database import (
    crear_usuario, get_usuarios, crear_equipo, get_equipos,
    get_presupuesto, añadir_jugador, get_jugadores_equipo,
    jugador_ya_en_equipo, contar_jugadores, cambiar_capitan,
    get_clasificacion, get_puntos_jornada
)
from fantasy import actualizar_puntos_jornada, _api_get, LEAGUE_ID, SEASON
from alineacion import pagina_alineacion

# ──────────────────────────────────────────
#  CONFIGURACIÓN DE PÁGINA
# ──────────────────────────────────────────
st.set_page_config(
    page_title="Fantasy Mundial 2026",
    page_icon="🏆",
    layout="wide"
)

st.markdown("""
<style>
    .titulo { font-size: 2.5rem; font-weight: bold; text-align: center; color: #1a472a; }
    .subtitulo { text-align: center; color: #666; margin-bottom: 2rem; }
    .pts { font-size: 1.8rem; font-weight: bold; color: #2ecc71; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────
#  SIDEBAR
# ──────────────────────────────────────────
st.sidebar.markdown("## 🏆 Fantasy Mundial 2026")
st.sidebar.markdown("---")

pagina = st.sidebar.radio("Navegar", [
    "🏅 Clasificación",
    "👤 Mi equipo",
    "⚽ Mi alineación",
    "➕ Crear usuario/equipo",
    "🔍 Buscar jugadores",
    "🔄 Actualizar puntos",
    "⚙️ Configuración API"
])

api_key = os.getenv("API_FOOTBALL_KEY", "")
if not api_key or api_key == "TU_API_KEY_AQUI":
    st.sidebar.warning("⚠️ Sin API key — solo modo demo")
else:
    st.sidebar.success("✅ API conectada")

# ──────────────────────────────────────────
#  CLASIFICACIÓN
# ──────────────────────────────────────────
if pagina == "🏅 Clasificación":
    st.markdown('<div class="titulo">🏆 Fantasy Mundial 2026</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitulo">Liga privada · Clasificación general</div>', unsafe_allow_html=True)

    clasificacion = get_clasificacion()

    if not clasificacion:
        st.info("Aún no hay equipos creados. Ve a **Crear usuario/equipo** para empezar.")
    else:
        medallas = {1: "🥇", 2: "🥈", 3: "🥉"}
        for i, (usuario, equipo, equipo_id, pts) in enumerate(clasificacion, 1):
            medal = medallas.get(i, f"{i}.")
            col1, col2, col3 = st.columns([1, 4, 2])
            with col1:
                st.markdown(f"<div style='font-size:2rem;text-align:center'>{medal}</div>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"**{usuario}**  \n_{equipo}_")
            with col3:
                st.markdown(f"<div class='pts'>{pts:.0f} pts</div>", unsafe_allow_html=True)
            st.divider()

        if len(clasificacion) > 1:
            st.markdown("### 📊 Comparativa de puntos")
            import pandas as pd
            df = pd.DataFrame(clasificacion, columns=["Usuario", "Equipo", "ID", "Puntos"])
            st.bar_chart(df.set_index("Usuario")["Puntos"])

# ──────────────────────────────────────────
#  MI EQUIPO
# ──────────────────────────────────────────
elif pagina == "👤 Mi equipo":
    st.markdown("## 👤 Mi equipo")

    usuarios = get_usuarios()
    if not usuarios:
        st.warning("No hay usuarios creados. Ve a **Crear usuario/equipo**.")
    else:
        nombres = [u[1] for u in usuarios]
        sel = st.selectbox("Selecciona tu usuario", nombres)
        uid = next(u[0] for u in usuarios if u[1] == sel)

        equipos = get_equipos(uid)
        if not equipos:
            st.warning("Este usuario no tiene equipo. Ve a **Crear usuario/equipo**.")
        else:
            eq_nombres = [e[1] for e in equipos]
            eq_sel = st.selectbox("Selecciona equipo", eq_nombres)
            equipo_id = next(e[0] for e in equipos if e[1] == eq_sel)
            presupuesto = get_presupuesto(equipo_id)

            st.metric("💰 Presupuesto restante", f"${presupuesto:.1f}M")

            jugadores = get_jugadores_equipo(equipo_id)
            if not jugadores:
                st.info("El equipo está vacío. Ve a **Buscar jugadores** para añadirlos.")
            else:
                pos_icons = {"G": "🧤", "D": "🛡️", "M": "⚙️", "F": "⚡"}
                total = 0
                for jug_id, nombre, pos, precio, capitan, pts in jugadores:
                    cap = " 👑" if capitan else ""
                    icon = pos_icons.get(pos, "⚽")
                    col1, col2, col3, col4, col5 = st.columns([1, 4, 2, 2, 2])
                    with col1:
                        foto_url = f"https://media.api-sports.io/football/players/{jug_id}.png"
                        st.markdown(f'''<img src="{foto_url}" style="width:40px;height:40px;border-radius:50%;object-fit:cover;" onerror="this.src=''">'''  , unsafe_allow_html=True)
                    with col2:
                        st.write(f"**{nombre}**{cap}")
                        st.caption(f"{icon} {pos} · ${precio}M")
                    with col3:
                        st.metric("", f"{pts:.0f} pts")
                    with col4:
                        if not capitan:
                            if st.button("👑 Capitán", key=f"cap_btn_{jug_id}"):
                                cambiar_capitan(equipo_id, jug_id)
                                st.success(f"👑 {nombre} es el nuevo capitán")
                                st.rerun()
                        else:
                            st.success("👑 Capitán")
                    total += pts

                st.divider()
                st.markdown(f"### 📊 Total: **{total:.0f} puntos**")

                historial = get_puntos_jornada(equipo_id)
                if historial:
                    st.markdown("### 📈 Evolución por jornada")
                    import pandas as pd
                    df = pd.DataFrame(historial, columns=["Jornada", "Puntos"])
                    st.line_chart(df.set_index("Jornada"))

# ──────────────────────────────────────────
#  MI ALINEACIÓN
# ──────────────────────────────────────────
elif pagina == "⚽ Mi alineación":
    usuarios = get_usuarios()
    if not usuarios:
        st.warning("No hay usuarios creados.")
    else:
        nombres = [u[1] for u in usuarios]
        sel = st.selectbox("Selecciona tu usuario", nombres, key="alin_user")
        uid = next(u[0] for u in usuarios if u[1] == sel)
        equipos = get_equipos(uid)
        if not equipos:
            st.warning("Este usuario no tiene equipo.")
        else:
            eq_nombres = [e[1] for e in equipos]
            eq_sel = st.selectbox("Selecciona equipo", eq_nombres, key="alin_eq")
            equipo_id = next(e[0] for e in equipos if e[1] == eq_sel)
            jornada = st.number_input("Jornada", min_value=1, max_value=7, value=1, key="alin_jornada")
            pagina_alineacion(equipo_id, int(jornada))

# ──────────────────────────────────────────
#  CREAR USUARIO / EQUIPO
# ──────────────────────────────────────────
elif pagina == "➕ Crear usuario/equipo":
    st.markdown("## ➕ Crear usuario y equipo")

    tab1, tab2 = st.tabs(["👤 Nuevo usuario", "🏟️ Nuevo equipo"])

    with tab1:
        st.markdown("### Crear usuario")
        nombre_usuario = st.text_input("Tu nombre")
        if st.button("Crear usuario", type="primary"):
            if nombre_usuario.strip():
                crear_usuario(nombre_usuario.strip())
                st.success(f"✅ Usuario **{nombre_usuario}** creado correctamente.")
            else:
                st.error("Escribe un nombre.")

    with tab2:
        st.markdown("### Crear equipo")
        usuarios = get_usuarios()
        if not usuarios:
            st.warning("Primero crea un usuario.")
        else:
            nombres = [u[1] for u in usuarios]
            sel_u = st.selectbox("Selecciona usuario", nombres, key="crear_eq_user")
            uid = next(u[0] for u in usuarios if u[1] == sel_u)
            nombre_equipo = st.text_input("Nombre de tu equipo")
            if st.button("Crear equipo", type="primary"):
                if nombre_equipo.strip():
                    crear_equipo(uid, nombre_equipo.strip())
                    st.success(f"✅ Equipo **{nombre_equipo}** creado con $100M de presupuesto.")
                else:
                    st.error("Escribe un nombre para el equipo.")

# ──────────────────────────────────────────
#  BUSCAR JUGADORES
# ──────────────────────────────────────────
elif pagina == "🔍 Buscar jugadores":
    st.markdown("## 🔍 Buscar y añadir jugadores")

    api_key = os.getenv("API_FOOTBALL_KEY", "")
    if not api_key or api_key == "TU_API_KEY_AQUI":
        st.error("⚠️ Necesitas configurar tu API key. Ve a **⚙️ Configuración API**.")
    else:
        col1, col2 = st.columns([3, 1])
        with col1:
            nombre_busqueda = st.text_input("Nombre del jugador", placeholder="ej: Pedri, Mbappé, Yamal...")
        with col2:
            st.write("")
            st.write("")
            buscar = st.button("🔍 Buscar", type="primary")

        if buscar and nombre_busqueda:
            with st.spinner("Buscando..."):
                data = _api_get("players/profiles", {"search": nombre_busqueda.replace(" ", "%20")})
                resultados = data.get("response", [])

            if not resultados:
                st.warning("No se encontraron jugadores. Prueba con otro nombre.")
            else:
                st.markdown(f"### Resultados para '{nombre_busqueda}'")

                equipos = get_equipos()
                if not equipos:
                    st.warning("Primero crea un equipo.")
                else:
                    eq_opciones = {f"{e[2]} — {e[1]}": e[0] for e in equipos}
                    eq_sel = st.selectbox("Añadir al equipo:", list(eq_opciones.keys()))
                    equipo_destino = eq_opciones[eq_sel]
                    presupuesto = get_presupuesto(equipo_destino)
                    st.info(f"💰 Presupuesto disponible: **${presupuesto:.1f}M**")

                    pos_icons = {"G": "🧤", "D": "🛡️", "M": "⚙️", "F": "⚡"}

                    for item in resultados[:8]:
                        p = item["player"]
                        pos = "M"
                        icon = pos_icons.get(pos, "⚽")

                        with st.container():
                            c1, c2, c3, c4, c5 = st.columns([1, 3, 1, 2, 2])
                            with c1:
                                st.write(icon)
                            with c2:
                                st.write(f"**{p['name']}**  \n{p.get('nationality','')}")
                            with c3:
                                st.write(pos)
                            with c4:
                                precio = st.number_input("Precio $M", min_value=0.0, max_value=20.0, value=7.0, step=0.5, key=f"precio_{p['id']}")
                            with c5:
                                es_cap = st.checkbox("Capitán", key=f"cap_{p['id']}")
                                if st.button("➕ Añadir", key=f"add_{p['id']}"):
                                    if jugador_ya_en_equipo(equipo_destino, p['id']):
                                        st.warning("Este jugador ya está en tu equipo.")
                                    elif precio > presupuesto:
                                        st.error(f"Sin presupuesto. Tienes ${presupuesto:.1f}M")
                                    elif contar_jugadores(equipo_destino) >= 15:
                                        st.error("Equipo lleno (máx. 15 jugadores).")
                                    else:
                                        añadir_jugador(equipo_destino, p['id'], p['name'], pos, precio, es_cap)
                                        st.success(f"✅ {p['name']} añadido al equipo.")
                                        st.rerun()
                            st.divider()

# ──────────────────────────────────────────
#  ACTUALIZAR PUNTOS
# ──────────────────────────────────────────
elif pagina == "🔄 Actualizar puntos":
    st.markdown("## 🔄 Actualizar puntos")

    api_key = os.getenv("API_FOOTBALL_KEY", "")
    if not api_key or api_key == "TU_API_KEY_AQUI":
        st.error("⚠️ Necesitas configurar tu API key.")
    else:
        st.info("Actualiza los puntos después de que terminen los partidos de cada jornada.")

        col1, col2 = st.columns([2, 1])
        with col1:
            jornada = st.number_input("Número de jornada", min_value=1, max_value=7, value=1)
        with col2:
            st.write("")
            st.write("")
            if st.button("🔄 Actualizar ahora", type="primary"):
                with st.spinner(f"Calculando puntos de jornada {jornada}..."):
                    actualizar_puntos_jornada(int(jornada))
                st.success(f"✅ Jornada {jornada} actualizada.")
                st.balloons()

        st.divider()
        st.markdown("### 📅 Calendario del Mundial 2026")
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

# ──────────────────────────────────────────
#  CONFIGURACIÓN API
# ──────────────────────────────────────────
elif pagina == "⚙️ Configuración API":
    st.markdown("## ⚙️ Configuración API")

    api_key = os.getenv("API_FOOTBALL_KEY", "")
    if api_key and api_key != "TU_API_KEY_AQUI":
        st.success("✅ API key detectada y activa")
        if st.button("🧪 Probar conexión"):
            with st.spinner("Conectando..."):
                data = _api_get("status", {})
            if data:
                subs = data.get("response", {}).get("subscription", {})
                reqs = data.get("response", {}).get("requests", {})
                st.success("✅ Conexión exitosa")
                col1, col2, col3 = st.columns(3)
                col1.metric("Plan", subs.get("plan", "Free"))
                col2.metric("Requests hoy", reqs.get("current", 0))
                col3.metric("Límite diario", reqs.get("limit_day", 100))
            else:
                st.error("❌ No se pudo conectar.")
    else:
        st.warning("⚠️ No se detecta API key.")
