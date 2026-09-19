# Guia de Usuario — EA FC Clubes Pro

Plataforma web para gestionar ligas competitivas de **EA Sports FC — Clubes Pro**.

## Inicio de sesion

1. Ir a la URL de la plataforma
2. Click en "Iniciar Sesion"
3. Ingresar usuario y contrasena
4. El sistema mostrara tu rol en el header (SUPERADMIN, ADMIN_LIGA, ADMIN_CLUB, PLAYER, USER)

## Navegacion

### Inicio (`/`)
- Temporadas activas
- Clubes destacados
- Goleadores lideres

### Ligas (`/leagues`)
- Lista de todas las ligas por pais
- Click en una liga para ver sus temporadas

### Temporadas (`/seasons`)
- Lista de temporadas con estado (Proxima/Activa/Finalizada)
- Click en una temporada para ver la tabla de posiciones

### Tabla de Posiciones (`/standings/:seasonId`)
- Posiciones, puntos, diferencia de goles
- Colores por zona: CAMPEON (oro), REDUCIDO (azul), PROMOCION (verde), DESCENSO (rojo)
- Boton "Recalcular Tabla" (solo ADMIN_LIGA+)

### Clubes (`/clubs`)
- Lista de todos los clubes
- Busqueda por nombre
- Click en un club para ver detalle, titulos e historial

### Jugadores (`/players`)
- Lista de todos los jugadores
- Busqueda por nickname
- Click en un jugador para ver estadisticas e historial

### Partidos (`/matches`)
- Lista de partidos con filtro por estado
- Programados, En Juego, Finalizados
- Click en un partido para ver detalle

### Estadisticas (`/statistics`)
- Tabs: Goleadores / Asistencias / MVP
- Filtro por temporada y division

## Roles

| Rol | Que puede hacer |
|-----|-----------------|
| **SUPERADMIN** | Todo: crear clubes, jugadores, administrar usuarios |
| **ADMIN_LIGA** | Gestionar ligas asignadas, partidos, recalcular tablas |
| **ADMIN_CLUB** | Gestionar su club |
| **PLAYER** | Ver su perfil |
| **USER** | Solo lectura |

## API Documentacion

- **Swagger UI**: `/api/docs/` — Interfaz interactiva para probar endpoints
- **ReDoc**: `/api/redoc/` — Documentacion completa de la API
- **Schema OpenAPI**: `/api/schema/` — Schema JSON/YAML descargable

## Preguntas frecuentes

### Como recalcular la tabla de posiciones?
Solo ADMIN_LIGA o SUPERADMIN pueden hacerlo. Ir a la temporada > click en "Recalcular Tabla".

### Como cambiar el nickname de un jugador?
Solo SUPERADMIN puede cambiar nicknames. Ir al perfil del jugador > editar.

### Los ascensos/descensos son automaticos?
No. Los administradores otorgan titulos y mueven clubes manualmente entre divisiones.
