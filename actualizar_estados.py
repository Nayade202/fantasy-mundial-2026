"""
actualizar_estados.py — Actualiza el estado de lesiones de los jugadores
Se ejecuta diariamente via GitHub Actions
"""

import os, json, urllib.request, urllib.error
from datetime import datetime, timezone
from dotenv import load_dotenv
load_dotenv()

API_KEY  = os.getenv("API_FOOTBALL_KEY", "")
BASE_URL = "https://v3.football.api-sports.io"
LEAGUE_ID = 1
SEASON = 2026

def api_get(endpoint, params={}):
    query = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"{BASE_URL}/{endpoint}?{query}"
    req = urllib.request.Request(url, headers={"x-apisports-key": API_KEY})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"❌ Error API: {e}")
        return {}

if __name__ == "__main__":
    print(f"🏥 Actualizando estados de jugadores — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")

    from database import get_db

    db = get_db()

    # Obtener todos los jugadores del fantasy
    res = db.table("jugadores_equipo").select("jugador_id, nombre").execute()
    jugadores = {j["jugador_id"]: j["nombre"] for j in (res.data or [])}

    if not jugadores:
        print("⚠️  Sin jugadores en la BD")
        exit(0)

    # Consultar lesiones del Mundial 2026
    hoy = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    data = api_get("injuries", {"league": LEAGUE_ID, "season": SEASON})
    lesiones = data.get("response", [])

    # Primero marcar todos como disponibles
    for jug_id, nombre in jugadores.items():
        db.table("estado_jugadores").upsert({
            "jugador_id": jug_id,
            "nombre": nombre,
            "estado": "disponible",
            "motivo": "",
            "actualizado": hoy
        }).execute()

    # Luego marcar los lesionados
    lesionados = 0
    for l in lesiones:
        player = l.get("player", {})
        jug_id = player.get("id")
        if jug_id and jug_id in jugadores:
            motivo = l.get("reason", "Lesión")
            db.table("estado_jugadores").upsert({
                "jugador_id": jug_id,
                "nombre": jugadores[jug_id],
                "estado": "lesionado",
                "motivo": motivo,
                "actualizado": hoy
            }).execute()
            print(f"  🔴 {jugadores[jug_id]} — {motivo}")
            lesionados += 1

    print(f"\n✅ {len(jugadores)} jugadores actualizados | {lesionados} lesionados")
