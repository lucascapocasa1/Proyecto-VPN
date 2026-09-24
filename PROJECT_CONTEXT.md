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
| 4. Frontend React | ✅ | 14 páginas, Matchday Broadcast theme, JWT auth, API client |
| 5. Auth y Permisos | ✅ | 7 clases de permisos, role-based en todos los ViewSets |
| 6. Tests | ✅ | 139 tests pasando en 6 archivos |
| 7. Frontend-Backend Integration | ✅ | CRUD, loading, error handling, role-based UI |
| 8. Optimization | ✅ | DRF pagination, django-filter, cache, GZip, select_related/prefetch_related |
| 9. Deployment | ✅ | Render (backend + PostgreSQL) + Cloudflare Pages (frontend) |
| 10. Documentation | ✅ | drf-spectacular (Swagger/ReDoc), USER_GUIDE.md, DEVELOPER_GUIDE.md |
| 11. Zonas y datos S2 | ✅ | Zonas por división, títulos S1 corregidos, transiciones S1→S2, fixtures S2 regenerados |
| 12. Mercado de pases (v1) | ✅ | Modelo Transfer, API `/api/transfers/`, página Mercado con búsqueda y revert |
| 13. Edición admin inline | ✅ | MatchDetail con CRUD + auto-recalc, edición de títulos/temporadas/jugadores/clubes |
| 14. Rate limits | ✅ | Sin throttles globales; auth 10/min por IP; retry de 429 en frontend |
| 15. Rendimiento Fase 1 | ✅ | `MatchPerformance` + API + historial (commit `1ab0e2f`) |
| 16. Rendimiento Fase 2 | ✅ | OCR pytesseract + UI de capturas + Docker en Render (commit `6307d43`) — **deploy real pendiente de verificar** |
| 17. Seed rendimiento + fixes | ✅ | `seed_performances` (34,800 filas), fix clubs fetch-all, credenciales documentadas |

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
- `CAMPEÓN` = posición 1 (todas las divisiones)
- `REDUCIDO` = positions `playoff_zone_start` a `playoff_zone_end` (solo Segunda↓: pos 2-9)
- `PROMOCIÓN` = positions `promotion_zone_start` a `promotion_zone_end` (pos 19)
- `DESCENSO` = positions `relegation_zone_start` a `relegation_zone_end` (pos 20)
- `NORMAL` = todo lo demás

Config actual del seed:
| División | Pos 1 | Pos 2-9 | Pos 19 | Pos 20 |
|----------|-------|---------|--------|--------|
| Primera | CAMPEÓN | NORMAL | PROMOCIÓN | DESCENSO |
| Segunda↓ | CAMPEÓN | REDUCIDO | PROMOCIÓN | DESCENSO |

### Transiciones entre temporadas (no automáticas)
- Directas: pos 20 Primera ↓ Segunda, campeón Segunda ↑ Primera; campeón de liga queda en Primera; la Promoción (19 Primera vs campeón Reducido) se resuelve a mano
- Comando idempotente: `python manage.py fix_season_transitions` (corrige títulos, aplica movimientos, backfillea Transfer, regenera fixtures de S2)

### Mercado de pases (v1 — registro admin)
- Modelo `Transfer`: player, from_club_season, to_club_season, date, registered_by
- Escritura: ADMIN_LIGA+; `DELETE` revierte solo la última transferencia del jugador
- 160 transferencias backfilleadas desde los movimientos S1→S2
- **Falta (ver PROXIMOS_CAMBIOS.md)**: ventana de pases, free agents, invitaciones con expiración

### Rate limiting
- Sin `DEFAULT_THROTTLE_Classes` globales (los 429 rompían la navegación)
- `ScopedRateThrottle` 10/min por IP solo en `login`, `register` y `token/refresh`
- El axios client reintenta **1 vez** las respuestas 429 esperando `Retry-After` (máx 5s)

---

## Estructura del backend

```
backend/
├── config/settings/          # base.py, development.py, production.py
├── apps/
│   ├── accounts/             # User (roles), LeagueAdmin, ClubAdmin, permissions, JWT, health check
│   ├── competitions/         # Country, Game, CompetitionFormat, League, Season, Division
│   ├── clubs/                # Club, ClubSeason, ClubTitle
│   ├── players/              # Player, PlayerIdentityHistory, PlayerClubHistory, Transfer
│   ├── matches/              # Matchday, Match, MatchPlayer, MatchEvent
│   ├── standings/            # Standing (derivated), services.py, zones.py, seed/fix commands
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
| clubs | ClubViewSet, ClubSeasonViewSet, ClubTitleViewSet | Público | Club: CanManageClub, ClubSeason/ClubTitle: ADMIN_LIGA |
| players | PlayerViewSet, PlayerIdentityHistoryViewSet, PlayerClubHistoryViewSet, TransferViewSet | Público | ADMIN_LIGA (lectura/list/retrieve: AllowAny) |
| matches | MatchdayViewSet, MatchViewSet, MatchPlayerViewSet, MatchEventViewSet | Público | ADMIN_LIGA |
| standings | StandingViewSet (recalculate action) | Público | Lectura: público, Recalculate: ADMIN_LIGA |
| statistics | StatisticsViewSet (player, top_scorers, top_assists, top_mvp) | Público | — (solo lectura) |

### Endpoints de auth

```
POST /api/auth/login/         → {access, refresh}   (throttle 10/min por IP)
POST /api/auth/register/      → User                (throttle 10/min por IP)
GET  /api/auth/profile/       → User (requiere auth)
POST /api/token/refresh/      → {access}             (throttle 10/min por IP)
```

### Endpoints de statistics

```
GET /api/statistics/player/?player_id=1&season_id=1
GET /api/statistics/player_history/?player_id=1
GET /api/statistics/top_scorers/?season_id=1&division_id=1&limit=10
GET /api/statistics/top_assists/?season_id=1&division_id=1&limit=10
GET /api/statistics/top_mvp/?season_id=1&division_id=1&limit=10
```

### Endpoint de mercado de pases

```
GET/POST/GET{id}/PATCH/DELETE /api/transfers/?season=1&page_size=100
# Escritura: ADMIN_LIGA. DELETE revierte solo la última transferencia del jugador.
```

---

## Estructura del frontend

```
frontend/
├── src/
│   ├── api/
│   │   ├── client.ts          # Axios + JWT interceptors (auto-refresh + retry 429)
│   │   └── index.ts           # API functions CRUD para todos los endpoints
│   ├── components/
│   │   ├── layout/Layout.tsx   # Header (con role badge), Nav, Footer
│   │   └── ui/
│   │       ├── StandingsTable.tsx  # Tabla con colores de zona (CAMPEÓN/REDUCIDO/etc)
│   │       ├── MatchCard.tsx       # Link a /matches/:id (detalle)
│   │       ├── PlayerCard.tsx
│   │       ├── ClubCard.tsx
│   │       ├── Loading.tsx         # Spinner animado
│   │       └── ErrorMessage.tsx    # Error con retry button
│   ├── context/
│   │   └── AuthContext.tsx     # JWT auth (login, logout, profile)
│   ├── hooks/
│   │   └── useCanEdit.ts       # true si rol SUPERADMIN o ADMIN_LIGA
│   ├── pages/
│   │   ├── Home.tsx            # Seasons + clubs + top scorers
│   │   ├── Countries.tsx       # Lista países
│   │   ├── Leagues.tsx         # Lista ligas
│   │   ├── Seasons.tsx         # Temporadas + edit inline (estado/nombre, admin)
│   │   ├── Standings.tsx       # Tabla posiciones + recalculate button
│   │   ├── Clubs.tsx           # Lista clubs + crear (SUPERADMIN)
│   │   ├── ClubProfile.tsx     # Detalle club + edit inline + CRUD títulos (admin)
│   │   ├── Players.tsx         # Lista jugadores + crear (SUPERADMIN)
│   │   ├── PlayerProfile.tsx   # Detalle jugador + stats + edit inline (admin)
│   │   ├── Matches.tsx         # Lista partidos + filtro por estado
│   │   ├── MatchDetail.tsx     # Marcador + editar resultado/alineaciones/eventos (admin)
│   │   ├── Transfers.tsx       # Mercado de pases + alta/baja (admin)
│   │   ├── Statistics.tsx      # Tabs goleadores/asistencias/MVP
│   │   └── Login.tsx           # Login JWT
│   ├── types/index.ts         # TypeScript interfaces
│   ├── App.tsx                 # React Router
│   ├── App.css                 # Matchday Broadcast theme + forms + filters
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
seasonsApi:       list, get, create, update
clubsApi:         list (pagina hasta traer todos), get, create, update, delete
clubTitlesApi:    list, create, delete
playersApi:       list, get, create, update, delete
transfersApi:     list, create, delete
matchesApi:       list, get, create, update, delete
matchPlayersApi:  list, create, delete
matchEventsApi:   list, create, update, delete
playerClubHistoryApi: list
standingsApi:     list, recalculate
statisticsApi:    player, playerHistory, topScorers, topAssists, topMvp
matchPerformancesApi: list, saveBatch, forPlayer, update, delete, analyze (OCR)
```

### Role-based UI (hook `useCanEdit`)

| Acción | Permisos |
|--------|----------|
| Editar resultado/partido, alineaciones, eventos | SUPERADMIN, ADMIN_LIGA |
| Editar club, títulos, jugador, temporada | SUPERADMIN, ADMIN_LIGA |
| Mercado de pases (alta/baja) | SUPERADMIN, ADMIN_LIGA |
| Recalcular tabla | SUPERADMIN, ADMIN_LIGA |
| Crear club / jugador | SUPERADMIN |
| Ver todo | Todos los roles (lectura pública) |

### Vite proxy
```ts
// vite.config.ts
proxy: {
  '/api': 'http://localhost:8000'
}
```

### Client JWT (client.ts)
- `request` interceptor: agrega `Authorization: Bearer <token>`
- `response` interceptor: si **429**, espera `Retry-After` (default 1s, máx 5s) y reintenta **1 vez**
- Si 401, intenta refresh con refresh_token → renueva access_token
- Si falla el refresh, redirige a `/login`

---

## Tests

```bash
cd backend
python manage.py test
```

### Resumen de tests (139 total)

| Archivo | Tests | Qué cubre |
|---------|-------|-----------|
| `apps/players/tests.py` | 20 | Creación, nicknames, historial, clubes, mercado de pases (Transfer API) |
| `apps/clubs/tests.py` | 11 | Clubs, club-season, títulos (CRUD API), validación única |
| `apps/matches/tests.py` | 51 | Partidos, alineaciones, BOT, eventos, permisos, auto-recalc + MatchPerformance (modelo/batch/historial) + endpoint OCR (parser, preprocessing, perms con pytesseract mockeado) |
| `apps/standings/tests.py` | 16 | Victoria=3pts, empate, diferencia, posiciones, zonas por división |
| `apps/statistics/tests.py` | 12 | Goals, assists, own goals, cards, MVP, rankings |
| `apps/accounts/tests.py` | 29 | Login, register, profile, permisos por rol en todos los endpoints |

### Base de tests
- `apps/test_helpers/base.py`: `BaseTestCase` con fixtures comunes (users, country, league, season, divisions, 10 clubs, 10 club_seasons, 22 players, player_club_history)

---

## Credenciales de desarrollo (local)

Base local `ea_fc_platform` (creadas por `seed_data`, mismo password para todas):

| Usuario | Rol | Password |
|---------|-----|----------|
| `admin` | SUPERADMIN + superuser de `/admin/` | `admin123` |
| `admin_liga` | ADMIN_LIGA | `admin123` |
| `admin_club` | ADMIN_CLUB | `admin123` |
| `player1` | PLAYER | `admin123` |

---

## Datos de prueba (seed data)

Tres scripts de seed disponibles:

### seed_data.py — Dataset completo (~34,000 registros)

```bash
python manage.py seed_data
```

- 4 users (superadmin, admin_liga, admin_club, player)
- 2 countries (Argentina, Uruguay)
- 40 clubs per country (20 Primera + 20 Segunda)
- 600 players per country (15 por club, con position)
- S1 FINISHED: 380 partidos por país (round-robin, 2 divisiones)
- S2 ACTIVE: 11 matchdays por división (J1-J10 FINISHED, J11 SCHEDULED), transiciones S1→S2 aplicadas, 160 Transfer backfilleados
- ~29,500+ MatchEvents total
- Standings recalculados
- Nicknames realistas (ej: lucas_gar10, diego_pro)
- Goles pesados por posición (DEL=10x, MED=5x, DEF=2x, ARQ=0.5x)

### Comandos de corrección de datos

```bash
python manage.py fix_season_transitions   # idempotente: zonas, títulos S1, transiciones S1→S2, regenera fixtures S2
python manage.py seed_s2                  # upgrade idempotente de un seed viejo a S2 ACTIVE
python manage.py recalculate_standings --all
```

### seed_dev.py — Dataset chico (~1,200 registros)

```bash
python manage.py seed_dev
```

- 1 country (Argentina)
- 10 clubs, 60 players
- S1 FINISHED + S2 UPCOMING
- ~370 eventos

### seed_performances — Rendimiento por jugador y partido

```bash
python manage.py seed_performances            # completa solo las apariciones sin performance
python manage.py seed_performances --reset    # borra todo y regenera
python manage.py seed_performances --seed 7   # otra semilla (default 42)
```

- Crea `MatchPerformance` para todas las apariciones de partidos FINISHED (~34,800 filas)
- **goals/assists derivados de los `MatchEvent` reales** (consistente con rankings de goleadores/asistencias)
- El resto de las 18 stats es realista por posición (ARQ/DEF/MED/DEL), rating correlacionado con rendimiento
- Idempotente: solo rellena filas faltantes; determinista: el RNG se siembra con `--seed` + id de la aparición

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

1. **Estadísticas detalladas por partido (rendimiento)** — **Fase 1 ✅ (`1ab0e2f`) y Fase 2 ✅ (`6307d43`)**: modelo `MatchPerformance` (18 campos por jugador por partido), carga manual + OCR (`pytesseract` + Pillow, port de FIFASTATS), Docker en Render (`Dockerfile` + `render.yaml runtime: docker`), imágenes descartadas tras verificar, solo ADMIN_LIGA escribe. **Pendiente (no arrancar hasta que el usuario lo pida): (a) verificar el primer deploy Docker en Render, (b) probar OCR con capturas reales de FIFA.** Sigue Fase 3 (analítica/gráficos)
2. **Mercado de pases (v2)** — ventana de pases, free agents, invitaciones con expiración (v1 de registro admin ya está)
3. **Brasil** — Agregar como tercer país
4. **Reducido/Promoción** — generar las llaves del Reducido y la Promoción como partidos (formato por definir)

---

## Testing

### Backend (Django test runner)

```bash
cd backend
python manage.py test --verbosity=2
```

139 tests en 6 archivos, todos pasando.

### Frontend (Playwright)

```bash
python test_app.py
```

Recorre las 14 páginas + detalle de partido, verifica la API y guarda screenshots en `test_screenshots/`.

---

*Última actualización: plan aprobado de estadísticas detalladas + OCR (MatchPerformance, pytesseract + Docker en Render Free) — ver PROXIMOS_CAMBIOS.md #4*
