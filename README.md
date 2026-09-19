# EA FC Clubes Pro — Plataforma de Gestión de Ligas

Plataforma web profesional para gestionar competiciones de **EA Sports FC — Clubes Pro**.

## Stack

| Capa | Tecnología |
|------|-----------|
| Backend | Python, Django, Django REST Framework |
| Base de datos | PostgreSQL |
| Frontend | React, TypeScript, Vite |

## Estructura del proyecto

```
ea-fc-platform/
├── backend/
│   ├── config/                    # Configuración Django
│   │   ├── settings/
│   │   │   ├── base.py
│   │   │   ├── development.py
│   │   │   └── production.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── apps/
│   │   ├── accounts/              # Users, roles, permisos, JWT auth
│   │   ├── competitions/          # Countries, Games, Leagues, Seasons, Divisions
│   │   ├── clubs/                 # Clubs, ClubSeason, ClubTitle
│   │   ├── players/               # Players, historial de identidad y clubes
│   │   ├── matches/               # Matchdays, Matches, MatchPlayers, MatchEvents
│   │   ├── standings/             # Standing (derivado), services, zones
│   │   └── statistics/            # Estadísticas derivadas de MatchEvents
│   ├── test_helpers/              # Base de tests reutilizable
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/                   # Axios client + endpoints
│   │   ├── components/            # Layout, UI components
│   │   ├── context/               # AuthContext (JWT)
│   │   ├── pages/                 # Todas las páginas
│   │   ├── types/                 # TypeScript interfaces
│   │   ├── App.tsx
│   │   └── App.css                # Dark theme sports UI
│   ├── vite.config.ts
│   └── package.json
├── .gitignore
├── .env.example
└── README.md
```

## Fases de desarrollo

### Fase 1 — Arquitectura y modelos

- **Configuración modular de settings** (base, development, production)
- **7 apps de Django** con sus modelos (21 modelos)
- **Django Admin** configurado para todos los modelos
- **Migraciones** creadas y aplicadas
- **Base de datos PostgreSQL** `ea_fc_platform` creada

### Fase 2 — Lógica de negocio

- **Standings service**: Recálculo de posiciones desde resultados de partidos
- **Statistics service**: Cálculo de estadísticas on-demand desde MatchEvents
- **Zones service**: Determinación de zonas competitivas (CAMPEÓN, REDUCIDO, PROMOCIÓN, DESCENSO)
- **Match validation**: Validación de alineaciones, BOT, integridad de goles
- **Management commands**: `recalculate_standings`, `generate_fixtures`, `seed_data`
- **Seed data**: 4 users, 20 clubs, 31 players, 121 partidos, 665 eventos, 40 standings

### Fase 3 — API REST

- **Serializers** para todos los modelos (list, detail, create/update)
- **ViewSets** con CRUD completo para las 7 apps
- **Auth endpoints**: login, register, profile, token refresh
- **Statistics endpoints**: top scorers, assists, MVP, player stats
- **Standings recalculate endpoint**

### Fase 4 — Frontend React

- **API client** con Axios + JWT interceptors (auto-refresh)
- **TypeScript types** para todos los modelos
- **AuthContext** con login/logout/profile
- **Layout** con Header, navegación, Footer
- **UI Components**: StandingsTable (colores de zona), MatchCard, PlayerCard, ClubCard, Loading, ErrorMessage
- **12 páginas**: Home, Countries, Leagues, Seasons, Standings, Clubs, ClubProfile, Players, PlayerProfile, Matches, Statistics, Login
- **Dark theme** con estilos deportivos, spinner animado, forms inline, filters
- **Build** pasa sin errores

### Fase 5 — Autenticación y Permisos

- **7 clases de permisos**: IsSuperAdmin, IsAdminLiga, IsAdminClub, IsAdminOrPlayer, IsOwnerOrAdmin, CanManageLeague, CanManageClub
- **Permisos por ViewSet**: lectura pública, escritura según rol
- **Nickname change**: solo SUPERADMIN puede cambiar nicknames
- **Token refresh automático** en el frontend

### Fase 6 — Tests

- **74 tests**, todos pasando
- **6 archivos de tests**:
  - `apps/players/tests.py` (9 tests): creación, nickname único, historial
  - `apps/clubs/tests.py` (8 tests): clubs, club-season, títulos
  - `apps/matches/tests.py` (10 tests): partidos, alineaciones, BOT, eventos
  - `apps/standings/tests.py` (10 tests): recálculo de posiciones, zonas
  - `apps/statistics/tests.py` (8 tests): estadísticas derivadas, rankings
  - `apps/accounts/tests.py` (29 tests): auth, permisos por rol en todos los endpoints

```bash
python manage.py test apps.accounts.tests apps.players.tests apps.clubs.tests apps.matches.tests apps.standings.tests apps.statistics.tests -v 2
```

### Fase 7 — Frontend-Backend Integration

- **API client CRUD**: métodos create, update, delete para todos los recursos
- **Loading states**: componente `Loading` con spinner animado
- **Error handling**: componente `ErrorMessage` con retry button
- **Páginas conectadas con API real**:
  - **Home**: carga seasons, clubs, top scorers desde API
  - **Standings**: tabla de posiciones + botón "Recalcular Tabla" (solo ADMIN_LIGA+)
  - **Clubs**: lista + formulario crear club (solo SUPERADMIN)
  - **ClubProfile**: detalle con títulos y participaciones
  - **Players**: lista + formulario crear jugador (solo SUPERADMIN)
  - **PlayerProfile**: detalle con stats, historial de clubes y nicknames
  - **Matches**: lista con filtro por estado (SCHEDULED/IN_PROGRESS/FINISHED)
  - **Statistics**: tabs Goleadores/Asistencias/MVP
  - **Countries, Leagues, Seasons**: listas con loading/error/empty states
- **Role-based UI**: botones de crear/recalcular visibles solo según rol
- **Role badge** en header del Layout
- **Filtros**: select de estado en Matches
- **Formularios inline**: crear clubs y jugadores desde la lista
- **Empty states**: mensajes cuando no hay datos

---

## Modelo de datos

### Jerarquía de competiciones

```
Country → League → Season → Division → ClubSeason → Match → MatchPlayer → MatchEvent
            ↑
           Game
```

### Entidades principales

| Entidad | Descripción |
|---------|-------------|
| `Country` | País (Argentina, Uruguay, etc.) |
| `Game` | Edición del juego (EA FC 26, EA FC 27) |
| `League` | Liga dentro de un país |
| `Season` | Temporada dentro de una liga y juego |
| `Division` | División dentro de una temporada |
| `CompetitionFormat` | Formato (liga, doble, personalizado) |
| `Club` | Club (entidad histórica estable) |
| `ClubSeason` | Participación de un club en una temporada/división |
| `ClubTitle` | Título otorgado manualmente por un admin |
| `Player` | Jugador (identidad interna estable) |
| `PlayerIdentityHistory` | Historial de nicknames |
| `PlayerClubHistory` | Historial de clubes del jugador |
| `Matchday` | Jornada dentro de una temporada/división |
| `Match` | Partido entre dos clubes |
| `MatchPlayer` | Jugador que participó en un partido |
| `MatchEvent` | Evento durante un partido (gol, asistencia, tarjeta, etc.) |
| `Standing` | Posición en la tabla (dato derivado) |
| `User` | Usuario de la plataforma con rol |
| `LeagueAdmin` | Administrador asignado a una liga |
| `ClubAdmin` | Administrador asignado a un club |

### Datos derivados vs fuente de verdad

**Fuente de verdad:** Player, Club, Season, Match, MatchPlayer, MatchEvent

**Datos derivados:** Standing (se recalcula desde Matches), Estadísticas (se calculan desde MatchEvent)

---

## Roles y permisos

| Rol | Lectura | Escritura |
|-----|---------|-----------|
| `SUPERADMIN` | Todo | Todo |
| `ADMIN_LIGA` | Todo | Ligas asignadas, partidos, standings |
| `ADMIN_CLUB` | Todo | Su club |
| `PLAYER` | Todo | Solo su perfil (lectura) |
| `USER` | Todo | Ninguno |

### Permisos por recurso

| Recurso | Lectura | Escritura |
|---------|---------|-----------|
| Countries, Games, Formats | Público | SUPERADMIN |
| Leagues, Seasons, Divisions | Público | ADMIN_LIGA |
| Clubs | Público | CanManageClub |
| Players | Público | Solo nickname: SUPERADMIN |
| Matches, Events | Público | ADMIN_LIGA |
| Standings | Público | Recalculate: ADMIN_LIGA |
| Statistics | Público | — |

---

## API REST

### Autenticación

```bash
POST /api/auth/login/          # Login → {access, refresh}
POST /api/auth/register/       # Registro
GET  /api/auth/profile/        # Perfil del usuario autenticado
POST /api/token/refresh/       # Refresh token
```

### Endpoints públicos

```bash
GET /api/countries/
GET /api/games/
GET /api/leagues/
GET /api/seasons/
GET /api/divisions/
GET /api/clubs/
GET /api/players/
GET /api/matches/
GET /api/standings/
GET /api/statistics/top_scorers/?season_id=1
GET /api/statistics/top_assists/?season_id=1
GET /api/statistics/top_mvp/?season_id=1
GET /api/statistics/player/?player_id=1
GET /api/statistics/player_history/?player_id=1
```

### Endpoints administrativos

```bash
GET/POST/PUT/PATCH/DELETE /api/clubs/
GET/POST/PUT/PATCH/DELETE /api/players/
GET/POST/PUT/PATCH/DELETE /api/matches/
GET/POST/PUT/PATCH/DELETE /api/match-events/
POST /api/standings/recalculate/   {"season_id": 1, "division_id": 1}
```

---

## Commands de gestión

```bash
python manage.py recalculate_standings --season 1 --division 1
python manage.py recalculate_standings --all
python manage.py generate_fixtures --season 1 --division 1
python manage.py seed_data
```

---

## Instalación

```bash
# Backend
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data
python manage.py createsuperuser
python manage.py runserver

# Tests
python manage.py test apps.accounts.tests apps.players.tests apps.clubs.tests apps.matches.tests apps.standings.tests apps.statistics.tests -v 2

# Frontend
cd frontend
npm install
npm run dev
```

---

## Decisiones arquitectónicas clave

1. **Player tiene ID interno estable**: El nickname es externo y puede cambiar, pero el ID nunca cambia
2. **MatchEvent es una sola entidad**: No tablas separadas para goles, asistencias, tarjetas
3. **OWN_GOAL**: El gol se computa para el equipo rival, el evento queda registrado en el jugador que lo hizo
4. **Standing es derivado**: Se recalcula desde los partidos, nunca se edita manualmente
5. **Estadísticas son derivadas**: Se calculan desde MatchEvent on-demand
6. **BOT**: No es un Player global, solo un MatchPlayer con player=NULL
7. **Ascensos/descensos no son automáticos**: El administrador otorga títulos y mueve clubes manualmente
8. **Platform es opcional**: No divide ligas ni tablas (EA FC tiene crossplay)
9. **CompetitionFormat**: Configurable por Season (round robin, doble, personalizado)
10. **Zonas de tabla**: Configurables por Division (campeón, reducido, promoción, descenso)
