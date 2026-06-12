"""
draft.py — Reparto aleatorio de jugadores entre equipos de una liga
"""
import random
from database import get_db, crear_usuario, crear_equipo, añadir_jugador

def get_todos_jugadores():
    """Obtiene todos los jugadores disponibles por posición."""
    db = get_db()
    res = db.table("jugadores_equipo").select(
        "jugador_id, nombre, posicion, precio, foto_url"
    ).execute()
    
    # Eliminar duplicados por jugador_id
    vistos = set()
    jugadores = {"G": [], "D": [], "M": [], "F": []}
    for j in (res.data or []):
        if j["jugador_id"] not in vistos:
            vistos.add(j["jugador_id"])
            pos = j["posicion"]
            if pos in jugadores:
                jugadores[pos].append(j)
    return jugadores

def draft_aleatorio(liga_id: int, participantes: list[str]) -> dict:
    """
    Reparte los 75 jugadores aleatoriamente entre los participantes.
    
    Distribución:
    - 2 porteros por equipo (6 total)
    - Defensas: 9-8-8 (25 total)
    - 8 medios por equipo (24 total)  
    - Delanteros: 7-7-6 (20 total)
    
    Devuelve dict con los equipos creados.
    """
    if len(participantes) != 3:
        raise ValueError("Se necesitan exactamente 3 participantes")
    
    jugadores = get_todos_jugadores()
    
    # Mezclar aleatoriamente cada posición
    for pos in jugadores:
        random.shuffle(jugadores[pos])
    
    # Distribución por posición
    # Porteros: 2-2-2
    dist_G = [2, 2, 2]
    # Defensas: 9-8-8 (aleatorio quién tiene 9)
    dist_D = [9, 8, 8]
    random.shuffle(dist_D)
    # Medios: 8-8-8
    dist_M = [8, 8, 8]
    # Delanteros: 7-7-6 (aleatorio quién tiene 6)
    dist_F = [7, 7, 6]
    random.shuffle(dist_F)
    
    equipos_creados = {}
    db = get_db()
    
    idx = {"G": 0, "D": 0, "M": 0, "F": 0}
    
    for i, nombre_participante in enumerate(participantes):
        # Crear usuario y equipo
        uid = crear_usuario(nombre_participante)
        nombre_equipo = f"Equipo {nombre_participante}"
        eid = crear_equipo(uid, nombre_equipo, liga_id=liga_id)
        
        jugadores_equipo = []
        
        # Asignar jugadores por posición
        for pos, dist in [("G", dist_G), ("D", dist_D), ("M", dist_M), ("F", dist_F)]:
            n = dist[i]
            jugs_pos = jugadores[pos][idx[pos]: idx[pos] + n]
            idx[pos] += n
            jugadores_equipo.extend(jugs_pos)
        
        # Guardar jugadores en Supabase
        for j in jugadores_equipo:
            db.table("jugadores_equipo").upsert({
                "equipo_id": eid,
                "jugador_id": j["jugador_id"],
                "nombre": j["nombre"],
                "posicion": j["posicion"],
                "precio": j.get("precio", 0),
                "es_capitan": False,
                "foto_url": j.get("foto_url", "")
            }).execute()
        
        # Actualizar presupuesto
        total_precio = sum(j.get("precio", 0) for j in jugadores_equipo)
        db.table("equipos").update({"presupuesto": 100.0 - total_precio}).eq("id", eid).execute()
        
        equipos_creados[nombre_participante] = {
            "equipo_id": eid,
            "nombre_equipo": nombre_equipo,
            "jugadores": jugadores_equipo,
            "total": len(jugadores_equipo)
        }
        
        print(f"  ✅ {nombre_participante} → {nombre_equipo} ({len(jugadores_equipo)} jugadores)")
    
    return equipos_creados


def pagina_draft(liga_id: int):
    """Página de Streamlit para hacer el draft de una liga nueva."""
    import streamlit as st
    
    db = get_db()
    
    # Verificar si ya hay equipos en esta liga
    res = db.table("equipos").select("id, nombre").eq("liga_id", liga_id).execute()
    equipos_existentes = res.data or []
    
    if equipos_existentes:
        st.success(f"✅ Esta liga ya tiene {len(equipos_existentes)} equipos creados.")
        for e in equipos_existentes:
            st.write(f"• {e['nombre']}")
        return
    
    st.markdown("""
    <div class="fifa-header">
      <div class="fifa-header-logo">🎲</div>
      <div><p class="fifa-header-title">Crear equipos</p>
      <p class="fifa-header-sub">Reparto aleatorio de jugadores</p></div>
    </div>""", unsafe_allow_html=True)
    
    st.info("""
    Los 75 jugadores se repartirán aleatoriamente entre 3 participantes:
    - 🧤 **2 porteros** por equipo
    - 🛡️ **8-9 defensas** por equipo  
    - ⚙️ **8 centrocampistas** por equipo
    - ⚡ **6-7 delanteros** por equipo
    """)
    
    st.markdown("### Introduce los 3 participantes")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        p1 = st.text_input("Participante 1", placeholder="Nombre...")
    with col2:
        p2 = st.text_input("Participante 2", placeholder="Nombre...")
    with col3:
        p3 = st.text_input("Participante 3", placeholder="Nombre...")
    
    participantes = [p.strip() for p in [p1, p2, p3] if p.strip()]
    
    if len(participantes) == 3:
        st.markdown("---")
        col_a, col_b, col_c = st.columns([1, 2, 1])
        with col_b:
            if st.button("🎲 Repartir jugadores aleatoriamente", type="primary", use_container_width=True):
                with st.spinner("Repartiendo jugadores..."):
                    try:
                        equipos = draft_aleatorio(liga_id, participantes)
                        st.success("✅ ¡Jugadores repartidos correctamente!")
                        st.balloons()
                        
                        # Mostrar resumen
                        for nombre, info in equipos.items():
                            with st.expander(f"👤 {nombre} — {info['total']} jugadores"):
                                pos_labels = {"G": "🧤", "D": "🛡️", "M": "⚙️", "F": "⚡"}
                                for pos in ["G", "D", "M", "F"]:
                                    jugs = [j for j in info["jugadores"] if j["posicion"] == pos]
                                    if jugs:
                                        st.write(f"{pos_labels[pos]} " + ", ".join(j["nombre"] for j in jugs))
                        
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
    else:
        st.warning("Introduce los nombres de los 3 participantes para continuar.")
