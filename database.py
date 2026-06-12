"""
database.py — Conexión a Supabase (reemplaza SQLite para la nube)
"""
import os
from supabase import create_client
from dotenv import load_dotenv
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://xoxhapglilzvlyobknzc.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

def get_db():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

# ── USUARIOS ───────────────────────────────
def crear_usuario(nombre: str) -> int:
    db = get_db()
    # Buscar si ya existe
    res = db.table("usuarios").select("id").eq("nombre", nombre).execute()
    if res.data:
        return res.data[0]["id"]
    res = db.table("usuarios").insert({"nombre": nombre}).execute()
    return res.data[0]["id"]

def get_usuarios():
    db = get_db()
    res = db.table("usuarios").select("id, nombre").order("nombre").execute()
    return [(r["id"], r["nombre"]) for r in res.data]

# ── EQUIPOS ────────────────────────────────
def crear_equipo(usuario_id: int, nombre: str, liga_id: int = None) -> int:
    db = get_db()
    data = {"usuario_id": usuario_id, "nombre": nombre, "presupuesto": 100.0}
    if liga_id:
        data["liga_id"] = liga_id
    res = db.table("equipos").insert(data).execute()
    return res.data[0]["id"]

def get_equipos(usuario_id=None, liga_id=None):
    db = get_db()
    query = db.table("equipos").select("id, nombre, presupuesto, liga_id, usuarios(nombre)")
    if usuario_id:
        query = query.eq("usuario_id", usuario_id)
    if liga_id:
        query = query.eq("liga_id", liga_id)
    res = query.execute()
    return [(r["id"], r["nombre"], r["usuarios"]["nombre"], r["presupuesto"]) for r in res.data]

def get_presupuesto(equipo_id: int) -> float:
    db = get_db()
    res = db.table("equipos").select("presupuesto").eq("id", equipo_id).execute()
    return res.data[0]["presupuesto"] if res.data else 100.0

# ── JUGADORES ──────────────────────────────
def añadir_jugador(equipo_id: int, jugador_id: int, nombre: str, posicion: str, precio: float, capitan: bool = False):
    db = get_db()
    if capitan:
        db.table("jugadores_equipo").update({"es_capitan": False}).eq("equipo_id", equipo_id).execute()
    db.table("jugadores_equipo").upsert({
        "equipo_id": equipo_id,
        "jugador_id": jugador_id,
        "nombre": nombre,
        "posicion": posicion,
        "precio": precio,
        "es_capitan": capitan
    }).execute()
    db.table("equipos").update({"presupuesto": get_presupuesto(equipo_id) - precio}).eq("id", equipo_id).execute()

def get_jugadores_equipo(equipo_id: int):
    db = get_db()
    res = db.table("jugadores_equipo").select("jugador_id, nombre, posicion, precio, es_capitan, foto_url").eq("equipo_id", equipo_id).execute()
    jugadores = []
    for j in res.data:
        pts_res = db.table("puntos_historico").select("puntos").eq("equipo_id", equipo_id).eq("jugador_id", j["jugador_id"]).execute()
        total_pts = sum(p["puntos"] for p in pts_res.data) if pts_res.data else 0
        jugadores.append((j["jugador_id"], j["nombre"], j["posicion"], j["precio"], j["es_capitan"], total_pts, j.get("foto_url","")))
    pos_order = {"G": 1, "D": 2, "M": 3, "F": 4}
    jugadores.sort(key=lambda x: pos_order.get(x[2], 5))
    return jugadores

def jugador_ya_en_equipo(equipo_id: int, jugador_id: int) -> bool:
    db = get_db()
    res = db.table("jugadores_equipo").select("jugador_id").eq("equipo_id", equipo_id).eq("jugador_id", jugador_id).execute()
    return len(res.data) > 0

def contar_jugadores(equipo_id: int) -> int:
    db = get_db()
    res = db.table("jugadores_equipo").select("jugador_id").eq("equipo_id", equipo_id).execute()
    return len(res.data)

def cambiar_capitan(equipo_id: int, jugador_id: int):
    db = get_db()
    db.table("jugadores_equipo").update({"es_capitan": False}).eq("equipo_id", equipo_id).execute()
    db.table("jugadores_equipo").update({"es_capitan": True}).eq("equipo_id", equipo_id).eq("jugador_id", jugador_id).execute()

# ── PUNTOS ─────────────────────────────────
def guardar_puntos(equipo_id: int, jugador_id: int, fixture_id: int, jornada: int, puntos: float, desglose: str):
    db = get_db()
    db.table("puntos_historico").upsert({
        "equipo_id": equipo_id,
        "jugador_id": jugador_id,
        "fixture_id": fixture_id,
        "jornada": jornada,
        "puntos": puntos,
        "desglose": desglose
    }).execute()

def get_clasificacion(liga_id: int = None):
    db = get_db()
    query = db.table("equipos").select("id, nombre, usuarios(nombre)")
    if liga_id:
        query = query.eq("liga_id", liga_id)
    equipos = query.execute()
    resultado = []
    for e in equipos.data:
        pts_res = db.table("puntos_historico").select("puntos").eq("equipo_id", e["id"]).execute()
        total = sum(p["puntos"] for p in pts_res.data) if pts_res.data else 0
        resultado.append((e["usuarios"]["nombre"], e["nombre"], e["id"], total))
    resultado.sort(key=lambda x: x[3], reverse=True)
    return resultado

def get_puntos_jornada(equipo_id: int):
    db = get_db()
    res = db.table("puntos_historico").select("jornada, puntos").eq("equipo_id", equipo_id).execute()
    jornadas = {}
    for r in res.data:
        j = r["jornada"]
        jornadas[j] = jornadas.get(j, 0) + r["puntos"]
    return sorted(jornadas.items())
