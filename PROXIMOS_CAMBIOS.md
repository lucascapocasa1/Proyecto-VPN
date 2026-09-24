# Proximos Cambios

Ideas y planes pendientes de implementacion.

---

## 1. Base de datos grande (volumen realista)

### Descripcion

Crear un dataset grande y realista para pruebas finales, con 20 equipos por division y 15 jugadores por equipo. Tambien un dataset mas chico para desarrollo/testing.

### Paises (por ahora)

- Argentina
- Uruguay
- (Brasil se puede agregar despues, misma logica)

### Estructura por pais

```
Liga
├── Temporada 1 (FINISHED)
│   ├── Primera Division (20 equipos)
│   └── Segunda Division (20 equipos)
└── Temporada 2 (ACTIVE, con fixtures)
    ├── Primera Division (20 equipos, armada por admin)
    └── Segunda Division (20 equipos)
```

### Zonas por division

| Division | Pos 1 | Pos 2-9 | Pos 19 | Pos 20 |
|----------|-------|---------|--------|--------|
| Primera | CAMPEON | NORMAL | PROMOCION | DESCENSO |
| Segunda | CAMPEON (asciende directo) | REDUCIDO | PROMOCION | DESCENSO |

### Formato de partidos

- **Liga**: round-robin simple, 19 partidos por equipo, cancha neutral (sin ida/vuelta)
- **Reducido Segunda**: 2vs9, 3vs8, 4vs7, 5vs6, semifinales, final (ida y vuelta en cada ronda)
- **Promocion**: Pos 19 Primera vs Campeon Reducido Segunda (ida y vuelta)
- Sin penales, todos los partidos se resuelven en tiempo regular

### Ascensos/descensos entre temporadas

- Manual por el admin (no automatico)
- La temporada 2 muestra los equipos ya posicionados por el admin

### Jugadores

- 15 por equipo (2 ARQ, 4 DEF, 5 MED, 4 DEL)
- Maximo 3 extranjeros por equipo
- Nacionalidades mezcladas (mayoria del pais local)
- Nicknames realistas (ej: lucas_gar10, diego_pro)
- Estadisticas realistas por posicion (goles pesados: DEL=10x, MED=5x, DEF=2x, ARQ=0.5x)

### Volumen final (2 paises, S1 FINISHED + S2 ACTIVE)

| Entidad | Argentina | Uruguay | Total |
|---------|-----------|---------|-------|
| Countries | 1 | 1 | 2 |
| Leagues | 1 | 1 | 2 |
| Seasons | 2 | 2 | 4 |
| Divisions | 4 | 4 | 8 |
| Clubs | 40 | 40 | 80 |
| ClubSeasons | 80 | 80 | 160 |
| Players | 600 | 600 | 1,200 |
| PlayerClubHistory | 1,200 | 1,200 | 2,400 |
| Matchdays | 38 | 38 | 76 |
| Matches (S1) | 380 | 380 | 760 |
| MatchPlayers | 11,400 | 11,400 | 22,800 |
| MatchEvents | ~14,850 | ~14,850 | ~29,700 |
| Standings | 40 | 40 | 80 |
| **Total** | | | **~34,354** |

Nota: desde la Fase 11, S2 esta ACTIVE con fixtures: +22 matchdays (11 por division) y +220 matches por pais (J1-J10 FINISHED, J11 SCHEDULED), mas ~160 Transfer backfilleados.

### Archivos creados/modificados

- `apps/players/models.py` — Campo `position` agregado (ARQ/DEF/MED/DEL)
- `apps/players/migrations/0002_player_position.py` — Migracion creada
- `apps/players/serializers.py` — position incluido en PlayerSerializer y PlayerDetailSerializer
- `apps/standings/management/commands/seed_data.py` — Reescrito (dataset completo, nicknames realistas, position-based stats)
- `apps/standings/management/commands/seed_dev.py` — Creado (dataset chico para dev)
- `frontend/src/types/index.ts` — position agregado a Player interface
- `frontend/src/components/ui/PlayerCard.tsx` — Badge de posicion

### Estado

✅ Implementado y verificado (147 tests pasando, E2E Playwright OK)

**S2 ahora está ACTIVE** (no UPCOMING): 11 matchdays por división (J1-J10 FINISHED, J11 SCHEDULED), con transiciones S1→S2 aplicadas y fixtures regenerados. Comandos idempotentes: `seed_data`, `seed_s2`, `fix_season_transitions`.

---

## 2. Mercado de pases

### Descripcion

Sistema de transferencias donde jugadores sin club aparecen automaticamente en el mercado. Los admin de club pueden enviar invitaciones. El admin general controla el periodo de fichajes.

### ✅ v1 — Implementado (registro manual del admin)

Lo que ya esta en producción:

- **Modelo `Transfer`** (`apps/players/models.py`): player, from_club_season, to_club_season, date, registered_by, created_at — migracion `players/0003_transfer`
- **API `/api/transfers/`**: CRUD (lectura publica, escritura ADMIN_LIGA+). `DELETE` revierte solo la ultima transferencia del jugador
- **160 transferencias backfilleadas** desde los movimientos directos S1→S2
- **Pagina `/transfers` (Mercado)**: alta/baja de transferencias, busqueda de jugadores, filtro por temporada, links a clubes origen/destino
- **Tests**: 10 transfer API tests (`TransferApiTest`)

### Pendiente (v2) — logica de mercado

#### Modelo Transfer (version propuesta original, aun no implementada)

```python
class Status(models.TextChoices):
    PENDING / ACCEPTED / REJECTED / EXPIRED / CANCELLED

offering_club = ForeignKey(ClubSeason)
season = ForeignKey(Season)
message = TextField(blank=True)
expires_at = DateTimeField()  # created_at + 24h
unique_together = ["player", "offering_club", "season"]
```

#### Modificar Season — ventana de pases

```python
transfer_window_open = BooleanField(default=False)
```

### Logica de negocio (v2)

- **Free agent**: jugador sin PlayerClubHistory con left_at=None en la temporada activa
- **Aceptacion**: al aceptar, se cancelan las demas invitaciones PENDING del jugador en esa temporada y se crea PlayerClubHistory
- **Expiracion**: invitaciones expiran a las 24h, vuelven al mercado
- **Multiples ofertas**: un jugador puede tener varias ofertas pendientes a la vez

### Endpoints (v2)

| Metodo | Endpoint | Descripcion | Permisos |
|--------|----------|-------------|----------|
| GET | `/api/transfer-market/` | Listar free agents con stats | Publico |
| POST | `/api/transfers/` | Enviar invitacion | ADMIN_CLUB |
| PUT | `/api/transfers/{id}/accept/` | Aceptar invitacion | PLAYER |
| PUT | `/api/transfers/{id}/reject/` | Rechazar invitacion | PLAYER |
| POST | `/api/seasons/{id}/open-transfer-window/` | Abrir ventana | ADMIN_LIGA |
| POST | `/api/seasons/{id}/close-transfer-window/` | Cerrar ventana | ADMIN_LIGA |

### Estado

✅ v1 implementado (registro manual + pagina Mercado)
📋 v2 aprobado — free agents, invitaciones, ventana de pases: implementar despues de Brasil

---

## 3. Brasil (futuro)

### Descripcion

Agregar Brasil como tercer pais con la misma logica (2 divisiones, 20 equipos cada una, playoffs, etc.)

### Estado

Pendiente — agregar cuando la base de datos de 2 paises funcione bien

---

## 4. Estadisticas detalladas por partido (rendimiento) — PLAN APROBADO

### Descripcion

Sistema para recolectar el rendimiento detallado de **cada jugador en cada partido** (18 campos numericos), inspirado en FIFASTATS (https://github.com/lucascapocasa1/FIFASTATS---Al-Yateh): el admin de division sube una captura por jugador de la pestaña "Rendimiento" de EA FC, el sistema extrae los datos por OCR, el admin verifica/corrige antes de guardar, y despues se muestran por jugador (historial partido a partido) y se agregan en tablas y graficos.

Esto es **ademas** de la Opcion A actual (resultados/alineaciones/eventos), que no cambia.

### Decisiones aprobadas

| Tema | Decision |
|------|----------|
| Modelo | Nuevo `MatchPerformance` (OneToOne a `MatchPlayer`), no toca Match/MatchPlayer/MatchEvent existentes |
| Campos | 18 numericos de FIFASTATS: rating, goles, asistencias, tiros, precision tiros, pases, precision pases, regates, exito regates, entradas, exito entradas, offsides, faltas, posesion ganada, posesion perdida, minutos, distancia km, sprint km (sin mvp_ig/part_ig; posicion vive en Player) |
| OCR | `pytesseract` + `Pillow` en el backend Django, port de `parser.js`/`ocr.js`/`imageProcessor.js` de FIFASTATS |
| Deploy | **Migracion del backend a Docker en Render Free** (Dockerfile con `tesseract-ocr` + `tesseract-ocr-spa`; sigue siendo Render gratis, mismo deploy por push) |
| Imagenes | Se procesan y se **descartan** tras verificar (no se persisten; el disco de Render es efimero) |
| Permisos | Escritura solo ADMIN_LIGA (mismo patron que MatchEventViewSet: `IsAdminLiga` / lectura `AllowAny`) |
| Identidad OCR | El nombre detectado se fuzzy-matcea (Levenshtein) contra el plantel real de los dos clubes del partido (nickname + PlayerIdentityHistory); el admin confirma/corrige en la UI |
| Competencia | `MatchEvent` + resultado siguen siendo autoridad para standings y rankings actuales; `MatchPerformance` es solo analitica (si los goles de la captura difieren, se guardan ambos) |
| Volumen | ~11 filas x 18 campos por partido cargado; S1 completa (~760 partidos) = ~8.400 filas, unos pocos MB en Postgres (no es problema de escala; lo pesado serian las capturas, que se descartan) |

### ✅ Fase 1 — Modelo, API e historial (sin OCR, sin tocar deploy) — commit `1ab0e2f`

- `apps/matches/models.py`: `MatchPerformance` — `match_player = OneToOne(MatchPlayer)` + 18 campos (`rating Decimal(3,1)` 0-10; porcentajes enteros 0-100; km `Decimal(4,1)`; conteos enteros) + `clean()` que exige `match_player.player` distinto de `None` (BOT no tiene rendimiento). Migracion nueva.
- `MatchPerformanceViewSet`: `filterset_fields=["match","match_player"]`, lectura publica, escritura `IsAdminLiga`, `perform_* -> cache.clear()`.
- `POST /api/matches/{id}/performances/batch/`: upsert por jugador; si no existe `MatchPlayer`, lo crea (`is_starter=True`, `display_name=nickname`) validando via `PlayerClubHistory` que el jugador tenga stint en el club_season local o visitante; jugador ajeno al partido -> 400.
- `GET /api/players/{id}/performances/`: historial con contexto de partido (fecha, rival, resultado + los 18 campos), filtros opcionales season/division.
- Frontend: seccion "Rendimiento detallado" en MatchDetail (una fila por jugador con rating/minutos/resumen; expand para editar los 18 campos, guardar por fila) y seccion "Partidos y rendimiento" en PlayerProfile (historial con rating, fallback "sin datos" para partidos legacy).
- Tests: validaciones de modelo, batch (upsert/auto-create/jugador ajeno), permisos, historial.

### ✅ Fase 2 — OCR (pytesseract + Docker) — commit `6307d43`

- `requirements.txt`: + `pytesseract` (Pillow ya esta).
- **Dockerfile** en la raiz (`python:3.12-slim` + `apt-get install tesseract-ocr tesseract-ocr-spa` + pip + collectstatic) y **`render.yaml` migrado a Docker** (preservando migrate, envVars y la DB `ea-fc-db`; plan Free igual, $0). Local: instalar Tesseract + spa (winget UB-Mannheim.TesseractOCR) y documentarlo.
- `apps/matches/services/ocr.py`:
  - `preprocess()` con Pillow replicando los ratios de `imageProcessor.js` (panel stats: x>=0.62, y>=0.10; panel nombre: x 0.02-0.44, y 0.08-0.30; x3, greyscale, linear(1.5,-30), threshold, sharpen)
  - `ocr()` con lang `spa` + config/whitelist de `ocr.js`
  - Port de `parser.js`: keywords -> campo (siempre el primer numero de la linea), fix rating 6<->9 (espejo), O->0, coma->punto, Levenshtein contra el plantel del partido
  - Concurrencia 2 (como el worker pool de FIFASTATS)
- `POST /api/matches/{id}/performances/analyze/`: multipart (campo `images`), hasta 30 archivos, devuelve `{total, exitosos, fallidos, results: [{filename, detected_name, player, stats, warnings, errors, ocr_debug}]}`, **no persiste imagenes**.
- Frontend: bloque "OCR upload" en MatchDetail — select de capturas (max 30), "Analizar" -> fichas por resultado con jugador sugerido (select del plantel; "Editar" rellena el form manual) -> "Guardar" via batch. Smoke local con imagen sintetica OK (nombre, rating, goles, pases, minutos, distancia).
- Tests: parser con textos OCR fijos, preprocessing con imagen Pillow generada, endpoint con `pytesseract` mockeado (sin binario en CI), permisos.
- Al arrancar la fase: re-fetchear `parser.js`, `ocr.js`, `imageProcessor.js`, `routes.js` del repo FIFASTATS para portar al detalle exacto.

### Fase 3 — Analitica (esenciales ✅, opcionales pendientes)

**Hecho:**

- `statistics/services.py`: `PERFORMANCE_METRICS` (18 campos) + `get_performance_leaderboard` (AVG/SUM con `min_matches`, orden por valor), `get_performance_by_position` (4 posiciones, 6 metricas), `get_player_match_series` (cronologica; rating/minutos/km de MatchPerformance, goles/asis/MVP/tarjetas de MatchEvent para calzar con las tarjetas del perfil); filtros season/division; cache 600s (los `cache.clear()` ya estan cubiertos por las mutaciones de la Fase 1).
- Endpoints en `statistics/views.py`: `performance_leaderboard` (400 en metrica/agg invalidos), `performance_by_position`, `player_match_series` (400 sin player, 404 invalido); publicos.
- Frontend con **recharts v3**: tab "Rendimiento" en Statistics (selector de metrica, toggle promedio/total, min 1/3/5/10+ partidos, top-10 oro/plata/bronce + grilla "Promedios por posicion" ARQ/DEF/MED/DEL), "Evolucion de rendimiento" (area de rating con linea de promedio) y sparklines en las tarjetas de PlayerProfile.
- Tests: +8 (`PerformanceAnalyticsTest`) = **147 totales**; smoke Playwright OK (0 errores de consola, 0 requests fallidas).

**Diferidos (opcionales, cuando el usuario lo pida):** graficos #3 (heatmap), #6 (radar por jugador), #7 (tendencia por club), #8 (scatter rating vs victoria), #10 (distribucion de minutos). Los cambios esteticos quedaron resueltos con el rediseño frontend (README "Fase 18" / PROJECT_CONTEXT fila 19): paleta azul/violeta en los charts, shell sidebar+topbar, Home estilo referencia.

### Garantias

- **Competicion intacta**: standings/rankings actuales salen de MatchEvent + resultado; una migracion nueva y cero cambios en modelos viejos (los 147 tests siguen pasando).
- Partidos seed/legacy sin capturas -> sin fila de performance (fallback en UI, jamas rellenar con ceros).
- BOT (`MatchPlayer.player=NULL`) no puede tener performance (validado en el modelo).

### Referencia FIFASTATS (para el port)

- Repo: https://github.com/lucascapocasa1/FIFASTATS---Al-Yateh
- `backend/db-pg.js` — esquema `stats` (~21 campos por jugador por partido)
- `backend/imageProcessor.js` — recortes y preproceso (Sharp)
- `backend/ocr.js` — Tesseract.js, pool de 2 workers, lang spa, whitelist
- `backend/parser.js` — keywords, first-number, fix 6/9, Levenshtein vs CANONICAL_NAMES
- `backend/routes.js` — upload -> analyze -> verificacion humana -> save

### Estado

✅ **Fase 1 implementada** (commit `1ab0e2f`): modelo `MatchPerformance` + migracion, ViewSet/filtros, batch upsert con auto-create, historial publico, secciones MatchDetail/PlayerProfile, tests.
✅ **Fase 2 implementada** (commit `6307d43`): `apps/matches/services/ocr.py` (port completo de FIFASTATS), endpoint `analyze`, bloque OCR con verificacion humana en MatchDetail, `Dockerfile` + `render.yaml` (`runtime: docker`, `preDeployCommand: migrate`), `pytesseract` en requirements; smoke OCR con imagen sintetica OK.
✅ **Fase 3 esenciales implementada**: 3 endpoints de analitica (leaderboard AVG/SUM, promedios por posicion, serie cronologica), tab "Rendimiento" en Statistics, "Evolucion de rendimiento" + sparklines en PlayerProfile (recharts v3), +8 tests = 147, smoke Playwright OK.
✅ **Rediseño frontend implementado (README Fase 18 / PROJECT_CONTEXT fila 19)**: sidebar/topbar con buscador global, Home estilo referencia, paleta azul/violeta en charts, responsive, smoke Playwright OK.

**Pendiente (no arrancar hasta que el usuario lo pida):**

1. **Verificar el primer deploy Docker en Render** — build de la imagen, migrate automatico, smoke de `/api/health/`; el codigo esta, el deploy real no se probo.
2. **Probar OCR con capturas reales de FIFA** — afinar recortes/keywords si hace falta.
3. **Graficos opcionales de la Fase 3** (#3, #6, #7, #8, #10) — los 4 esenciales ya estan; estos solo si el usuario los pide.

Seed local de desarrollo: `python manage.py seed_performances` crea ~34,800 filas (goals/assists derivados de MatchEvent reales, RNG determinista `--seed`, idempotente, `--reset`).

### Archivos ya existentes que se usan (Opcion A — sin cambios)

- `apps/matches/views.py` — endpoints Match/MatchPlayer/MatchEvent con auto-recalc (`_refresh_derived`)
- `apps/matches/serializers.py` — validate() compatible con PATCH parcial
- `frontend/src/pages/MatchDetail.tsx` — scoreboard + form resultado + alineaciones + CRUD de eventos (la Fase 1 agrega una 4ta seccion)
- Las estadisticas basicas se derivan de MatchEvent on-demand (statistics/services.py)
