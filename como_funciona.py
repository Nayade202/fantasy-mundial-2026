"""
Página de cómo funciona el Fantasy Mundial 2026
"""
import streamlit as st

def pagina_como_funciona():
    st.markdown("""
    <div class="fifa-header">
      <div class="fifa-header-logo">📖</div>
      <div><p class="fifa-header-title">Cómo funciona</p>
      <p class="fifa-header-sub">Reglas y sistema de puntuación</p></div>
    </div>""", unsafe_allow_html=True)

    # ── RESUMEN ────────────────────────────
    st.markdown("""
    <div style="background:#e8f5ee;border-radius:12px;padding:16px 20px;margin-bottom:1.5rem;">
        <p style="font-size:15px;font-weight:600;color:#085041;margin:0 0 8px;">⚽ Fantasy Mundial 2026 — Liga privada entre Nayade, Mikel y Julen</p>
        <p style="font-size:13px;color:#0f6e56;margin:0;">Cada uno tiene <strong>25 jugadores fijos</strong> para todo el torneo. Antes de cada jornada seleccionas tu <strong>11 titular</strong> y hasta <strong>3 suplentes</strong>. Solo puntúan los jugadores de tu alineación guardada.</p>
    </div>
    """, unsafe_allow_html=True)

    # ── ALINEACIÓN ─────────────────────────
    st.markdown('<p class="seccion-titulo">La alineación</p>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div style="background:white;border:0.5px solid #e8e8e8;border-radius:12px;padding:14px;">
            <p style="font-weight:600;color:#1a7a4a;margin:0 0 10px;">✅ Antes de cada jornada</p>
            <ul style="margin:0;padding-left:18px;font-size:13px;color:#444;line-height:1.8;">
                <li>Ve a <strong>⚽ Mi alineación</strong></li>
                <li>Elige tu formación (4-3-3, 4-4-2...)</li>
                <li>Selecciona <strong>11 titulares</strong></li>
                <li>Añade hasta <strong>3 suplentes</strong> por orden</li>
                <li>Pulsa <strong>Guardar alineación</strong></li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="background:white;border:0.5px solid #e8e8e8;border-radius:12px;padding:14px;">
            <p style="font-weight:600;color:#dc2626;margin:0 0 10px;">⏰ Deadline importante</p>
            <ul style="margin:0;padding-left:18px;font-size:13px;color:#444;line-height:1.8;">
                <li>La alineación se <strong>bloquea 15 minutos</strong> antes del primer partido de cada jornada</li>
                <li>Si no guardas alineación → <strong>no puntúas</strong></li>
                <li>Los suplentes entran si un titular <strong>no juega ni un minuto</strong></li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    # ── SISTEMA DE PUNTOS ──────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<p class="seccion-titulo">Sistema de puntuación</p>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Todos los jugadores**")
        puntos = [
            ("⏱️ Jugar 60 min o más", "+2 pts"),
            ("⏱️ Jugar menos de 60 min", "+1 pt"),
            ("🎯 Asistencia", "+3 pts"),
            ("🟨 Tarjeta amarilla", "-1 pt"),
            ("🟥 Tarjeta roja", "-3 pts"),
            ("🔴 Doble amarilla", "-3 pts"),
            ("❌ Penalti fallado", "-2 pts"),
            ("🤦 Gol en propia", "-2 pts"),
        ]
        for accion, pts in puntos:
            color = "#dc2626" if "-" in pts else "#1a7a4a"
            st.markdown(f'<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:0.5px solid #f0f0f0;font-size:13px;"><span>{accion}</span><span style="font-weight:600;color:{color};">{pts}</span></div>', unsafe_allow_html=True)

    with col2:
        st.markdown("**Por posición**")
        puntos_pos = [
            ("⚡ Gol delantero", "+5 pts"),
            ("⚙️ Gol centrocampista", "+6 pts"),
            ("🛡️ Gol defensa", "+8 pts"),
            ("🧤 Gol portero", "+10 pts"),
            ("🧤 Portero sin goles (90 min)", "+6 pts"),
            ("🛡️ Defensa sin goles (90 min)", "+4 pts"),
            ("🧤 Penalti parado (portero)", "+5 pts"),
            ("🧤 Gol recibido (portero)", "-1 pt"),
        ]
        for accion, pts in puntos_pos:
            color = "#dc2626" if "-" in pts else "#1a7a4a"
            st.markdown(f'<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:0.5px solid #f0f0f0;font-size:13px;"><span>{accion}</span><span style="font-weight:600;color:{color};">{pts}</span></div>', unsafe_allow_html=True)

    # ── CAPITÁN ────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="background:#fff8e1;border:1px solid #f59e0b;border-radius:12px;padding:14px 18px;">
        <p style="font-weight:600;color:#92400e;margin:0 0 6px;">👑 El Capitán — dobla los puntos</p>
        <p style="font-size:13px;color:#78350f;margin:0;">El jugador que elijas como capitán <strong>multiplica sus puntos por 2</strong>. Elige bien — si mete gol en un buen partido puede darte 20+ puntos de golpe. Puedes cambiar el capitán desde <strong>👤 Mi equipo</strong> antes del deadline.</p>
    </div>
    """, unsafe_allow_html=True)

    # ── CUÁNDO SE ACTUALIZAN ───────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<p class="seccion-titulo">¿Cuándo se actualizan los puntos?</p>', unsafe_allow_html=True)

    pasos = [
        ("1", "⚽", "Termina el último partido de la jornada"),
        ("2", "🌙", "A la 01:00h (hora española) el sistema actualiza automáticamente"),
        ("3", "📨", "Recibes un mensaje en Telegram con la clasificación"),
        ("4", "📊", "Puedes ver los puntos en la app al día siguiente"),
    ]

    for num, icon, texto in pasos:
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:12px;padding:10px 0;border-bottom:0.5px solid #f0f0f0;">
            <div style="width:28px;height:28px;border-radius:50%;background:#1a7a4a;display:flex;align-items:center;justify-content:center;color:white;font-size:12px;font-weight:600;flex-shrink:0;">{num}</div>
            <span style="font-size:18px;">{icon}</span>
            <span style="font-size:13px;color:#444;">{texto}</span>
        </div>
        """, unsafe_allow_html=True)

    # ── CALENDARIO ─────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<p class="seccion-titulo">Calendario y deadlines</p>', unsafe_allow_html=True)

    jornadas = [
        ("1", "Fase de grupos", "11–17 jun", "11 jun 20:45h"),
        ("2", "Fase de grupos", "18–23 jun", "18 jun 20:45h"),
        ("3", "Fase de grupos", "24–27 jun", "24 jun 20:45h"),
        ("4", "Octavos de final", "29 jun–3 jul", "29 jun 20:45h"),
        ("5", "Cuartos de final", "7–9 jul", "7 jul 20:45h"),
        ("6", "Semifinales", "14–15 jul", "14 jul 20:45h"),
        ("7", "Final", "19 jul", "19 jul 15:45h"),
    ]

    for jornada, fase, fechas, deadline in jornadas:
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:12px;padding:8px 0;border-bottom:0.5px solid #f0f0f0;">
            <div style="width:28px;height:28px;border-radius:50%;background:#e8f5ee;display:flex;align-items:center;justify-content:center;color:#1a7a4a;font-size:12px;font-weight:600;flex-shrink:0;">J{jornada}</div>
            <div style="flex:1;">
                <p style="margin:0;font-size:13px;font-weight:500;">{fase}</p>
                <p style="margin:0;font-size:11px;color:#888;">{fechas}</p>
            </div>
            <div style="text-align:right;">
                <p style="margin:0;font-size:11px;color:#dc2626;font-weight:500;">⏰ {deadline}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
