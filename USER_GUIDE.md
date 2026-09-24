# Guia de Usuario — VPN · Virtual Pro Network (FC 27 Pro Clubs)

Plataforma web para gestionar ligas competitivas de **EA Sports FC — Clubes Pro**, con identidad **VPN (Virtual Pro Network)**.

## Inicio de sesion

1. Ir a la URL de la plataforma
2. Click en "Iniciar Sesion"
3. Ingresar usuario y contrasena
4. El sistema mostrara tu rol en la barra superior (SUPERADMIN, ADMIN_LIGA, ADMIN_CLUB, PLAYER, USER)

## Navegacion

La interfaz tiene un **menu lateral (sidebar)** con la marca "FC 27 PRO CLUBS" y, al pie, el sello **VPN — VIRTUAL PRO NETWORK**. La barra superior incluye un **buscador global** (escribi 2+ letras para encontrar equipos o jugadores), el usuario con su rol y el boton de salir. La campanita de notificaciones es decorativa por ahora.

### Inicio (`/`)
- Hero "Virtual Pro Network" con la temporada destacada
- **Tabla de Posiciones** (top 8) y **Ultimos Resultados** (columna izquierda)
- **Proximos Partidos**, **Maximos Goleadores** y **Partido Destacado** (columna derecha)

### Ligas (`/leagues`)
- Lista de todas las ligas por pais
- Click en una liga para ver sus temporadas

### Temporadas (`/seasons`)
- Lista de temporadas con estado (Proxima/Activa/Finalizada)
- Los ADMIN_LIGA+ pueden cambiar el estado y renombrar la temporada directamente en la tarjeta
- Click en una temporada para ver la tabla de posiciones

### Tabla de Posiciones (`/standings/:seasonId`)
- Posiciones, puntos, diferencia de goles
- Colores por zona: CAMPEON (oro), REDUCIDO (azul), PROMOCION (verde), DESCENSO (rojo)
- Zonas: Primera (p1 campeon, p19 promocion, p20 descenso) y Segunda (p2-9 reducido ademas)
- Boton "Recalcular Tabla" (solo ADMIN_LIGA+)

### Clubes (`/clubs`)
- Lista de todos los clubes
- Busqueda por nombre
- Click en un club para ver detalle, titulos e historial
- Los ADMIN_LIGA+ pueden editar el club y agregar/eliminar titulos desde el perfil

### Jugadores (`/players`)
- Lista de todos los jugadores
- Busqueda por nickname
- Click en un jugador para ver estadisticas, historial y rendimiento partido a partido (rating, minutos, goles, asistencias)
- El perfil incluye "Evolucion de rendimiento" (grafico de rating por partido) y sparklines en las tarjetas de estadisticas
- Los ADMIN_LIGA+ pueden editar nickname, posicion, plataforma, pais y estado desde el perfil

### Partidos (`/matches`)
- Lista de partidos con filtro por estado
- Programados, En Juego, Finalizados
- Click en un partido para ver detalle

### Detalle de Partido (`/matches/:id`)
- Marcador, fecha, hora y estado del partido
- Editar resultado/estado/fecha/hora (ADMIN_LIGA+) — las posiciones se recalculan automaticamente
- Alineaciones: agregar jugadores del club y quitarlos (con confirmacion)
- Eventos: goles, asistencias, autogoles, tarjetas y MVP — alta, edicion inline y baja
- Rendimiento detallado: rating, minutos y las 18 stats por jugador; fila expandible para editar y guardar (ADMIN_LIGA+)
- OCR: seleccionar capturas de la pestaña "Rendimiento" de EA FC → Analizar → verificar/corregir el jugador sugerido → Guardar (ADMIN_LIGA+)

### Mercado de Pases (`/transfers`)
- Lista de transferencias registradas con club de origen y destino
- Busqueda de jugadores y filtro por temporada
- Alta y baja de transferencias (ADMIN_LIGA+); eliminar revierte la ultima transferencia del jugador

### Estadisticas (`/statistics`)
- Tabs: Goleadores / Asistencias / MVP / **Rendimiento**
- Filtro por temporada y division
- Tab "Rendimiento": leaderboard de las 18 metricas (rating, goles, km, precision...) con promedio o total y minimo de partidos; abajo, promedios por posicion (ARQ/DEF/MED/DEL)

## Roles

| Rol | Que puede hacer |
|-----|-----------------|
| **SUPERADMIN** | Todo: crear clubes, jugadores, administrar usuarios |
| **ADMIN_LIGA** | Gestionar ligas asignadas, partidos, posiciones, mercado de pases, titulos, temporadas, clubes y jugadores |
| **ADMIN_CLUB** | Gestionar su club |
| **PLAYER** | Ver su perfil |
| **USER** | Solo lectura |

## API Documentacion

- **Swagger UI**: `/api/docs/` — Interfaz interactiva para probar endpoints
- **ReDoc**: `/api/redoc/` — Documentacion completa de la API
- **Schema OpenAPI**: `/api/schema/` — Schema JSON/YAML descargable

## Preguntas frecuentes

### Como recalcular la tabla de posiciones?
No hace falta hacerlo a mano: cada resultado cargado la recalcula automaticamente. Igual existe el boton "Recalcular Tabla" (solo ADMIN_LIGA+) para forzarlo.

### Como cargar el resultado de un partido?
Ir a Partidos > click en el partido > en "Editar resultado" completar goles, estado, fecha y hora > Guardar. Las posiciones se actualizan solas.

### Como registrar una transferencia?
Ir a Mercado > completar jugador, club origen, club destino y fecha > Guardar. Solo ADMIN_LIGA+ puede dar de alta o borrar transferencias.

### Como cambiar el nickname de un jugador?
Ir al perfil del jugador > Editar > cambiar nickname > Guardar. Pueden hacerlo SUPERADMIN y ADMIN_LIGA.

### Los ascensos/descensos son automaticos?
No. Los administradores otorgan titulos y mueven clubes manualmente entre divisiones.

### Por que aparece un 429 (Too Many Requests)?
El login, registro y refresh de sesion estan limitados a 10 intentos por minuto. El resto de la navegacion no tiene limite; si aun asi ves un 429 puntual, el sistema lo reintenta automaticamente.
