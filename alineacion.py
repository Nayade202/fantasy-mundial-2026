"""
alineacion.py — Página de selección de alineación con campo visual
"""
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime, timezone
import json
import os
from database import get_db, get_jugadores_equipo

FORMACIONES = {
    "4-3-3": {"D": 4, "M": 3, "F": 3},
    "4-4-2": {"D": 4, "M": 4, "F": 2},
    "4-2-3-1": {"D": 4, "M": 5, "F": 1},
    "3-5-2": {"D": 3, "M": 5, "F": 2},
    "3-4-3": {"D": 3, "M": 4, "F": 3},
    "5-3-2": {"D": 5, "M": 3, "F": 2},
    "5-4-1": {"D": 5, "M": 4, "F": 1},
    "4-5-1": {"D": 4, "M": 5, "F": 1},
}

def get_deadline(jornada: int):
    db = get_db()
    res = db.table("jornadas_info").select("deadline").eq("jornada", jornada).execute()
    if res.data:
        raw = res.data[0]["deadline"]
        try:
            if isinstance(raw, str):
                raw = raw.replace("Z", "+00:00")
                return datetime.fromisoformat(raw)
            return raw
        except Exception:
            return None
    return None

def is_deadline_passed(jornada: int) -> bool:
    deadline = get_deadline(jornada)
    if not deadline:
        return False
    ahora = datetime.now(timezone.utc)
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)
    return ahora > deadline

def get_alineacion(equipo_id: int, jornada: int):
    db = get_db()
    res = db.table("alineaciones").select("*").eq("equipo_id", equipo_id).eq("jornada", jornada).execute()
    return res.data or []

def guardar_alineacion(equipo_id: int, jornada: int, titulares: list, suplentes: list):
    db = get_db()
    db.table("alineaciones").delete().eq("equipo_id", equipo_id).eq("jornada", jornada).execute()
    for jug_id in titulares:
        db.table("alineaciones").insert({
            "equipo_id": equipo_id,
            "jugador_id": jug_id,
            "jornada": jornada,
            "es_titular": True,
            "orden_suplente": None
        }).execute()
    for i, jug_id in enumerate(suplentes, 1):
        db.table("alineaciones").insert({
            "equipo_id": equipo_id,
            "jugador_id": jug_id,
            "jornada": jornada,
            "es_titular": False,
            "orden_suplente": i
        }).execute()

def render_campo(titulares_por_pos: dict, formacion: str):
    """Renderiza el campo de fútbol con los jugadores."""
    pos_data = {}
    for jug in titulares_por_pos.get("G", []):
        pos_data.setdefault("G", []).append(jug)
    for jug in titulares_por_pos.get("D", []):
        pos_data.setdefault("D", []).append(jug)
    for jug in titulares_por_pos.get("M", []):
        pos_data.setdefault("M", []).append(jug)
    for jug in titulares_por_pos.get("F", []):
        pos_data.setdefault("F", []).append(jug)

    def jugadores_html(jugs):
        html = ""
        for j in jugs:
            nombre = j["nombre"].split()[-1]  # Solo apellido
            jid = j["jugador_id"]
            html += f"""
            <div class="player">
                <img src="https://media.api-sports.io/football/players/{jid}.png"
                     onerror="this.style.display='none';this.nextSibling.style.display='flex'"
                     style="width:40px;height:40px;border-radius:50%;border:2px solid white;object-fit:cover;">
                <div class="avatar" style="display:none;width:40px;height:40px;border-radius:50%;background:#1D9E75;border:2px solid white;align-items:center;justify-content:center;font-weight:500;font-size:12px;color:white;">{nombre[:2].upper()}</div>
                <span>{nombre}</span>
            </div>"""
        return html

    campo_html = f"""
    <div style="font-family:sans-serif;width:100%;max-width:500px;margin:0 auto;">
        <div style="background:#2d5a27;border-radius:12px;padding:16px;position:relative;min-height:520px;">
            <div style="border:2px solid rgba(255,255,255,0.3);border-radius:8px;height:490px;position:relative;overflow:hidden;">
                <div style="position:absolute;top:50%;left:0;right:0;border-top:1px solid rgba(255,255,255,0.2);"></div>
                <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:80px;height:80px;border:1px solid rgba(255,255,255,0.2);border-radius:50%;"></div>

                <style>
                .fila{{display:flex;justify-content:space-around;align-items:center;padding:8px 4px;}}
                .player{{display:flex;flex-direction:column;align-items:center;gap:3px;}}
                .player span{{color:white;font-size:11px;font-weight:500;text-shadow:1px 1px 2px rgba(0,0,0,0.8);max-width:60px;text-align:center;overflow:hidden;white-space:nowrap;text-overflow:ellipsis;}}
                </style>

                <div style="position:absolute;top:8px;left:0;right:0;">
                    <div class="fila">{jugadores_html(pos_data.get("F", []))}</div>
                </div>
                <div style="position:absolute;top:calc(8px + 130px);left:0;right:0;">
                    <div class="fila">{jugadores_html(pos_data.get("M", []))}</div>
                </div>
                <div style="position:absolute;top:calc(8px + 260px);left:0;right:0;">
                    <div class="fila">{jugadores_html(pos_data.get("D", []))}</div>
                </div>
                <div style="position:absolute;bottom:8px;left:0;right:0;">
                    <div class="fila">{jugadores_html(pos_data.get("G", []))}</div>
                </div>
            </div>
        </div>
        <div style="text-align:center;margin-top:8px;font-size:13px;color:#666;">{formacion}</div>
    </div>
    """
    components.html(campo_html, height=560)


def pagina_alineacion(equipo_id: int, jornada: int):
    """Página principal de gestión de alineación."""
    st.markdown("## ⚽ Mi alineación")

    # Verificar deadline
    deadline = get_deadline(jornada)
    bloqueado = is_deadline_passed(jornada)

    if deadline:
        if bloqueado:
            st.error(f"🔒 Deadline superado — la alineación está bloqueada para la jornada {jornada}")
        else:
            ahora = datetime.now(timezone.utc)
            if deadline.tzinfo is None:
                deadline = deadline.replace(tzinfo=timezone.utc)
            tiempo_restante = deadline - ahora
            horas = int(tiempo_restante.total_seconds() // 3600)
            minutos = int((tiempo_restante.total_seconds() % 3600) // 60)
            st.info(f"⏰ Tiempo para guardar la alineación: **{horas}h {minutos}min**")

    # Obtener jugadores del equipo
    todos = get_jugadores_equipo(equipo_id)
    porteros = [j for j in todos if j[2] == "G"]
    defensas = [j for j in todos if j[2] == "D"]
    medios   = [j for j in todos if j[2] == "M"]
    delanteros = [j for j in todos if j[2] == "F"]

    # Selector de formación
    col1, col2 = st.columns([2, 1])
    with col1:
        formacion = st.selectbox("Formación", list(FORMACIONES.keys()), disabled=bloqueado)
    config = FORMACIONES[formacion]

    st.divider()
    col_campo, col_seleccion = st.columns([1, 1])

    with col_seleccion:
        st.markdown("### Selecciona titulares")

        # Portero
        st.markdown("**🧤 Portero (1)**")
        opts_g = {j[1]: j[0] for j in porteros}
        sel_g = st.selectbox("Portero", list(opts_g.keys()), disabled=bloqueado, key="sel_g")

        # Defensas
        n_d = config["D"]
        st.markdown(f"**🛡️ Defensas ({n_d})**")
        opts_d = {j[1]: j[0] for j in defensas}
        sel_d = st.multiselect(f"Elige {n_d} defensas", list(opts_d.keys()),
                               max_selections=n_d, disabled=bloqueado, key="sel_d")

        # Medios
        n_m = config["M"]
        st.markdown(f"**⚙️ Centrocampistas ({n_m})**")
        opts_m = {j[1]: j[0] for j in medios}
        sel_m = st.multiselect(f"Elige {n_m} centrocampistas", list(opts_m.keys()),
                               max_selections=n_m, disabled=bloqueado, key="sel_m")

        # Delanteros
        n_f = config["F"]
        st.markdown(f"**⚡ Delanteros ({n_f})**")
        opts_f = {j[1]: j[0] for j in delanteros}
        sel_f = st.multiselect(f"Elige {n_f} delanteros", list(opts_f.keys()),
                               max_selections=n_f, disabled=bloqueado, key="sel_f")

        st.divider()
        st.markdown("**🔄 Suplentes (máx. 3)**")
        ya_seleccionados = set([sel_g] + sel_d + sel_m + sel_f)
        disponibles_sup = [j[1] for j in todos if j[1] not in ya_seleccionados]
        sel_suplentes = st.multiselect("Suplentes (por orden)", disponibles_sup,
                                       max_selections=3, disabled=bloqueado, key="sel_sup")

        # Validar y guardar
        total_titulares = 1 + len(sel_d) + len(sel_m) + len(sel_f)
        valido = (
            len(sel_d) == n_d and
            len(sel_m) == n_m and
            len(sel_f) == n_f
        )

        if not bloqueado:
            if st.button("💾 Guardar alineación", type="primary", disabled=not valido):
                titulares_ids = (
                    [opts_g[sel_g]] +
                    [opts_d[n] for n in sel_d] +
                    [opts_m[n] for n in sel_m] +
                    [opts_f[n] for n in sel_f]
                )
                # Suplentes: buscar IDs
                todos_dict = {j[1]: j[0] for j in todos}
                suplentes_ids = [todos_dict[n] for n in sel_suplentes]
                guardar_alineacion(equipo_id, jornada, titulares_ids, suplentes_ids)
                st.success(f"✅ Alineación {formacion} guardada para jornada {jornada}")
                st.rerun()

            if not valido:
                st.warning(f"Necesitas: 1 portero, {n_d} defensas, {n_m} centros, {n_f} delanteros")

    with col_campo:
        st.markdown("### Vista del campo")
        # Construir datos para el campo
        titulares_por_pos = {}
        if sel_g:
            jug = next((j for j in porteros if j[1] == sel_g), None)
            if jug:
                titulares_por_pos["G"] = [{"nombre": jug[1], "jugador_id": jug[0]}]
        titulares_por_pos["D"] = [{"nombre": n, "jugador_id": opts_d[n]} for n in sel_d]
        titulares_por_pos["M"] = [{"nombre": n, "jugador_id": opts_m[n]} for n in sel_m]
        titulares_por_pos["F"] = [{"nombre": n, "jugador_id": opts_f[n]} for n in sel_f]

        if total_titulares >= 5:
            render_campo(titulares_por_pos, formacion)
        else:
            st.info("Selecciona jugadores para ver el campo")
