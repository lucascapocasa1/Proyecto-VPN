import random
from datetime import timedelta

from django.utils import timezone
from django.db.models import Count

from apps.clubs.models import ClubSeason
from apps.players.models import Player, PlayerClubHistory
from apps.matches.models import Matchday, Match, MatchPlayer, MatchEvent

# S1: 19 matchdays weekly, J1 = 203 days ago (29 weeks), J19 = 77 days ago
S1_J1_OFFSET = -203
S1_MATCHDAYS = 19

# S2: 10 played matchdays weekly, J1 = 70 days ago, J10 = 7 days ago, J11 = +7 days
S2_J1_OFFSET = -70
S2_PLAYED_MATCHDAYS = 10
S2_J11_OFFSET = 7

S2_TOTAL_MATCHDAYS = S2_PLAYED_MATCHDAYS + 1


def date_offset(days):
    return timezone.now().date() + timedelta(days=days)


def s1_matchday_date(number):
    return date_offset(S1_J1_OFFSET + (number - 1) * 7)


def s2_matchday_date(number):
    if number <= S2_PLAYED_MATCHDAYS:
        return date_offset(S2_J1_OFFSET + (number - 1) * 7)
    return date_offset(S2_J11_OFFSET + (number - S2_PLAYED_MATCHDAYS - 1) * 7)


def joined_at_s1():
    return timezone.now() + timedelta(days=S1_J1_OFFSET)


def left_at_s1():
    return timezone.now() + timedelta(days=S2_J1_OFFSET)


def joined_at_s2():
    return timezone.now() + timedelta(days=S2_J1_OFFSET)


def roster_for(club_season):
    return list(
        Player.objects.filter(club_history__club_season=club_season).order_by("id")
    )


def round_robin_rounds(club_seasons):
    """
    Classic circle-method round robin.
    Returns a list of rounds; each round is a perfect matching of disjoint
    pairs, so every club plays exactly once per round.
    """
    teams = sorted(club_seasons, key=lambda cs: cs.id)
    n = len(teams)
    if n < 2:
        return []
    arr = teams[:]
    if n % 2:
        arr.append(None)
        n += 1

    rounds = []
    for _ in range(n - 1):
        pairs = []
        for i in range(n // 2):
            home, away = arr[i], arr[n - 1 - i]
            if home is not None and away is not None:
                if (len(rounds) + i) % 2:
                    pairs.append((away, home))
                else:
                    pairs.append((home, away))
        rounds.append(pairs)
        arr = [arr[0], arr[-1]] + arr[1:-1]
    return rounds


def create_match_events(match, home_cs, away_cs):
    events_count = 0
    used_minutes = set()

    def _pick_minute():
        m = random.randint(1, 90)
        while m in used_minutes:
            m = random.randint(1, 90)
        used_minutes.add(m)
        return m

    home_players = roster_for(home_cs)
    away_players = roster_for(away_cs)

    home_mps, away_mps = [], []
    for p in home_players:
        mp = MatchPlayer.objects.create(
            match=match, player=p, club_season=home_cs,
            display_name=p.nickname, is_starter=True,
        )
        home_mps.append(mp)
        events_count += 1
    for p in away_players:
        mp = MatchPlayer.objects.create(
            match=match, player=p, club_season=away_cs,
            display_name=p.nickname, is_starter=True,
        )
        away_mps.append(mp)
        events_count += 1

    def _weighted_scorer(team_mps):
        weights = []
        for mp in team_mps:
            if not mp.player:
                continue
            pos = mp.player.position
            if pos == "DEL":
                weights.append(10)
            elif pos == "MED":
                weights.append(5)
            elif pos == "DEF":
                weights.append(2)
            elif pos == "ARQ":
                weights.append(0.5)
            else:
                weights.append(3)
        real = [mp for mp in team_mps if mp.player]
        if not real:
            return None
        return random.choices(real, weights=weights, k=1)[0]

    for team_mps, goals in [(home_mps, match.home_goals), (away_mps, match.away_goals)]:
        for _ in range(goals or 0):
            scorer = _weighted_scorer(team_mps)
            if not scorer:
                continue
            minute = _pick_minute()
            MatchEvent.objects.create(
                match=match, match_player=scorer,
                event_type=MatchEvent.EventType.GOAL, minute=minute,
            )
            events_count += 1
            if random.random() < 0.7:
                real = [mp for mp in team_mps if mp.player and mp != scorer]
                if real:
                    assister = random.choice(real)
                    MatchEvent.objects.create(
                        match=match, match_player=assister,
                        event_type=MatchEvent.EventType.ASSIST, minute=minute,
                    )
                    events_count += 1

    if random.random() < 0.3:
        team = random.choice([home_mps, away_mps])
        real = [mp for mp in team if mp.player]
        if real:
            MatchEvent.objects.create(
                match=match, match_player=random.choice(real),
                event_type=MatchEvent.EventType.OWN_GOAL, minute=_pick_minute(),
            )
            events_count += 1

    for _ in range(random.randint(0, 3)):
        team = random.choice([home_mps, away_mps])
        real = [mp for mp in team if mp.player]
        if real:
            MatchEvent.objects.create(
                match=match, match_player=random.choice(real),
                event_type=random.choice([
                    MatchEvent.EventType.YELLOW_CARD,
                    MatchEvent.EventType.RED_CARD,
                ]),
                minute=_pick_minute(),
            )
            events_count += 1

    mvp_team = random.choice([home_mps, away_mps])
    real = [mp for mp in mvp_team if mp.player]
    if real:
        MatchEvent.objects.create(
            match=match, match_player=random.choice(real),
            event_type=MatchEvent.EventType.MVP, minute=90,
        )
        events_count += 1

    return events_count


def ensure_matchday(season, division, number, date):
    matchday, _ = Matchday.objects.get_or_create(
        season=season, division=division, number=number,
        defaults={"name": f"Jornada {number}", "date": date},
    )
    if matchday.date != date:
        matchday.date = date
        matchday.save(update_fields=["date"])
    return matchday


def create_finished_match(season, division, matchday, home_cs, away_cs):
    home_goals = random.randint(0, 4)
    away_goals = random.randint(0, 3)
    match = Match.objects.create(
        season=season, division=division, matchday=matchday,
        home_club_season=home_cs, away_club_season=away_cs,
        home_goals=home_goals, away_goals=away_goals,
        status=Match.Status.FINISHED, date=matchday.date,
    )
    events = create_match_events(match, home_cs, away_cs)
    return match, events


def create_scheduled_match(season, division, matchday, home_cs, away_cs):
    return Match.objects.create(
        season=season, division=division, matchday=matchday,
        home_club_season=home_cs, away_club_season=away_cs,
        home_goals=None, away_goals=None,
        status=Match.Status.SCHEDULED, date=matchday.date,
    )


def create_matchdays(
    season, division, club_seasons, date_fn,
    first_number, last_number, finished,
):
    """
    Create matchdays first_number..last_number with matches using a
    round-robin schedule (every club plays exactly once per matchday).
    Pairing is deterministic, so partial or repeated runs never duplicate
    fixtures. Matchdays that already have matches are skipped (idempotent).
    Returns (matches_created, events_created).
    """
    rounds = round_robin_rounds(club_seasons)

    matches_created = 0
    events_created = 0

    for number in range(first_number, last_number + 1):
        matchday = ensure_matchday(season, division, number, date_fn(number))
        if matchday.matches.exists():
            continue

        if number - 1 >= len(rounds):
            break
        batch = rounds[number - 1]

        for home_cs, away_cs in batch:
            if finished:
                _, events = create_finished_match(
                    season, division, matchday, home_cs, away_cs,
                )
                events_created += events
            else:
                create_scheduled_match(season, division, matchday, home_cs, away_cs)
            matches_created += 1

    return matches_created, events_created


def top_scorer_player_ids(country, season, limit=10):
    qs = (
        MatchEvent.objects.filter(
            event_type=MatchEvent.EventType.GOAL,
            match__status=Match.Status.FINISHED,
            match__season=season,
            match_player__club_season__club__country=country,
        )
        .order_by()
        .values("match_player__player_id")
        .annotate(goals=Count("id"))
        .order_by("-goals", "match_player__player_id")[:limit]
    )
    return [row["match_player__player_id"] for row in qs if row["match_player__player_id"]]


def pick_forced_transfer_ids(country, season, count=5, top_limit=10):
    """
    Pick `count` players from the S1 top scorers to force a transfer,
    preferring distinct clubs.
    """
    top_ids = top_scorer_player_ids(country, season, limit=top_limit)
    if not top_ids:
        return []

    history = list(
        PlayerClubHistory.objects.filter(
            player_id__in=top_ids,
            club_season__season=season,
            club_season__club__country=country,
        ).select_related("club_season")
    )
    by_player = {h.player_id: h for h in history}

    ordered = []
    for pid in top_ids:
        if pid in by_player:
            ordered.append((pid, by_player[pid].club_season_id))

    picked, used_clubs, used_players = [], set(), set()
    for pid, cs_id in ordered:
        if len(picked) >= count:
            break
        if cs_id in used_clubs:
            continue
        picked.append(pid)
        used_clubs.add(cs_id)
        used_players.add(pid)

    for pid, _cs_id in ordered:
        if len(picked) >= count:
            break
        if pid in used_players:
            continue
        picked.append(pid)
        used_players.add(pid)

    return picked


def apply_transfers(country, season, forced_player_ids=(), out_per_club=2, max_roster=17):
    """
    Move `out_per_club` players' season PCH per club to a random other club
    of the same country (Primera <-> Segunda free). Forced players transfer
    first. Destination rosters never exceed `max_roster`.
    Returns the number of transfers applied.
    """
    club_seasons = list(
        ClubSeason.objects.filter(season=season, club__country=country)
    )
    if not club_seasons:
        return 0

    roster = {}
    for h in PlayerClubHistory.objects.filter(club_season__in=club_seasons):
        roster.setdefault(h.club_season_id, []).append(h)

    sizes = {cs_id: len(items) for cs_id, items in roster.items()}
    all_pch = [h for items in roster.values() for h in items]

    leavers = []
    leaving_ids = set()

    for pid in forced_player_ids:
        match = next((h for h in all_pch if h.player_id == pid), None)
        if match is None or match.id in leaving_ids:
            continue
        leavers.append(match)
        leaving_ids.add(match.id)

    for cs in club_seasons:
        current = sum(1 for h in leavers if h.club_season_id == cs.id)
        need = out_per_club - current
        if need <= 0:
            continue
        candidates = [h for h in roster[cs.id] if h.id not in leaving_ids]
        random.shuffle(candidates)
        for h in candidates[:need]:
            leavers.append(h)
            leaving_ids.add(h.id)

    for h in leavers:
        sizes[h.club_season_id] -= 1

    transfers = 0
    for h in leavers:
        from_id = h.club_season_id
        possible = [
            cs for cs in club_seasons
            if cs.id != from_id and sizes[cs.id] < max_roster
        ]
        if not possible:
            possible = [cs for cs in club_seasons if cs.id != from_id]
        dest = random.choice(possible)
        h.club_season = dest
        h.save(update_fields=["club_season"])
        sizes[dest.id] += 1
        transfers += 1

    return transfers
