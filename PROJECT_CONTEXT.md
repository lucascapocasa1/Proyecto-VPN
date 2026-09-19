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
| **7. Frontend-Backend Integration** | ⏳ | **PRÓXIMA — No iniciar sin autorización** |
| 8. Optimization | ⏳ | Pendiente |
| 9. Deployment | ⏳ | Pendiente |
| 10. Documentation | ⏳ | Pendiente |

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
│   ├── accounts/             # User (roles), LeagueAdmin, ClubAdmin, permissions, JWT
│   ├── competitions/         # Country, Game, CompetitionFormat, League, Season, Division
│   ├── clubs/                # Club, ClubSeason, ClubTitle
│   ├── players/              # Player, PlayerIdentityHistory, PlayerClubHistory
│   ├── matches/              # Matchday, Match, MatchPlayer, MatchEvent
│   ├── standings/            # Standing (derivated), services.py, zones.py
│   └── statistics/           # services.py (calcula desde MatchEvent on-demand)
├── test_helpers/base.py      # BaseTestCase reutilizable
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
│   │   └── index.ts           # API functions para todos los endpoints
│   ├── components/
│   │   ├── layout/Layout.tsx   # Header, Nav, Footer
│   │   └── ui/
│   │       ├── StandingsTable.tsx  # Tabla con colores de zona
│   │       ├── MatchCard.tsx
│   │       ├── PlayerCard.tsx
│   │       └── ClubCard.tsx
│   ├── context/
│   │   └── AuthContext.tsx     # JWT auth (login, logout, profile)
│   ├── pages/
│   │   ├── Home.tsx
│   │   ├── Countries.tsx
│   │   ├── Leagues.tsx
│   │   ├── Seasons.tsx
│   │   ├── Standings.tsx
│   │   ├── Clubs.tsx
│   │   ├── ClubProfile.tsx
│   │   ├── Players.tsx
│   │   ├── PlayerProfile.tsx
│   │   ├── Matches.tsx
│   │   ├── Statistics.tsx
│   │   └── Login.tsx
│   ├── types/index.ts         # TypeScript interfaces
│   ├── App.tsx                 # React Router
│   ├── App.css                 # Dark theme sports UI
│   └── main.tsx
├── vite.config.ts             # Proxy a localhost:8000
├── package.json
└── tsconfig.json
```

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

Seed data disponible via `python manage.py seed_data`:
- 4 users (superadmin, admin_liga, admin_club, player)
- 20 clubs (10 por división)
- 31 players
- 121 partidos
- 665 eventos
- 40 standings

---

## Archivos importantes

| Archivo | Descripción |
|---------|-------------|
| `backend/config/settings/base.py` | Config Django, AUTH_USER_MODEL, REST_FRAMEWORK, JWT |
| `backend/config/settings/development.py` | SQLite para tests, PostgreSQL default |
| `backend/apps/accounts/permissions.py` | 7 clases de permisos custom |
| `backend/apps/standings/services.py` | recalculate_standings, recalculate_all_standings |
| `backend/apps/statistics/services.py` | Player/club statistics, top scorers/assists/mvp |
| `backend/apps/matches/services.py` | Lineup validation, BOT completion, goal consistency |
| `frontend/src/api/client.ts` | Axios + JWT interceptors |
| `frontend/src/context/AuthContext.tsx` | Auth context con JWT |
| `frontend/vite.config.ts` | Vite config con proxy |

---

## Pendiente (Fase 7+)

### Fase 7 — Frontend-Backend Integration
- Conectar páginas del frontend con la API real
- manejo de errores en UI
- Loading states
- Formularios CRUD funcionales
- Navegación condicional según rol

### Fase 8 — Optimization
- Paginación
- Búsqueda/filtros
- Cache de estadísticas
- Optimización de queries

### Fase 9 — Deployment
- Docker/docker-compose
- Variables de entorno
- HTTPS, CORS production
- Static files

### Fase 10 — Documentation
- API docs (DRF Spectacular o similar)
- User guide
- Developer guide

---

*Última actualización: Fase 6 completada, commit 7ab3e69*
