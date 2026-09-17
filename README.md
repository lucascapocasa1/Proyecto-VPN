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
│   │   │   ├── base.py            # Configuración base
│   │   │   ├── development.py     # Entorno de desarrollo
│   │   │   └── production.py      # Entorno de producción
│   │   ├── urls.py                # URLs principales
│   │   └── wsgi.py
│   ├── apps/
│   │   ├── accounts/              # Users, roles, permisos
│   │   ├── competitions/          # Countries, Games, Leagues, Seasons, Divisions
│   │   ├── clubs/                 # Clubs, ClubSeason, ClubTitle
│   │   ├── players/               # Players, historial de identidad y clubes
│   │   ├── matches/               # Matchdays, Matches, MatchPlayers, MatchEvents
│   │   ├── standings/             # Standings (derivado), services, zones
│   │   └── statistics/            # Estadísticas derivadas de MatchEvents
│   ├── management/commands/       # Commands obsoletos (verificados)
│   ├── manage.py
│   └── .env
├── frontend/                      # React + TypeScript + Vite (por implementar)
├── .gitignore
├── .env.example
└── README.md
```

## Fases de desarrollo

### Fase 1 — Arquitectura y modelos

Se creó la estructura completa del proyecto backend con Django y PostgreSQL:

- **Configuración modular de settings** (base, development, production)
- **6 apps de Django** con sus modelos:
  - `accounts`: User (con roles), LeagueAdmin, ClubAdmin
  - `competitions`: Country, Game, CompetitionFormat, League, Season, Division
  - `clubs`: Club, ClubSeason, ClubTitle
  - `players`: Player, PlayerIdentityHistory, PlayerClubHistory
  - `matches`: Matchday, Match, MatchPlayer, MatchEvent
  - `standings`: Standing
- **Django Admin** configurado para todos los modelos (21 modelos registrados)
- **Migraciones** creadas y aplicadas

### Fase 2 — Lógica de negocio

Se implementaron los services y management commands:

- **Standings service** (`apps/standings/services.py`): Recálculo de posiciones a partir de resultados de partidos
- **Statistics service** (`apps/statistics/services.py`): Cálculo de estadísticas de jugadores y clubes desde MatchEvents
- **Zones service** (`apps/standings/zones.py`): Determinación de zonas competitivas (CAMPEÓN, REDUCIDO, PROMOCIÓN, DESCENSO)
- **Match validation service** (`apps/matches/services.py`): Validación de alineaciones, BOT, integridad
- **Management commands**:
  - `recalculate_standings`: Recalcula posiciones para una temporada/división o todas las activas
  - `generate_fixtures`: Genera fixtures automáticamente (round robin, double round robin)
  - `seed_data`: Crea datos de prueba completos

### Fase 3 — API REST

Se implementó la API REST completa con Django REST Framework:

- **Serializers** para todos los modelos (list, detail, create/update)
- **ViewSets** con CRUD completo
- **Endpoints de autenticación**: login, register, profile, token refresh
- **Endpoints públicos**: standings, statistics, top scorers, assists, MVP
- **Endpoints administrativos**: recalculate standings

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

**Fuente de verdad:**
- Player, Club, Season, Match, MatchPlayer, MatchEvent

**Datos derivados:**
- Standing (se recalcula desde Matches)
- Estadísticas (se calculan desde MatchEvent)

---

## Roles y permisos

| Rol | Descripción |
|-----|-------------|
| `SUPERADMIN` | Acceso total al sistema |
| `ADMIN_LIGA` | Gestiona competiciones asignadas |
| `ADMIN_CLUB` | Gestiona su club y plantilla |
| `PLAYER` | Consulta información, gestiona su perfil |
| `USER` | Consulta información pública |

---

## API REST

### Autenticación

```bash
# Login
POST /api/auth/login/
{"username": "admin", "password": "admin123"}

# Register
POST /api/auth/register/
{"username": "newuser", "email": "user@test.com", "password": "pass1234", "role": "USER"}

# Profile
GET /api/auth/profile/
Authorization: Bearer <token>

# Refresh token
POST /api/token/refresh/
{"refresh": "<refresh_token>"}
```

### Endpoints públicos (no requieren autenticación)

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

### Endpoints administrativos (requieren autenticación)

```bash
# CRUD completo
GET/POST/PUT/PATCH/DELETE /api/clubs/
GET/POST/PUT/PATCH/DELETE /api/players/
GET/POST/PUT/PATCH/DELETE /api/matches/
GET/POST/PUT/PATCH/DELETE /api/match-events/
# ... etc

# Recalcular standings
POST /api/standings/recalculate/
{"season_id": 1, "division_id": 1}
```

---

## Commands de gestión

```bash
# Recalcular posiciones
python manage.py recalculate_standings --season 1 --division 1
python manage.py recalculate_standings --all

# Generar fixtures
python manage.py generate_fixtures --season 1 --division 1
python manage.py generate_fixtures --season 1 --division 1 --dry-run

# Crear datos de prueba
python manage.py seed_data
```

---

## Configuración

### Variables de entorno (.env)

```bash
SECRET_KEY=tu-clave-secreta
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=ea_fc_platform
DB_USER=postgres
DB_PASSWORD=tu-password
DB_HOST=localhost
DB_PORT=5432

CORS_ALLOWED_ORIGINS=http://localhost:5173
```

### Instalación

```bash
# Backend
cd backend
pip install -r requirements.txt  # o instalar manualmente
python manage.py migrate
python manage.py seed_data  # datos de prueba
python manage.py createsuperuser
python manage.py runserver

# Frontend (por implementar)
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
