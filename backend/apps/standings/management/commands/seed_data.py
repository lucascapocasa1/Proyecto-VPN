import random
from datetime import timedelta
from django.utils import timezone
from django.core.management.base import BaseCommand
from apps.accounts.models import User
from apps.competitions.models import Country, Game, CompetitionFormat, League, Season, Division
from apps.clubs.models import Club, ClubSeason, ClubTitle
from apps.players.models import Player, PlayerClubHistory
from apps.standings.services import recalculate_standings
from apps.standings.management.commands._seed_helpers import (
    S1_MATCHDAYS,
    S2_PLAYED_MATCHDAYS,
    S2_TOTAL_MATCHDAYS,
    s1_matchday_date,
    s2_matchday_date,
    joined_at_s1,
    left_at_s1,
    joined_at_s2,
    create_matchdays,
    apply_transfers,
    pick_forced_transfer_ids,
)


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

FIRST_NAMES = [
    "Lucas", "Mateo", "Santiago", "Thiago", "Mateo", "Valentino", "Joaquín",
    "Benjamín", "Santino", "Lautaro", "Emiliano", "Agustín", "Dylan", "Ian",
    "Alejandro", "Diego", "Martín", "Nicolás", "Franco", "Facundo", "Tomás",
    "Ramiro", "Bruno", "Gonzalo", "Axel", "Mateo", "Luciano", "Fernando",
    "Eduardo", "Carlos", "Sergio", "Andrés", "Miguel", "Ricardo", "Pablo",
    "Roberto", "Daniel", "Marcelo", "Gustavo", "Héctor", "Raúl", "Oscar",
    "Enzo", "Kevin", "Alan", "Thiago", "Gastón", "Cristian", "Maximiliano",
]

LAST_NAMES = [
    "García", "López", "Martínez", "Rodríguez", "Fernández", "Álvarez",
    "Romero", "Díaz", "Torres", "Acuña", "Ruiz", "Flores", "Benítez",
    "Medina", "Herrera", "Aguilar", "Pereyra", "Giménez", "Morales",
    "Ortiz", "Sosa", "Rojas", "Vargas", "Castro", "Mendoza", "Luna",
    "Quiroga", "Muñoz", "Córdoba", "Ríos", "Paz", "González", "Ávila",
    "Campos", "Vera", "Navarro", "Campos", "Reyes", "Figueroa",
]

NICKNAME_SUFFIXES = [
    "10", "7", "9", "11", "5", "8", "3", "6", "4", "2",
    "FC", "pro", "goal", "king", "ace", "star", "magic",
]


class Command(BaseCommand):
    help = "Create full seed data: 2 countries, 2 seasons each, ~34K records"

    def handle(self, *args, **options):
        random.seed(42)
        self.stdout.write("Creating full seed data (2 countries)...")

        self._create_users()
        self._create_shared_infra()

        self.used_nicknames = set()

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

    def _generate_nickname(self):
        while True:
            first = random.choice(FIRST_NAMES)
            last = random.choice(LAST_NAMES)
            suffix = random.choice(NICKNAME_SUFFIXES)
            nickname_type = random.choice(["first_last", "first_suffix", "last_suffix", "firstlast"])
            if nickname_type == "first_last":
                nick = f"{first}_{last[:3].lower()}"
            elif nickname_type == "first_suffix":
                nick = f"{first.lower()}{suffix}"
            elif nickname_type == "last_suffix":
                nick = f"{last.lower()}{suffix}"
            else:
                nick = f"{first.lower()}{last.lower()}"
            if nick not in self.used_nicknames:
                self.used_nicknames.add(nick)
                return nick

    def _populate_country(self, country, club_names, league_name):
        league = League.objects.create(name=league_name, country=country)

        season1 = Season.objects.create(
            name="Temporada 1", league=league, game=self.ea_fc_26,
            number=1, format=self.rr_format, status=Season.Status.FINISHED,
        )
        season2 = Season.objects.create(
            name="Temporada 2", league=league, game=self.ea_fc_26,
            number=2, format=self.rr_format, status=Season.Status.ACTIVE,
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
                    nickname=self._generate_nickname(),
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
                    joined_at=joined_at_s1(),
                    left_at=left_at_s1(),
                )

        all_cs_s2 = cs_s2_primera + cs_s2_segunda
        for cs in all_cs_s2:
            club_idx = clubs.index(cs.club)
            club_players = players[club_idx * 15:(club_idx + 1) * 15]
            for p in club_players:
                PlayerClubHistory.objects.create(
                    player=p, club_season=cs,
                    joined_at=joined_at_s2(),
                )

        self.stdout.write(f"    S1: creating matches for Primera + Segunda...")
        for div, css in [(primera_s1, cs_s1_primera), (segunda_s1, cs_s1_segunda)]:
            created, events = create_matchdays(
                season1, div, css, s1_matchday_date,
                1, S1_MATCHDAYS, finished=True,
            )
            self.stdout.write(f"      {div.name}: {created} matches, {events} events")

        recalculate_standings(season1, primera_s1)
        recalculate_standings(season1, segunda_s1)

        ClubTitle.objects.create(
            club=clubs_primera[0], season=season1, division=primera_s1,
            title_type=ClubTitle.TitleType.CHAMPION,
            name=f"Campeón {league_name} Temporada 1",
            awarded_at=timezone.now() + timedelta(days=-77),
            awarded_by=self.superadmin,
        )

        forced_ids = pick_forced_transfer_ids(country, season1, count=5, top_limit=10)
        transfers = apply_transfers(country, season2, forced_player_ids=forced_ids)
        self.stdout.write(f"    S2: {transfers} transfers ({len(forced_ids)} forced top scorers)")

        self.stdout.write(f"    S2: creating matchdays 1-{S2_TOTAL_MATCHDAYS} "
                          f"(1-10 finished, 11 scheduled)...")
        for div, css in [(primera_s2, cs_s2_primera), (segunda_s2, cs_s2_segunda)]:
            finished_matches, finished_events = create_matchdays(
                season2, div, css, s2_matchday_date,
                1, S2_PLAYED_MATCHDAYS, finished=True,
            )
            scheduled_matches, _ = create_matchdays(
                season2, div, css, s2_matchday_date,
                S2_TOTAL_MATCHDAYS, S2_TOTAL_MATCHDAYS, finished=False,
            )
            self.stdout.write(
                f"      {div.name}: {finished_matches} finished "
                f"({finished_events} events), {scheduled_matches} scheduled"
            )

        recalculate_standings(season2, primera_s2)
        recalculate_standings(season2, segunda_s2)
