# Guia de Desarrollador — VPN · FC 27 Pro Clubs

## Stack

| Capa | Tecnologia |
|------|-----------|
| Backend | Python, Django, Django REST Framework |
| Base de datos | PostgreSQL |
| Frontend | React, TypeScript, Vite |
| Auth | JWT (SimpleJWT) |
| API Docs | drf-spectacular (OpenAPI 3.0) |
| Deployment | Render (backend) + Cloudflare Pages (frontend) |

## Setup local

### Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Editar .env con tus credenciales de PostgreSQL
python manage.py migrate
python manage.py seed_data
python manage.py createsuperuser
python manage.py runserver
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

El frontend corre en `http://localhost:5173` y proxea `/api` a `http://localhost:8000`.

## Tests

```bash
cd backend
python manage.py test
```

**147 tests** cubriendo auth, permisos, players, clubs, matches, standings, statistics (incluida la analítica de rendimiento: leaderboards AVG/SUM, promedios por posición, serie cronológica), mercado de pases, rendimiento por partido (MatchPerformance) y OCR (con `pytesseract` mockeado).

Para E2E con Playwright (requiere backend + frontend corriendo):

```bash
python test_app.py
```

## Arquitectura

### Modelo de datos

```
Country -> League -> Season -> Division -> ClubSeason -> Match -> MatchPlayer -> MatchEvent
            ^
           Game
```

### Datos derivados vs fuente de verdad

**FUENTE DE VERDAD**: Player, Club, Season, Division, Match, MatchPlayer, MatchEvent

**DATOS DERIVADOS**: Standing (desde Matches), Estadisticas (desde MatchEvent)

### Permisos

| Recurso | Lectura | Escritura |
|---------|---------|-----------|
| Countries, Games, Formats | Publico | SUPERADMIN |
| Leagues, Seasons, Divisions | Publico | ADMIN_LIGA |
| Clubs | Publico | CanManageClub |
| ClubSeason, ClubTitle | Publico | ADMIN_LIGA |
| Players, IdentityHistory, ClubHistory, Transfers | Publico | ADMIN_LIGA |
| Matches, MatchPlayers, MatchEvents | Publico | ADMIN_LIGA |
| Standings | Publico | Recalculate: ADMIN_LIGA |
| Statistics | Publico | Solo lectura |

El frontend unifica los controles de edicion con el hook `useCanEdit()` (SUPERADMIN o ADMIN_LIGA).

### Cache

- **Standings**: 300 segundos (5 min)
- **Statistics**: 600 segundos (10 min)
- Invalidacion: toda mutacion de Match/MatchPlayer/MatchEvent ejecuta `_refresh_derived` (recalcula la tabla de la division) y `cache.clear()`

### Rate limiting

- Sin `DEFAULT_THROTTLE_CLASSES` globales (rompian la navegacion con 429)
- `ScopedRateThrottle` con `throttle_scope = "auth"` (10/min por IP) en `AuthViewSet.login/register` y `ScopedTokenRefreshView`
- El axios client (`frontend/src/api/client.ts`) reintenta **1 vez** las respuestas 429 esperando `Retry-After` (default 1s, max 5s)

## API Endpoints

### Auth y Docs

```
POST /api/auth/login/          -> {access, refresh, user}   (throttle 10/min)
POST /api/auth/register/       -> {access, refresh, user}   (throttle 10/min)
GET  /api/auth/profile/        -> User
POST /api/token/refresh/       -> {access}                  (throttle 10/min)
GET  /api/health/              -> {"status": "ok", "db": "ok"}
GET  /api/docs/                -> Swagger UI
GET  /api/redoc/               -> ReDoc
GET  /api/schema/              -> OpenAPI schema
```

### CRUD (todos siguen patron GET/POST/GET{id}/PUT/PATCH{id}/DELETE{id})

countries, leagues, seasons, divisions, clubs, club-seasons, club-titles, players, transfers, matchdays, matches, match-players, match-events, match-performances, standings, users, league-admins, club-admins

Nota: `DELETE /api/transfers/{id}/` revierte solo la ultima transferencia del jugador.

### Statistics

```
GET /api/statistics/player/?player_id=1&season_id=1
GET /api/statistics/player_history/?player_id=1
GET /api/statistics/top_scorers/?season_id=1&division_id=1&limit=10
GET /api/statistics/top_assists/?season_id=1&division_id=1&limit=10
GET /api/statistics/top_mvp/?season_id=1&division_id=1&limit=10
GET /api/statistics/performance_leaderboard/?metric=rating&agg=avg&min_matches=3&season_id=1
GET /api/statistics/performance_by_position/?season_id=1
GET /api/statistics/player_match_series/?player_id=1
```

### Rendimiento por partido (MatchPerformance)

```
GET  /api/match-performances/?match=1&match_player=2   # listado (lectura publica, escritura ADMIN_LIGA)
POST /api/matches/{id}/performances/batch/             # upsert por jugador (auto-crea MatchPlayer si hubo stint)
POST /api/matches/{id}/performances/analyze/           # OCR: multipart "images" (<=30), no persiste; ADMIN_LIGA
GET  /api/players/{id}/performances/?season_id=1       # historial con contexto de partido (publico)
```

- Los campos de `MatchPerformance` son solo analitica: **standings/rankings siguen saliendo de `MatchEvent` + resultado**.
- OCR portado de FIFASTATS: recortes de paneles (stats y nombre), binarizado, lang `spa`+fallback `eng`, fix rating 6<->9 y O->0, Levenshtein contra el plantel real, concurrencia 2.
- Requiere Tesseract instalado (local: `winget UB-Mannheim.TesseractOCR` + `spa.traineddata`; en Render: la imagen Docker ya lo trae).

### Filtros

```
GET /api/clubs/?country=1&is_active=true&search=boca
GET /api/players/?platform=PC&search=jugador
GET /api/matches/?season=1&division=1&status=FINISHED
GET /api/standings/?season=1&division=1
GET /api/leagues/?country=1&search=liga
GET /api/seasons/?league=1&status=ACTIVE
```

## Deployment

### Backend (Render)

1. Crear cuenta en render.com
2. Conectar repositorio de GitHub
3. Render detecta `render.yaml` automaticamente — **runtime `docker`** (lee `Dockerfile` de la raiz: python 3.12 + tesseract-ocr + tesseract-ocr-spa + gunicorn)
4. `preDeployCommand: python manage.py migrate` corre antes del corte; config vars: `SECRET_KEY`, `CORS_ALLOWED_ORIGINS`
5. Push a GitHub -> build de imagen + deploy automatico (plan Free, $0)

> **Pendiente de verificar**: el primer deploy Docker real en Render (build + migrate + smoke de `/api/health/`). El codigo y la config estan, pero el deploy todavia no se probo.

### Frontend (Cloudflare Pages)

1. Crear cuenta en Cloudflare Pages
2. Conectar repositorio de GitHub
3. Build command: `cd frontend && npm install && npm run build`
4. Build output: `frontend/dist`
5. Variable de entorno: `VITE_API_URL=https://tu-backend.onrender.com/api`

## Management Commands

```bash
python manage.py recalculate_standings --season 1 --division 1
python manage.py recalculate_standings --all
python manage.py generate_fixtures --season 1 --division 1
python manage.py seed_data               # Dataset completo, 2 paises, S2 ACTIVE
python manage.py seed_dev                # Dataset chico (1 pais)
python manage.py seed_s2                 # Upgrade idempotente a S2 ACTIVE
python manage.py fix_season_transitions  # Zonas, titulos S1, transiciones S1->S2, regenera fixtures S2
python manage.py seed_performances       # Rendimiento por jugador/partido (idempotente, --reset, --seed 42)
```

## Frontend

- **Rutas**: 14 paginas, incluye `/matches/:id` (MatchDetail) y `/transfers` (Mercado)
- **Edicion inline**: cada pagina expone sus formularios cuando `useCanEdit()` es true
- **API client**: JWT auto-refresh en 401 + retry unico en 429

## Rendimiento por partido — estado

Ver `PROXIMOS_CAMBIOS.md` #4 para el plan completo de **estadisticas detalladas por partido**:

1. **Fase 1 ✅** (commit `1ab0e2f`) — Modelo `MatchPerformance` (OneToOne a `MatchPlayer`, 18 campos, valida no-BOT), `MatchPerformanceViewSet`, batch upsert con auto-create de `MatchPlayer` (validado contra `PlayerClubHistory`), historial por jugador, secciones en MatchDetail/PlayerProfile, tests.
2. **Fase 2 ✅** (commit `6307d43`) — OCR: `apps/matches/services/ocr.py` (preprocess con ratios de `imageProcessor.js` + port de `parser.js`: first-number, fix 6/9, O->0, Levenshtein vs plantel), `POST /api/matches/{id}/performances/analyze/` (hasta 30 imgs, concurrencia 2, imagenes descartadas), bloque OCR con verificacion en MatchDetail. **Dockerfile + render.yaml migrados a Docker en Render Free** (paquetes `tesseract-ocr` + `tesseract-ocr-spa`); local: Tesseract via winget.
3. **Fase 3 esenciales ✅** — Analitica: `get_performance_leaderboard` (AVG/SUM de cualquiera de las 18 metricas, `min_matches`), `get_performance_by_position` (ARQ/DEF/MED/DEL), `get_player_match_series` (serie cronologica; rating/minutos/km de MatchPerformance, goles/asis/MVP/tarjetas de MatchEvent) en `statistics/services.py` + acciones `performance_leaderboard` / `performance_by_position` / `player_match_series` en `statistics/views.py` (cache 600s, publicos). Frontend: tab "Rendimiento" en Statistics (selector de metrica, toggle promedio/total, minimo de partidos, top-10 con medallas, grilla por posicion) + "Evolución de rendimiento" y sparklines en PlayerProfile, con recharts v3. Estetica resuelta con el rediseño de la Fase 18 (paleta azul/violeta). Diferidos: graficos opcionales #3/#6/#7/#8/#10.

**Pendiente (no arrancar hasta que el usuario lo pida):** (a) verificar el primer deploy Docker en Render, (b) probar OCR con capturas reales de FIFA y afinar recortes/keywords.

Garantias: Match/MatchPlayer/MatchEvent intactos (147 tests sin riesgo); MatchEvent sigue siendo autoridad para standings/rankings; seed local `seed_performances` consistente con los MatchEvent reales.

---

## Frontend — shell y rediseño (Fase 18)

- `frontend/src/components/layout/Layout.tsx` — sidebar (`NAV_ITEMS` con rutas + íconos lucide-react, drawer para ≤900px) + topbar (buscador, campanita decorativa, usuario/rol/logout); preserva toda la lógica de `AuthContext`.
- `frontend/src/components/ui/GlobalSearch.tsx` — buscador global con debounce 250ms: jugadores via `playersApi.list({search})` y clubs via `clubsApi.list()` filtrados client-side (la API de clubs no acepta texto libre; se cachea en un module-level promise). Enter navega al primer resultado.
- `frontend/src/App.css` — secciones `SHELL — SIDEBAR + TOPBAR`, `HOME - PANELS`, `FASE D/E`; tokens de color en `:root` (navy `#050B18`, azul `#3b82f6`, violeta `#7c3aed`).
- Charts (`frontend/src/components/charts/`): paleta azul/violeta; `LeaderboardChart` conserva oro/plata/bronce para el podio y usa azul para el resto.
- Smoke: `with_server.py` usa `cmd.exe` → los comandos `--server` deben usar `&&` (no `;`). Ojo con `page.screenshot(full_page=True)` justo tras un click: puede capturar un frame stale; usar viewport screenshot para verificar cambios de estado.
