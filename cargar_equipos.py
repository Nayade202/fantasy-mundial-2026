"""
Carga automática de los 3 equipos del Fantasy Mundial 2026 en Supabase
IDs verificados de api-football.com
Ejecutar UNA SOLA VEZ: python cargar_equipos.py
"""

import sqlite3
from dotenv import load_dotenv
load_dotenv()
from database import crear_usuario, crear_equipo, añadir_jugador, get_db

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
            (541,    "Joshua Kimmich",       "M", 7.5),
            (1158,   "Pedri",                "M", 9.0),
            (594,    "Jamal Musiala",        "M", 9.5),
            (1247,   "Mikel Oyarzabal",      "M", 7.0),
            (338361, "Aurélien Tchouaméni",  "M", 7.0),
            (364156, "Xavi Simons",          "M", 7.0),
            (284788, "Fabián Ruiz",          "M", 7.0),
            (762,    "Alexis Mac Allister",  "M", 7.5),
            (570,    "Vinícius Jr.",         "F", 10.0),
            (288,    "Neymar Jr.",           "F", 8.0),
            (995,    "Julián Álvarez",       "F", 8.5),
            (283,    "Ousmane Dembélé",      "F", 8.0),
            (284796, "Rafael Leão",          "F", 8.0),
            (874,    "Cristiano Ronaldo",    "F", 9.0),
            (306263, "Michael Olise",        "F", 7.5),
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
            (284523, "Ronald Araújo",        "D", 6.5),
            (284524, "Rodri",                "M", 9.5),
            (284525, "Florian Wirtz",        "M", 9.0),
            (284526, "Bruno Fernandes",      "M", 8.5),
            (284527, "Vitinha",              "M", 7.5),
            (284528, "Bernardo Silva",       "M", 8.5),
            (284529, "Martín Zubimendi",     "M", 7.5),
            (350022, "Kouadio Koné",         "M", 6.5),
            (184942, "Luka Modrić",          "M", 7.5),
            (278,    "Kylian Mbappé",        "F", 12.0),
            (284531, "Bukayo Saka",          "F", 9.0),
            (284532, "Raphinha",             "F", 8.5),
            (284533, "Lamine Yamal",         "F", 9.5),
            (284534, "Luis Díaz",            "F", 8.0),
            (200295, "Take Kubo",            "F", 7.0),
            (284535, "Endrick",              "F", 7.5),
        ]
    }
]

def limpiar_db():
    db = get_db()
    db.table("puntos_historico").delete().neq("id", 0).execute()
    db.table("alineaciones").delete().neq("id", 0).execute()
    db.table("jugadores_equipo").delete().neq("equipo_id", 0).execute()
    db.table("equipos").delete().neq("id", 0).execute()
    db.table("usuarios").delete().neq("id", 0).execute()
    print("🗑️  Datos anteriores borrados.")

if __name__ == "__main__":
    print("🏆 Cargando equipos corregidos en Supabase...\n")

    resp = input("⚠️  Esto borrará TODOS los datos actuales. ¿Continuar? (s/n): ")
    if resp.lower() != "s":
        print("Cancelado.")
        exit()

    limpiar_db()

    for datos in EQUIPOS:
        uid = crear_usuario(datos["usuario"])
        eid = crear_equipo(uid, datos["equipo"])
        print(f"\n👤 {datos['usuario']} — {datos['equipo']}")
        for jid, nombre, pos, precio in datos["jugadores"]:
            añadir_jugador(eid, jid, nombre, pos, precio)
            print(f"  ✅ {nombre} (ID: {jid})")

    db = get_db()
    total = len(db.table("jugadores_equipo").select("jugador_id").execute().data or [])
    print(f"\n{'='*50}")
    print(f"✅ {total} jugadores cargados en Supabase")
    print("👑 Elige tu capitán desde 'Mi equipo' en la app")
    print("🖼️  Ejecuta: python actualizar_fotos.py")
