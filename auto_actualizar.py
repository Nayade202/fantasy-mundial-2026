"""
auto_actualizar.py — Se ejecuta automáticamente cada noche via GitHub Actions
Detecta qué jornada está activa y actualiza los puntos
"""

import os
import json
import urllib.request
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
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"❌ Error API: {e}")
        return {}


def obtener_jornadas_con_partidos_hoy():
    """Busca partidos terminados hoy en el Mundial."""
    hoy = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    data = api_get("fixtures", {
        "league": LEAGUE_ID,
        "season": SEASON,
        "date": hoy,
        "status": "FT"
    })
    partidos = data.get("response", [])
    if not partidos:
        print(f"ℹ️  No hay partidos terminados hoy ({hoy})")
        return []

    # Obtener jornadas únicas
    jornadas = set()
    for p in partidos:
        round_str = p.get("league", {}).get("round", "")
        if "Group Stage" in round_str:
            try:
                num = int(round_str.split("-")[-1].strip())
                jornadas.add(num)
            except:
                pass
        elif "Round of" in round_str or "Quarter" in round_str or "Semi" in round_str or "Final" in round_str:
            jornadas.add(round_str)

    print(f"📅 Partidos terminados hoy: {len(partidos)} | Jornadas: {jornadas}")
    return list(jornadas)


if __name__ == "__main__":
    print(f"🔄 Auto-actualización — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")

    if not API_KEY:
        print("❌ Sin API key")
        exit(1)

    # Importar aquí para que solo se ejecute si hay API key
    from fantasy import actualizar_puntos_jornada

    jornadas = obtener_jornadas_con_partidos_hoy()

    if not jornadas:
        print("✅ Nada que actualizar hoy")
        exit(0)

    for jornada in jornadas:
        if isinstance(jornada, int):
            print(f"\n⚽ Actualizando jornada {jornada}...")
            actualizar_puntos_jornada(jornada)
        else:
            print(f"\n⚽ Actualizando fase: {jornada}...")

    print("\n✅ Auto-actualización completada")

    # Enviar clasificación por Telegram
    try:
        from telegram_notificaciones import notificar_clasificacion_jornada
        for jornada in jornadas:
            if isinstance(jornada, int):
                notificar_clasificacion_jornada(jornada)
        print("📨 Notificaciones Telegram enviadas")
    except Exception as e:
        print(f"⚠️  Error Telegram: {e}")
