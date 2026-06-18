# 📖 Manual del Desarrollador — Fantasy Mundial 2026

> Escrito para alguien que está aprendiendo Python. Lenguaje sencillo, sin tecnicismos.

---

## Índice
1. [¿Qué es esta app?](#qué-es)
2. [Archivos del proyecto](#archivos)
3. [Tecnologías usadas](#tecnologías)
4. [Base de datos Supabase](#base-de-datos)
5. [APIs externas](#apis)
6. [Cómo ejecutar en local](#local)
7. [Cómo subir cambios](#subir-cambios)
8. [Cómo funciona por dentro](#flujo)
9. [Tareas de mantenimiento](#mantenimiento)
10. [Solución de errores comunes](#errores)

---

## 1. ¿Qué es esta app?

Un **fantasy de fútbol** para el Mundial 2026 entre Nayade, Mikel y Julen. Cada uno tiene 25 jugadores fijos, elige su once titular antes de cada jornada y los jugadores puntúan según lo que hacen en los partidos reales.

**¿Cómo está montada?**
- La interfaz web está hecha con **Python + Streamlit**
- Los datos se guardan en **Supabase** (una base de datos en la nube)
- Los puntos se calculan automáticamente con datos de **API-Football**
- Todo está publicado en **Streamlit Cloud** (gratis)
- Los puntos se actualizan solos cada noche gracias a **GitHub Actions**

---

## 2. Archivos del proyecto

```
📁 Python/
│
├── app.py                    ← La app web (todas las páginas)
├── fantasy.py                ← Calcula los puntos de cada jugador
├── database.py               ← Todo lo que se guarda/lee de Supabase
├── alineacion.py             ← Página del campo visual con la alineación
├── historial.py              ← Página de historial de jornadas
├── como_funciona.py          ← Página de reglas y puntuación
├── auto_actualizar.py        ← Se ejecuta cada noche automáticamente
├── actualizar_estados.py     ← Actualiza lesiones de jugadores
├── telegram_notificaciones.py← Envía mensajes por Telegram
│
├── cargar_equipos.py         ← Solo se usó una vez para cargar los 3 equipos
├── actualizar_fotos.py       ← Solo se usó una vez para cargar las fotos
├── buscar_jugador.py         ← Para buscar IDs de jugadores en la API
│
├── .env                      ← Contraseñas y claves (NO subir a GitHub)
├── .gitignore                ← Archivos que Git ignora
├── requirements.txt          ← Librerías Python necesarias
├── README.md                 ← Documentación básica
│
└── .github/
    └── workflows/
        └── actualizar_puntos.yml  ← Tarea automática de GitHub
```

---

## 3. Tecnologías usadas

| Tecnología | Para qué sirve | Coste |
|---|---|---|
| **Python** | El lenguaje de programación | Gratis |
| **Streamlit** | Convierte código Python en una web | Gratis |
| **Supabase** | Base de datos en la nube | Gratis |
| **API-Football** | Datos del Mundial en tiempo real | ~$19/mes (Plan Pro) |
| **TheSportsDB** | Fotos de los jugadores | Gratis |
| **Telegram Bot** | Notificaciones automáticas | Gratis |
| **GitHub Actions** | Ejecuta scripts automáticamente cada noche | Gratis |
| **Streamlit Cloud** | Publica la app en internet | Gratis |

---

## 4. Base de datos Supabase

La base de datos tiene estas tablas:

### `usuarios`
Almacena los 3 participantes.
```
id | nombre
1  | Nayade
2  | Mikel
3  | Julen
```

### `equipos`
El equipo de cada participante con su presupuesto restante.
```
id | usuario_id | nombre         | presupuesto
1  | 1          | Equipo Nayade  | 57.0
```

### `jugadores_equipo`
Los 25 jugadores de cada equipo con su foto y si es capitán.
```
equipo_id | jugador_id | nombre    | posicion | precio | es_capitan | foto_url
1         | 570        | Vinicius  | F        | 10.0   | false      | https://...
```

### `alineaciones`
El once titular y suplentes guardados antes de cada jornada.
```
equipo_id | jugador_id | jornada | es_titular | orden_suplente
1         | 570        | 1       | true       | null
1         | 288        | 1       | false      | 1    ← primer suplente
```

### `puntos_historico`
Los puntos que ha ganado cada jugador en cada partido.
```
equipo_id | jugador_id | fixture_id | jornada | puntos | desglose
1         | 570        | 12345      | 1       | 8.0    | {"gol": 6, "titular": 2}
```

### `jornadas_info`
Los deadlines de cada jornada (15 min antes del primer partido).
```
jornada | deadline              | descripcion
1       | 2026-06-11 18:45:00  | Fase de grupos - Jornada 1
```

### `estado_jugadores`
El estado de cada jugador (disponible o lesionado).
```
jugador_id | nombre   | estado      | motivo
570        | Vinicius | disponible  |
288        | Neymar   | lesionado   | Muscular
```

### Acceder a Supabase
→ https://supabase.com/dashboard/project/xoxhapglilzvlyobknzc

- **Ver datos**: Table Editor en el menú izquierdo
- **Ejecutar SQL**: SQL Editor en el menú izquierdo

---

## 5. APIs externas

### API-Football ($19/mes — Plan Pro)
Proporciona todos los datos del Mundial en tiempo real.

- **Dashboard**: https://dashboard.api-football.com
- **Variable**: `API_FOOTBALL_KEY` en el `.env`
- **¿Qué usamos?**
  - `GET /fixtures` → Partidos del Mundial
  - `GET /fixtures/players` → Stats de jugadores en un partido
  - `GET /fixtures/events` → Goles, tarjetas, sustituciones
  - `GET /injuries` → Jugadores lesionados
  - `GET /players/profiles` → Buscar jugadores por nombre

### TheSportsDB (Gratis)
Fotos de los jugadores.
- **Sin API key** — funciona sin registro
- Solo se usó en `actualizar_fotos.py` (ya no se necesita)

### Telegram Bot (Gratis)
Envía mensajes automáticos a Nayade y Mikel.
- **Token**: `TELEGRAM_TOKEN` en el `.env`
- **Chat IDs**: `TELEGRAM_CHAT_NAYADE` y `TELEGRAM_CHAT_MIKEL`
- **Bot**: @FantasyMundial2026Bot

---

## 6. Cómo ejecutar en local

```cmd
REM 1. Ir a la carpeta del proyecto
cd "C:\Users\Administracion1\...\Python"

REM 2. Asegurarse de tener el .env con todas las keys:
REM    API_FOOTBALL_KEY=...
REM    SUPABASE_URL=https://xoxhapglilzvlyobknzc.supabase.co
REM    SUPABASE_KEY=...
REM    TELEGRAM_TOKEN=...
REM    TELEGRAM_CHAT_NAYADE=...
REM    TELEGRAM_CHAT_MIKEL=...

REM 3. Lanzar la app
streamlit run app.py

REM La app se abre en http://localhost:8501
```

---

## 7. Cómo subir cambios

Cada vez que modificas un archivo y quieres que se actualice en la web:

```cmd
REM 1. Añadir los archivos modificados
git add nombre_del_archivo.py

REM 2. Describir qué has cambiado
git commit -m "Descripción del cambio"

REM 3. Subir a GitHub (la web se actualiza sola en ~2 minutos)
git push
```

**Ejemplo real:**
```cmd
git add app.py historial.py
git commit -m "Mejorar página de historial"
git push
```

> ⚠️ Si el push falla con "rejected", ejecuta primero `git pull --rebase` y luego `git push`.

---

## 8. Cómo funciona por dentro

### Flujo de una jornada

```
Antes del partido (deadline 20:45h)
    → Cada uno guarda su alineación en la app
    → Se guarda en Supabase (tabla alineaciones)

Durante el partido
    → Nada automático (la API no tiene webhooks gratis)

Después del último partido (01:00h hora española)
    → GitHub Actions ejecuta auto_actualizar.py
    → Se consultan los fixtures terminados del día
    → Para cada partido → se calculan puntos por jugador
    → Solo puntúan los 11 titulares de la alineación guardada
    → Si un titular no jugó → entra el suplente 1, luego el 2...
    → El capitán dobla sus puntos
    → Los puntos se guardan en Supabase (tabla puntos_historico)
    → Se envía la clasificación por Telegram a Nayade y Mikel
```

### Sistema de puntos

| Acción | Puntos |
|---|---|
| Jugar ≥ 60 min | +2 |
| Jugar < 60 min | +1 |
| Gol (delantero) | +5 |
| Gol (centrocampista) | +6 |
| Gol (defensa) | +8 |
| Gol (portero) | +10 |
| Asistencia | +3 |
| Clean sheet portero (90 min) | +6 |
| Clean sheet defensa (90 min) | +4 |
| Penalti parado (portero) | +5 |
| Gol recibido (portero) | -1 |
| Tarjeta amarilla | -1 |
| Tarjeta roja | -3 |
| Penalti fallado | -2 |
| Gol en propia | -2 |
| **Capitán** | **×2 todos los puntos** |

> Para cambiar estos valores edita el diccionario `PUNTOS` al principio de `fantasy.py`.

---

## 9. Tareas de mantenimiento

### Actualizar puntos manualmente (si el automático falla)
```cmd
python -c "from dotenv import load_dotenv; load_dotenv(); from fantasy import actualizar_puntos_jornada; actualizar_puntos_jornada(1)"
```

### Enviar clasificación por Telegram manualmente
```cmd
python telegram_notificaciones.py clasificacion 1
```

### Probar que Telegram funciona
```cmd
python telegram_notificaciones.py test
```

### Actualizar estados de lesiones manualmente
```cmd
python actualizar_estados.py
```

### Cambiar el deadline de una jornada
En Supabase → SQL Editor:
```sql
UPDATE jornadas_info 
SET deadline = '2026-06-18 18:45:00+00' 
WHERE jornada = 2;
```

### Corregir la foto de un jugador
```cmd
python -c "from dotenv import load_dotenv; load_dotenv(); from database import get_db; db=get_db(); db.table('jugadores_equipo').update({'foto_url':'URL_NUEVA'}).eq('jugador_id', ID_JUGADOR).execute(); print('OK')"
```

### Ver puntos de un equipo en Supabase
En Supabase → SQL Editor:
```sql
SELECT je.nombre, SUM(ph.puntos) as total
FROM jugadores_equipo je
LEFT JOIN puntos_historico ph ON ph.jugador_id = je.jugador_id
WHERE je.equipo_id = 1
GROUP BY je.nombre
ORDER BY total DESC;
```

### Añadir el chat ID de Julen a Telegram
Cuando Julen se una al bot:
1. Añade en `.env`: `TELEGRAM_CHAT_JULEN=su_chat_id`
2. Añade en GitHub Secrets: `TELEGRAM_CHAT_JULEN`
3. Añade en Streamlit Cloud Secrets: `TELEGRAM_CHAT_JULEN = "su_id"`

---

## 10. Solución de errores comunes

### La app no carga / error en Streamlit Cloud
1. Ve a https://share.streamlit.io
2. Busca tu app → clic en `⋮` → "View logs"
3. Lee el error

### "No module named X"
```cmd
pip install nombre_modulo
```
Luego añade el módulo a `requirements.txt`, guarda y sube con git.

### La API no devuelve datos
```cmd
python -c "from dotenv import load_dotenv; load_dotenv(); from fantasy import _api_get; print(_api_get('status',{}))"
```

### Los puntos no se actualizan solos
1. Ve a GitHub → Actions
2. Si hay ❌ → clic en el workflow → ver los logs del error
3. Puedes ejecutarlo manualmente con "Run workflow"

### Supabase no conecta
```cmd
python -c "from dotenv import load_dotenv; load_dotenv(); from database import get_usuarios; print(get_usuarios())"
```

### Telegram no envía mensajes
```cmd
python telegram_notificaciones.py test
```

### El push de git falla
```cmd
git pull --rebase
git push
```

---

## Variables del archivo .env

```
API_FOOTBALL_KEY=tu_key          → dashboard.api-football.com
SUPABASE_URL=https://xxx...      → supabase.com → proyecto → Settings → API
SUPABASE_KEY=sb_secret_xxx       → supabase.com → proyecto → Settings → API
TELEGRAM_TOKEN=xxx               → @BotFather en Telegram
TELEGRAM_CHAT_NAYADE=2030913174  → Chat ID de Nayade
TELEGRAM_CHAT_MIKEL=6624924166   → Chat ID de Mikel
```

> ⚠️ El `.env` NUNCA se sube a GitHub. Está protegido por `.gitignore`.
> En Streamlit Cloud se configuran en: Settings → Secrets
> En GitHub Actions se configuran en: Settings → Secrets → Actions

---

## URLs importantes

| Servicio | URL |
|---|---|
| **App en producción** | https://fantasy-mundial-2026.streamlit.app |
| **GitHub** | https://github.com/Nayade202/fantasy-mundial-2026 |
| **Supabase** | https://supabase.com/dashboard/project/xoxhapglilzvlyobknzc |
| **API-Football** | https://dashboard.api-football.com |
| **Streamlit Cloud** | https://share.streamlit.io |

---

*Manual actualizado el 11 de junio de 2026 · Fantasy Mundial 2026*
