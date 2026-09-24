# Guia de Desarrollador — EA FC Clubes Pro

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

**106 tests** cubriendo auth, permisos, players, clubs, matches, standings, statistics y mercado de pases.

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

countries, leagues, seasons, divisions, clubs, club-seasons, club-titles, players, transfers, matchdays, matches, match-players, match-events, standings, users, league-admins, club-admins

Nota: `DELETE /api/transfers/{id}/` revierte solo la ultima transferencia del jugador.

### Statistics

```
GET /api/statistics/player/?player_id=1&season_id=1
GET /api/statistics/player_history/?player_id=1
GET /api/statistics/top_scorers/?season_id=1&division_id=1&limit=10
GET /api/statistics/top_assists/?season_id=1&division_id=1&limit=10
GET /api/statistics/top_mvp/?season_id=1&division_id=1&limit=10
```

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
3. Render detecta `render.yaml` automaticamente
4. Configurar variables de entorno: `SECRET_KEY`, `CORS_ALLOWED_ORIGINS`
5. Push a GitHub -> deploy automatico

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
```

## Frontend

- **Rutas**: 14 paginas, incluye `/matches/:id` (MatchDetail) y `/transfers` (Mercado)
- **Edicion inline**: cada pagina expone sus formularios cuando `useCanEdit()` es true
- **API client**: JWT auto-refresh en 401 + retry unico en 429

## Proximas fases (aprobadas)

Ver `PROXIMOS_CAMBIOS.md` #4 para el plan completo de **estadisticas detalladas por partido**:

1. **Fase 1** — Modelo `MatchPerformance` (OneToOne a `MatchPlayer`, 18 campos, valida no-BOT), `MatchPerformanceViewSet`, batch upsert con auto-create de `MatchPlayer` (validado contra `PlayerClubHistory`), historial por jugador, secciones en MatchDetail/PlayerProfile, tests. Sin tocar deploy.
2. **Fase 2** — OCR: `apps/matches/services/ocr.py` (preprocess con ratios de `imageProcessor.js` + port de `parser.js`: first-number, fix 6/9, O->0, Levenshtein vs plantel), `POST /api/matches/{id}/performances/analyze/` (hasta 30 imgs, concurrencia 2, imagenes descartadas), `PerformanceUploadModal` con verificacion humana. Requiere **Dockerfile + render.yaml migrado a Docker en Render Free** (paquetes `tesseract-ocr` + `tesseract-ocr-spa`); local: Tesseract via winget.
3. **Fase 3** — Analitica: leaderboards AVG/SUM por metrica, evolucion por jugador, graficos (cache 600s).

Garantias: Match/MatchPlayer/MatchEvent intactos (106 tests sin riesgo); MatchEvent sigue siendo autoridad para standings/rankings.
