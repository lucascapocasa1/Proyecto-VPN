import random
from datetime import timedelta
from django.utils import timezone
from django.core.management.base import BaseCommand
from apps.accounts.models import User
from apps.competitions.models import Country, Game, CompetitionFormat, League, Season, Division
from apps.clubs.models import Club, ClubSeason, ClubTitle
from apps.players.models import Player, PlayerIdentityHistory, PlayerClubHistory
from apps.matches.models import Matchday, Match, MatchPlayer, MatchEvent
from apps.standings.models import Standing
from apps.standings.services import recalculate_standings


class Command(BaseCommand):
    help = "Create seed data for testing"

    def handle(self, *args, **options):
        self.stdout.write("Creating seed data...")

        self._create_users()
        self._create_countries_and_games()
        self._create_leagues_and_formats()
        self._create_seasons_and_divisions()
        self._create_clubs()
        self._create_players()
        self._create_season1_data()
        self._create_season2_data()

        self.stdout.write(self.style.SUCCESS("Seed data created successfully!"))

    def _create_users(self):
        self.stdout.write("  Creating users...")

        self.superadmin = User.objects.create_superuser(
            username="admin",
            email="admin@test.com",
            password="admin123",
            role=User.Role.SUPERADMIN,
        )

        self.admin_liga = User.objects.create_user(
            username="admin_liga",
            email="admin_liga@test.com",
            password="admin123",
            role=User.Role.ADMIN_LIGA,
        )

        self.admin_club = User.objects.create_user(
            username="admin_club",
            email="admin_club@test.com",
            password="admin123",
            role=User.Role.ADMIN_CLUB,
        )

        self.player_user = User.objects.create_user(
            username="player1",
            email="player1@test.com",
            password="admin123",
            role=User.Role.PLAYER,
        )

    def _create_countries_and_games(self):
        self.stdout.write("  Creating countries and games...")

        self.argentina = Country.objects.create(name="Argentina", code="AR")
        self.uruguay = Country.objects.create(name="Uruguay", code="UY")

        self.ea_fc_26 = Game.objects.create(name="EA FC 26", year=2026)
        self.ea_fc_27 = Game.objects.create(name="EA FC 27", year=2027)

    def _create_leagues_and_formats(self):
        self.stdout.write("  Creating leagues and formats...")

        self.liga_format = CompetitionFormat.objects.create(
            name="Liga Doble",
            format_type=CompetitionFormat.FormatType.DOUBLE_ROUND_ROBIN,
            has_playoffs=False,
        )

        self.copa_format = CompetitionFormat.objects.create(
            name="Copa - Grupos + Eliminación",
            format_type=CompetitionFormat.FormatType.CUSTOM,
            has_playoffs=True,
        )

        self.liga_argentina = League.objects.create(
            name="Liga Argentina",
            country=self.argentina,
        )

        self.liga_uruguay = League.objects.create(
            name="Liga Uruguaya",
            country=self.uruguay,
        )

    def _create_seasons_and_divisions(self):
        self.stdout.write("  Creating seasons and divisions...")

        self.season1 = Season.objects.create(
            name="Temporada 1",
            league=self.liga_argentina,
            game=self.ea_fc_26,
            number=1,
            format=self.liga_format,
            status=Season.Status.FINISHED,
        )

        self.primera_s1 = Division.objects.create(
            name="Primera División",
            season=self.season1,
            order=1,
            max_clubs=20,
            has_relegation=True,
            relegation_zone_start=18,
            relegation_zone_end=20,
        )

        self.segunda_s1 = Division.objects.create(
            name="Segunda División",
            season=self.season1,
            order=2,
            max_clubs=20,
            has_relegation=True,
            playoff_zone_start=2,
            playoff_zone_end=9,
            promotion_zone_start=1,
            promotion_zone_end=1,
            relegation_zone_start=18,
            relegation_zone_end=20,
        )

        self.season2 = Season.objects.create(
            name="Temporada 2",
            league=self.liga_argentina,
            game=self.ea_fc_26,
            number=2,
            format=self.liga_format,
            status=Season.Status.ACTIVE,
        )

        self.primera_s2 = Division.objects.create(
            name="Primera División",
            season=self.season2,
            order=1,
            max_clubs=20,
            has_relegation=True,
            relegation_zone_start=18,
            relegation_zone_end=20,
        )

        self.segunda_s2 = Division.objects.create(
            name="Segunda División",
            season=self.season2,
            order=2,
            max_clubs=20,
            has_relegation=True,
            playoff_zone_start=2,
            playoff_zone_end=9,
            promotion_zone_start=1,
            promotion_zone_end=1,
            relegation_zone_start=18,
            relegation_zone_end=20,
        )

    def _create_clubs(self):
        self.stdout.write("  Creating clubs...")

        club_names = [
            ("Buenos Aires FC", "BAFC"),
            ("Rosario United", "RUFC"),
            ("Córdoba Pro", "CDPR"),
            ("Patagonia FC", "PAFC"),
            ("Mendoza City", "MZFC"),
            ("Santa Fe SC", "SFSC"),
            ("Tucumán Town", "TCTN"),
            ("Salta Sport", "SALT"),
            ("Entre Ríos FC", "ERFC"),
            ("Chaco United", "CHUN"),
            ("La Plata FC", "LPFC"),
            ("Mar del Plata", "MDPL"),
            ("San Juan FC", "SJFC"),
            ("Santiago Est.", "SSET"),
            ("Corrientes AC", "CRAC"),
            ("Neuquén FC", "NQFC"),
            ("Formosa United", "FMUN"),
            ("San Luis Pro", "SLPR"),
            ("Catamarca FC", "CMFC"),
            ("Jujuy City", "JJCY"),
        ]

        self.clubs = []
        for name, short_name in club_names:
            club = Club.objects.create(
                name=name,
                short_name=short_name,
                country=self.argentina,
            )
            self.clubs.append(club)

    def _create_players(self):
        self.stdout.write("  Creating players...")

        player_data = [
            ("lucaspro10", "PLAYSTATION"),
            ("mati10", "XBOX"),
            ("proplayer99", "PC"),
            ("facu_fc", "PLAYSTATION"),
            ("pepe_goals", "XBOX"),
            ("carlos_assist", "PC"),
            ("diego_mvp", "PLAYSTATION"),
            ("fernando_def", "XBOX"),
            ("gabi_mid", "PC"),
            ("hector_gk", "PLAYSTATION"),
            ("ivan_wing", "XBOX"),
            ("julian_striker", "PC"),
            ("kevin_cb", "PLAYSTATION"),
            ("leo_right", "XBOX"),
            ("marco_left", "PC"),
            ("nico_str", "PLAYSTATION"),
            ("oscar_cam", "XBOX"),
            ("pablo_vol", "PC"),
            ("raul_att", "PLAYSTATION"),
            ("sergio_mid", "XBOX"),
            ("tomas_def", "PC"),
            ("ulises_gk", "PLAYSTATION"),
            ("victor_wing", "XBOX"),
            ("walter_striker", "PC"),
            ("xavier_cb", "PLAYSTATION"),
            ("yuri_right", "XBOX"),
            ("zeta_left", "PC"),
            ("bot_sergio", None),
            ("bot_pedro", None),
            ("bot_jorge", None),
        ]

        self.players = []
        for nickname, platform in player_data:
            player = Player.objects.create(
                nickname=nickname,
                platform=platform,
                country=self.argentina,
            )
            self.players.append(player)

        Player.objects.create(
            nickname="lucaspro10_v2",
            platform="PC",
            country=self.argentina,
        )

        PlayerIdentityHistory.objects.create(
            player=self.players[0],
            nickname="lucaspro10_old",
            changed_at=timezone.now() - timedelta(days=30),
            changed_by=self.superadmin,
            reason="Cambio de nickname",
        )

    def _create_season1_data(self):
        self.stdout.write("  Creating Season 1 data...")

        club_seasons_s1_primera = []
        for club in self.clubs[:10]:
            cs = ClubSeason.objects.create(
                club=club,
                season=self.season1,
                division=self.primera_s1,
            )
            club_seasons_s1_primera.append(cs)

        club_seasons_s1_segunda = []
        for club in self.clubs[10:20]:
            cs = ClubSeason.objects.create(
                club=club,
                season=self.season1,
                division=self.segunda_s1,
            )
            club_seasons_s1_segunda.append(cs)

        self._create_matches_for_division(
            self.season1,
            self.primera_s1,
            club_seasons_s1_primera,
            finished=True,
        )

        self._create_matches_for_division(
            self.season1,
            self.segunda_s1,
            club_seasons_s1_segunda,
            finished=True,
        )

        recalculate_standings(self.season1, self.primera_s1)
        recalculate_standings(self.season1, self.segunda_s1)

        ClubTitle.objects.create(
            club=self.clubs[0],
            season=self.season1,
            division=self.primera_s1,
            title_type=ClubTitle.TitleType.CHAMPION,
            name="Campeón Liga Argentina Temporada 1",
            awarded_at=timezone.now() - timedelta(days=15),
            awarded_by=self.superadmin,
        )

    def _create_season2_data(self):
        self.stdout.write("  Creating Season 2 data...")

        club_seasons_s2 = []
        for club in self.clubs[:20]:
            cs = ClubSeason.objects.create(
                club=club,
                season=self.season2,
                division=self.primera_s2,
            )
            club_seasons_s2.append(cs)

        self._create_matches_for_division(
            self.season2,
            self.primera_s2,
            club_seasons_s2[:10],
            finished=False,
            scheduled_count=5,
        )

        recalculate_standings(self.season2, self.primera_s2)

    def _create_matches_for_division(self, season, division, club_seasons, finished=True, scheduled_count=0):
        self.stdout.write(f"    Creating matches for {division.name}...")

        matches_created = 0
        events_created = 0

        import itertools
        pairs = list(itertools.combinations(club_seasons, 2))
        random.shuffle(pairs)

        matchdays_needed = min(len(pairs), 19 if finished else scheduled_count)
        pairs_per_matchday = len(pairs) // max(matchdays_needed, 1)

        for matchday_num in range(1, matchdays_needed + 1):
            matchday = Matchday.objects.create(
                season=season,
                division=division,
                number=matchday_num,
                name=f"Jornada {matchday_num}",
                date=timezone.now().date() + timedelta(days=matchday_num * 7),
            )

            start_idx = (matchday_num - 1) * pairs_per_matchday
            end_idx = start_idx + pairs_per_matchday
            matchday_pairs = pairs[start_idx:end_idx]

            for home_cs, away_cs in matchday_pairs:
                match_status = Match.Status.FINISHED if finished else Match.Status.SCHEDULED
                home_goals = random.randint(0, 4) if finished else None
                away_goals = random.randint(0, 3) if finished else None

                match = Match.objects.create(
                    season=season,
                    division=division,
                    matchday=matchday,
                    home_club_season=home_cs,
                    away_club_season=away_cs,
                    home_goals=home_goals,
                    away_goals=away_goals,
                    status=match_status,
                    date=matchday.date,
                )
                matches_created += 1

                if finished:
                    events_created += self._create_match_events(match, home_cs, away_cs)

        self.stdout.write(
            f"      {matches_created} matches, {events_created} events"
        )

    def _create_match_events(self, match, home_cs, away_cs):
        events_count = 0

        home_players = self.players[:6]
        away_players = self.players[6:12]

        home_match_players = []
        away_match_players = []

        for i, player in enumerate(home_players):
            mp = MatchPlayer.objects.create(
                match=match,
                player=player,
                club_season=home_cs,
                display_name=player.nickname,
                is_starter=i < 11,
            )
            home_match_players.append(mp)
            events_count += 1

        for i in range(11 - len(home_players)):
            mp = MatchPlayer.objects.create(
                match=match,
                player=None,
                club_season=home_cs,
                display_name="BOT",
                is_starter=False,
            )
            home_match_players.append(mp)
            events_count += 1

        for i, player in enumerate(away_players):
            mp = MatchPlayer.objects.create(
                match=match,
                player=player,
                club_season=away_cs,
                display_name=player.nickname,
                is_starter=i < 11,
            )
            away_match_players.append(mp)
            events_count += 1

        for i in range(11 - len(away_players)):
            mp = MatchPlayer.objects.create(
                match=match,
                player=None,
                club_season=away_cs,
                display_name="BOT",
                is_starter=False,
            )
            away_match_players.append(mp)
            events_count += 1

        if match.home_goals and match.home_goals > 0:
            for _ in range(match.home_goals):
                scorer = random.choice([mp for mp in home_match_players if mp.player])
                minute = random.randint(1, 90)
                MatchEvent.objects.create(
                    match=match,
                    match_player=scorer,
                    event_type=MatchEvent.EventType.GOAL,
                    minute=minute,
                )
                events_count += 1

                if random.random() < 0.7:
                    assister = random.choice(
                        [mp for mp in home_match_players if mp.player and mp != scorer]
                    )
                    MatchEvent.objects.create(
                        match=match,
                        match_player=assister,
                        event_type=MatchEvent.EventType.ASSIST,
                        minute=minute,
                    )
                    events_count += 1

        if match.away_goals and match.away_goals > 0:
            for _ in range(match.away_goals):
                scorer = random.choice([mp for mp in away_match_players if mp.player])
                minute = random.randint(1, 90)
                MatchEvent.objects.create(
                    match=match,
                    match_player=scorer,
                    event_type=MatchEvent.EventType.GOAL,
                    minute=minute,
                )
                events_count += 1

                if random.random() < 0.7:
                    assister = random.choice(
                        [mp for mp in away_match_players if mp.player and mp != scorer]
                    )
                    MatchEvent.objects.create(
                        match=match,
                        match_player=assister,
                        event_type=MatchEvent.EventType.ASSIST,
                        minute=minute,
                    )
                    events_count += 1

        if random.random() < 0.3:
            own_goal_team = random.choice([home_match_players, away_match_players])
            own_goal_mp = random.choice([mp for mp in own_goal_team if mp.player])
            MatchEvent.objects.create(
                match=match,
                match_player=own_goal_mp,
                event_type=MatchEvent.EventType.OWN_GOAL,
                minute=random.randint(1, 90),
            )
            events_count += 1

        for _ in range(random.randint(0, 4)):
            team = random.choice([home_match_players, away_match_players])
            card_mp = random.choice([mp for mp in team if mp.player])
            event_type = random.choice([
                MatchEvent.EventType.YELLOW_CARD,
                MatchEvent.EventType.RED_CARD,
            ])
            MatchEvent.objects.create(
                match=match,
                match_player=card_mp,
                event_type=event_type,
                minute=random.randint(1, 90),
            )
            events_count += 1

        mvp_team = random.choice([home_match_players, away_match_players])
        mvp_mp = random.choice([mp for mp in mvp_team if mp.player])
        MatchEvent.objects.create(
            match=match,
            match_player=mvp_mp,
            event_type=MatchEvent.EventType.MVP,
            minute=90,
        )
        events_count += 1

        return events_count
