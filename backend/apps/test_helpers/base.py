from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from apps.accounts.models import User
from apps.competitions.models import Country, Game, CompetitionFormat, League, Season, Division
from apps.clubs.models import Club, ClubSeason
from apps.players.models import Player, PlayerClubHistory
from apps.matches.models import Matchday, Match, MatchPlayer, MatchEvent


class BaseTestCase(TestCase):
    """Base test case with common fixtures."""

    def setUp(self):
        # Users
        self.superadmin = User.objects.create_superuser(
            username="superadmin",
            email="superadmin@test.com",
            password="test1234",
            role=User.Role.SUPERADMIN,
        )
        self.admin_liga_user = User.objects.create_user(
            username="admin_liga",
            email="admin_liga@test.com",
            password="test1234",
            role=User.Role.ADMIN_LIGA,
        )
        self.admin_club_user = User.objects.create_user(
            username="admin_club",
            email="admin_club@test.com",
            password="test1234",
            role=User.Role.ADMIN_CLUB,
        )
        self.player_user = User.objects.create_user(
            username="player_user",
            email="player@test.com",
            password="test1234",
            role=User.Role.PLAYER,
        )
        self.normal_user = User.objects.create_user(
            username="normal_user",
            email="normal@test.com",
            password="test1234",
            role=User.Role.USER,
        )

        # Country and Game
        self.argentina = Country.objects.create(name="Argentina", code="AR")
        self.ea_fc_26 = Game.objects.create(name="EA FC 26", year=2026)

        # Format
        self.liga_format = CompetitionFormat.objects.create(
            name="Liga Doble",
            format_type=CompetitionFormat.FormatType.DOUBLE_ROUND_ROBIN,
            has_playoffs=False,
        )

        # League
        self.league = League.objects.create(
            name="Liga Argentina",
            country=self.argentina,
        )

        # Season
        self.season = Season.objects.create(
            name="Temporada 1",
            league=self.league,
            game=self.ea_fc_26,
            number=1,
            format=self.liga_format,
            status=Season.Status.ACTIVE,
        )

        # Divisions
        self.primera = Division.objects.create(
            name="Primera División",
            season=self.season,
            order=1,
            max_clubs=20,
            has_relegation=True,
            relegation_zone_start=18,
            relegation_zone_end=20,
        )
        self.segunda = Division.objects.create(
            name="Segunda División",
            season=self.season,
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

        # Clubs
        self.clubs = []
        for i in range(10):
            club = Club.objects.create(
                name=f"Club {i+1}",
                short_name=f"C{i+1}",
                country=self.argentina,
            )
            self.clubs.append(club)

        # ClubSeasons
        self.club_seasons = []
        for i, club in enumerate(self.clubs):
            cs = ClubSeason.objects.create(
                club=club,
                season=self.season,
                division=self.primera,
            )
            self.club_seasons.append(cs)

        # Players
        self.players = []
        for i in range(22):
            player = Player.objects.create(
                nickname=f"player{i+1}",
                platform=["PLAYSTATION", "XBOX", "PC"][i % 3],
                country=self.argentina,
            )
            self.players.append(player)

        # PlayerClubHistory
        for i, player in enumerate(self.players[:10]):
            PlayerClubHistory.objects.create(
                player=player,
                club_season=self.club_seasons[i],
                joined_at=timezone.now() - timedelta(days=30),
            )
