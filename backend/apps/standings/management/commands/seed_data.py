import random
import itertools
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


CLUB_NAMES_ARG = [
    ("Buenos Aires FC", "BAFC"), ("Rosario United", "RUFC"),
    ("Córdoba Pro", "CDPR"), ("Patagonia FC", "PAFC"),
    ("Mendoza City", "MZFC"), ("Santa Fe SC", "SFSC"),
    ("Tucumán Town", "TCTN"), ("Salta Sport", "SALT"),
    ("Entre Ríos FC", "ERFC"), ("Chaco United", "CHUN"),
    ("La Plata FC", "LPFC"), ("Mar del Plata MDQ", "MDPL"),
    ("San Juan FC", "SJFC"), ("Santiago Est.", "SSET"),
    ("Corrientes AC", "CRAC"), ("Neuquén FC", "NQFC"),
    ("Formosa United", "FMUN"), ("San Luis Pro", "SLPR"),
    ("Catamarca FC", "CMFC"), ("Jujuy City", "JJCY"),
    ("Villa María VC", "VMMC"), ("Río Cuarto FC", "RCFC"),
    ("Concepción FC", "CCFC"), ("Resistencia RC", "RESI"),
    ("Posadas FC", "POFC"), ("Rawson WR", "RAWS"),
    ("Bahía Blanca BB", "BBFC"), ("Junín FC", "JUFC"),
    ("Pergamino PG", "PGFC"), ("Olavarría OV", "OVFC"),
    ("Zárate ZR", "ZRFC"), ("Lobos LB", "LBFC"),
    ("Chivilcoy CH", "CHFC"), ("Bragado BG", "BGFC"),
    ("25 de Mayo FM", "FMDM"), ("General Roca GR", "GRFC"),
    ("Cipolletti CI", "CIFC"), ("Viedma VD", "VDFC"),
    ("Bariloche BR", "BRFC"), ("Comodoro CD", "CDFC"),
]

CLUB_NAMES_URY = [
    ("Montevideo FC", "MVFC"), ("Nacional UY", "NACU"),
    ("Peñarol UY", "PENU"), ("Danubio FC", "DANU"),
    ("Defensor SC", "DEFU"), ("Wanderers FC", "WAND"),
    ("Cerro Largo CL", "CLFC"), ("Liverpool UY", "LIUY"),
    ("Plaza Colonia PC", "PLCO"), ("Rentistas FC", "RENT"),
    ("Boston River BR", "BURI"), ("Fénix FC", "FENI"),
    ("Miramar FC", "MIRA"), ("Progreso FC", "PROG"),
    ("Racing UY", "RACU"), ("Suites FC", "SUIF"),
    ("Artigas FC", "ARTI"), ("Durazno FC", "DURF"),
    ("Maldonado FC", "MALF"), ("Paysandú FC", "PAFC"),
    ("River Plate UY", "RPUY"), ("Colón FC", "COLU"),
    ("San Carlos FC", "SCFC"), ("Tacuarembó FC", "TACF"),
    ("Cerro FC", "CERU"), ("Urreta FC", "URRE"),
    ("Juventud UY", "JUUU"), ("Villa Española VE", "VESP"),
    ("Albión FC", "ALBI"), ("Bella Vista BV", "BVFC"),
    ("Deportivo MVD", "DPMV"), ("Huracán FC", "HURU"),
    ("Mar de Fondo MF", "MDFF"), ("Oriental FC", "ORIE"),
    ("Parque FC", "PARF"), ("Solís FC", "SOLF"),
    ("Villa Teresa VT", "VITE"), ("Atenas FC", "ATEN"),
    ("Malvín FC", "MALF"), ("Sayago FC", "SAYF"),
]

POSITIONS = ["ARQ"] * 2 + ["DEF"] * 4 + ["MED"] * 5 + ["DEL"] * 4
PLATFORMS = ["PLAYSTATION", "XBOX", "PC"]


class Command(BaseCommand):
    help = "Create full seed data: 2 countries, 2 seasons each, ~26K records"

    def handle(self, *args, **options):
        random.seed(42)
        self.stdout.write("Creating full seed data (2 countries)...")

        self._create_users()
        self._create_shared_infra()

        self.argentina = self._create_country("Argentina", "AR")
        self._populate_country(self.argentina, CLUB_NAMES_ARG, "Liga Argentina")

        self.uruguay = self._create_country("Uruguay", "UY")
        self._populate_country(self.uruguay, CLUB_NAMES_URY, "Liga Uruguaya")

        self.stdout.write(self.style.SUCCESS("Full seed data created successfully!"))

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

    def _create_shared_infra(self):
        self.stdout.write("  Creating shared infrastructure...")
        self.ea_fc_26 = Game.objects.create(name="EA FC 26", year=2026)
        self.ea_fc_27 = Game.objects.create(name="EA FC 27", year=2027)
        self.rr_format = CompetitionFormat.objects.create(
            name="Liga Round Robin",
            format_type=CompetitionFormat.FormatType.ROUND_ROBIN,
            has_playoffs=False,
        )

    def _create_country(self, name, code):
        self.stdout.write(f"\n  === {name} ===")
        return Country.objects.create(name=name, code=code)

    def _populate_country(self, country, club_names, league_name):
        league = League.objects.create(name=league_name, country=country)

        season1 = Season.objects.create(
            name="Temporada 1", league=league, game=self.ea_fc_26,
            number=1, format=self.rr_format, status=Season.Status.FINISHED,
        )
        season2 = Season.objects.create(
            name="Temporada 2", league=league, game=self.ea_fc_26,
            number=2, format=self.rr_format, status=Season.Status.UPCOMING,
        )

        primera_s1 = Division.objects.create(
            name="Primera División", season=season1, order=1, max_clubs=20,
            has_relegation=True,
            relegation_zone_start=19, relegation_zone_end=20,
        )
        segunda_s1 = Division.objects.create(
            name="Segunda División", season=season1, order=2, max_clubs=20,
            has_relegation=True,
            playoff_zone_start=2, playoff_zone_end=9,
            promotion_zone_start=1, promotion_zone_end=1,
            relegation_zone_start=19, relegation_zone_end=20,
        )
        primera_s2 = Division.objects.create(
            name="Primera División", season=season2, order=1, max_clubs=20,
            has_relegation=True,
            relegation_zone_start=19, relegation_zone_end=20,
        )
        segunda_s2 = Division.objects.create(
            name="Segunda División", season=season2, order=2, max_clubs=20,
            has_relegation=True,
            playoff_zone_start=2, playoff_zone_end=9,
            promotion_zone_start=1, promotion_zone_end=1,
            relegation_zone_start=19, relegation_zone_end=20,
        )

        clubs = []
        for name, short in club_names:
            club = Club.objects.create(name=name, short_name=short, country=country)
            clubs.append(club)

        clubs_primera = clubs[:20]
        clubs_segunda = clubs[20:40]

        players = []
        for ci, club in enumerate(clubs):
            for pi, pos in enumerate(POSITIONS):
                player = Player.objects.create(
                    nickname=f"{country.code.lower()}_{ci}_{pi}_{pos.lower()}",
                    platform=random.choice(PLATFORMS),
                    country=country,
                    position=pos,
                )
                players.append(player)

        self.stdout.write(f"    {len(clubs)} clubs, {len(players)} players")

        cs_s1_primera, cs_s1_segunda = [], []
        for club in clubs_primera:
            cs = ClubSeason.objects.create(club=club, season=season1, division=primera_s1)
            cs_s1_primera.append(cs)
        for club in clubs_segunda:
            cs = ClubSeason.objects.create(club=club, season=season1, division=segunda_s1)
            cs_s1_segunda.append(cs)

        cs_s2_primera, cs_s2_segunda = [], []
        for club in clubs_primera:
            cs = ClubSeason.objects.create(club=club, season=season2, division=primera_s2)
            cs_s2_primera.append(cs)
        for club in clubs_segunda:
            cs = ClubSeason.objects.create(club=club, season=season2, division=segunda_s2)
            cs_s2_segunda.append(cs)

        all_cs_s1 = cs_s1_primera + cs_s1_segunda
        for cs in all_cs_s1:
            club_idx = clubs.index(cs.club)
            club_players = players[club_idx * 15:(club_idx + 1) * 15]
            for p in club_players:
                PlayerClubHistory.objects.create(
                    player=p, club_season=cs,
                    joined_at=timezone.now() - timedelta(days=180),
                    left_at=timezone.now() - timedelta(days=30),
                )

        all_cs_s2 = cs_s2_primera + cs_s2_segunda
        for cs in all_cs_s2:
            club_idx = clubs.index(cs.club)
            club_players = players[club_idx * 15:(club_idx + 1) * 15]
            for p in club_players:
                PlayerClubHistory.objects.create(
                    player=p, club_season=cs,
                    joined_at=timezone.now() + timedelta(days=30),
                )

        self.stdout.write(f"    S1: creating matches for Primera + Segunda...")
        self._create_matches_for_division(
            season1, primera_s1, cs_s1_primera, players, clubs, finished=True,
        )
        self._create_matches_for_division(
            season1, segunda_s1, cs_s1_segunda, players, clubs, finished=True,
        )

        recalculate_standings(season1, primera_s1)
        recalculate_standings(season1, segunda_s1)

        ClubTitle.objects.create(
            club=clubs_primera[0], season=season1, division=primera_s1,
            title_type=ClubTitle.TitleType.CHAMPION,
            name=f"Campeón {league_name} Temporada 1",
            awarded_at=timezone.now() - timedelta(days=15),
            awarded_by=self.superadmin,
        )

        self.stdout.write(f"    S2: UPCOMING, no matches")

    def _create_matches_for_division(self, season, division, club_seasons, players, clubs, finished=True):
        pairs = list(itertools.combinations(club_seasons, 2))
        random.shuffle(pairs)

        matchdays_needed = 19
        pairs_per_matchday = len(pairs) // matchdays_needed

        matches_created = 0
        events_created = 0

        for matchday_num in range(1, matchdays_needed + 1):
            matchday = Matchday.objects.create(
                season=season, division=division,
                number=matchday_num, name=f"Jornada {matchday_num}",
                date=timezone.now().date() + timedelta(days=matchday_num * 7),
            )

            start = (matchday_num - 1) * pairs_per_matchday
            batch = pairs[start:start + pairs_per_matchday]

            for home_cs, away_cs in batch:
                home_goals = random.randint(0, 4)
                away_goals = random.randint(0, 3)
                match = Match.objects.create(
                    season=season, division=division, matchday=matchday,
                    home_club_season=home_cs, away_club_season=away_cs,
                    home_goals=home_goals, away_goals=away_goals,
                    status=Match.Status.FINISHED, date=matchday.date,
                )
                matches_created += 1
                events_created += self._create_match_events(match, home_cs, away_cs, players, clubs)

        self.stdout.write(f"      {division.name}: {matches_created} matches, {events_created} events")

    def _create_match_events(self, match, home_cs, away_cs, players, clubs):
        events_count = 0
        used_minutes = set()

        def _pick_minute():
            m = random.randint(1, 90)
            while m in used_minutes:
                m = random.randint(1, 90)
            used_minutes.add(m)
            return m

        home_idx = clubs.index(home_cs.club) * 15
        away_idx = clubs.index(away_cs.club) * 15
        home_players = players[home_idx:home_idx + 15]
        away_players = players[away_idx:away_idx + 15]

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

        for team_mps, goals in [(home_mps, match.home_goals), (away_mps, match.away_goals)]:
            for _ in range(goals or 0):
                real_players = [mp for mp in team_mps if mp.player]
                if not real_players:
                    continue
                scorer = random.choice(real_players)
                minute = _pick_minute()
                MatchEvent.objects.create(
                    match=match, match_player=scorer,
                    event_type=MatchEvent.EventType.GOAL, minute=minute,
                )
                events_count += 1
                if random.random() < 0.7:
                    others = [mp for mp in real_players if mp != scorer]
                    if others:
                        assister = random.choice(others)
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
