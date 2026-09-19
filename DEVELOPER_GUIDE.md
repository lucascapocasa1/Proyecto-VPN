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
python manage.py test apps.accounts.tests apps.players.tests apps.clubs.tests apps.matches.tests apps.standings.tests apps.statistics.tests -v 2
```

**74 tests** cubriendo auth, permisos, players, clubs, matches, standings y statistics.

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
| Players | Publico | SUPERADMIN (nickname) |
| Matches, Events | Publico | ADMIN_LIGA |
| Standings | Publico | Recalculate: ADMIN_LIGA |
| Statistics | Publico | Solo lectura |

### Cache

- **Standings**: 300 segundos (5 min)
- **Statistics**: 600 segundos (10 min)
- Invalidacion: al recalcular standings se limpia el cache

## API Endpoints

### Auth y Docs

```
POST /api/auth/login/          -> {access, refresh, user}
POST /api/auth/register/       -> {access, refresh, user}
GET  /api/auth/profile/        -> User
POST /api/token/refresh/       -> {access}
GET  /api/health/              -> {"status": "ok", "db": "ok"}
GET  /api/docs/                -> Swagger UI
GET  /api/redoc/               -> ReDoc
GET  /api/schema/              -> OpenAPI schema
```

### CRUD (todos siguen patron GET/POST/GET{id}/PUT/PATCH{id}/DELETE{id})

countries, leagues, seasons, divisions, clubs, players, matches, matchdays, match-players, match-events, standings, club-seasons, club-titles, users, league-admins, club-admins

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
python manage.py seed_data
```
