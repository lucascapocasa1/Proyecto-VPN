# Contexto del Proyecto — EA FC Clubes Pro

**Leer este archivo al inicio de cada sesión para entender el estado del proyecto.**

---

## Qué es

Plataforma web para gestionar ligas competitivas de **EA Sports FC — Clubes Pro** (1v1, clubes ficticios). Los usuarios son administradores y jugadores que participan en ligas organizadas.

## Stack

| Capa | Tecnología |
|------|-----------|
| Backend | Python 3.14, Django 5.x, Django REST Framework |
| Base de datos | PostgreSQL (`ea_fc_platform`, user=`postgres`, pass=`1234`, port=`5432`) |
| Frontend | React 19, TypeScript, Vite |
| Auth | JWT (SimpleJWT) |

## Repo

- **GitHub**: `https://github.com/lucascapocasa1/Proyecto-VPN`
- **Rama**: `main`
- **Directorio de trabajo**: `C:\Users\Capocasa\Desktop\PROYECTO VPN`

---

## Estado de las fases

| Fase | Estado | Descripción |
|------|--------|-------------|
| 1. Arquitectura y modelos | ✅ | 7 apps Django, 21 modelos, Admin, migraciones |
| 2. Lógica de negocio | ✅ | Services, zones, management commands, seed data |
| 3. API REST | ✅ | ViewSets, serializers, URLs, auth endpoints |
| 4. Frontend React | ✅ | 12 páginas, dark theme, JWT auth, API client |
| 5. Auth y Permisos | ✅ | 7 clases de permisos, role-based en todos los ViewSets |
| 6. Tests | ✅ | 74 tests pasando en 6 archivos |
| 7. Frontend-Backend Integration | ✅ | CRUD, loading, error handling, role-based UI |
| 8. Optimization | ✅ | DRF pagination, django-filter, cache, GZip, select_related/prefetch_related |
| 9. Deployment | ✅ | Render (backend + PostgreSQL) + Cloudflare Pages (frontend) |
| 10. Documentation | ✅ | drf-spectacular (Swagger/ReDoc), USER_GUIDE.md, DEVELOPER_GUIDE.md |

---

## Reglas del proyecto (INVIOLABLES)

1. **Sin decisiones arquitectónicas sin aprobación del usuario.** Solo se pueden tomar decisiones de implementación menores (nombres de variables, formatos de archivos, etc.)
2. **Stack fijo**: Django + DRF + PostgreSQL + React + TypeScript + Vite. No se puede cambiar.
3. **No commitear sin que el usuario lo pida explícitamente.**
4. **El jugador se identifica por `nickname`**, no por `Player.id`. El ID es solo interno.
5. **Ascensos/descensos no automáticos**: el admin mueve clubes manualmente.
6. **Las zonas de tabla son configurables** por Division, no hardcodeadas.
7. **La implementación de playoffs/reducidos** es un detalle que se definirá más adelante (formato llaves, ida/vuelta, etc.) — preguntar antes de implementar.

---

## Lógica de negocio clave

### Datos derivados vs fuente de verdad

**FUENTE DE VERDAD** (se editan directamente):
- Player, Club, Season, Division, Match, MatchPlayer, MatchEvent

**DATOS DERIVADOS** (se recalculan):
- **Standing** → se recalcula desde Match (home_goals/away_goals)
- **Estadísticas** → se calculan desde MatchEvent on-demand

### OWN_GOAL
- El gol OWN_GOAL se computa para el **equipo rival** (suma goals_for del rival)
- El evento queda registrado en el MatchPlayer que lo cometió
- NO suma goles al jugador en sus estadísticas personales

### Player
- `Player.id` = ID interno estable, NUNCA cambia
- `nickname` = identificador externo, solo admin puede cambiarlo
- `position` = ARQ/DEF/MED/DEL (opcional, usado para stats realistas)
- `PlayerIdentityHistory` registra cambios de nickname

### BOT
- No es un Player global. Es un MatchPlayer con `player=NULL`
- Máximo 1 per team per match, en posición "BOT"

### ClubSeason
- Un club no puede estar en 2 divisiones en la misma temporada
- Un club puede estar en diferentes temporadas

### Zonas de tabla (configurables por Division)
- `CAMPEÓN` = posición 1
- `REDUCIDO` = positions `playoff_zone_start` a `playoff_zone_end`
- `PROMOCIÓN` = positions `promotion_zone_start` a `promotion_zone_end`
- `DESCENSO` = positions `relegation_zone_start` a `relegation_zone_end`
- `NORMAL` = todo lo demás

---

## Estructura del backend

```
backend/
├── config/settings/          # base.py, development.py, production.py
├── apps/
│   ├── accounts/             # User (roles), LeagueAdmin, ClubAdmin, permissions, JWT, health check
│   ├── competitions/         # Country, Game, CompetitionFormat, League, Season, Division
│   ├── clubs/                # Club, ClubSeason, ClubTitle
│   ├── players/              # Player, PlayerIdentityHistory, PlayerClubHistory
│   ├── matches/              # Matchday, Match, MatchPlayer, MatchEvent
│   ├── standings/            # Standing (derivated), services.py, zones.py
│   └── statistics/           # services.py (calcula desde MatchEvent on-demand)
├── test_helpers/base.py      # BaseTestCase reutilizable
├── runtime.txt               # Python version for Render
├── manage.py
└── requirements.txt
```

### Apps y sus ViewSets

| App | ViewSets | Permisos lectura | Permisos escritura |
|-----|----------|-----------------|-------------------|
| accounts | UserViewSet, LeagueAdminViewSet, ClubAdminViewSet, AuthViewSet | Autenticado | SUPERADMIN |
| competitions | CountryViewSet, GameViewSet, CompetitionFormatViewSet, LeagueViewSet, SeasonViewSet, DivisionViewSet | Público | Country/Game/Format: SUPERADMIN, League/Season/Division: ADMIN_LIGA |
| clubs | ClubViewSet, ClubSeasonViewSet, ClubTitleViewSet | Público | CanManageClub / ADMIN_LIGA |
| players | PlayerViewSet, PlayerIdentityHistoryViewSet, PlayerClubHistoryViewSet | Público | SUPERADMIN (nickname: solo SUPERADMIN) |
| matches | MatchdayViewSet, MatchViewSet, MatchPlayerViewSet, MatchEventViewSet | Público | ADMIN_LIGA |
| standings | StandingViewSet (recalculate action) | Público | Lectura: público, Recalculate: ADMIN_LIGA |
| statistics | StatisticsViewSet (player, top_scorers, top_assists, top_mvp) | Público | — (solo lectura) |

### Endpoints de auth

```
POST /api/auth/login/         → {access, refresh}
POST /api/auth/register/      → User
GET  /api/auth/profile/       → User (requiere auth)
POST /api/token/refresh/      → {access}
```

### Endpoints de statistics

```
GET /api/statistics/player/?player_id=1&season_id=1
GET /api/statistics/player_history/?player_id=1
GET /api/statistics/top_scorers/?season_id=1&division_id=1&limit=10
GET /api/statistics/top_assists/?season_id=1&division_id=1&limit=10
GET /api/statistics/top_mvp/?season_id=1&division_id=1&limit=10
```

---

## Estructura del frontend

```
frontend/
├── src/
│   ├── api/
│   │   ├── client.ts          # Axios + JWT interceptors (auto-refresh)
│   │   └── index.ts           # API functions CRUD para todos los endpoints
│   ├── components/
│   │   ├── layout/Layout.tsx   # Header (con role badge), Nav, Footer
│   │   └── ui/
│   │       ├── StandingsTable.tsx  # Tabla con colores de zona (CAMPEÓN/REDUCIDO/etc)
│   │       ├── MatchCard.tsx
│   │       ├── PlayerCard.tsx
│   │       ├── ClubCard.tsx
│   │       ├── Loading.tsx         # Spinner animado
│   │       └── ErrorMessage.tsx    # Error con retry button
│   ├── context/
│   │   └── AuthContext.tsx     # JWT auth (login, logout, profile)
│   ├── pages/
│   │   ├── Home.tsx            # Seasons + clubs + top scorers
│   │   ├── Countries.tsx       # Lista países
│   │   ├── Leagues.tsx         # Lista ligas
│   │   ├── Seasons.tsx         # Lista temporadas con badges de estado
│   │   ├── Standings.tsx       # Tabla posiciones + recalculate button
│   │   ├── Clubs.tsx           # Lista clubs + crear (SUPERADMIN)
│   │   ├── ClubProfile.tsx     # Detalle club + títulos + participaciones
│   │   ├── Players.tsx         # Lista jugadores + crear (SUPERADMIN)
│   │   ├── PlayerProfile.tsx   # Detalle jugador + stats + historial
│   │   ├── Matches.tsx         # Lista partidos + filtro por estado
│   │   ├── Statistics.tsx      # Tabs goleadores/asistencias/MVP
│   │   └── Login.tsx           # Login JWT
│   ├── types/index.ts         # TypeScript interfaces
│   ├── App.tsx                 # React Router
│   ├── App.css                 # Dark theme + spinner + forms + filters
│   └── main.tsx
├── vite.config.ts             # Proxy a localhost:8000
├── package.json
└── tsconfig.json
```

### API Client — Métodos disponibles

```ts
// CRUD completo
authApi:          login, register, profile
countriesApi:     list, get, create, update, delete
leaguesApi:       list, get, create, update, delete
seasonsApi:       list, get, create
clubsApi:         list, get, create, update, delete
playersApi:       list, get, create, update, delete
matchesApi:       list, get, create, update, delete
matchPlayersApi:  create, delete
matchEventsApi:   create, delete
standingsApi:     list, recalculate
statisticsApi:    player, playerHistory, topScorers, topAssists, topMvp
```

### Role-based UI

| Acción | Permisos |
|--------|----------|
| Crear club | SUPERADMIN |
| Crear jugador | SUPERADMIN |
| Recalcular tabla | SUPERADMIN, ADMIN_LIGA |
| Ver todo | Todos los roles autenticados |

### Vite proxy
```ts
// vite.config.ts
proxy: {
  '/api': 'http://localhost:8000'
}
```

### Client JWT (client.ts)
- `request` interceptor: agrega `Authorization: Bearer <token>`
- `response` interceptor: si 401, intenta refresh con refresh_token → renueva access_token
- Si falla el refresh, redirige a `/login`

---

## Tests

```bash
cd backend
python manage.py test apps.accounts.tests apps.players.tests apps.clubs.tests apps.matches.tests apps.standings.tests apps.statistics.tests -v 2
```

### Resumen de tests (74 total)

| Archivo | Tests | Qué cubre |
|---------|-------|-----------|
| `apps/players/tests.py` | 9 | Creación, nickname único, historial de cambios, historial de clubes |
| `apps/clubs/tests.py` | 8 | Clubs, club-season, títulos, validación única |
| `apps/matches/tests.py` | 10 | Partidos, validación home≠away, alineaciones, BOT, eventos |
| `apps/standings/tests.py` | 10 | Victoria=3pts, empate=1pt, diferencia de goles, posiciones, zonas |
| `apps/statistics/tests.py` | 8 | Goals, assists, own goals, cards, MVP, rankings |
| `apps/accounts/tests.py` | 29 | Login, register, profile, permisos por rol en todos los endpoints |

### Base de tests
- `apps/test_helpers/base.py`: `BaseTestCase` con fixtures comunes (users, country, league, season, divisions, 10 clubs, 10 club_seasons, 22 players, player_club_history)

---

## Datos de prueba (seed data)

Dos scripts de seed disponibles:

### seed_data.py — Dataset completo (~34,000 registros)

```bash
python manage.py seed_data
```

- 4 users (superadmin, admin_liga, admin_club, player)
- 2 countries (Argentina, Uruguay)
- 40 clubs per country (20 Primera + 20 Segunda)
- 600 players per country (15 por club, con position)
- S1 FINISHED: 380 partidos por país (round-robin, 2 divisiones)
- S2 UPCOMING: sin partidos, solo equipos asignados
- ~15,000 MatchEvents total
- 80 standings (recalculados)

### seed_dev.py — Dataset chico (~1,200 registros)

```bash
python manage.py seed_dev
```

- 1 country (Argentina)
- 10 clubs, 60 players
- S1 FINISHED + S2 UPCOMING
- ~370 eventos

---

## Deployment

### Stack de producción

| Servicio | Plataforma | Puerto |
|----------|------------|--------|
| Backend (Django + Gunicorn) | Render | 8000 (interno) |
| PostgreSQL | Render (manejada) | 5432 (interno) |
| Frontend (React + Vite) | Cloudflare Pages | 443 (HTTPS) |

### Archivos de deployment

| Archivo | Descripción |
|---------|-------------|
| `render.yaml` | Infraestructura como código para Render |
| `backend/runtime.txt` | Versión de Python para Render |
| `backend/config/settings/production.py` | Settings para Render (Whitenoise, CORS, etc.) |
| `.env.example` | Variables de entorno documentadas |

### Variables de entorno (Render)

```bash
DJANGO_SETTINGS_MODULE=config.settings.production
SECRET_KEY=<auto-generado>
DEBUG=false
ALLOWED_HOSTS=.onrender.com
DB_NAME=ea_fc_platform  # from Render PostgreSQL
DB_USER=<from database>
DB_PASSWORD=<from database>
DB_HOST=<from database>
DB_PORT=<from database>
CORS_ALLOWED_ORIGINS=https://*.pages.dev,https://*.cloudflarepages.com
```

### Health Check

```
GET /api/health/ → {"status": "ok", "db": "ok"}
```

### Frontend (Cloudflare Pages)

- Variable de entorno: `VITE_API_URL=https://tu-backend.onrender.com/api`
- Proxy API configurado en `client.ts`

### Deploy

```bash
# Backend: Push a GitHub → Render deploy automático
# Frontend: Push a GitHub → Cloudflare Pages deploy automático
```

---

## Archivos importantes

| Archivo | Descripción |
|---------|-------------|
| `render.yaml` | Infraestructura Render (app + PostgreSQL) |
| `backend/config/settings/base.py` | Config Django, AUTH_USER_MODEL, REST_FRAMEWORK, JWT |
| `backend/config/settings/development.py` | SQLite para tests, PostgreSQL default |
| `backend/config/settings/production.py` | Settings Render (Whitenoise, CORS, HSTS) |
| `backend/apps/accounts/permissions.py` | 7 clases de permisos custom |
| `backend/apps/accounts/urls.py` | Health check endpoint |
| `backend/apps/standings/services.py` | recalculate_standings, recalculate_all_standings |
| `backend/apps/statistics/services.py` | Player/club statistics, top scorers/assists/mvp |
| `backend/apps/matches/services.py` | Lineup validation, BOT completion, goal consistency |
| `frontend/src/api/client.ts` | Axios + JWT interceptors + VITE_API_URL |
| `frontend/src/api/index.ts` | API CRUD functions para todos los endpoints |
| `frontend/src/context/AuthContext.tsx` | Auth context con JWT |
| `frontend/src/components/ui/Loading.tsx` | Spinner animado |
| `frontend/src/components/ui/ErrorMessage.tsx` | Error con retry button |
| `frontend/vite.config.ts` | Vite config con proxy + build output |

---

## Pendiente

Ver `PROXIMOS_CAMBIOS.md` para detalles completos:

1. **Base de datos grande** — 20 equipos/división, 15 jugadores/equipo, Argentina + Uruguay
2. **Mercado de pases** — Free agents, invitaciones, ventana de pases
3. **Brasil** — Agregar como tercer país
4. **Carga de estadísticas** — Formulario manual para goles, asistencias, tarjetas, MVP

---

*Última actualización: Fase 10 completada — Features pendientes documentadas*
