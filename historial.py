"""
Página de historial de jornadas para Fantasy Mundial 2026
"""
import streamlit as st
import pandas as pd
from database import get_db, get_clasificacion

def get_historial_completo():
    """Obtiene puntos por equipo y jornada."""
    db = get_db()
    res = db.table("puntos_historico").select("equipo_id, jornada, puntos, jugador_id").execute()
    return res.data or []

def get_equipos_info():
    """Devuelve dict {equipo_id: (nombre_equipo, nombre_usuario)}."""
    db = get_db()
    res = db.table("equipos").select("id, nombre, usuarios(nombre)").execute()
    return {e["id"]: (e["nombre"], e["usuarios"]["nombre"]) for e in (res.data or [])}

def get_jugadores_info():
    """Devuelve dict {jugador_id: nombre}."""
    db = get_db()
    res = db.table("jugadores_equipo").select("jugador_id, nombre, foto_url").execute()
    jugadores = {}
    for j in (res.data or []):
        if j["jugador_id"] not in jugadores:
            jugadores[j["jugador_id"]] = {"nombre": j["nombre"], "foto": j.get("foto_url", "")}
    return jugadores

def pagina_historial():
    st.markdown("""
    <div class="fifa-header">
      <div class="fifa-header-logo">🏆</div>
      <div><p class="fifa-header-title">Historial de jornadas</p>
      <p class="fifa-header-sub">Resultados y estadísticas por jornada</p></div>
    </div>""", unsafe_allow_html=True)

    historial = get_historial_completo()

    if not historial:
        st.info("⏳ Aún no hay datos de jornadas. ¡El torneo empieza mañana!")
        return

    equipos_info = get_equipos_info()
    jugadores_info = get_jugadores_info()

    # Puntos por equipo y jornada
    pts_jornada = {}  # {jornada: {equipo_id: total}}
    pts_jugador = {}  # {jornada: {jugador_id: total}}

    for r in historial:
        j = r["jornada"]
        eid = r["equipo_id"]
        jid = r["jugador_id"]
        pts = r["puntos"]

        pts_jornada.setdefault(j, {})
        pts_jornada[j][eid] = pts_jornada[j].get(eid, 0) + pts

        pts_jugador.setdefault(j, {})
        pts_jugador[j][jid] = pts_jugador[j].get(jid, 0) + pts

    jornadas = sorted(pts_jornada.keys())

    # ── RESUMEN POR JORNADA ────────────────
    st.markdown('<p class="seccion-titulo">Resumen por jornada</p>', unsafe_allow_html=True)

    for jornada in reversed(jornadas):
        pts_eq = pts_jornada[jornada]
        pts_jug = pts_jugador[jornada]

        # Ganador de la jornada
        if pts_eq:
            ganador_id = max(pts_eq, key=pts_eq.get)
            ganador_info = equipos_info.get(ganador_id, ("?", "?"))
            max_pts = pts_eq[ganador_id]

        # Jugador de la jornada
        if pts_jug:
            mejor_jug_id = max(pts_jug, key=pts_jug.get)
            mejor_jug = jugadores_info.get(mejor_jug_id, {"nombre": "?", "foto": ""})
            mejor_pts = pts_jug[mejor_jug_id]

        with st.expander(f"⚽ Jornada {jornada}", expanded=(jornada == max(jornadas))):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown(f"""
                <div style="background:#e8f5ee;border-radius:10px;padding:12px;text-align:center;">
                    <p style="font-size:11px;color:#0f6e56;font-weight:600;text-transform:uppercase;margin:0 0 4px;">Ganador jornada</p>
                    <p style="font-size:20px;margin:0;">🥇</p>
                    <p style="font-size:14px;font-weight:600;color:#085041;margin:0;">{ganador_info[1]}</p>
                    <p style="font-size:12px;color:#1a7a4a;margin:0;">{max_pts:.0f} pts</p>
                </div>""", unsafe_allow_html=True)

            with col2:
                foto = mejor_jug.get("foto", "")
                foto_html = f'<img src="{foto}" style="width:40px;height:40px;border-radius:50%;object-fit:cover;object-position:top;border:2px solid #1a7a4a;">' if foto else f'<div style="width:40px;height:40px;border-radius:50%;background:#1a7a4a;display:flex;align-items:center;justify-content:center;color:white;font-weight:600;font-size:13px;">{mejor_jug["nombre"][:2].upper()}</div>'
                st.markdown(f"""
                <div style="background:#e8f5ee;border-radius:10px;padding:12px;text-align:center;">
                    <p style="font-size:11px;color:#0f6e56;font-weight:600;text-transform:uppercase;margin:0 0 6px;">Jugador jornada</p>
                    <div style="display:flex;justify-content:center;margin-bottom:4px;">{foto_html}</div>
                    <p style="font-size:13px;font-weight:600;color:#085041;margin:0;">{mejor_jug["nombre"].split()[-1]}</p>
                    <p style="font-size:12px;color:#1a7a4a;margin:0;">{mejor_pts:.0f} pts</p>
                </div>""", unsafe_allow_html=True)

            with col3:
                st.markdown('<p style="font-size:11px;color:#0f6e56;font-weight:600;text-transform:uppercase;margin:0 0 8px;">Clasificación jornada</p>', unsafe_allow_html=True)
                ranking = sorted(pts_eq.items(), key=lambda x: x[1], reverse=True)
                medallas = ["🥇", "🥈", "🥉"]
                for i, (eid, pts) in enumerate(ranking):
                    info = equipos_info.get(eid, ("?", "?"))
                    medal = medallas[i] if i < 3 else f"{i+1}."
                    st.markdown(f'<div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:0.5px solid #e8f5ee;"><span style="font-size:13px;">{medal} {info[1]}</span><span style="font-size:13px;font-weight:600;color:#1a7a4a;">{pts:.0f}</span></div>', unsafe_allow_html=True)

    # ── EVOLUCIÓN ACUMULADA ────────────────
    if len(jornadas) > 1:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<p class="seccion-titulo">Evolución acumulada</p>', unsafe_allow_html=True)

        datos = {}
        for eid, info in equipos_info.items():
            acumulado = 0
            fila = []
            for j in jornadas:
                acumulado += pts_jornada.get(j, {}).get(eid, 0)
                fila.append(acumulado)
            datos[info[1]] = fila

        df = pd.DataFrame(datos, index=[f"J{j}" for j in jornadas])
        st.line_chart(df, color=["#1a7a4a", "#2563eb", "#dc2626"])

    # ── MÁXIMO ANOTADOR ────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<p class="seccion-titulo">Máximos anotadores del fantasy</p>', unsafe_allow_html=True)

    # Total puntos por jugador
    total_por_jug = {}
    for r in historial:
        jid = r["jugador_id"]
        total_por_jug[jid] = total_por_jug.get(jid, 0) + r["puntos"]

    top10 = sorted(total_por_jug.items(), key=lambda x: x[1], reverse=True)[:10]

    for i, (jid, total) in enumerate(top10, 1):
        jug = jugadores_info.get(jid, {"nombre": "?", "foto": ""})
        foto = jug.get("foto", "")
        foto_html = f'<img src="{foto}" style="width:36px;height:36px;border-radius:50%;object-fit:cover;object-position:top;border:2px solid #e8f5ee;">' if foto else f'<div style="width:36px;height:36px;border-radius:50%;background:#1a7a4a;display:flex;align-items:center;justify-content:center;color:white;font-size:11px;font-weight:600;">{jug["nombre"][:2].upper()}</div>'
        medal = ["🥇","🥈","🥉"][i-1] if i <= 3 else f"{i}."
        st.markdown(f"""
        <div style="background:white;border:0.5px solid #e8e8e8;border-radius:10px;padding:10px 14px;display:flex;align-items:center;gap:10px;margin-bottom:6px;">
            <span style="font-size:18px;min-width:28px;">{medal}</span>
            {foto_html}
            <span style="flex:1;font-size:14px;font-weight:500;">{jug["nombre"]}</span>
            <span style="font-size:16px;font-weight:700;color:#1a7a4a;">{total:.0f} pts</span>
        </div>""", unsafe_allow_html=True)
