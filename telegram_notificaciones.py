"""
telegram_notificaciones.py — Envía notificaciones a los jugadores vía Telegram
"""

import os
import urllib.request
import urllib.parse
import json
from dotenv import load_dotenv
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")

# Chat IDs de cada jugador
CHAT_IDS = {
    "Nayade": os.getenv("TELEGRAM_CHAT_NAYADE", ""),
    "Mikel":  os.getenv("TELEGRAM_CHAT_MIKEL", ""),
    "Julen":  os.getenv("TELEGRAM_CHAT_JULEN", ""),
}

def enviar_mensaje(chat_id: str, mensaje: str):
    """Envía un mensaje de Telegram a un chat_id."""
    if not chat_id or not TELEGRAM_TOKEN:
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    datos = {
        "chat_id": chat_id,
        "text": mensaje,
        }
    data = urllib.parse.urlencode(datos).encode()
    req = urllib.request.Request(url, data=data)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read()).get("ok", False)
    except Exception as e:
        print(f"❌ Error Telegram: {e}")
        return False

def notificar_todos(mensaje: str):
    """Envía el mismo mensaje a todos los jugadores."""
    for nombre, chat_id in CHAT_IDS.items():
        if chat_id:
            ok = enviar_mensaje(chat_id, mensaje)
            print(f"  {'✅' if ok else '❌'} {nombre}")

def notificar_clasificacion_jornada(jornada: int):
    """Envía la clasificación tras una jornada."""
    from database import get_clasificacion, get_db

    clasificacion = get_clasificacion()
    db = get_db()

    # Puntos de esta jornada
    res = db.table("puntos_historico").select("equipo_id, puntos").eq("jornada", jornada).execute()
    pts_jornada = {}
    for r in res.data or []:
        eid = r["equipo_id"]
        pts_jornada[eid] = pts_jornada.get(eid, 0) + r["puntos"]

    medallas = ["🥇", "🥈", "🥉"]
    lineas = [f"*⚽ Fantasy Mundial 2026 — Jornada {jornada}*\n"]

    for i, (usuario, equipo, equipo_id, total) in enumerate(clasificacion):
        medal = medallas[i] if i < 3 else f"{i+1}."
        pts_esta = pts_jornada.get(equipo_id, 0)
        lineas.append(f"{medal} *{usuario}* — {total:.0f} pts (+{pts_esta:.0f} esta jornada)")

    mensaje = "\n".join(lineas)
    print(f"\n📨 Enviando clasificación jornada {jornada}...")
    notificar_todos(mensaje)

def notificar_gol(nombre_jugador: str, equipo_propietario: str, minuto: int = None):
    """Notifica a un usuario que su jugador ha marcado."""
    chat_id = CHAT_IDS.get(equipo_propietario, "")
    if not chat_id:
        return
    min_str = f" (min {minuto})" if minuto else ""
    mensaje = f"⚽ *¡GOL!* {nombre_jugador} ha marcado{min_str}\n+6 puntos para tu equipo 🎉"
    enviar_mensaje(chat_id, mensaje)

def notificar_deadline(jornada: int, minutos_restantes: int):
    """Avisa cuando queda poco para el deadline."""
    mensaje = f"⏰ *¡Atención!* Quedan {minutos_restantes} minutos para cerrar la alineación de la Jornada {jornada}.\n¡Guarda tu once antes de las 20:45! 🏃"
    print(f"\n📨 Enviando aviso deadline jornada {jornada}...")
    notificar_todos(mensaje)

def test_conexion():
    """Prueba que el bot funciona enviando un mensaje de test."""
    mensaje = "✅ *Fantasy Mundial 2026*\n¡Bot de notificaciones conectado correctamente! 🏆"
    print("🧪 Probando conexión...")
    notificar_todos(mensaje)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            test_conexion()
        elif sys.argv[1] == "clasificacion" and len(sys.argv) > 2:
            notificar_clasificacion_jornada(int(sys.argv[2]))
        elif sys.argv[1] == "deadline" and len(sys.argv) > 2:
            notificar_deadline(int(sys.argv[2]), 30)
    else:
        print("""
📨 Notificaciones Telegram — Fantasy Mundial 2026

Uso:
  python telegram_notificaciones.py test                → Prueba la conexión
  python telegram_notificaciones.py clasificacion 1     → Envía clasificación jornada 1
  python telegram_notificaciones.py deadline 1          → Aviso deadline jornada 1
        """)
