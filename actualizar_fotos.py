"""
actualizar_fotos.py — Busca fotos de jugadores en TheSportsDB y las guarda en Supabase
Ejecutar UNA VEZ: python actualizar_fotos.py
"""

import urllib.request
import urllib.error
import json
import time
from dotenv import load_dotenv
load_dotenv()

from database import get_db

def limpiar_nombre(nombre: str) -> str:
    """Elimina acentos y caracteres especiales para la búsqueda."""
    import unicodedata
    nfkd = unicodedata.normalize('NFKD', nombre)
    return ''.join(c for c in nfkd if not unicodedata.combining(c))

def buscar_foto(nombre: str) -> str:
    """Busca la foto de un jugador en TheSportsDB."""
    nombre_limpio = limpiar_nombre(nombre).replace(" ", "%20")
    url = f"https://www.thesportsdb.com/api/v1/json/3/searchplayers.php?p={nombre_limpio}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        players = data.get("player", [])
        if players:
            foto = players[0].get("strThumb") or players[0].get("strCutout") or players[0].get("strRender")
            if foto:
                return foto
    except urllib.error.HTTPError as e:
        if e.code == 429:
            print(f"  ⏳ Límite alcanzado, esperando 10s...")
            time.sleep(10)
            try:
                with urllib.request.urlopen(req, timeout=10) as r:
                    data = json.loads(r.read())
                players = data.get("player", [])
                if players:
                    foto = players[0].get("strThumb") or players[0].get("strCutout")
                    if foto:
                        return foto
            except Exception:
                pass
        else:
            print(f"  ⚠️  Error buscando {nombre}: {e}")
    except Exception as e:
        print(f"  ⚠️  Error buscando {nombre}: {e}")
    return ""

if __name__ == "__main__":
    print("🖼️  Actualizando fotos de jugadores desde TheSportsDB...\n")

    db = get_db()
    res = db.table("jugadores_equipo").select("jugador_id, nombre, foto_url").execute()
    jugadores = res.data

    # Eliminar duplicados por jugador_id
    vistos = set()
    unicos = []
    for j in jugadores:
        if j["jugador_id"] not in vistos:
            vistos.add(j["jugador_id"])
            unicos.append(j)

    print(f"Total jugadores únicos: {len(unicos)}\n")

    encontrados = 0
    no_encontrados = []

    for j in unicos:
        nombre = j["nombre"]
        foto_actual = j.get("foto_url", "")

        if foto_actual:
            print(f"  ✅ {nombre} — ya tiene foto")
            encontrados += 1
            continue

        foto = buscar_foto(nombre)
        time.sleep(1.5)  # Respetar límite de la API

        if foto:
            db.table("jugadores_equipo").update({"foto_url": foto}).eq("jugador_id", j["jugador_id"]).execute()
            print(f"  ✅ {nombre}")
            encontrados += 1
        else:
            # Intentar con apellido solo
            apellido = nombre.split()[-1]
            foto = buscar_foto(apellido)
            time.sleep(0.5)
            if foto:
                db.table("jugadores_equipo").update({"foto_url": foto}).eq("jugador_id", j["jugador_id"]).execute()
                print(f"  ✅ {nombre} (encontrado por apellido)")
                encontrados += 1
            else:
                print(f"  ❌ {nombre} — sin foto")
                no_encontrados.append(nombre)

    print(f"\n{'='*50}")
    print(f"✅ {encontrados}/{len(unicos)} jugadores con foto")
    if no_encontrados:
        print(f"\n❌ Sin foto ({len(no_encontrados)}):")
        for n in no_encontrados:
            print(f"   - {n}")
