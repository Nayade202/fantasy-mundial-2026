# 🏆 Fantasy Mundial 2026 — Python

Fantasy de fútbol con puntos automáticos conectado a datos reales del Mundial 2026.

## Archivos

| Archivo | Qué hace |
|---|---|
| `fantasy.py` | Motor principal: puntos, BD, equipos |
| `buscar_jugador.py` | Busca IDs de jugadores por nombre |

## Instalación

```bash
# Solo usa librerías estándar de Python — no necesita pip install
python --version  # Requiere Python 3.10+
```

## Configuración (2 pasos)

### 1. Obtener API key gratuita
1. Regístrate en → https://dashboard.api-football.com/register
2. En el dashboard copia tu API key
3. Exporta la variable de entorno:

```bash
export API_FOOTBALL_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 2. Probar sin API key (modo demo)
```bash
python fantasy.py demo
```

---

## Uso

### Probar sin API key
```bash
python fantasy.py demo
```

### Buscar IDs de jugadores
```bash
export API_FOOTBALL_KEY=tu_clave
python buscar_jugador.py mbappe
python buscar_jugador.py pedri
python buscar_jugador.py lewandowski
```

### Crear usuarios y equipos en tu código
```python
from fantasy import init_db, crear_usuario, crear_equipo, añadir_jugador, ver_equipo

init_db()

uid = crear_usuario("Mikel")
equipo = crear_equipo(uid, "Ikurriña FC")

# ID obtenidos con buscar_jugador.py
añadir_jugador(equipo, 278,  "Mbappé",     "F", precio=12.0, capitan=True)
añadir_jugador(equipo, 521,  "Bellingham", "M", precio=10.5)
añadir_jugador(equipo, 794,  "Oblak",      "G", precio=5.0)

ver_equipo(equipo)
```

### Actualizar puntos tras una jornada
```bash
python fantasy.py jornada 1
python fantasy.py jornada 2
```

### Ver clasificación
```bash
python fantasy.py clasificacion
```

---

## Sistema de puntos

| Acción | Puntos |
|---|---|
| Jugar ≥ 60 min | +2 |
| Jugar < 60 min | +1 |
| Gol (delantero) | +5 |
| Gol (centrocampista) | +6 |
| Gol (defensa) | +8 |
| Gol (portero) | +10 |
| Asistencia | +3 |
| Clean sheet (portero) | +6 |
| Clean sheet (defensa) | +4 |
| Tarjeta amarilla | -1 |
| Tarjeta roja | -3 |
| Penalti fallado | -2 |
| Gol en propia | -2 |
| **Capitán** | **×2 todos los puntos** |

---

## Ampliar el proyecto

Ideas para cuando tengas esto funcionando:

- **Bot de Telegram** — notificaciones automáticas tras cada partido
- **API REST con FastAPI** — para que varios amigos gestionen su equipo desde el móvil
- **Interfaz web** — con Streamlit en pocas líneas
- **Transferencias** — ventana de fichajes entre jornadas
- **Ligas privadas** — con código de invitación

```bash
# Añadir Streamlit para interfaz web
pip install streamlit
```
