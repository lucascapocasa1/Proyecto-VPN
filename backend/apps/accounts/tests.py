from rest_framework.test import APIClient
from django.test import TestCase

from apps.accounts.models import User, LeagueAdmin, ClubAdmin
from apps.competitions.models import Country, Game, League, Season, Division, CompetitionFormat
from apps.clubs.models import Club, ClubSeason
from apps.players.models import Player
from apps.matches.models import Matchday, Match
from apps.standings.models import Standing


class BaseAPITestCase(TestCase):
    """Base API test with authentication setup."""

    def setUp(self):
        self.client = APIClient()

        self.superadmin = User.objects.create_superuser(
            username="superadmin", email="super@test.com",
            password="test1234", role=User.Role.SUPERADMIN,
        )
        self.admin_liga_user = User.objects.create_user(
            username="admin_liga", email="liga@test.com",
            password="test1234", role=User.Role.ADMIN_LIGA,
        )
        self.admin_club_user = User.objects.create_user(
            username="admin_club", email="club@test.com",
            password="test1234", role=User.Role.ADMIN_CLUB,
        )
        self.player_user = User.objects.create_user(
            username="player_user", email="player@test.com",
            password="test1234", role=User.Role.PLAYER,
        )
        self.normal_user = User.objects.create_user(
            username="normal_user", email="normal@test.com",
            password="test1234", role=User.Role.USER,
        )

        self.argentina = Country.objects.create(name="Argentina", code="AR")
        self.ea_fc = Game.objects.create(name="EA FC 26", year=2026)
        self.liga_format = CompetitionFormat.objects.create(
            name="Liga", format_type="RR", has_playoffs=False,
        )
        self.league = League.objects.create(
            name="Liga Argentina", country=self.argentina,
        )
        self.season = Season.objects.create(
            name="Temporada 1", league=self.league,
            game=self.ea_fc, number=1, format=self.liga_format,
        )
        self.division = Division.objects.create(
            name="Primera", season=self.season, order=1, max_clubs=20,
        )
        self.club = Club.objects.create(
            name="Boca", short_name="BOC", country=self.argentina,
        )
        self.club2 = Club.objects.create(
            name="River", short_name="RIV", country=self.argentina,
        )
        self.club_season = ClubSeason.objects.create(
            club=self.club, season=self.season, division=self.division,
        )
        self.club_season2 = ClubSeason.objects.create(
            club=self.club2, season=self.season, division=self.division,
        )
        self.player = Player.objects.create(nickname="player1", country=self.argentina)


class AuthenticationTest(BaseAPITestCase):
    def test_login(self):
        resp = self.client.post("/api/auth/login/", {
            "username": "superadmin", "password": "test1234",
        }, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)

    def test_login_wrong_password(self):
        resp = self.client.post("/api/auth/login/", {
            "username": "superadmin", "password": "wrong",
        }, format="json")
        self.assertEqual(resp.status_code, 401)

    def test_register(self):
        resp = self.client.post("/api/auth/register/", {
            "username": "newuser",
            "email": "new@test.com",
            "password": "test1234",
            "password_confirm": "test1234",
            "first_name": "New",
            "last_name": "User",
        }, format="json")
        self.assertEqual(resp.status_code, 201)

    def test_profile_authenticated(self):
        self.client.force_authenticate(user=self.normal_user)
        resp = self.client.get("/api/auth/profile/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["username"], "normal_user")

    def test_profile_unauthenticated(self):
        resp = self.client.get("/api/auth/profile/")
        self.assertEqual(resp.status_code, 401)


class CountryPermissionTest(BaseAPITestCase):
    def test_list_public(self):
        resp = self.client.get("/api/countries/")
        self.assertEqual(resp.status_code, 200)

    def test_create_superadmin(self):
        self.client.force_authenticate(user=self.superadmin)
        resp = self.client.post("/api/countries/", {
            "name": "Chile", "code": "CL",
        }, format="json")
        self.assertEqual(resp.status_code, 201)

    def test_create_user_denied(self):
        self.client.force_authenticate(user=self.normal_user)
        resp = self.client.post("/api/countries/", {
            "name": "Chile", "code": "CL",
        }, format="json")
        self.assertEqual(resp.status_code, 403)

    def test_create_player_denied(self):
        self.client.force_authenticate(user=self.player_user)
        resp = self.client.post("/api/countries/", {
            "name": "Chile", "code": "CL",
        }, format="json")
        self.assertEqual(resp.status_code, 403)


class LeaguePermissionTest(BaseAPITestCase):
    def test_list_public(self):
        resp = self.client.get("/api/leagues/")
        self.assertEqual(resp.status_code, 200)

    def test_create_admin_liga(self):
        self.client.force_authenticate(user=self.admin_liga_user)
        resp = self.client.post("/api/leagues/", {
            "name": "Nueva Liga", "country": self.argentina.id,
        }, format="json")
        self.assertEqual(resp.status_code, 201)

    def test_create_user_denied(self):
        self.client.force_authenticate(user=self.normal_user)
        resp = self.client.post("/api/leagues/", {
            "name": "Nueva Liga", "country": self.argentina.id,
        }, format="json")
        self.assertEqual(resp.status_code, 403)


class ClubPermissionTest(BaseAPITestCase):
    def test_list_public(self):
        resp = self.client.get("/api/clubs/")
        self.assertEqual(resp.status_code, 200)

    def test_create_superadmin(self):
        self.client.force_authenticate(user=self.superadmin)
        resp = self.client.post("/api/clubs/", {
            "name": "New Club", "short_name": "NC", "country": self.argentina.id,
        }, format="json")
        self.assertEqual(resp.status_code, 201)

    def test_create_user_denied(self):
        self.client.force_authenticate(user=self.normal_user)
        resp = self.client.post("/api/clubs/", {
            "name": "New Club", "short_name": "NC", "country": self.argentina.id,
        }, format="json")
        self.assertEqual(resp.status_code, 403)


class PlayerPermissionTest(BaseAPITestCase):
    def test_list_public(self):
        resp = self.client.get("/api/players/")
        self.assertEqual(resp.status_code, 200)

    def test_create_superadmin(self):
        self.client.force_authenticate(user=self.superadmin)
        resp = self.client.post("/api/players/", {
            "nickname": "newplayer", "country": self.argentina.id,
        }, format="json")
        self.assertEqual(resp.status_code, 201)

    def test_update_nickname_user_denied(self):
        self.client.force_authenticate(user=self.normal_user)
        resp = self.client.patch(f"/api/players/{self.player.id}/", {
            "nickname": "hacked",
        }, format="json")
        self.assertEqual(resp.status_code, 403)

    def test_update_nickname_superadmin_allowed(self):
        self.client.force_authenticate(user=self.superadmin)
        resp = self.client.patch(f"/api/players/{self.player.id}/", {
            "nickname": "newname",
        }, format="json")
        self.assertEqual(resp.status_code, 200)


class MatchPermissionTest(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.matchday = Matchday.objects.create(
            season=self.season, division=self.division,
            number=1, name="J1",
        )

    def test_list_public(self):
        resp = self.client.get("/api/matches/")
        self.assertEqual(resp.status_code, 200)

    def test_create_admin_liga(self):
        self.client.force_authenticate(user=self.admin_liga_user)
        resp = self.client.post("/api/matches/", {
            "season": self.season.id,
            "division": self.division.id,
            "matchday": self.matchday.id,
            "home_club_season": self.club_season.id,
            "away_club_season": self.club_season2.id,
            "status": "SCHEDULED",
        }, format="json")
        self.assertEqual(resp.status_code, 201)

    def test_create_user_denied(self):
        self.client.force_authenticate(user=self.normal_user)
        resp = self.client.post("/api/matches/", {
            "season": self.season.id,
            "division": self.division.id,
            "matchday": self.matchday.id,
            "home_club_season": self.club_season.id,
            "away_club_season": self.club_season2.id,
            "status": "SCHEDULED",
        }, format="json")
        self.assertEqual(resp.status_code, 403)


class StandingPermissionTest(BaseAPITestCase):
    def test_list_public(self):
        resp = self.client.get("/api/standings/")
        self.assertEqual(resp.status_code, 200)

    def test_recalculate_admin_liga(self):
        self.client.force_authenticate(user=self.admin_liga_user)
        resp = self.client.post("/api/standings/recalculate/", {
            "season_id": self.season.id,
        }, format="json")
        self.assertEqual(resp.status_code, 200)

    def test_recalculate_user_denied(self):
        self.client.force_authenticate(user=self.normal_user)
        resp = self.client.post("/api/standings/recalculate/", {
            "season_id": self.season.id,
        }, format="json")
        self.assertEqual(resp.status_code, 403)


class UserPermissionTest(BaseAPITestCase):
    def test_list_authenticated(self):
        self.client.force_authenticate(user=self.normal_user)
        resp = self.client.get("/api/users/")
        self.assertEqual(resp.status_code, 200)

    def test_list_unauthenticated(self):
        resp = self.client.get("/api/users/")
        self.assertEqual(resp.status_code, 401)

    def test_create_superadmin(self):
        self.client.force_authenticate(user=self.superadmin)
        resp = self.client.post("/api/users/", {
            "username": "newadmin",
            "email": "newadmin@test.com",
            "password": "test1234",
            "role": "ADMIN_LIGA",
        }, format="json")
        self.assertEqual(resp.status_code, 201)

    def test_create_user_denied(self):
        self.client.force_authenticate(user=self.normal_user)
        resp = self.client.post("/api/users/", {
            "username": "newadmin2",
            "email": "newadmin2@test.com",
            "password": "test1234",
            "role": "ADMIN_LIGA",
        }, format="json")
        self.assertEqual(resp.status_code, 403)
