from django.db.models import Q
from apps.matches.models import MatchEvent, Match, MatchPlayer


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
