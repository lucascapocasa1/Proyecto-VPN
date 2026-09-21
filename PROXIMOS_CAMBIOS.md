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
├── Temporada 2 (FINISHED)
│   ├── Primera Division (20 equipos)
│   └── Segunda Division (20 equipos)
└── Temporada 3 (UPCOMING, sin partidos)
    ├── Primera Division (20 equipos, armada por admin)
    └── Segunda Division (20 equipos)
```

### Zonas por division

| Division | Pos 1 | Pos 2-9 | Pos 19 | Pos 20 |
|----------|-------|---------|--------|--------|
| Primera | CAMPEON | - | PROMOCION | DESCENSO |
| Segunda | CAMPEON (asciende directo) | REDUCIDO | - | - |

### Formato de partidos

- **Liga**: round-robin simple, 19 partidos por equipo, cancha neutral (sin ida/vuelta)
- **Reducido Segunda**: 2vs9, 3vs8, 4vs7, 5vs6, semifinales, final (ida y vuelta en cada ronda)
- **Promocion**: Pos 19 Primera vs Campeon Reducido Segunda (ida y vuelta)
- Sin penales, todos los partidos se resuelven en tiempo regular

### Ascensos/descensos entre temporadas

- Manual por el admin (no automatico)
- La temporada 3 muestra los equipos ya posicionados por el admin

### Jugadores

- 15 por equipo (2 ARQ, 4 DEF, 5 MED, 4 DEL)
- Maximo 3 extranjeros por equipo
- Nacionalidades mezcladas (mayoria del pais local)
- Estadisticas realistas por posicion

### Estadisticas por posicion

| Pos | Goles/partido | Asistencias/partido | Amarillas | Rojas |
|-----|--------------|--------------------|-----------|-------|
| ARQ | 0.01 | 0.02 | 2-5 | 0-1 |
| DEF | 0.05 | 0.08 | 5-10 | 0-2 |
| MED | 0.12 | 0.15 | 4-8 | 0-1 |
| DEL | 0.35 | 0.08 | 3-6 | 0-1 |

### Volumen final (2 paises, S1 FINISHED + S2 UPCOMING)

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
| MatchEvents | ~7,500 | ~7,500 | ~15,000 |
| Standings | 40 | 40 | 80 |
| **Total** | | | **~34,354** |

### Archivos creados/modificados

- `apps/players/models.py` — Campo `position` agregado (ARQ/DEF/MED/DEL)
- `apps/players/migrations/0002_player_position.py` — Migración creada
- `apps/standings/management/commands/seed_data.py` — Reescrito (dataset completo)
- `apps/standings/management/commands/seed_dev.py` — Creado (dataset chico para dev)

### Estado

✅ Implementado y verificado

---

## 2. Mercado de pases

### Descripcion

Sistema de transferencias donde jugadores sin club aparecen automaticamente en el mercado. Los admin de club pueden enviar invitaciones. El admin general controla el periodo de fichajes.

### Modelos

#### Modificar Player — agregar posicion

```python
position = models.CharField(
    max_length=3,
    choices=[
        ("ARQ", "Arquero"),
        ("DEF", "Defensor"),
        ("MED", "Mediocampista"),
        ("DEL", "Delantero"),
    ],
    null=True, blank=True,
)
```

#### Nuevo modelo Transfer

```python
class Transfer(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pendiente"
        ACCEPTED = "ACCEPTED", "Aceptada"
        REJECTED = "REJECTED", "Rechazada"
        EXPIRED = "EXPIRED", "Expirada"
        CANCELLED = "CANCELLED", "Cancelada"

    player = ForeignKey(Player, related_name="transfers")
    offering_club = ForeignKey(ClubSeason, related_name="transfer_offers")
    season = ForeignKey(Season, related_name="transfers")
    message = TextField(blank=True)
    status = CharField(default=Status.PENDING)
    expires_at = DateTimeField()  # created_at + 24h
    created_at = DateTimeField(auto_now_add=True)
    responded_at = DateTimeField(null=True, blank=True)

    unique_together = ["player", "offering_club", "season"]
```

#### Modificar Season — ventana de pases

```python
transfer_window_open = BooleanField(default=False)
```

### Logica de negocio

- **Free agent**: jugador sin PlayerClubHistory con left_at=None en la temporada activa
- **Aceptacion**: al aceptar, se cancelan las demas invitaciones PENDING del jugador en esa temporada y se crea PlayerClubHistory
- **Expiracion**: invitaciones expiran a las 24h, vuelven al mercado
- **Multiples ofertas**: un jugador puede tener varias ofertas pendientes a la vez

### Endpoints

| Metodo | Endpoint | Descripcion | Permisos |
|--------|----------|-------------|----------|
| GET | `/api/transfer-market/` | Listar free agents con stats | Publico |
| POST | `/api/transfers/` | Enviar invitacion | ADMIN_CLUB |
| GET | `/api/transfers/` | Ver mis invitaciones | Autenticado |
| PUT | `/api/transfers/{id}/accept/` | Aceptar invitacion | PLAYER |
| PUT | `/api/transfers/{id}/reject/` | Rechazar invitacion | PLAYER |
| POST | `/api/seasons/{id}/open-transfer-window/` | Abrir ventana | ADMIN_LIGA |
| POST | `/api/seasons/{id}/close-transfer-window/` | Cerrar ventana | ADMIN_LIGA |

### Frontend — Pagina /transfer-market

- Filtros: posicion (ARQ/DEF/MED/DEL), busqueda por nickname
- Ordenamiento: goles, asistencias, MVP, amarillas, rojas
- Cards con stats resumidas
- Boton "Invitar" (solo ADMIN_CLUB + ventana abierta)
- Modal de invitacion (mensaje opcional)

### Archivos a crear/modificar

- **Nueva app**: `apps/transfers/` (models, serializers, views, urls, admin)
- `apps/players/models.py` — campo position
- `apps/players/serializers.py` — incluir position
- `apps/competitions/models.py` — transfer_window_open en Season
- `apps/competitions/serializers.py` — incluir campo
- `apps/competitions/views.py` — acciones open/close transfer window
- `apps/statistics/services.py` — funcion get_market_players()
- `config/urls.py` — incluir URLs de transfers
- `config/settings/base.py` — agregar apps.transfers
- `frontend/src/pages/TransferMarket.tsx` — nueva pagina
- `frontend/src/api/index.ts` — endpoints del mercado
- `frontend/src/App.tsx` — ruta /transfer-market

### Estado

Aprobado — implementar despues de la base de datos grande

---

## 3. Brasil (futuro)

### Descripcion

Agregar Brasil como tercer pais con la misma logica (2 divisiones, 20 equipos cada una, playoffs, etc.)

### Estado

Pendiente — agregar cuando la base de datos de 2 paises funcione bien

---

## 4. Carga de estadisticas de partidos

### Descripcion

Sistema para cargar las estadisticas de cada partido (goles, asistencias, tarjetas, MVP). Hay dos opciones posibles.

### Opcion A — Carga manual (seleccionada por ahora)

**Flujo:**
1. El capitan del equipo graba el video de la pestaña "Rendimiento" del partido
2. Sube el video a YouTube y comparte el link
3. El admin de la division carga manualmente: goles, asistencias, tarjetas y MVP

**Ventajas:**
- Sin dependencias tecnologicas额外
- Flujo conocido y confiable
- Menos puntos de fallo
- Datos suficientes para standings y rankings

**Desventajas:**
- Menos datos (solo lo esencial)
- Dependiente del admin

### Opcion B — Carga via OCR (futuro)

**Flujo:**
1. El capitan sube un screenshot de la pantalla "Rendimiento"
2. El sistema parsea la imagen con OCR y extrae todas las estadisticas
3. El admin verifica y corrige si es necesario
4. Se guardan los datos

**Tecnologias existentes:**
- Proyecto: FIFASTATS (https://github.com/lucascapocasa1/FIFASTATS---Al-Yateh)
- Backend: Node.js, Express, PostgreSQL
- OCR: Tesseract.js + Sharp (image processing)
- Frontend: Chart.js (dashboards, radar charts, comparaciones)

**Integracion con Django:**
- Opcion 1: Servicio Node.js separado (puerto diferente)
- Opcion 2: Reescribir OCR en Python con pytesseract + Pillow
- Opcion 3: Microservicio Docker con el proyecto FIFASTATS

**Ventajas:**
- Mas datos (goles, asistencias, pases, rating, km, etc.)
- Menos carga manual
- Dashboards y graficos comparativos

**Desventajas:**
- Complejidad de integracion
- Errores de OCR que requieren verificacion
- Mas dependencias

### Estado

Opcion A seleccionada. Opcion B pendiente para futuro.

### Archivos a crear/modificar (Opcion A)

- `apps/matches/views.py` — Endpoint para cargar stats de un partido
- `apps/matches/serializers.py` — Serializer para carga de stats
- `frontend/src/pages/MatchDetail.tsx` — Formulario de carga de stats
- `apps/statistics/services.py` — Recalcular stats despues de cargar eventos
