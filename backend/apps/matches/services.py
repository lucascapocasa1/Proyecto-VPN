"""
Match validation service.
Handles lineup validation, BOT completion, and integrity checks.
"""
from django.core.exceptions import ValidationError
from apps.matches.models import Match, MatchPlayer


MAX_PLAYERS_PER_TEAM = 11


def validate_lineup_count(match, club_season):
    """
    Validate that a team doesn't exceed MAX_PLAYERS_PER_TEAM.
    """
    count = MatchPlayer.objects.filter(
        match=match,
        club_season=club_season,
    ).count()

    if count > MAX_PLAYERS_PER_TEAM:
        raise ValidationError(
            f"El equipo {club_season.club.name} tiene {count} jugadores. "
            f"Máximo permitido: {MAX_PLAYERS_PER_TEAM}."
        )


def complete_lineup_with_bots(match, club_season):
    """
    Complete a team's lineup with BOTs up to MAX_PLAYERS_PER_TEAM.
    Returns the list of created MatchPlayer objects.
    """
    current_count = MatchPlayer.objects.filter(
        match=match,
        club_season=club_season,
    ).count()

    bots_needed = MAX_PLAYERS_PER_TEAM - current_count
    created_bots = []

    for _ in range(bots_needed):
        bot = MatchPlayer.objects.create(
            match=match,
            player=None,
            club_season=club_season,
            display_name="BOT",
            is_starter=False,
        )
        created_bots.append(bot)

    return created_bots


def replace_bot_with_player(match_player, player):
    """
    Replace a BOT MatchPlayer with a real player.
    Events associated with the MatchPlayer remain unchanged.
    """
    if match_player.player is not None:
        raise ValidationError(
            "Este MatchPlayer ya tiene un jugador real asignado."
        )

    existing_with_player = MatchPlayer.objects.filter(
        match=match_player.match,
        player=player,
    ).exclude(id=match_player.id)

    if existing_with_player.exists():
        raise ValidationError(
            f"El jugador {player.nickname} ya participa en este partido."
        )

    match_player.player = player
    match_player.display_name = player.nickname
    match_player.save()

    return match_player


def validate_match_integrity(match):
    """
    Validate that a match has valid lineups for both teams.
    """
    home_count = MatchPlayer.objects.filter(
        match=match,
        club_season=match.home_club_season,
    ).count()

    away_count = MatchPlayer.objects.filter(
        match=match,
        club_season=match.away_club_season,
    ).count()

    if home_count == 0:
        raise ValidationError(
            f"El equipo local {match.home_club_season.club.name} no tiene jugadores."
        )

    if away_count == 0:
        raise ValidationError(
            f"El equipo visitante {match.away_club_season.club.name} no tiene jugadores."
        )

    if home_count > MAX_PLAYERS_PER_TEAM:
        raise ValidationError(
            f"El equipo local tiene {home_count} jugadores. "
            f"Máximo permitido: {MAX_PLAYERS_PER_TEAM}."
        )

    if away_count > MAX_PLAYERS_PER_TEAM:
        raise ValidationError(
            f"El equipo visitante tiene {away_count} jugadores. "
            f"Máximo permitido: {MAX_PLAYERS_PER_TEAM}."
        )


def validate_event_match_player(match, match_player):
    """
    Validate that a match_player belongs to the given match.
    """
    if match_player.match_id != match.id:
        raise ValidationError(
            "El jugador no pertenece a este partido."
        )


def validate_goals_consistency(match):
    """
    Validate that goals in events match the match result.
    This is a soft validation - returns warnings, not errors.
    """
    from apps.matches.models import MatchEvent

    warnings = []

    home_goals_from_events = MatchEvent.objects.filter(
        match=match,
        match_player__club_season=match.home_club_season,
        event_type=MatchEvent.EventType.GOAL,
    ).count()

    away_goals_from_events = MatchEvent.objects.filter(
        match=match,
        match_player__club_season=match.away_club_season,
        event_type=MatchEvent.EventType.GOAL,
    ).count()

    home_own_goals = MatchEvent.objects.filter(
        match=match,
        match_player__club_season=match.away_club_season,
        event_type=MatchEvent.EventType.OWN_GOAL,
    ).count()

    away_own_goals = MatchEvent.objects.filter(
        match=match,
        match_player__club_season=match.home_club_season,
        event_type=MatchEvent.EventType.OWN_GOAL,
    ).count()

    total_home = home_goals_from_events + away_own_goals
    total_away = away_goals_from_events + home_own_goals

    if match.home_goals is not None and total_home != match.home_goals:
        warnings.append(
            f"Goles del local: evento={total_home}, resultado={match.home_goals}"
        )

    if match.away_goals is not None and total_away != match.away_goals:
        warnings.append(
            f"Goles del visitante: evento={total_away}, resultado={match.away_goals}"
        )

    return warnings
