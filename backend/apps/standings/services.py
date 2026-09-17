from django.db import transaction
from apps.matches.models import Match
from apps.clubs.models import ClubSeason
from apps.standings.models import Standing


def recalculate_standings(season, division):
    """
    Recalculate standings for a specific season and division.
    This is the source of truth: standings are derived from match results.
    """
    matches = Match.objects.filter(
        season=season,
        division=division,
        status=Match.Status.FINISHED,
    ).select_related("home_club_season", "away_club_season")

    club_stats = {}
    for cs in ClubSeason.objects.filter(season=season, division=division):
        club_stats[cs.id] = {
            "club_season": cs,
            "played": 0,
            "won": 0,
            "drawn": 0,
            "lost": 0,
            "goals_for": 0,
            "goals_against": 0,
        }

    for match in matches:
        home = club_stats.get(match.home_club_season_id)
        away = club_stats.get(match.away_club_season_id)

        if not home or not away:
            continue

        home["played"] += 1
        away["played"] += 1

        home_goals = match.home_goals or 0
        away_goals = match.away_goals or 0

        home["goals_for"] += home_goals
        home["goals_against"] += away_goals
        away["goals_for"] += away_goals
        away["goals_against"] += home_goals

        if home_goals > away_goals:
            home["won"] += 1
            away["lost"] += 1
        elif home_goals < away_goals:
            home["lost"] += 1
            away["won"] += 1
        else:
            home["drawn"] += 1
            away["drawn"] += 1

    for stats in club_stats.values():
        stats["goal_difference"] = stats["goals_for"] - stats["goals_against"]
        stats["points"] = stats["won"] * 3 + stats["drawn"]

    sorted_clubs = sorted(
        club_stats.values(),
        key=lambda x: (-x["points"], -x["goal_difference"], -x["goals_for"]),
    )

    with transaction.atomic():
        Standing.objects.filter(season=season, division=division).delete()

        standing_objects = []
        for position, stats in enumerate(sorted_clubs, 1):
            standing_objects.append(
                Standing(
                    season=season,
                    division=division,
                    club_season=stats["club_season"],
                    played=stats["played"],
                    won=stats["won"],
                    drawn=stats["drawn"],
                    lost=stats["lost"],
                    goals_for=stats["goals_for"],
                    goals_against=stats["goals_against"],
                    goal_difference=stats["goal_difference"],
                    points=stats["points"],
                    position=position,
                )
            )

        Standing.objects.bulk_create(standing_objects)

    return Standing.objects.filter(season=season, division=division)


def recalculate_all_standings(season):
    """
    Recalculate standings for all divisions in a season.
    """
    from apps.competitions.models import Division

    divisions = Division.objects.filter(season=season)
    results = {}
    for division in divisions:
        results[division.id] = recalculate_standings(season, division)
    return results
