# EA FC Clubes Pro — Plataforma de Gestión de Ligas

Plataforma web profesional para gestionar competiciones de **EA Sports FC — Clubes Pro**.

## Stack

| Capa | Tecnología |
|------|-----------|
| Backend | Python, Django, Django REST Framework, django-filter |
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
│   │   ├── players/               # Players, historial de identidad y clubes, Transfer
│   │   ├── matches/               # Matchdays, Matches, MatchPlayers, MatchEvents
│   │   ├── standings/             # Standing (derivado), services, zones, seed/fix commands
│   │   └── statistics/            # Estadísticas derivadas de MatchEvents
│   ├── test_helpers/              # Base de tests reutilizable
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/                   # Axios client + endpoints
│   │   ├── components/            # Layout, UI components
│   │   │   ├── layout/Layout.tsx
│   │   │   └── ui/
│   │   │       ├── StandingsTable.tsx
│   │   │       ├── MatchCard.tsx
│   │   │       ├── PlayerCard.tsx
│   │   │       ├── ClubCard.tsx
│   │   │       ├── Loading.tsx
│   │   │       ├── ErrorMessage.tsx
│   │   │       ├── Pagination.tsx
│   │   │       └── SearchBar.tsx
│   │   ├── context/               # AuthContext (JWT)
│   │   ├── hooks/                 # useCanEdit (SUPERADMIN/ADMIN_LIGA)
│   │   ├── pages/                 # Todas las páginas (14)
│   │   ├── types/                 # TypeScript interfaces
│   │   ├── App.tsx
│   │   └── App.css                # Matchday Broadcast theme
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
- **UI Components**: StandingsTable (colores de zona), MatchCard (link al detalle), PlayerCard, ClubCard, Loading, ErrorMessage
- **14 páginas**: Home, Countries, Leagues, Seasons, Standings, Clubs, ClubProfile, Players, PlayerProfile, Matches, MatchDetail, Transfers, Statistics, Login
- **Tema Matchday Broadcast**: Barlow Condensed + IBM Plex Sans, accent verde césped `#22c55e`
- **Build** pasa sin errores

### Fase 5 — Autenticación y Permisos

- **7 clases de permisos**: IsSuperAdmin, IsAdminLiga, IsAdminClub, IsAdminOrPlayer, IsOwnerOrAdmin, CanManageLeague, CanManageClub
- **Permisos por ViewSet**: lectura pública, escritura según rol
- **Nickname change**: SUPERADMIN y ADMIN_LIGA pueden cambiar nicknames (IsAdminLiga)
- **Token refresh automático** en el frontend

### Fase 6 — Tests

- **139 tests**, todos pasando
- **6 archivos de tests**:
  - `apps/players/tests.py` (20 tests): creación, nicknames, historial, mercado de pases
  - `apps/clubs/tests.py` (11 tests): clubs, club-season, títulos (CRUD API)
  - `apps/matches/tests.py` (18 tests): partidos, alineaciones, BOT, eventos, permisos, auto-recalc
  - `apps/standings/tests.py` (16 tests): recálculo de posiciones, zonas por división
  - `apps/statistics/tests.py` (12 tests): estadísticas derivadas, rankings
  - `apps/accounts/tests.py` (29 tests): auth, permisos por rol en todos los endpoints

```bash
python manage.py test
```

### Fase 7 — Frontend-Backend Integration

- **API client CRUD**: métodos create, update, delete para todos los recursos
- **Loading states**: componente `Loading` con spinner animado
- **Error handling**: componente `ErrorMessage` con retry button
- **Páginas conectadas con API real**:
  - **Home**: carga seasons, clubs, top scorers desde API
  - **Standings**: tabla de posiciones + botón "Recalcular Tabla" (solo ADMIN_LIGA+)
  - **Clubs**: lista + formulario crear club (SUPERADMIN/ADMIN_LIGA)
  - **ClubProfile**: detalle con títulos y participaciones
  - **Players**: lista + formulario crear jugador (SUPERADMIN/ADMIN_LIGA)
  - **PlayerProfile**: detalle con stats, historial de clubes y nicknames
  - **Matches**: lista con filtro por estado (SCHEDULED/IN_PROGRESS/FINISHED)
  - **Statistics**: tabs Goleadores/Asistencias/MVP
  - **Countries, Leagues, Seasons**: listas con loading/error/empty states
- **Role-based UI**: botones de crear/recalcular visibles solo según rol
- **Role badge** en header del Layout
- **Filtros**: select de estado en Matches
- **Formularios inline**: crear clubs y jugadores desde la lista
- **Empty states**: mensajes cuando no hay datos

### Fase 8 — Optimization

- **DRF Pagination**: configurada en todos los ViewSets (page 1-25 por defecto)
- **django-filter**: búsqueda y filtros en todas las entidades
  - Clubs: `?country=1&is_active=true&search=boca`
  - Players: `?platform=PC&search=jugador`
  - Matches: `?season=1&division=1&status=FINISHED`
  - Standings: `?season=1&division=1`
  - Leagues: `?country=1&search=liga`
  - Seasons: `?league=1&status=ACTIVE`
- **Cache**: `LocMemCache` con timeout 300s para standings, 600s para statistics
- **GZip Middleware**: compresión de respuestas HTTP
- **Frontend Pagination**: componente `Pagination` con navegación entre páginas
- **Frontend SearchBar**: componente `SearchBar` con búsqueda en tiempo real
- **Páginas con búsqueda**: Clubs, Players, Matches, Countries, Leagues, Seasons

### Fase 9 — Deployment

- **Render**: Backend desplegado como Web Service con PostgreSQL manejada
  - `render.yaml`: infraestructura como código (app + database)
  - `runtime.txt`: Python 3.12 para Render
  - `gunicorn`: servidor WSGI de producción
  - `whitenoise`: sirve archivos estáticos sin nginx
  - `collectstatic`: genera archivos estáticos optimizados
- **Cloudflare Pages**: Frontend estático con SPA routing
  - Variable de entorno `VITE_API_URL` para URL del backend
  - Proxy API configurado en `client.ts`
- **Variables de entorno**: configuradas en Render dashboard
- **Health Check**: `GET /api/health/` → `{"status": "ok", "db": "ok"}`
- **HTTPS**: manejado por Render (backend) y Cloudflare (frontend)
- **CORS**: configurado para dominios Cloudflare Pages

```bash
# Deploy backend: Push a GitHub → Render deploy automático
# Deploy frontend: Push a GitHub → Cloudflare Pages deploy automático
```

### Fase 10 — Documentation

- **drf-spectacular**: documentación interactiva de la API
  - **Swagger UI**: `/api/docs/` — probar endpoints en el navegador
  - **ReDoc**: `/api/redoc/` — documentación completa y elegante
  - **OpenAPI Schema**: `/api/schema/` — schema JSON/YAML descargable
- **Tags en ViewSets**: 22 ViewSets organizados por categoría (Auth, Users, Countries, Games, Leagues, Seasons, Clubs, Players, Matches, Standings, Statistics)
- **USER_GUIDE.md**: guía de uso para usuarios de la plataforma
- **DEVELOPER_GUIDE.md**: guía de desarrollo para programadores

### Fase 11 — Datos y zonas (S2 activa)

- **Zonas por división** corregidas: Primera (p1 CAMPEÓN, p19 PROMOCIÓN, p20 DESCENSO), Segunda↓ (+ REDUCIDO p2-9)
- **Títulos S1 corregidos** (Rosario United AR, Peñarol UY)
- **Transiciones S1→S2**: descenso directo p20, ascenso del campeón de Segunda; Promoción manual
- **S2 ACTIVE**: 11 matchdays por división (J1-J10 FINISHED, J11 SCHEDULED), fixtures regenerados
- **Comandos idempotentes**: `fix_season_transitions`, `seed_s2`

### Fase 12 — Mercado de pases (v1)

- **Modelo `Transfer`**: player, from_club_season, to_club_season, date, registered_by (migración `0003_transfer`)
- **API `/api/transfers/`**: CRUD, escritura ADMIN_LIGA, DELETE revierte la última transferencia
- **160 transferencias backfilleadas** desde los movimientos S1→S2
- **Página `/transfers`**: alta/baja, búsqueda de jugadores, filtro por temporada

### Fase 13 — Edición admin inline

- **`MatchDetail` (`/matches/:id`)**: scoreboard, editar resultado/estado/fecha/hora, alineaciones (agregar/quitar), CRUD de eventos — con **recálculo automático de posiciones** en el backend (`_refresh_derived`)
- **Edición inline en página**: ClubProfile (club + títulos CRUD), PlayerProfile (nickname/posición/plataforma/país), Seasons (estado/nombre)
- **Hook `useCanEdit`**: unifica la visibilidad de controles de edición (SUPERADMIN/ADMIN_LIGA)
- **Fixes**: links a clubes usaban id de club_season (ahora id de club), ruta `/standings` sin temporada, `ClubTitleViewSet` sin serializer, PATCH parcial de partidos, loop infinito por ordering de `MatchPlayer`

### Fase 14 — Rate limits (429)

- **Sin throttles globales**: se eliminaron `AnonRateThrottle`/`UserRateThrottle` por defecto (rompían la navegación con 429)
- **Scope `auth` 10/min por IP**: solo en `login`, `register` y `token/refresh` (anti fuerza bruta)
- **Retry en frontend**: el axios client reintenta 1 vez las respuestas 429 esperando `Retry-After`
- Verificado: 150 GETs anónimos → 150×200; 12 logins → 10×200 + 2×429

### Fase 15 — Rendimiento por partido (MatchPerformance + OCR + Docker)

- **Modelo `MatchPerformance`** (OneToOne a `MatchPlayer`): rating + 18 campos por jugador por partido; el modelo rechaza BOT (`player=NULL`); no toca Match/MatchPlayer/MatchEvent
- **API**: `GET/POST /api/match-performances/`, `POST /api/matches/{id}/performances/batch/` (upsert con auto-create validado contra `PlayerClubHistory`), `GET /api/players/{id}/performances/` (historial público); escritura solo ADMIN_LIGA
- **OCR**: `POST /api/matches/{id}/performances/analyze/` — pytesseract + Pillow, port de FIFASTATS (recortes de paneles, binarizado, `spa`+fallback `eng`, fix rating 6↔9 y O→0, Levenshtein vs plantel real, concurrencia 2, ≤30 imgs ≤20MB); imágenes descartadas tras analizar
- **Docker en Render**: `Dockerfile` raíz (`python:3.12-slim` + `tesseract-ocr` + `tesseract-ocr-spa`), `render.yaml` con `runtime: docker` y `preDeployCommand: python manage.py migrate`; local: Tesseract vía `winget UB-Mannheim.TesseractOCR`
- **UI**: "Rendimiento detallado" en MatchDetail (fila por jugador, expand para editar los 18 campos) + bloque OCR (seleccionar capturas → Analizar → verificar jugador sugerido → Guardar); "Partidos y rendimiento" en PlayerProfile

### Fase 16 — Seed de rendimiento + fixes

- **`seed_performances`**: ~34,800 rendimientos generados; goals/assists derivados de los `MatchEvent` reales (consistente con rankings), stats restantes realistas por posición; idempotente, determinista (`--seed`, default 42), `--reset` para regenerar
- **Clubes**: `clubsApi.list` pagina hasta traer todos los clubs (antes se cortaba en la página de 25/20 del backend); el hero de Home ahora dice "Equipos en liga" (40 = filas de la tabla de la temporada destacada, semántica correcta)
- **Credenciales de desarrollo** documentadas en `PROJECT_CONTEXT.md` (4 usuarios, todos `admin123`)

---

## Modelo de datos

### Jerarquía de competiciones

```
Country → League → Season → Division → ClubSeason → Match → MatchPlayer → MatchEvent / MatchPerformance
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
| `Player` | Jugador (identidad interna estable, con position ARQ/DEF/MED/DEL) |
| `PlayerIdentityHistory` | Historial de nicknames |
| `PlayerClubHistory` | Historial de clubes del jugador |
| `Transfer` | Movimiento de mercado entre clubes (registro manual del admin) |
| `Matchday` | Jornada dentro de una temporada/división |
| `Match` | Partido entre dos clubes |
| `MatchPlayer` | Jugador que participó en un partido |
| `MatchEvent` | Evento durante un partido (gol, asistencia, tarjeta, etc.) |
| `MatchPerformance` | Rendimiento detallado por jugador por partido (rating + 18 stats; analítica, no afecta standings) |
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
| ClubSeason, ClubTitle | Público | ADMIN_LIGA |
| Players, IdentityHistory, ClubHistory, Transfers | Público | ADMIN_LIGA |
| Matches, MatchPlayers, MatchEvents | Público | ADMIN_LIGA |
| Standings | Público | Recalculate: ADMIN_LIGA |
| Statistics | Público | — |

---

## API REST

### Health Check

```bash
GET /api/health/              # Health check → {"status": "ok", "db": "ok"}
```

### Documentación de la API

```bash
GET /api/docs/                # Swagger UI (interfaz interactiva)
GET /api/redoc/               # ReDoc (documentación elegante)
GET /api/schema/              # OpenAPI schema (JSON/YAML)
```

### Autenticación

```bash
POST /api/auth/login/          # Login → {access, refresh}   (throttle 10/min)
POST /api/auth/register/       # Registro                    (throttle 10/min)
GET  /api/auth/profile/        # Perfil del usuario autenticado
POST /api/token/refresh/       # Refresh token               (throttle 10/min)
```

### Endpoints públicos

```bash
GET /api/countries/?search=argentina
GET /api/games/
GET /api/leagues/?country=1&search=liga
GET /api/seasons/?league=1&status=ACTIVE
GET /api/divisions/
GET /api/clubs/?country=1&is_active=true&search=boca
GET /api/players/?platform=PC&search=jugador
GET /api/matches/?season=1&division=1&status=FINISHED
GET /api/standings/?season=1&division=1
GET /api/statistics/top_scorers/?season_id=1&division_id=1&limit=10
GET /api/statistics/top_assists/?season_id=1&division_id=1&limit=10
GET /api/statistics/top_mvp/?season_id=1&division_id=1&limit=10
GET /api/statistics/player/?player_id=1&season_id=1
GET /api/statistics/player_history/?player_id=1
GET /api/match-performances/?match=1&match_player=2
GET /api/players/1/performances/?season_id=1
```

### Endpoints administrativos

```bash
GET/POST/PUT/PATCH/DELETE /api/clubs/
GET/POST/PUT/PATCH/DELETE /api/players/
GET/POST/PUT/PATCH/DELETE /api/matches/
GET/POST/PUT/PATCH/DELETE /api/match-events/
GET/POST/PUT/PATCH/DELETE /api/match-players/
GET/POST/PUT/PATCH/DELETE /api/club-titles/
GET/POST/PUT/PATCH/DELETE /api/transfers/
GET/POST/PUT/PATCH/DELETE /api/match-performances/
POST /api/matches/{id}/performances/batch/     # upsert rendimiento por jugador
POST /api/matches/{id}/performances/analyze/   # OCR multipart "images", ≤30 (no persiste)
PATCH /api/seasons/{id}/            # actualizar temporada (estado, nombre)
POST /api/standings/recalculate/   {"season_id": 1, "division_id": 1}
```

---

## Commands de gestión

```bash
python manage.py recalculate_standings --season 1 --division 1
python manage.py recalculate_standings --all
python manage.py generate_fixtures --season 1 --division 1
python manage.py seed_data        # Dataset completo (~34K registros, 2 países, S2 ACTIVE)
python manage.py seed_dev         # Dataset chico (~1.2K registros, 1 país)
python manage.py seed_s2          # Upgrade idempotente de un seed viejo a S2 ACTIVE
python manage.py fix_season_transitions  # Zonas, títulos S1, transiciones S1→S2, regenera S2
python manage.py seed_performances       # Rendimientos por jugador/partido (idempotente, --reset, --seed)
python manage.py flush            # Limpiar base de datos
```

---

## Instalación

```bash
# Backend
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data        # O seed_dev para desarrollo rápido
python manage.py seed_performances  # Opcional: rendimiento por jugador/partido
python manage.py createsuperuser
python manage.py runserver

# Tests
python manage.py test

# Frontend
cd frontend
npm install
npm run dev

# O desde la raíz (arranca backend + frontend juntos)
npm install
npm run dev
```

### Despliegue en Render

```bash
# 1. Crear cuenta en Render (https://render.com)
# 2. Conectar repositorio de GitHub
# 3. Render detecta render.yaml automáticamente
# 4. Configurar variables de entorno en dashboard:
#    - SECRET_KEY: generar uno seguro
#    - CORS_ALLOWED_ORIGINS: https://tu-proyecto.pages.dev
# 5. Deploy automático al hacer push a GitHub
```

### Despliegue en Cloudflare Pages

```bash
# 1. Crear cuenta en Cloudflare (https://pages.cloudflare.com)
# 2. Conectar repositorio de GitHub
# 3. Configurar build:
#    - Build command: cd frontend && npm install && npm run build
#    - Build output: frontend/dist
# 4. Agregar variable de entorno:
#    - VITE_API_URL: https://tu-backend.onrender.com/api
# 5. Deploy automático al hacer push a GitHub
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
11. **Edición inline por página**: no hay panel admin central; cada página (partido, club, jugador, temporada) expone sus controles de edición según `useCanEdit`
12. **Recálculo automático de posiciones**: toda mutación de Match/MatchPlayer/MatchEvent dispara `_refresh_derived` → `recalculate_standings` + `cache.clear()`
13. **Rate limit solo en auth**: sin throttles globales; `login/register/refresh` limitados a 10/min por IP; el frontend reintenta 429 una vez
14. **Rendimiento por partido**: `MatchPerformance` (19 stats) + carga manual y por OCR (pytesseract, port de FIFASTATS) + seed local consistente con los MatchEvent

---

## Proximamente

Ver `PROXIMOS_CAMBIOS.md` para el plan detallado:

- **Estadísticas detalladas por partido** — **Fase 1 ✅ (`1ab0e2f`) y Fase 2 ✅ (`6307d43`) implementadas** (PROXIMOS_CAMBIOS.md #4): modelo `MatchPerformance`, OCR con `pytesseract` + Pillow (port de FIFASTATS) con verificación humana antes de guardar, backend con Docker en Render. **Pendiente: verificar el primer deploy en Render y probar OCR con capturas reales; Fase 3 (analítica/gráficos) sin arrancar**
- **Mercado de pases v2** — Free agents, invitaciones a clubes, ventana de pases controlada por admin (v1 de registro manual ya implementada)
- **Reducido/Promoción** — Generar las llaves del Reducido y la Promoción como partidos
- **Brasil** — Tercer país con la misma estructura de ligas
