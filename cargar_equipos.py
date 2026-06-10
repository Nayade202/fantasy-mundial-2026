"""
Carga automática de los 3 equipos del Fantasy Mundial 2026
IDs verificados de api-football.com
Ejecutar UNA SOLA VEZ: python cargar_equipos.py
"""

import sqlite3
DB_FILE = "fantasy_mundial.db"

EQUIPOS = [
    {
        "usuario": "Nayade", "equipo": "Equipo Nayade",
        "jugadores": [
            # (id_api, nombre, posicion, precio)
            (246,    "Emiliano Martínez",   "G", 5.5),
            (280,    "Alisson Becker",       "G", 5.0),
            (622,    "Aymeric Laporte",      "D", 6.0),
            (259,    "Virgil van Dijk",      "D", 7.0),
            (747,    "Alphonso Davies",      "D", 6.5),
            (1118,   "Dayot Upamecano",      "D", 5.5),
            (263482, "Nuno Mendes",          "D", 6.0),
            (396623, "Pau Cubarsí",          "D", 5.0),
            (627,    "Nathan Aké",           "D", 5.0),
            (200054, "Gleison Bremer",       "D", 5.0),
            (1485,   "Nico Schlotterbeck",   "D", 5.0),
            (1158,   "Pedri",                "M", 9.0),
            (594,    "Jamal Musiala",        "M", 9.5),
            (1247,   "Mikel Oyarzabal",      "M", 7.0),
            (338361, "Aurélien Tchouaméni",  "M", 7.0),
            (541,    "Joshua Kimmich",       "M", 7.5),
            (364156, "Xavi Simons",          "M", 7.0),
            (284788, "Fabián Ruiz",          "M", 7.0),
            (762,    "Alexis Mac Allister",  "M", 7.5),
            (570,    "Vinícius Jr.",         "F", 10.0),
            (288,    "Neymar Jr.",           "F", 8.0),
            (995,    "Julián Álvarez",       "F", 8.5),
            (283,    "Ousmane Dembélé",      "F", 8.0),
            (284796, "Rafael Leão",          "F", 8.0),
            (874,    "Cristiano Ronaldo",    "F", 9.0),
            (365768, "Kvaratskhelia",        "F", 8.5),
        ]
    },
    {
        "usuario": "Mikel", "equipo": "Equipo Mikel",
        "jugadores": [
            (22221,  "Mike Maignan",         "G", 5.5),
            (629,    "Jordan Pickford",      "G", 4.5),
            (723836, "William Saliba",       "D", 6.5),
            (268,    "Rúben Dias",           "D", 7.0),
            (9,      "Achraf Hakimi",        "D", 7.5),
            (996,    "Marc Cucurella",       "D", 5.5),
            (218,    "Marquinhos",           "D", 6.5),
            (1082,   "João Cancelo",         "D", 6.0),
            (284517, "Gabriel Magalhães",    "D", 6.0),
            (284509, "Nahuel Molina",        "D", 5.5),
            (284965, "Lisandro Martínez",    "D", 6.5),
            (755,    "Jude Bellingham",      "M", 10.5),
            (284510, "Fede Valverde",        "M", 8.5),
            (284967, "Declan Rice",          "M", 8.0),
            (284966, "Enzo Fernández",       "M", 8.0),
            (284511, "Rodrigo De Paul",      "M", 7.0),
            (284512, "Brahim Díaz",          "M", 7.5),
            (284513, "Bruno Guimarães",      "M", 7.5),
            (521,    "Frenkie de Jong",      "M", 8.0),
            (154,    "Lionel Messi",         "F", 10.0),
            (1100,   "Erling Haaland",       "F", 11.0),
            (184,    "Harry Kane",           "F", 10.0),
            (284514, "Nico Williams",        "F", 8.5),
            (749,    "Lautaro Martínez",     "F", 9.0),
            (628,    "Marcus Rashford",      "F", 7.5),
        ]
    },
    {
        "usuario": "Julen", "equipo": "Equipo Julen",
        "jugadores": [
            (284515, "Unai Simón",           "G", 5.0),
            (284516, "Diogo Costa",          "G", 5.5),
            (47,     "Theo Hernández",       "D", 7.0),
            (284518, "Joško Gvardiol",       "D", 7.0),
            (626,    "John Stones",          "D", 6.5),
            (303,    "Antonio Rüdiger",      "D", 6.5),
            (284519, "Malo Gusto",           "D", 5.5),
            (284520, "Cristian Romero",      "D", 7.0),
            (284521, "Ibrahima Konaté",      "D", 6.5),
            (284522, "Jules Koundé",         "D", 6.5),
            (284523, "Ronald Araújo",        "D", 6.5),
            (284524, "Rodri",                "M", 9.5),
            (284525, "Florian Wirtz",        "M", 9.0),
            (284526, "Bruno Fernandes",      "M", 8.5),
            (284527, "Vitinha",              "M", 7.5),
            (284528, "Bernardo Silva",       "M", 8.5),
            (284529, "Martín Zubimendi",     "M", 7.5),
            (284530, "Granit Xhaka",         "M", 7.0),
            (184942, "Luka Modrić",          "M", 7.5),
            (278,    "Kylian Mbappé",        "F", 12.0),
            (284531, "Bukayo Saka",          "F", 9.0),
            (284532, "Raphinha",             "F", 8.5),
            (284533, "Lamine Yamal",         "F", 9.5),
            (284534, "Luis Díaz",            "F", 8.0),
            (284535, "Endrick",              "F", 7.5),
        ]
    }
]

# ── BD ─────────────────────────────────────
def init_db():
    con = sqlite3.connect(DB_FILE)
    con.executescript("""
        CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT UNIQUE NOT NULL);
        CREATE TABLE IF NOT EXISTS equipos (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario_id INTEGER, nombre TEXT NOT NULL, presupuesto REAL DEFAULT 100.0);
        CREATE TABLE IF NOT EXISTS jugadores_equipo (equipo_id INTEGER, jugador_id INTEGER, nombre TEXT, posicion TEXT, precio REAL DEFAULT 0.0, es_capitan INTEGER DEFAULT 0, PRIMARY KEY(equipo_id, jugador_id));
        CREATE TABLE IF NOT EXISTS puntos_historico (id INTEGER PRIMARY KEY AUTOINCREMENT, equipo_id INTEGER, jugador_id INTEGER, fixture_id INTEGER, jornada INTEGER, puntos REAL DEFAULT 0, desglose TEXT, calculado TEXT DEFAULT (datetime('now')), UNIQUE(equipo_id, jugador_id, fixture_id));
    """)
    con.commit()
    con.close()

def limpiar_db():
    con = sqlite3.connect(DB_FILE)
    con.executescript("DELETE FROM puntos_historico; DELETE FROM jugadores_equipo; DELETE FROM equipos; DELETE FROM usuarios;")
    con.commit()
    con.close()

def crear_usuario(nombre):
    con = sqlite3.connect(DB_FILE)
    con.execute("INSERT OR IGNORE INTO usuarios (nombre) VALUES (?)", (nombre,))
    con.commit()
    uid = con.execute("SELECT id FROM usuarios WHERE nombre=?", (nombre,)).fetchone()[0]
    con.close()
    return uid

def crear_equipo(uid, nombre):
    con = sqlite3.connect(DB_FILE)
    cur = con.execute("INSERT INTO equipos (usuario_id, nombre) VALUES (?,?)", (uid, nombre))
    con.commit()
    eid = cur.lastrowid
    con.close()
    return eid

def añadir_jugador(eid, jid, nombre, pos, precio):
    con = sqlite3.connect(DB_FILE)
    con.execute("INSERT OR REPLACE INTO jugadores_equipo (equipo_id,jugador_id,nombre,posicion,precio,es_capitan) VALUES (?,?,?,?,?,0)",
                (eid, jid, nombre, pos, precio))
    con.execute("UPDATE equipos SET presupuesto=presupuesto-? WHERE id=?", (precio, eid))
    con.commit()
    con.close()

# ── MAIN ───────────────────────────────────
if __name__ == "__main__":
    print("🏆 Cargando equipos del Fantasy Mundial 2026...\n")
    init_db()

    con = sqlite3.connect(DB_FILE)
    n = con.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
    con.close()
    if n > 0:
        resp = input(f"Ya hay {n} usuarios en la BD. ¿Borrar todo y recargar? (s/n): ")
        if resp.lower() != "s":
            print("Cancelado.")
            exit()
        limpiar_db()
        print("🗑️  Datos anteriores borrados.\n")

    for datos in EQUIPOS:
        uid = crear_usuario(datos["usuario"])
        eid = crear_equipo(uid, datos["equipo"])
        print(f"\n👤 {datos['usuario']} — {datos['equipo']}")
        for jid, nombre, pos, precio in datos["jugadores"]:
            añadir_jugador(eid, jid, nombre, pos, precio)
            print(f"  ✅ {nombre} (ID: {jid})")

    con = sqlite3.connect(DB_FILE)
    total = con.execute("SELECT COUNT(*) FROM jugadores_equipo").fetchone()[0]
    con.close()

    print(f"\n{'='*50}")
    print(f"✅ {total} jugadores cargados correctamente")
    print("\n🚀 Lanza la app: streamlit run app.py")
    print("👑 Elige tu capitán desde 'Mi equipo' en la app")
