"""
Fantasy Mundial 2026 🏆
Calcula puntos automáticamente usando API-Football (gratuita)
Registro: https://dashboard.api-football.com/register
"""

import json
import sqlite3
import os
from datetime import datetime
from typing import Optional
import urllib.request
import urllib.error
from dotenv import load_dotenv

load_dotenv()  # Carga las variables del archivo .env

# ──────────────────────────────────────────
#  CONFIGURACIÓN
# ──────────────────────────────────────────
API_KEY = os.getenv("API_FOOTBALL_KEY", "TU_API_KEY_AQUI")
BASE_URL = "https://v3.football.api-sports.io"
LEAGUE_ID = 1       # FIFA World Cup
SEASON = 2026
DB_FILE = "fantasy_mundial.db"

# ──────────────────────────────────────────
#  SISTEMA DE PUNTUACIÓN
# ──────────────────────────────────────────
PUNTOS = {
    # Todos los jugadores
    "titular":              2,
    "entrada_como_suplente": 1,
    "gol_jugador_campo":    6,
    "gol_delantero":        5,   # delanteros puntúan menos por gol (más esperado)
    "gol_mediocampista":    6,
    "gol_defensa":          8,
    "gol_portero":          10,
    "asistencia":           3,
    "tarjeta_amarilla":    -1,
    "tarjeta_roja":        -3,
    "doble_amarilla":      -3,
    "penalti_fallado":     -2,
    "gol_en_propia":       -2,

    # Porteros
    "portero_sin_goles_recibidos":   6,   # clean sheet 90 min
    "portero_penalti_parado":        5,
    "portero_gol_recibido":         -1,   # por cada gol recibido

    # Defensa
    "defensa_sin_goles_recibidos":   4,

    # Capitán (multiplicador ×2)
    # Se aplica automáticamente en calcular_puntos_equipo()
}


# ──────────────────────────────────────────
#  CLIENTE API
# ──────────────────────────────────────────
def _api_get(endpoint: str, params: dict = {}) -> dict:
    """Llama a API-Football y devuelve el JSON."""
    query = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"{BASE_URL}/{endpoint}?{query}"
    req = urllib.request.Request(url, headers={
        "x-apisports-key": API_KEY,
        "Accept": "application/json"
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"❌ Error HTTP {e.code}: {e.reason}")
        return {}
    except urllib.error.URLError as e:
        print(f"❌ Error de red: {e.reason}")
        return {}


def obtener_partidos_jornada(jornada: int) -> list[dict]:
    """Devuelve los partidos de una jornada del Mundial."""
    data = _api_get("fixtures", {
        "league": LEAGUE_ID,
        "season": SEASON,
        "round": f"Group%20Stage%20-%20{jornada}"
    })
    partidos = data.get("response", [])
    print(f"📅 Jornada {jornada}: {len(partidos)} partidos encontrados")
    return partidos


def obtener_stats_jugador(fixture_id: int) -> list[dict]:
    """Devuelve estadísticas de todos los jugadores de un partido."""
    data = _api_get("fixtures/players", {"fixture": fixture_id})
    return data.get("response", [])


def obtener_eventos_partido(fixture_id: int) -> list[dict]:
    """Devuelve eventos (goles, tarjetas, sustituciones) de un partido."""
    data = _api_get("fixtures/events", {"fixture": fixture_id})
    return data.get("response", [])


# ──────────────────────────────────────────
#  MOTOR DE PUNTUACIÓN
# ──────────────────────────────────────────
def calcular_puntos_jugador(jugador_id: int, fixture_id: int) -> dict:
    """
    Calcula los puntos de un jugador en un partido específico.
    Devuelve un dict con desglose de puntos.
    """
    stats_raw = obtener_stats_jugador(fixture_id)
    eventos = obtener_eventos_partido(fixture_id)

    # Buscar stats del jugador
    stats_jugador = None
    posicion = "M"  # Mediocampista por defecto
    for equipo_data in stats_raw:
        for p in equipo_data.get("players", []):
            if p["player"]["id"] == jugador_id:
                stats_jugador = p["statistics"][0]
                posicion = p["player"].get("pos", "M")
                break

    if not stats_jugador:
        return {"total": 0, "desglose": {"no_jugó": 0}}

    desglose = {}
    total = 0

    # Participación
    minutos = stats_jugador.get("games", {}).get("minutes", 0) or 0
    if minutos >= 60:
        desglose["titular"] = PUNTOS["titular"]
        total += PUNTOS["titular"]
    elif minutos > 0:
        desglose["suplente"] = PUNTOS["entrada_como_suplente"]
        total += PUNTOS["entrada_como_suplente"]
    else:
        return {"total": 0, "desglose": {"no_jugó": 0}}

    # Goles según posición
    goles = stats_jugador.get("goals", {}).get("total", 0) or 0
    if goles > 0:
        clave = {
            "G": "gol_portero",
            "D": "gol_defensa",
            "M": "gol_mediocampista",
            "F": "gol_delantero"
        }.get(posicion, "gol_jugador_campo")
        pts_gol = PUNTOS[clave] * goles
        desglose[f"goles({goles})"] = pts_gol
        total += pts_gol

    # Asistencias
    asistencias = stats_jugador.get("goals", {}).get("assists", 0) or 0
    if asistencias > 0:
        pts_asist = PUNTOS["asistencia"] * asistencias
        desglose[f"asistencias({asistencias})"] = pts_asist
        total += pts_asist

    # Tarjetas
    amarillas = stats_jugador.get("cards", {}).get("yellow", 0) or 0
    rojas = stats_jugador.get("cards", {}).get("red", 0) or 0
    if amarillas == 2:
        desglose["doble_amarilla"] = PUNTOS["doble_amarilla"]
        total += PUNTOS["doble_amarilla"]
    elif amarillas == 1:
        desglose["amarilla"] = PUNTOS["tarjeta_amarilla"]
        total += PUNTOS["tarjeta_amarilla"]
    if rojas == 1:
        desglose["roja"] = PUNTOS["tarjeta_roja"]
        total += PUNTOS["tarjeta_roja"]

    # Penaltis fallados
    penaltis_fallados = stats_jugador.get("penalty", {}).get("missed", 0) or 0
    if penaltis_fallados > 0:
        pts_pen = PUNTOS["penalti_fallado"] * penaltis_fallados
        desglose[f"penaltis_fallados({penaltis_fallados})"] = pts_pen
        total += pts_pen

    # Goles en propia
    goles_propia = stats_jugador.get("goals", {}).get("owngoals", 0) or 0
    if goles_propia > 0:
        pts_propia = PUNTOS["gol_en_propia"] * goles_propia
        desglose[f"propias({goles_propia})"] = pts_propia
        total += pts_propia

    # Portero: goles recibidos y clean sheet
    if posicion == "G":
        goles_recibidos = stats_jugador.get("goals", {}).get("conceded", 0) or 0
        if goles_recibidos == 0 and minutos >= 60:
            desglose["clean_sheet"] = PUNTOS["portero_sin_goles_recibidos"]
            total += PUNTOS["portero_sin_goles_recibidos"]
        else:
            pts_rec = PUNTOS["portero_gol_recibido"] * goles_recibidos
            desglose[f"goles_recibidos({goles_recibidos})"] = pts_rec
            total += pts_rec
        penaltis_parados = stats_jugador.get("penalty", {}).get("saved", 0) or 0
        if penaltis_parados > 0:
            pts_pp = PUNTOS["portero_penalti_parado"] * penaltis_parados
            desglose[f"penaltis_parados({penaltis_parados})"] = pts_pp
            total += pts_pp

    # Defensa: clean sheet
    if posicion == "D":
        # Para clean sheet de defensa necesitamos saber si el equipo no recibió goles
        # Lo calculamos a partir de los eventos del partido
        equipo_jugador = None
        for equipo_data in stats_raw:
            for p in equipo_data.get("players", []):
                if p["player"]["id"] == jugador_id:
                    equipo_jugador = equipo_data["team"]["id"]
        if equipo_jugador:
            goles_contra = sum(
                1 for e in eventos
                if e.get("type") == "Goal"
                and e.get("team", {}).get("id") != equipo_jugador
                and e.get("detail") != "Own Goal"
            )
            if goles_contra == 0 and minutos >= 60:
                desglose["clean_sheet_defensa"] = PUNTOS["defensa_sin_goles_recibidos"]
                total += PUNTOS["defensa_sin_goles_recibidos"]

    return {"total": total, "desglose": desglose}


# ──────────────────────────────────────────
#  BASE DE DATOS
# ──────────────────────────────────────────
def init_db():
    """Crea las tablas si no existen."""
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre  TEXT UNIQUE NOT NULL,
            creado  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS equipos (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id  INTEGER REFERENCES usuarios(id),
            nombre      TEXT NOT NULL,
            presupuesto REAL DEFAULT 100.0
        );

        CREATE TABLE IF NOT EXISTS jugadores_equipo (
            equipo_id   INTEGER REFERENCES equipos(id),
            jugador_id  INTEGER NOT NULL,
            nombre      TEXT NOT NULL,
            posicion    TEXT CHECK(posicion IN ('G','D','M','F')),
            precio      REAL DEFAULT 0.0,
            es_capitan  INTEGER DEFAULT 0,
            PRIMARY KEY (equipo_id, jugador_id)
        );

        CREATE TABLE IF NOT EXISTS puntos_historico (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            equipo_id   INTEGER REFERENCES equipos(id),
            jugador_id  INTEGER NOT NULL,
            fixture_id  INTEGER NOT NULL,
            jornada     INTEGER,
            puntos      REAL DEFAULT 0,
            desglose    TEXT,
            calculado   TEXT DEFAULT (datetime('now')),
            UNIQUE(equipo_id, jugador_id, fixture_id)
        );
    """)
    con.commit()
    con.close()
    print("✅ Base de datos inicializada")


# ──────────────────────────────────────────
#  GESTIÓN DE EQUIPOS
# ──────────────────────────────────────────
def crear_usuario(nombre: str) -> int:
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute("INSERT OR IGNORE INTO usuarios (nombre) VALUES (?)", (nombre,))
    con.commit()
    cur.execute("SELECT id FROM usuarios WHERE nombre=?", (nombre,))
    uid = cur.fetchone()[0]
    con.close()
    print(f"👤 Usuario '{nombre}' (id={uid})")
    return uid


def crear_equipo(usuario_id: int, nombre_equipo: str) -> int:
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute(
        "INSERT INTO equipos (usuario_id, nombre) VALUES (?, ?)",
        (usuario_id, nombre_equipo)
    )
    con.commit()
    eid = cur.lastrowid
    con.close()
    print(f"🏟️  Equipo '{nombre_equipo}' creado (id={eid})")
    return eid


def añadir_jugador(equipo_id: int, jugador_id: int, nombre: str,
                   posicion: str, precio: float = 0.0, capitan: bool = False):
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    # Desmarcar capitán anterior si aplica
    if capitan:
        cur.execute(
            "UPDATE jugadores_equipo SET es_capitan=0 WHERE equipo_id=?",
            (equipo_id,)
        )
    cur.execute("""
        INSERT OR REPLACE INTO jugadores_equipo
        (equipo_id, jugador_id, nombre, posicion, precio, es_capitan)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (equipo_id, jugador_id, nombre, posicion, precio, int(capitan)))
    # Restar del presupuesto
    cur.execute(
        "UPDATE equipos SET presupuesto = presupuesto - ? WHERE id=?",
        (precio, equipo_id)
    )
    con.commit()
    con.close()
    cap_str = " ©" if capitan else ""
    print(f"  ➕ {nombre} ({posicion}){cap_str} añadido al equipo {equipo_id}")


def ver_equipo(equipo_id: int):
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute("""
        SELECT j.nombre, j.posicion, j.precio, j.es_capitan,
               COALESCE(SUM(p.puntos), 0) as total_pts
        FROM jugadores_equipo j
        LEFT JOIN puntos_historico p
            ON p.equipo_id = j.equipo_id AND p.jugador_id = j.jugador_id
        WHERE j.equipo_id = ?
        GROUP BY j.jugador_id
        ORDER BY CASE j.posicion WHEN 'G' THEN 1 WHEN 'D' THEN 2 WHEN 'M' THEN 3 WHEN 'F' THEN 4 ELSE 5 END
    """, (equipo_id,))
    jugadores = cur.fetchall()
    cur.execute("SELECT nombre, presupuesto FROM equipos WHERE id=?", (equipo_id,))
    equipo = cur.fetchone()
    con.close()

    print(f"\n{'='*50}")
    print(f"  🏟️  {equipo[0]}   💰 Presupuesto restante: ${equipo[1]:.1f}M")
    print(f"{'='*50}")
    pos_icons = {"G": "🧤", "D": "🛡️", "M": "⚙️", "F": "⚡"}
    total_equipo = 0
    for nombre, pos, precio, capitan, pts in jugadores:
        cap = " ©" if capitan else "  "
        icon = pos_icons.get(pos, "⚽")
        print(f"  {icon} {cap}{nombre:<25} {pts:>5.0f} pts  (${precio}M)")
        total_equipo += pts
    print(f"{'='*50}")
    print(f"  📊 TOTAL: {total_equipo:.0f} puntos\n")


# ──────────────────────────────────────────
#  ACTUALIZACIÓN DE PUNTOS
# ──────────────────────────────────────────
def actualizar_puntos_jornada(jornada: int):
    """
    Recorre todos los partidos de una jornada,
    calcula puntos de cada jugador en cada equipo fantasy
    y los guarda en la BD.
    """
    print(f"\n🔄 Actualizando puntos — Jornada {jornada}")
    partidos = obtener_partidos_jornada(jornada)
    if not partidos:
        print("⚠️  No se encontraron partidos. Verifica la API key y la jornada.")
        return

    from database import get_equipos, get_jugadores_equipo, guardar_puntos, get_db

    # Obtener alineaciones guardadas para esta jornada
    # Usa la última alineación guardada ANTES del deadline del día del partido
    db = get_db()

    # Obtener la fecha de cada partido para saber qué alineación usar
    alineaciones_por_equipo = {}
    for partido in partidos:
        fixture_date = partido.get("fixture", {}).get("date", "")[:10]  # YYYY-MM-DD
        # Deadline de ese día (16:00 UTC = 18:00h española)
        deadline_dia = None
        if fixture_date:
            dd_res = db.table("deadlines_diarios").select("deadline").eq("fecha", fixture_date).execute()
            if dd_res.data:
                raw = dd_res.data[0]["deadline"]
                if isinstance(raw, str):
                    raw = raw.replace("Z", "+00:00")
                    import datetime as dt
                    deadline_dia = dt.datetime.fromisoformat(raw)

        # Obtener alineaciones guardadas ANTES del deadline de ese día
        if deadline_dia:
            alin_res = db.table("alineaciones").select("*").eq("jornada", jornada).lte("guardado", deadline_dia.isoformat()).execute()
        else:
            alin_res = db.table("alineaciones").select("*").eq("jornada", jornada).execute()

        for a in (alin_res.data or []):
            eid = a["equipo_id"]
            if eid not in alineaciones_por_equipo:
                alineaciones_por_equipo[eid] = {"titulares": set(), "suplentes": []}
            if a["es_titular"]:
                alineaciones_por_equipo[eid]["titulares"].add(a["jugador_id"])
            else:
                alineaciones_por_equipo[eid]["suplentes"].append((a.get("orden_suplente", 99), a["jugador_id"]))

    alineaciones = [a for adict in alineaciones_por_equipo.values() for a in [adict]]
    hay_alineaciones = len(alineaciones_por_equipo) > 0

    if hay_alineaciones:
        print(f"  📋 Usando alineaciones guardadas para jornada {jornada}")
        # Construir lista de titulares y suplentes por equipo
        titulares_por_equipo = {}
        suplentes_por_equipo = {}
        for a in alineaciones:
            eid = a["equipo_id"]
            if a["es_titular"]:
                titulares_por_equipo.setdefault(eid, set()).add(a["jugador_id"])
            else:
                suplentes_por_equipo.setdefault(eid, [])
                suplentes_por_equipo[eid].append((a["orden_suplente"], a["jugador_id"]))
        # Ordenar suplentes por orden
        for eid in suplentes_por_equipo:
            suplentes_por_equipo[eid].sort()
    else:
        print(f"  ⚠️  Sin alineaciones para jornada {jornada} — puntuando todos los jugadores")

    # Obtener jugadores con capitán
    equipos = get_equipos()
    capitan_por_equipo = {}
    todos_jugadores_equipo = {}
    for equipo in equipos:
        equipo_id = equipo[0]
        jugs = get_jugadores_equipo(equipo_id)
        todos_jugadores_equipo[equipo_id] = jugs
        for jug in jugs:
            if jug[4]:  # es_capitan
                capitan_por_equipo[equipo_id] = jug[0]

    for partido in partidos:
        fixture_id = partido["fixture"]["id"]
        estado = partido["fixture"]["status"]["short"]

        if estado not in ("FT", "AET", "PEN"):
            print(f"  ⏳ Partido {fixture_id} aún no terminado ({estado}), saltando…")
            continue

        print(f"  ⚽ Procesando fixture {fixture_id}…")

        for equipo_id, jugs in todos_jugadores_equipo.items():
            if hay_alineaciones:
                titulares = titulares_por_equipo.get(equipo_id, set())
                suplentes = suplentes_por_equipo.get(equipo_id, [])
                jugadores_a_puntuar = []

                for jug in jugs:
                    jug_id = jug[0]
                    if jug_id in titulares:
                        # Comprobar si el titular jugó
                        resultado = calcular_puntos_jugador(jug_id, fixture_id)
                        if resultado["total"] == 0 and "no_jugó" in resultado["desglose"]:
                            # Titular no jugó — buscar suplente
                            print(f"    ↩️  {jug[1]} no jugó, buscando suplente...")
                            for _, sup_id in suplentes:
                                sup_resultado = calcular_puntos_jugador(sup_id, fixture_id)
                                if sup_resultado["total"] > 0 or "no_jugó" not in sup_resultado["desglose"]:
                                    jugadores_a_puntuar.append((sup_id, sup_resultado))
                                    suplentes = [(o, s) for o, s in suplentes if s != sup_id]
                                    break
                        else:
                            jugadores_a_puntuar.append((jug_id, resultado))
            else:
                jugadores_a_puntuar = [(jug[0], calcular_puntos_jugador(jug[0], fixture_id)) for jug in jugs]

            capitan_id = capitan_por_equipo.get(equipo_id)
            for jugador_id, resultado in jugadores_a_puntuar:
                pts = resultado["total"]
                if jugador_id == capitan_id:
                    pts *= 2
                guardar_puntos(equipo_id, jugador_id, fixture_id, jornada,
                              pts, json.dumps(resultado["desglose"]))

    print(f"✅ Jornada {jornada} actualizada\n")


def clasificacion():
    """Muestra la clasificación general del fantasy."""
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute("""
        SELECT u.nombre, e.nombre, COALESCE(SUM(p.puntos), 0) as total
        FROM equipos e
        JOIN usuarios u ON u.id = e.usuario_id
        LEFT JOIN puntos_historico p ON p.equipo_id = e.id
        GROUP BY e.id
        ORDER BY total DESC
    """)
    rows = cur.fetchall()
    con.close()

    print(f"\n{'='*45}")
    print(f"  🏆  CLASIFICACIÓN FANTASY MUNDIAL 2026")
    print(f"{'='*45}")
    for i, (usuario, equipo, pts) in enumerate(rows, 1):
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}. ")
        print(f"  {medal}  {usuario:<15} ({equipo:<20}) {pts:>6.0f} pts")
    print(f"{'='*45}\n")


# ──────────────────────────────────────────
#  DEMO / MODO SIN API KEY
# ──────────────────────────────────────────
def demo_sin_api():
    """
    Carga datos ficticios para probar la app sin API key.
    Útil para ver cómo funciona el sistema.
    """
    print("\n🎮 Modo DEMO activado (sin API key real)\n")
    init_db()

    # Crear usuarios y equipos
    uid1 = crear_usuario("Mikel")
    uid2 = crear_usuario("Amaia")
    e1 = crear_equipo(uid1, "Ikurriña FC")
    e2 = crear_equipo(uid2, "Txuri-Urdin Stars")

    # Jugadores con IDs reales de API-Football (World Cup 2026)
    # Puedes buscar IDs en: GET /players?search=Mbappe&league=1&season=2026
    añadir_jugador(e1, 278,  "Mbappé",    "F", 12.0, capitan=True)
    añadir_jugador(e1, 521,  "Bellingham","M", 10.5)
    añadir_jugador(e1, 1163, "Vinicius",  "F",  9.0)
    añadir_jugador(e1, 303,  "Rüdiger",   "D",  6.5)
    añadir_jugador(e1, 794,  "Oblak",     "G",  5.0)

    añadir_jugador(e2, 306,  "Pedri",     "M", 10.0, capitan=True)
    añadir_jugador(e2, 2295, "Lewandowski","F", 9.5)
    añadir_jugador(e2, 284,  "Theo H.",   "D",  7.0)
    añadir_jugador(e2, 889,  "Salah",     "F", 11.0)
    añadir_jugador(e2, 50011,"Courtois",  "G",  5.5)

    ver_equipo(e1)
    ver_equipo(e2)

    # Simular puntos manualmente (como si hubieran jugado)
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    datos_simulados = [
        # (equipo_id, jugador_id, fixture_id, jornada, puntos)
        (e1, 278,  999001, 1, 14),  # Mbappé: gol + titular × capitán
        (e1, 521,  999001, 1,  5),  # Bellingham
        (e1, 1163, 999001, 1,  8),  # Vinicius: gol
        (e1, 303,  999001, 1,  6),  # Rüdiger: clean sheet
        (e1, 794,  999001, 1,  8),  # Oblak: clean sheet portero
        (e2, 306,  999002, 1, 10),  # Pedri: asistencia × capitán
        (e2, 2295, 999002, 1, 11),  # Lewandowski: 2 goles
        (e2, 284,  999002, 1,  2),  # Theo
        (e2, 889,  999002, 1,  9),  # Salah: gol
        (e2, 50011,999002, 1,  8),  # Courtois: clean sheet
    ]
    for equipo_id, jug_id, fix_id, jornada, pts in datos_simulados:
        cur.execute("""
            INSERT OR REPLACE INTO puntos_historico
            (equipo_id, jugador_id, fixture_id, jornada, puntos, desglose)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (equipo_id, jug_id, fix_id, jornada, pts, '{"simulado": true}'))
    con.commit()
    con.close()

    clasificacion()
    print("💡 Para usar con datos reales: pon tu API key en API_KEY o")
    print("   exporta la variable de entorno:  export API_FOOTBALL_KEY=tu_clave\n")


# ──────────────────────────────────────────
#  PUNTO DE ENTRADA
# ──────────────────────────────────────────
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo_sin_api()
    elif len(sys.argv) > 1 and sys.argv[1] == "jornada":
        jornada = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        init_db()
        actualizar_puntos_jornada(jornada)
        clasificacion()
    elif len(sys.argv) > 1 and sys.argv[1] == "clasificacion":
        init_db()
        clasificacion()
    else:
        print("""
🏆 Fantasy Mundial 2026

Uso:
  python fantasy.py demo              → Prueba con datos ficticios
  python fantasy.py jornada 1         → Actualiza puntos de jornada 1
  python fantasy.py clasificacion     → Ver clasificación actual

Variables de entorno:
  export API_FOOTBALL_KEY=tu_clave    → API key de api-football.com
        """)
