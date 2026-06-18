"""
Fantasy Mundial 2026 🏆
Calcula puntos automáticamente usando API-Football.

Registro API: https://dashboard.api-football.com/register

Uso:
  python fantasy_mundial_corregido.py demo
  python fantasy_mundial_corregido.py jornada 1
  python fantasy_mundial_corregido.py clasificacion

Variable de entorno:
  API_FOOTBALL_KEY=tu_clave
"""

import json
import os
import sqlite3
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from typing import Any, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv es opcional. También puedes usar variables de entorno normales.
    pass

# ──────────────────────────────────────────
#  CONFIGURACIÓN
# ──────────────────────────────────────────
API_KEY = os.getenv("API_FOOTBALL_KEY")
BASE_URL = "https://v3.football.api-sports.io"
LEAGUE_ID = 1       # FIFA World Cup
SEASON = 2026
DB_FILE = "fantasy_mundial.db"

# Para probar ahora, si la API no devuelve datos de 2026, cambia temporalmente:
# SEASON = 2022

# ──────────────────────────────────────────
#  SISTEMA DE PUNTUACIÓN
# ──────────────────────────────────────────
PUNTOS = {
    "titular": 2,
    "entrada_como_suplente": 1,
    "gol_jugador_campo": 6,
    "gol_delantero": 5,
    "gol_mediocampista": 6,
    "gol_defensa": 8,
    "gol_portero": 10,
    "asistencia": 3,
    "tarjeta_amarilla": -1,
    "tarjeta_roja": -3,
    "doble_amarilla": -3,
    "penalti_fallado": -2,
    "gol_en_propia": -2,
    "portero_sin_goles_recibidos": 6,
    "portero_penalti_parado": 5,
    "portero_gol_recibido": -1,
    "defensa_sin_goles_recibidos": 4,
}

POSICIONES_API = {
    "Goalkeeper": "G",
    "Defender": "D",
    "Midfielder": "M",
    "Attacker": "F",
    "G": "G",
    "D": "D",
    "M": "M",
    "F": "F",
}

# ──────────────────────────────────────────
#  CLIENTE API
# ──────────────────────────────────────────
def validar_api_key() -> None:
    if not API_KEY:
        raise RuntimeError(
            "Falta API_FOOTBALL_KEY. Configúrala antes de usar datos reales. "
            "Ejemplo: export API_FOOTBALL_KEY=tu_clave"
        )


def _api_get(endpoint: str, params: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """Llama a API-Football y devuelve el JSON."""
    validar_api_key()
    params = params or {}
    query = urllib.parse.urlencode(params)
    url = f"{BASE_URL}/{endpoint}"
    if query:
        url += f"?{query}"

    req = urllib.request.Request(
        url,
        headers={
            "x-apisports-key": API_KEY,
            "Accept": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        print(f"❌ Error HTTP {e.code}: {e.reason}\n{body}")
        return {}
    except urllib.error.URLError as e:
        print(f"❌ Error de red: {e.reason}")
        return {}
    except json.JSONDecodeError:
        print("❌ La API no devolvió JSON válido")
        return {}

    errors = data.get("errors")
    if errors:
        print(f"⚠️ Errores API: {errors}")
    return data


def obtener_partidos_jornada(jornada: int) -> list[dict[str, Any]]:
    """Devuelve partidos de una jornada del Mundial."""
    # No codificamos manualmente el round: urlencode lo hace por nosotros.
    round_name = f"Group Stage - {jornada}"
    data = _api_get("fixtures", {
        "league": LEAGUE_ID,
        "season": SEASON,
        "round": round_name,
    })
    partidos = data.get("response", [])
    print(f"📅 Jornada {jornada}: {len(partidos)} partidos encontrados")
    return partidos


def obtener_stats_jugador(fixture_id: int) -> list[dict[str, Any]]:
    data = _api_get("fixtures/players", {"fixture": fixture_id})
    return data.get("response", [])


def obtener_eventos_partido(fixture_id: int) -> list[dict[str, Any]]:
    data = _api_get("fixtures/events", {"fixture": fixture_id})
    return data.get("response", [])

# ──────────────────────────────────────────
#  HELPERS DE STATS
# ──────────────────────────────────────────
def normalizar_posicion(posicion_api: Optional[str]) -> str:
    if not posicion_api:
        return "M"
    return POSICIONES_API.get(posicion_api, "M")


def buscar_jugador_en_stats(
    jugador_id: int,
    stats_raw: list[dict[str, Any]],
) -> tuple[Optional[dict[str, Any]], str, Optional[int]]:
    """Devuelve stats, posición normalizada y equipo_id del jugador."""
    for equipo_data in stats_raw:
        equipo_id = equipo_data.get("team", {}).get("id")
        for p in equipo_data.get("players", []):
            if p.get("player", {}).get("id") == jugador_id:
                statistics = p.get("statistics") or []
                if not statistics:
                    return None, "M", equipo_id
                stats = statistics[0]
                posicion_api = stats.get("games", {}).get("position")
                posicion = normalizar_posicion(posicion_api)
                return stats, posicion, equipo_id
    return None, "M", None


def equipo_recibio_goles(equipo_id: int, fixture: dict[str, Any]) -> int:
    """Calcula goles recibidos por un equipo usando el marcador final del fixture."""
    teams = fixture.get("teams", {})
    goals = fixture.get("goals", {})

    home_id = teams.get("home", {}).get("id")
    away_id = teams.get("away", {}).get("id")

    home_goals = goals.get("home")
    away_goals = goals.get("away")

    if home_id == equipo_id:
        return int(away_goals or 0)
    if away_id == equipo_id:
        return int(home_goals or 0)
    return 0

# ──────────────────────────────────────────
#  MOTOR DE PUNTUACIÓN
# ──────────────────────────────────────────
def calcular_puntos_jugador(
    jugador_id: int,
    fixture_id: int,
    fixture: Optional[dict[str, Any]] = None,
    stats_raw: Optional[list[dict[str, Any]]] = None,
) -> dict[str, Any]:
    """
    Calcula los puntos de un jugador en un partido específico.
    Devuelve: {"total": int, "desglose": dict}
    """
    stats_raw = stats_raw if stats_raw is not None else obtener_stats_jugador(fixture_id)
    stats_jugador, posicion, equipo_id = buscar_jugador_en_stats(jugador_id, stats_raw)

    if not stats_jugador:
        return {"total": 0, "desglose": {"no_jugo": 0}}

    desglose: dict[str, int] = {}
    total = 0

    minutos = stats_jugador.get("games", {}).get("minutes") or 0
    if minutos >= 60:
        desglose["titular"] = PUNTOS["titular"]
        total += PUNTOS["titular"]
    elif minutos > 0:
        desglose["suplente"] = PUNTOS["entrada_como_suplente"]
        total += PUNTOS["entrada_como_suplente"]
    else:
        return {"total": 0, "desglose": {"no_jugo": 0}}

    goles = stats_jugador.get("goals", {}).get("total") or 0
    if goles > 0:
        clave = {
            "G": "gol_portero",
            "D": "gol_defensa",
            "M": "gol_mediocampista",
            "F": "gol_delantero",
        }.get(posicion, "gol_jugador_campo")
        pts = PUNTOS[clave] * goles
        desglose[f"goles({goles})"] = pts
        total += pts

    asistencias = stats_jugador.get("goals", {}).get("assists") or 0
    if asistencias > 0:
        pts = PUNTOS["asistencia"] * asistencias
        desglose[f"asistencias({asistencias})"] = pts
        total += pts

    amarillas = stats_jugador.get("cards", {}).get("yellow") or 0
    rojas = stats_jugador.get("cards", {}).get("red") or 0
    if amarillas >= 2:
        desglose["doble_amarilla"] = PUNTOS["doble_amarilla"]
        total += PUNTOS["doble_amarilla"]
    elif amarillas == 1:
        desglose["amarilla"] = PUNTOS["tarjeta_amarilla"]
        total += PUNTOS["tarjeta_amarilla"]

    if rojas > 0:
        desglose["roja"] = PUNTOS["tarjeta_roja"]
        total += PUNTOS["tarjeta_roja"]

    penalty = stats_jugador.get("penalty", {}) or {}
    penaltis_fallados = penalty.get("missed") or 0
    if penaltis_fallados > 0:
        pts = PUNTOS["penalti_fallado"] * penaltis_fallados
        desglose[f"penaltis_fallados({penaltis_fallados})"] = pts
        total += pts

    goles_propia = stats_jugador.get("goals", {}).get("owngoals") or 0
    if goles_propia > 0:
        pts = PUNTOS["gol_en_propia"] * goles_propia
        desglose[f"propias({goles_propia})"] = pts
        total += pts

    if posicion == "G":
        goles_recibidos = stats_jugador.get("goals", {}).get("conceded")
        if goles_recibidos is None and fixture and equipo_id:
            goles_recibidos = equipo_recibio_goles(equipo_id, fixture)
        goles_recibidos = goles_recibidos or 0

        if goles_recibidos == 0 and minutos >= 60:
            desglose["clean_sheet_portero"] = PUNTOS["portero_sin_goles_recibidos"]
            total += PUNTOS["portero_sin_goles_recibidos"]
        elif goles_recibidos > 0:
            pts = PUNTOS["portero_gol_recibido"] * goles_recibidos
            desglose[f"goles_recibidos({goles_recibidos})"] = pts
            total += pts

        penaltis_parados = penalty.get("saved") or 0
        if penaltis_parados > 0:
            pts = PUNTOS["portero_penalti_parado"] * penaltis_parados
            desglose[f"penaltis_parados({penaltis_parados})"] = pts
            total += pts

    if posicion == "D" and fixture and equipo_id:
        goles_recibidos = equipo_recibio_goles(equipo_id, fixture)
        if goles_recibidos == 0 and minutos >= 60:
            desglose["clean_sheet_defensa"] = PUNTOS["defensa_sin_goles_recibidos"]
            total += PUNTOS["defensa_sin_goles_recibidos"]

    return {"total": total, "desglose": desglose}

# ──────────────────────────────────────────
#  BASE DE DATOS SQLITE
# ──────────────────────────────────────────
def conectar() -> sqlite3.Connection:
    con = sqlite3.connect(DB_FILE)
    con.execute("PRAGMA foreign_keys = ON")
    return con


def init_db() -> None:
    con = conectar()
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

        CREATE TABLE IF NOT EXISTS alineaciones (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            equipo_id        INTEGER REFERENCES equipos(id),
            jugador_id       INTEGER NOT NULL,
            jornada          INTEGER NOT NULL,
            es_titular       INTEGER DEFAULT 1,
            orden_suplente   INTEGER DEFAULT 99,
            guardado         TEXT DEFAULT (datetime('now')),
            UNIQUE(equipo_id, jugador_id, jornada)
        );
    """)
    con.commit()
    con.close()
    print("✅ Base de datos inicializada")


def crear_usuario(nombre: str) -> int:
    con = conectar()
    cur = con.cursor()
    cur.execute("INSERT OR IGNORE INTO usuarios (nombre) VALUES (?)", (nombre,))
    con.commit()
    cur.execute("SELECT id FROM usuarios WHERE nombre=?", (nombre,))
    uid = cur.fetchone()[0]
    con.close()
    print(f"👤 Usuario '{nombre}' (id={uid})")
    return uid


def crear_equipo(usuario_id: int, nombre_equipo: str) -> int:
    con = conectar()
    cur = con.cursor()
    cur.execute("INSERT INTO equipos (usuario_id, nombre) VALUES (?, ?)", (usuario_id, nombre_equipo))
    con.commit()
    eid = cur.lastrowid
    con.close()
    print(f"🏟️ Equipo '{nombre_equipo}' creado (id={eid})")
    return eid


def añadir_jugador(
    equipo_id: int,
    jugador_id: int,
    nombre: str,
    posicion: str,
    precio: float = 0.0,
    capitan: bool = False,
) -> None:
    if posicion not in {"G", "D", "M", "F"}:
        raise ValueError("La posición debe ser G, D, M o F")

    con = conectar()
    cur = con.cursor()

    cur.execute("SELECT presupuesto FROM equipos WHERE id=?", (equipo_id,))
    row = cur.fetchone()
    if not row:
        con.close()
        raise ValueError(f"No existe el equipo {equipo_id}")

    presupuesto = row[0]
    cur.execute(
        "SELECT precio FROM jugadores_equipo WHERE equipo_id=? AND jugador_id=?",
        (equipo_id, jugador_id),
    )
    existente = cur.fetchone()
    precio_anterior = existente[0] if existente else 0.0
    nuevo_presupuesto = presupuesto + precio_anterior - precio

    if nuevo_presupuesto < 0:
        con.close()
        raise ValueError("Presupuesto insuficiente")

    if capitan:
        cur.execute("UPDATE jugadores_equipo SET es_capitan=0 WHERE equipo_id=?", (equipo_id,))

    cur.execute("""
        INSERT OR REPLACE INTO jugadores_equipo
        (equipo_id, jugador_id, nombre, posicion, precio, es_capitan)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (equipo_id, jugador_id, nombre, posicion, precio, int(capitan)))

    cur.execute("UPDATE equipos SET presupuesto=? WHERE id=?", (nuevo_presupuesto, equipo_id))
    con.commit()
    con.close()

    cap_str = " ©" if capitan else ""
    print(f"➕ {nombre} ({posicion}){cap_str} añadido al equipo {equipo_id}")


def get_equipos() -> list[tuple[Any, ...]]:
    con = conectar()
    cur = con.cursor()
    cur.execute("SELECT id, usuario_id, nombre, presupuesto FROM equipos")
    rows = cur.fetchall()
    con.close()
    return rows


def get_jugadores_equipo(equipo_id: int) -> list[tuple[Any, ...]]:
    con = conectar()
    cur = con.cursor()
    cur.execute("""
        SELECT jugador_id, nombre, posicion, precio, es_capitan
        FROM jugadores_equipo
        WHERE equipo_id=?
        ORDER BY CASE posicion WHEN 'G' THEN 1 WHEN 'D' THEN 2 WHEN 'M' THEN 3 WHEN 'F' THEN 4 ELSE 5 END
    """, (equipo_id,))
    rows = cur.fetchall()
    con.close()
    return rows


def guardar_puntos(
    equipo_id: int,
    jugador_id: int,
    fixture_id: int,
    jornada: int,
    puntos: float,
    desglose: str,
) -> None:
    con = conectar()
    cur = con.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO puntos_historico
        (equipo_id, jugador_id, fixture_id, jornada, puntos, desglose)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (equipo_id, jugador_id, fixture_id, jornada, puntos, desglose))
    con.commit()
    con.close()


def guardar_alineacion(
    equipo_id: int,
    jornada: int,
    titulares: list[int],
    suplentes: Optional[list[int]] = None,
) -> None:
    """Guarda alineación básica para una jornada."""
    suplentes = suplentes or []
    con = conectar()
    cur = con.cursor()
    cur.execute("DELETE FROM alineaciones WHERE equipo_id=? AND jornada=?", (equipo_id, jornada))

    ahora = datetime.utcnow().isoformat()
    for jugador_id in titulares:
        cur.execute("""
            INSERT INTO alineaciones
            (equipo_id, jugador_id, jornada, es_titular, orden_suplente, guardado)
            VALUES (?, ?, ?, 1, 99, ?)
        """, (equipo_id, jugador_id, jornada, ahora))

    for orden, jugador_id in enumerate(suplentes, start=1):
        cur.execute("""
            INSERT INTO alineaciones
            (equipo_id, jugador_id, jornada, es_titular, orden_suplente, guardado)
            VALUES (?, ?, ?, 0, ?, ?)
        """, (equipo_id, jugador_id, jornada, orden, ahora))

    con.commit()
    con.close()


def get_alineacion(equipo_id: int, jornada: int) -> tuple[set[int], list[int]]:
    con = conectar()
    cur = con.cursor()
    cur.execute("""
        SELECT jugador_id, es_titular, orden_suplente
        FROM alineaciones
        WHERE equipo_id=? AND jornada=?
        ORDER BY es_titular DESC, orden_suplente ASC
    """, (equipo_id, jornada))
    rows = cur.fetchall()
    con.close()

    titulares = {jugador_id for jugador_id, es_titular, _ in rows if es_titular}
    suplentes = [jugador_id for jugador_id, es_titular, _ in rows if not es_titular]
    return titulares, suplentes

# ──────────────────────────────────────────
#  VISTAS
# ──────────────────────────────────────────
def ver_equipo(equipo_id: int) -> None:
    con = conectar()
    cur = con.cursor()
    cur.execute("""
        SELECT j.nombre, j.posicion, j.precio, j.es_capitan,
               COALESCE(SUM(p.puntos), 0) as total_pts
        FROM jugadores_equipo j
        LEFT JOIN puntos_historico p
            ON p.equipo_id = j.equipo_id AND p.jugador_id = j.jugador_id
        WHERE j.equipo_id = ?
        GROUP BY j.jugador_id, j.nombre, j.posicion, j.precio, j.es_capitan
        ORDER BY CASE j.posicion WHEN 'G' THEN 1 WHEN 'D' THEN 2 WHEN 'M' THEN 3 WHEN 'F' THEN 4 ELSE 5 END
    """, (equipo_id,))
    jugadores = cur.fetchall()
    cur.execute("SELECT nombre, presupuesto FROM equipos WHERE id=?", (equipo_id,))
    equipo = cur.fetchone()
    con.close()

    if not equipo:
        print(f"No existe el equipo {equipo_id}")
        return

    print(f"\n{'=' * 50}")
    print(f"  🏟️ {equipo[0]}   💰 Presupuesto restante: ${equipo[1]:.1f}M")
    print(f"{'=' * 50}")

    pos_icons = {"G": "🧤", "D": "🛡️", "M": "⚙️", "F": "⚡"}
    total_equipo = 0
    for nombre, pos, precio, capitan, pts in jugadores:
        cap = "©" if capitan else " "
        icon = pos_icons.get(pos, "⚽")
        print(f"  {icon} {cap} {nombre:<25} {pts:>5.0f} pts  (${precio}M)")
        total_equipo += pts

    print(f"{'=' * 50}")
    print(f"  📊 TOTAL: {total_equipo:.0f} puntos\n")


def clasificacion() -> None:
    con = conectar()
    cur = con.cursor()
    cur.execute("""
        SELECT u.nombre, e.nombre, COALESCE(SUM(p.puntos), 0) as total
        FROM equipos e
        JOIN usuarios u ON u.id = e.usuario_id
        LEFT JOIN puntos_historico p ON p.equipo_id = e.id
        GROUP BY e.id, u.nombre, e.nombre
        ORDER BY total DESC
    """)
    rows = cur.fetchall()
    con.close()

    print(f"\n{'=' * 45}")
    print("  🏆 CLASIFICACIÓN FANTASY MUNDIAL")
    print(f"{'=' * 45}")
    for i, (usuario, equipo, pts) in enumerate(rows, 1):
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}.")
        print(f"  {medal} {usuario:<15} ({equipo:<20}) {pts:>6.0f} pts")
    print(f"{'=' * 45}\n")

# ──────────────────────────────────────────
#  ACTUALIZACIÓN DE PUNTOS
# ──────────────────────────────────────────
def actualizar_puntos_jornada(jornada: int) -> None:
    print(f"\n🔄 Actualizando puntos — Jornada {jornada}")
    partidos = obtener_partidos_jornada(jornada)
    if not partidos:
        print("⚠️ No se encontraron partidos. Revisa API key, season, league y round.")
        return

    equipos = get_equipos()
    if not equipos:
        print("⚠️ No hay equipos creados.")
        return

    for partido in partidos:
        fixture_id = partido.get("fixture", {}).get("id")
        estado = partido.get("fixture", {}).get("status", {}).get("short")
        if not fixture_id:
            continue

        if estado not in {"FT", "AET", "PEN"}:
            print(f"  ⏳ Partido {fixture_id} aún no terminado ({estado}), saltando…")
            continue

        print(f"  ⚽ Procesando fixture {fixture_id}…")
        stats_raw = obtener_stats_jugador(fixture_id)

        for equipo_id, *_ in equipos:
            jugadores = get_jugadores_equipo(equipo_id)
            capitan_id = next((j[0] for j in jugadores if j[4]), None)

            titulares, suplentes = get_alineacion(equipo_id, jornada)
            usar_alineacion = bool(titulares)

            if usar_alineacion:
                jugadores_a_puntuar: list[tuple[int, dict[str, Any]]] = []
                jugadores_dict = {j[0]: j for j in jugadores}

                for titular_id in titulares:
                    if titular_id not in jugadores_dict:
                        continue
                    resultado = calcular_puntos_jugador(titular_id, fixture_id, partido, stats_raw)

                    if "no_jugo" in resultado["desglose"]:
                        print(f"    ↩️ Titular {titular_id} no jugó, buscando suplente...")
                        suplente_encontrado = False
                        for suplente_id in list(suplentes):
                            sup_resultado = calcular_puntos_jugador(suplente_id, fixture_id, partido, stats_raw)
                            if "no_jugo" not in sup_resultado["desglose"]:
                                jugadores_a_puntuar.append((suplente_id, sup_resultado))
                                suplentes.remove(suplente_id)
                                suplente_encontrado = True
                                break
                        if not suplente_encontrado:
                            jugadores_a_puntuar.append((titular_id, resultado))
                    else:
                        jugadores_a_puntuar.append((titular_id, resultado))
            else:
                jugadores_a_puntuar = [
                    (j[0], calcular_puntos_jugador(j[0], fixture_id, partido, stats_raw))
                    for j in jugadores
                ]

            for jugador_id, resultado in jugadores_a_puntuar:
                pts = resultado["total"]
                if jugador_id == capitan_id:
                    pts *= 2
                    resultado["desglose"]["capitan_x2"] = pts

                guardar_puntos(
                    equipo_id,
                    jugador_id,
                    fixture_id,
                    jornada,
                    pts,
                    json.dumps(resultado["desglose"], ensure_ascii=False),
                )

    print(f"✅ Jornada {jornada} actualizada\n")

# ──────────────────────────────────────────
#  DEMO SIN API
# ──────────────────────────────────────────
def demo_sin_api() -> None:
    print("\n🎮 Modo DEMO activado\n")
    init_db()

    uid1 = crear_usuario("Mikel")
    uid2 = crear_usuario("Amaia")
    e1 = crear_equipo(uid1, "Ikurriña FC")
    e2 = crear_equipo(uid2, "Txuri-Urdin Stars")

    añadir_jugador(e1, 278, "Mbappé", "F", 12.0, capitan=True)
    añadir_jugador(e1, 521, "Bellingham", "M", 10.5)
    añadir_jugador(e1, 1163, "Vinicius", "F", 9.0)
    añadir_jugador(e1, 303, "Rüdiger", "D", 6.5)
    añadir_jugador(e1, 794, "Oblak", "G", 5.0)

    añadir_jugador(e2, 306, "Pedri", "M", 10.0, capitan=True)
    añadir_jugador(e2, 2295, "Lewandowski", "F", 9.5)
    añadir_jugador(e2, 284, "Theo H.", "D", 7.0)
    añadir_jugador(e2, 889, "Salah", "F", 11.0)
    añadir_jugador(e2, 50011, "Courtois", "G", 5.5)

    guardar_alineacion(e1, 1, titulares=[278, 521, 1163, 303, 794])
    guardar_alineacion(e2, 1, titulares=[306, 2295, 284, 889, 50011])

    datos_simulados = [
        (e1, 278, 999001, 1, 14),
        (e1, 521, 999001, 1, 5),
        (e1, 1163, 999001, 1, 8),
        (e1, 303, 999001, 1, 6),
        (e1, 794, 999001, 1, 8),
        (e2, 306, 999002, 1, 10),
        (e2, 2295, 999002, 1, 11),
        (e2, 284, 999002, 1, 2),
        (e2, 889, 999002, 1, 9),
        (e2, 50011, 999002, 1, 8),
    ]
    for equipo_id, jug_id, fix_id, jornada, pts in datos_simulados:
        guardar_puntos(equipo_id, jug_id, fix_id, jornada, pts, '{"simulado": true}')

    ver_equipo(e1)
    ver_equipo(e2)
    clasificacion()

# ──────────────────────────────────────────
#  ENTRADA CLI
# ──────────────────────────────────────────
def main() -> None:
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
  python fantasy_mundial_corregido.py demo
  python fantasy_mundial_corregido.py jornada 1
  python fantasy_mundial_corregido.py clasificacion

Variable de entorno:
  export API_FOOTBALL_KEY=tu_clave
        """)


if __name__ == "__main__":
    main()
