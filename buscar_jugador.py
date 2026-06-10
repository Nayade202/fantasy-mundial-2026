"""
Buscar jugadores del Mundial 2026 por nombre
Uso: python buscar_jugador.py mbappe
"""
import sys
import json
import os
import urllib.request

API_KEY = os.getenv("API_FOOTBALL_KEY", "TU_API_KEY_AQUI")
BASE_URL = "https://v3.football.api-sports.io"


def buscar_jugador(nombre: str):
    url = f"{BASE_URL}/players?search={nombre}&league=1&season=2026"
    req = urllib.request.Request(url, headers={
        "x-apisports-key": API_KEY,
        "Accept": "application/json"
    })
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())

    jugadores = data.get("response", [])
    if not jugadores:
        print(f"❌ No se encontraron jugadores con '{nombre}'")
        return

    print(f"\n🔍 Resultados para '{nombre}':\n")
    print(f"  {'ID':<8} {'Nombre':<25} {'Pos':<5} {'Nac.':<20} {'Precio sugerido'}")
    print(f"  {'-'*70}")
    for item in jugadores[:10]:
        p = item["player"]
        stats = item.get("statistics", [{}])[0]
        pos = stats.get("games", {}).get("position", "?")
        pos_short = {"Goalkeeper":"G","Defender":"D","Midfielder":"M","Attacker":"F"}.get(pos, "?")
        print(f"  {p['id']:<8} {p['name']:<25} {pos_short:<5} {p.get('nationality','?'):<20}")


if __name__ == "__main__":
    nombre = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "mbappe"
    buscar_jugador(nombre)
