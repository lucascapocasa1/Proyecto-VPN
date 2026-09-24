from django.db.models import Avg, Q, Count, Sum
from apps.matches.models import MatchEvent, Match, MatchPlayer, MatchPerformance


def get_player_statistics(player, season=None, division=None, league=None, country=None, game=None):
    """
    Calculate player statistics from MatchEvents.
    Statistics are derived data - always computed from the source of truth.
    """
    events = MatchEvent.objects.filter(
        match_player__player=player,
        match__status=Match.Status.FINISHED,
    )

    if season:
        events = events.filter(match__season=season)
    if division:
        events = events.filter(match__division=division)
    if league:
        events = events.filter(match__season__league=league)
    if country:
        events = events.filter(match__season__league__country=country)
    if game:
        events = events.filter(match__season__game=game)

    return {
        "goals": events.filter(event_type=MatchEvent.EventType.GOAL).count(),
        "own_goals": events.filter(event_type=MatchEvent.EventType.OWN_GOAL).count(),
        "assists": events.filter(event_type=MatchEvent.EventType.ASSIST).count(),
        "yellow_cards": events.filter(event_type=MatchEvent.EventType.YELLOW_CARD).count(),
        "red_cards": events.filter(event_type=MatchEvent.EventType.RED_CARD).count(),
        "mvp": events.filter(event_type=MatchEvent.EventType.MVP).count(),
    }


def get_player_statistics_by_season(player):
    """
    Get player statistics grouped by season.
    Returns a list of dicts with season info and stats.
    """
    from apps.competitions.models import Season

    seasons = Season.objects.filter(
        matches__match_players__player=player,
        matches__status=Match.Status.FINISHED,
    ).distinct()

    results = []
    for season in seasons:
        stats = get_player_statistics(player, season=season)
        results.append({
            "season": season,
            "stats": stats,
        })

    return results


def get_player_club_statistics(player, club_season=None):
    """
    Get player statistics for a specific club season.
    """
    events = MatchEvent.objects.filter(
        match_player__player=player,
        match_player__club_season=club_season,
        match__status=Match.Status.FINISHED,
    )

    return {
        "goals": events.filter(event_type=MatchEvent.EventType.GOAL).count(),
        "own_goals": events.filter(event_type=MatchEvent.EventType.OWN_GOAL).count(),
        "assists": events.filter(event_type=MatchEvent.EventType.ASSIST).count(),
        "yellow_cards": events.filter(event_type=MatchEvent.EventType.YELLOW_CARD).count(),
        "red_cards": events.filter(event_type=MatchEvent.EventType.RED_CARD).count(),
        "mvp": events.filter(event_type=MatchEvent.EventType.MVP).count(),
    }


EMPTY_CLUB_STATS = {
    "matches_played": 0,
    "goals": 0,
    "assists": 0,
    "mvp": 0,
    "yellow_cards": 0,
    "red_cards": 0,
}


def get_player_stats_by_club_season(player):
    """
    Player statistics grouped by club_season.
    Returns {club_season_id: {matches_played, goals, assists, mvp, yellow_cards, red_cards}}.
    Two aggregated queries total.
    """
    events = (
        MatchEvent.objects.filter(
            match_player__player=player,
            match__status=Match.Status.FINISHED,
        )
        .order_by()
        .values("match_player__club_season_id")
        .annotate(
            goals=Count("id", filter=Q(event_type=MatchEvent.EventType.GOAL)),
            assists=Count("id", filter=Q(event_type=MatchEvent.EventType.ASSIST)),
            mvp=Count("id", filter=Q(event_type=MatchEvent.EventType.MVP)),
            yellow_cards=Count("id", filter=Q(event_type=MatchEvent.EventType.YELLOW_CARD)),
            red_cards=Count("id", filter=Q(event_type=MatchEvent.EventType.RED_CARD)),
        )
    )

    matches = (
        MatchPlayer.objects.filter(
            player=player,
            match__status=Match.Status.FINISHED,
        )
        .order_by()
        .values("club_season_id")
        .annotate(matches_played=Count("match", distinct=True))
    )

    result = {}
    for row in events:
        club_season_id = row["match_player__club_season_id"]
        stats = dict(EMPTY_CLUB_STATS)
        stats.update({k: v for k, v in row.items() if k != "match_player__club_season_id"})
        result[club_season_id] = stats

    for row in matches:
        club_season_id = row["club_season_id"]
        if club_season_id not in result:
            result[club_season_id] = dict(EMPTY_CLUB_STATS)
        result[club_season_id]["matches_played"] = row["matches_played"]

    return result


def get_club_statistics(club, season=None, division=None):
    """
    Get aggregated statistics for a club across all players.
    """
    match_players = MatchPlayer.objects.filter(
        club_season__club=club,
        match__status=Match.Status.FINISHED,
    )

    if season:
        match_players = match_players.filter(club_season__season=season)
    if division:
        match_players = match_players.filter(club_season__division=division)

    events = MatchEvent.objects.filter(
        match_player__in=match_players,
        match__status=Match.Status.FINISHED,
    )

    return {
        "total_goals": events.filter(event_type=MatchEvent.EventType.GOAL).count(),
        "total_assists": events.filter(event_type=MatchEvent.EventType.ASSIST).count(),
        "total_yellow_cards": events.filter(event_type=MatchEvent.EventType.YELLOW_CARD).count(),
        "total_red_cards": events.filter(event_type=MatchEvent.EventType.RED_CARD).count(),
        "total_mvp": events.filter(event_type=MatchEvent.EventType.MVP).count(),
    }


def get_top_scorers(season=None, division=None, limit=10):
    """
    Get top scorers across all matches.
    """
    events = MatchEvent.objects.filter(
        event_type=MatchEvent.EventType.GOAL,
        match__status=Match.Status.FINISHED,
        match_player__player__isnull=False,
    )

    if season:
        events = events.filter(match__season=season)
    if division:
        events = events.filter(match__division=division)

    from django.db.models import Count
    top_scorers = (
        events.values(
            "match_player__player__id",
            "match_player__player__nickname",
            "match_player__player__position",
            "match_player__player__country__name",
        )
        .annotate(goal_count=Count("id"))
        .order_by("-goal_count")[:limit]
    )

    return [
        {
            "player_id": s["match_player__player__id"],
            "nickname": s["match_player__player__nickname"],
            "position": s["match_player__player__position"],
            "country_name": s["match_player__player__country__name"],
            "goals": s["goal_count"],
        }
        for s in top_scorers
    ]


def get_top_assists(season=None, division=None, limit=10):
    """
    Get top assist providers across all matches.
    """
    events = MatchEvent.objects.filter(
        event_type=MatchEvent.EventType.ASSIST,
        match__status=Match.Status.FINISHED,
        match_player__player__isnull=False,
    )

    if season:
        events = events.filter(match__season=season)
    if division:
        events = events.filter(match__division=division)

    from django.db.models import Count
    top_assists = (
        events.values(
            "match_player__player__id",
            "match_player__player__nickname",
            "match_player__player__position",
            "match_player__player__country__name",
        )
        .annotate(assist_count=Count("id"))
        .order_by("-assist_count")[:limit]
    )

    return [
        {
            "player_id": a["match_player__player__id"],
            "nickname": a["match_player__player__nickname"],
            "position": a["match_player__player__position"],
            "country_name": a["match_player__player__country__name"],
            "assists": a["assist_count"],
        }
        for a in top_assists
    ]


def get_top_mvp(season=None, division=None, limit=10):
    """
    Get players with most MVP awards.
    """
    events = MatchEvent.objects.filter(
        event_type=MatchEvent.EventType.MVP,
        match__status=Match.Status.FINISHED,
        match_player__player__isnull=False,
    )

    if season:
        events = events.filter(match__season=season)
    if division:
        events = events.filter(match__division=division)

    from django.db.models import Count
    top_mvp = (
        events.values(
            "match_player__player__id",
            "match_player__player__nickname",
            "match_player__player__position",
            "match_player__player__country__name",
        )
        .annotate(mvp_count=Count("id"))
        .order_by("-mvp_count")[:limit]
    )

    return [
        {
            "player_id": m["match_player__player__id"],
            "nickname": m["match_player__player__nickname"],
            "position": m["match_player__player__position"],
            "country_name": m["match_player__player__country__name"],
            "mvp_count": m["mvp_count"],
        }
        for m in top_mvp
    ]


# --- Analytics sobre MatchPerformance (Fase 3: graficos esenciales) ---

PERFORMANCE_METRICS = (
    "rating", "goals", "assists", "shots", "shot_accuracy_pct",
    "passes", "pass_accuracy_pct", "dribbles", "dribble_success_pct",
    "tackles", "tackle_success_pct", "offsides", "fouls",
    "possession_won", "possession_lost", "minutes_played",
    "distance_km", "sprint_distance_km",
)

POSITIONS = ("ARQ", "DEF", "MED", "DEL")


def _perf_queryset(season=None, division=None):
    qs = MatchPerformance.objects.filter(
        match_player__player__isnull=False,
        match_player__match__status=Match.Status.FINISHED,
    )
    if season:
        qs = qs.filter(match_player__match__season=season)
    if division:
        qs = qs.filter(match_player__match__division=division)
    return qs


def _num(value, digits=2):
    if value is None:
        return None
    return round(float(value), digits)


def get_performance_leaderboard(
    metric="rating", agg="avg", season=None, division=None,
    limit=10, min_matches=1,
):
    """Ranking de jugadores por cualquier metrica de MatchPerformance.

    agg: "avg" (promedio por partido) o "sum" (total acumulado).
    min_matches: exige un minimo de apariciones para evitar promedios de 1 partido.
    """
    if metric not in PERFORMANCE_METRICS:
        raise ValueError(f"Métrica inválida: {metric}")
    if agg not in ("avg", "sum"):
        raise ValueError("agg debe ser 'avg' o 'sum'")

    aggregate = Avg(metric) if agg == "avg" else Sum(metric)
    rows = (
        _perf_queryset(season, division)
        .values(
            "match_player__player__id",
            "match_player__player__nickname",
            "match_player__player__position",
            "match_player__player__country__name",
        )
        .annotate(value=aggregate, matches=Count("id"))
        .filter(matches__gte=max(1, min_matches))
        .order_by("-value", "match_player__player__nickname")[: max(1, min(limit, 50))]
    )
    return [
        {
            "player_id": row["match_player__player__id"],
            "nickname": row["match_player__player__nickname"],
            "position": row["match_player__player__position"],
            "country_name": row["match_player__player__country__name"],
            "matches": row["matches"],
            "value": _num(row["value"]) or 0.0,
        }
        for row in rows
    ]


def get_performance_by_position(season=None, division=None):
    """Promedio de metricas clave agrupadas por posicion (ARQ/DEF/MED/DEL)."""
    rows = {
        row["match_player__player__position"]: row
        for row in (
            _perf_queryset(season, division)
            .filter(match_player__player__position__in=POSITIONS)
            .values("match_player__player__position")
            .annotate(
                matches=Count("id"),
                rating=Avg("rating"),
                pass_accuracy_pct=Avg("pass_accuracy_pct"),
                dribbles=Avg("dribbles"),
                tackles=Avg("tackles"),
                distance_km=Avg("distance_km"),
                possession_won=Avg("possession_won"),
            )
        )
    }
    result = []
    for pos in POSITIONS:
        row = rows.get(pos)
        if not row:
            result.append({
                "position": pos, "matches": 0,
                "rating": None, "pass_accuracy_pct": None,
                "dribbles": None, "tackles": None,
                "distance_km": None, "possession_won": None,
            })
            continue
        result.append({
            "position": pos,
            "matches": row["matches"],
            "rating": _num(row["rating"], 1),
            "pass_accuracy_pct": _num(row["pass_accuracy_pct"], 1),
            "dribbles": _num(row["dribbles"]),
            "tackles": _num(row["tackles"]),
            "distance_km": _num(row["distance_km"], 1),
            "possession_won": _num(row["possession_won"]),
        })
    return result


def get_player_match_series(player, limit=100):
    """Serie cronologica por partido de un jugador: rating/min/km (MatchPerformance)
    + goles/asistencias/MVP/tarjetas (MatchEvent, la misma fuente que las tarjetas
    del perfil)."""
    participations = (
        MatchPlayer.objects.filter(player=player, match__status=Match.Status.FINISHED)
        .select_related(
            "match__home_club_season__club",
            "match__away_club_season__club",
            "club_season__club",
        )
        .order_by("match__date", "match__id", "id")[:limit]
    )
    perf_map = {
        p.match_player_id: p
        for p in MatchPerformance.objects.filter(match_player__in=participations)
    }
    event_counts: dict[int, dict[str, int]] = {}
    for row in (
        MatchEvent.objects.filter(match_player__in=participations)
        .values("match_player_id", "event_type")
        .annotate(n=Count("id"))
    ):
        event_counts.setdefault(row["match_player_id"], {})[row["event_type"]] = row["n"]

    series = []
    for mp in participations:
        match = mp.match
        is_home = mp.club_season_id == match.home_club_season_id
        home_name = match.home_club_season.club.name
        away_name = match.away_club_season.club.name
        perf = perf_map.get(mp.id)
        events = event_counts.get(mp.id, {})
        series.append({
            "match": match.id,
            "date": match.date.isoformat() if match.date else None,
            "home_club_name": home_name,
            "away_club_name": away_name,
            "home_goals": match.home_goals,
            "away_goals": match.away_goals,
            "opponent": away_name if is_home else home_name,
            "is_home": is_home,
            "rating": _num(perf.rating, 1) if perf else None,
            "goals": events.get(MatchEvent.EventType.GOAL, 0),
            "assists": events.get(MatchEvent.EventType.ASSIST, 0),
            "mvp": events.get(MatchEvent.EventType.MVP, 0),
            "yellow": events.get(MatchEvent.EventType.YELLOW_CARD, 0),
            "red": events.get(MatchEvent.EventType.RED_CARD, 0),
            "minutes_played": perf.minutes_played if perf else None,
            "distance_km": _num(perf.distance_km, 1) if perf else None,
        })
    return series
