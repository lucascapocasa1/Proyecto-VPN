import random
from datetime import timedelta
from django.utils import timezone
from django.core.management.base import BaseCommand
from apps.accounts.models import User
from apps.competitions.models import Country, Game, CompetitionFormat, League, Season, Division
from apps.clubs.models import Club, ClubSeason
from apps.players.models import Player, PlayerClubHistory
from apps.matches.models import Matchday, Match, MatchPlayer, MatchEvent
from apps.standings.models import Standing
from apps.standings.services import recalculate_standings


class Command(BaseCommand):
    help = "Create small seed data for development (~500 records)"

    def handle(self, *args, **options):
        random.seed(42)
        self.stdout.write("Creating dev seed data...")

        self._create_users()
        self._create_infra()
        self._create_clubs()
        self._create_players()
        self._create_season1()
        self._create_season2()

        self.stdout.write(self.style.SUCCESS("Dev seed data created successfully!"))

    def _create_users(self):
        self.stdout.write("  Creating users...")
        self.superadmin = User.objects.create_superuser(
            username="admin", email="admin@test.com",
            password="admin123", role=User.Role.SUPERADMIN,
        )
        self.admin_liga = User.objects.create_user(
            username="admin_liga", email="admin_liga@test.com",
            password="admin123", role=User.Role.ADMIN_LIGA,
        )
        self.admin_club = User.objects.create_user(
            username="admin_club", email="admin_club@test.com",
            password="admin123", role=User.Role.ADMIN_CLUB,
        )
        self.player_user = User.objects.create_user(
            username="player1", email="player1@test.com",
            password="admin123", role=User.Role.PLAYER,
        )

    def _create_infra(self):
        self.stdout.write("  Creating infrastructure...")
        self.argentina = Country.objects.create(name="Argentina", code="AR")
        self.ea_fc_26 = Game.objects.create(name="EA FC 26", year=2026)
        self.liga_format = CompetitionFormat.objects.create(
            name="Liga Round Robin",
            format_type=CompetitionFormat.FormatType.ROUND_ROBIN,
            has_playoffs=False,
        )
        self.league = League.objects.create(name="Liga Argentina", country=self.argentina)

        self.season1 = Season.objects.create(
            name="Temporada 1", league=self.league, game=self.ea_fc_26,
            number=1, format=self.liga_format, status=Season.Status.FINISHED,
        )
        self.primera_s1 = Division.objects.create(
            name="Primera División", season=self.season1, order=1, max_clubs=10,
            has_relegation=True, relegation_zone_start=9, relegation_zone_end=10,
        )

        self.season2 = Season.objects.create(
            name="Temporada 2", league=self.league, game=self.ea_fc_26,
            number=2, format=self.liga_format, status=Season.Status.UPCOMING,
        )
        self.primera_s2 = Division.objects.create(
            name="Primera División", season=self.season2, order=1, max_clubs=10,
            has_relegation=True, relegation_zone_start=9, relegation_zone_end=10,
        )

    def _create_clubs(self):
        self.stdout.write("  Creating 10 clubs...")
        club_names = [
            ("Buenos Aires FC", "BAFC"), ("Rosario United", "RUFC"),
            ("Córdoba Pro", "CDPR"), ("Patagonia FC", "PAFC"),
            ("Mendoza City", "MZFC"), ("Santa Fe SC", "SFSC"),
            ("Tucumán Town", "TCTN"), ("Salta Sport", "SALT"),
            ("Entre Ríos FC", "ERFC"), ("Chaco United", "CHUN"),
        ]
        self.clubs = []
        for name, short in club_names:
            club = Club.objects.create(name=name, short_name=short, country=self.argentina)
            self.clubs.append(club)

    def _create_players(self):
        self.stdout.write("  Creating 60 players (6 per club)...")
        positions = ["ARQ", "DEF", "DEF", "MED", "MED", "DEL"]
        platforms = ["PLAYSTATION", "XBOX", "PC"]

        self.players = []
        for ci, club in enumerate(self.clubs):
            for pi, pos in enumerate(positions):
                nickname = f"player_{ci}_{pi}"
                player = Player.objects.create(
                    nickname=nickname,
                    platform=random.choice(platforms),
                    country=self.argentina,
                    position=pos,
                )
                self.players.append(player)

    def _create_season1(self):
        self.stdout.write("  Creating Season 1 (FINISHED, 10 clubs, round-robin)...")

        club_seasons = []
        for club in self.clubs:
            cs = ClubSeason.objects.create(
                club=club, season=self.season1, division=self.primera_s1,
            )
            club_seasons.append(cs)

        for cs in club_seasons:
            player_in_club = [p for p in self.players
                              if p.nickname.startswith(f"player_{self.clubs.index(cs.club)}_")]
            for p in player_in_club:
                PlayerClubHistory.objects.create(
                    player=p, club_season=cs,
                    joined_at=timezone.now() - timedelta(days=180),
                    left_at=timezone.now() - timedelta(days=30),
                )

        import itertools
        pairs = list(itertools.combinations(club_seasons, 2))
        random.shuffle(pairs)

        matches_per_matchday = len(pairs) // 19 + 1
        matchday_num = 0
        idx = 0

        while idx < len(pairs):
            matchday_num += 1
            matchday = Matchday.objects.create(
                season=self.season1, division=self.primera_s1,
                number=matchday_num, name=f"Jornada {matchday_num}",
                date=timezone.now().date() + timedelta(days=matchday_num * 7),
            )
            batch = pairs[idx:idx + matches_per_matchday]
            idx += matches_per_matchday

            for home_cs, away_cs in batch:
                home_goals = random.randint(0, 4)
                away_goals = random.randint(0, 3)
                match = Match.objects.create(
                    season=self.season1, division=self.primera_s1,
                    matchday=matchday, home_club_season=home_cs,
                    away_club_season=away_cs, home_goals=home_goals,
                    away_goals=away_goals, status=Match.Status.FINISHED,
                    date=matchday.date,
                )
                self._create_match_events(match, home_cs, away_cs)

        recalculate_standings(self.season1, self.primera_s1)

    def _create_season2(self):
        self.stdout.write("  Creating Season 2 (UPCOMING, 10 clubs, no matches)...")

        for club in self.clubs:
            cs = ClubSeason.objects.create(
                club=club, season=self.season2, division=self.primera_s2,
            )
            player_in_club = [p for p in self.players
                              if p.nickname.startswith(f"player_{self.clubs.index(club)}_")]
            for p in player_in_club:
                PlayerClubHistory.objects.create(
                    player=p, club_season=cs,
                    joined_at=timezone.now() + timedelta(days=30),
                )

    def _create_match_events(self, match, home_cs, away_cs):
        home_player_idx = self.clubs.index(home_cs.club) * 6
        away_player_idx = self.clubs.index(away_cs.club) * 6

        home_players = self.players[home_player_idx:home_player_idx + 6]
        away_players = self.players[away_player_idx:away_player_idx + 6]

        home_mps, away_mps = [], []
        for p in home_players:
            mp = MatchPlayer.objects.create(
                match=match, player=p, club_season=home_cs,
                display_name=p.nickname, is_starter=True,
            )
            home_mps.append(mp)
        for p in away_players:
            mp = MatchPlayer.objects.create(
                match=match, player=p, club_season=away_cs,
                display_name=p.nickname, is_starter=True,
            )
            away_mps.append(mp)

        used_minutes = set()

        def _pick_minute():
            m = random.randint(1, 90)
            while m in used_minutes:
                m = random.randint(1, 90)
            used_minutes.add(m)
            return m

        for team_mps, goals in [(home_mps, match.home_goals), (away_mps, match.away_goals)]:
            for _ in range(goals or 0):
                scorer = random.choice([mp for mp in team_mps if mp.player])
                minute = _pick_minute()
                MatchEvent.objects.create(
                    match=match, match_player=scorer,
                    event_type=MatchEvent.EventType.GOAL, minute=minute,
                )
                if random.random() < 0.7:
                    assister = random.choice(
                        [mp for mp in team_mps if mp.player and mp != scorer]
                    )
                    MatchEvent.objects.create(
                        match=match, match_player=assister,
                        event_type=MatchEvent.EventType.ASSIST, minute=minute,
                    )

        if random.random() < 0.3:
            team = random.choice([home_mps, away_mps])
            mp = random.choice([mp for mp in team if mp.player])
            MatchEvent.objects.create(
                match=match, match_player=mp,
                event_type=MatchEvent.EventType.OWN_GOAL, minute=_pick_minute(),
            )

        for _ in range(random.randint(0, 3)):
            team = random.choice([home_mps, away_mps])
            mp = random.choice([mp for mp in team if mp.player])
            MatchEvent.objects.create(
                match=match, match_player=mp,
                event_type=random.choice([
                    MatchEvent.EventType.YELLOW_CARD,
                    MatchEvent.EventType.RED_CARD,
                ]),
                minute=_pick_minute(),
            )

        mvp_team = random.choice([home_mps, away_mps])
        mvp_mp = random.choice([mp for mp in mvp_team if mp.player])
        MatchEvent.objects.create(
            match=match, match_player=mvp_mp,
            event_type=MatchEvent.EventType.MVP, minute=90,
        )
