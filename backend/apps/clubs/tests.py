from django.utils import timezone
from django.test import TestCase
from rest_framework.test import APIClient
from apps.competitions.models import Country, Game, CompetitionFormat, Season, League, Division
from apps.clubs.models import Club, ClubSeason, ClubTitle
from apps.accounts.models import User
from apps.test_helpers.base import BaseTestCase


class BaseClubTestCase(TestCase):
    def setUp(self):
        self.superadmin = User.objects.create_superuser(
            username="superadmin", email="super@test.com",
            password="test1234", role=User.Role.SUPERADMIN,
        )
        self.argentina = Country.objects.create(name="Argentina", code="AR")
        self.ea_fc = Game.objects.create(name="EA FC 26", year=2026)
        self.liga_format = CompetitionFormat.objects.create(
            name="Liga", format_type="RR", has_playoffs=False,
        )
        self.league = League.objects.create(name="Liga Argentina", country=self.argentina)
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


class ClubTest(BaseClubTestCase):
    def test_club_creation(self):
        club = Club.objects.create(name="Test Club", short_name="TC", country=self.argentina)
        self.assertEqual(club.name, "Test Club")
        self.assertTrue(club.is_active)

    def test_club_season_creation(self):
        cs = ClubSeason.objects.create(
            club=self.club, season=self.season, division=self.division,
        )
        self.assertEqual(cs.club, self.club)
        self.assertEqual(cs.status, ClubSeason.Status.ACTIVE)

    def test_club_cannot_be_in_two_divisions_same_season(self):
        ClubSeason.objects.create(
            club=self.club, season=self.season, division=self.division,
        )
        with self.assertRaises(Exception):
            ClubSeason.objects.create(
                club=self.club, season=self.season, division=self.division,
            )

    def test_club_can_be_in_different_seasons(self):
        season2 = Season.objects.create(
            name="Temporada 2", league=self.league,
            game=self.ea_fc, number=2, format=self.liga_format,
        )
        ClubSeason.objects.create(
            club=self.club, season=self.season, division=self.division,
        )
        cs = ClubSeason.objects.create(
            club=self.club2, season=season2, division=self.division,
        )
        self.assertEqual(cs.club, self.club2)
        self.assertEqual(cs.season, season2)


class ClubTitleTest(BaseClubTestCase):
    def test_title_creation(self):
        title = ClubTitle.objects.create(
            club=self.club, season=self.season, division=self.division,
            title_type=ClubTitle.TitleType.CHAMPION, name="Campeón Liga Argentina",
            awarded_at=timezone.now(), awarded_by=self.superadmin,
        )
        self.assertEqual(title.title_type, ClubTitle.TitleType.CHAMPION)

    def test_title_types(self):
        for title_type in ClubTitle.TitleType:
            ClubTitle.objects.create(
                club=self.club, season=self.season, title_type=title_type,
                name=f"Test {title_type}", awarded_at=timezone.now(),
                awarded_by=self.superadmin,
            )
        titles = ClubTitle.objects.filter(club=self.club)
        self.assertEqual(titles.count(), len(ClubTitle.TitleType))

    def test_multiple_titles_per_club(self):
        ClubTitle.objects.create(
            club=self.club, season=self.season,
            title_type=ClubTitle.TitleType.CHAMPION, name="Campeón",
            awarded_at=timezone.now(), awarded_by=self.superadmin,
        )
        ClubTitle.objects.create(
            club=self.club, season=self.season,
            title_type=ClubTitle.TitleType.RUNNER_UP, name="Subcampeón",
            awarded_at=timezone.now(), awarded_by=self.superadmin,
        )
        titles = ClubTitle.objects.filter(club=self.club)
        self.assertEqual(titles.count(), 2)


class ClubTitleApiTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.client = APIClient()

    def test_anonymous_can_list_titles(self):
        resp = self.client.get("/api/club-titles/")
        self.assertEqual(resp.status_code, 200)

    def test_player_cannot_create_title(self):
        self.client.force_authenticate(self.player_user)
        resp = self.client.post(
            "/api/club-titles/",
            {
                "club": self.clubs[0].id,
                "season": self.season.id,
                "title_type": "CHAMPION",
                "name": "Campeón",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 403)

    def test_admin_liga_creates_title_with_awarded_by(self):
        self.client.force_authenticate(self.admin_liga_user)
        resp = self.client.post(
            "/api/club-titles/",
            {
                "club": self.clubs[0].id,
                "season": self.season.id,
                "title_type": "CHAMPION",
                "name": "Campeón Temporada 1",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.data)
        title = ClubTitle.objects.get(pk=resp.data["id"])
        self.assertEqual(title.awarded_by, self.admin_liga_user)
        self.assertIsNotNone(title.awarded_at)

    def test_admin_liga_can_delete_title(self):
        title = ClubTitle.objects.create(
            club=self.clubs[0], season=self.season,
            title_type=ClubTitle.TitleType.CHAMPION, name="Campeón",
            awarded_at=timezone.now(), awarded_by=self.superadmin,
        )
        self.client.force_authenticate(self.admin_liga_user)
        resp = self.client.delete(f"/api/club-titles/{title.id}/")
        self.assertEqual(resp.status_code, 204)
        self.assertFalse(ClubTitle.objects.filter(pk=title.id).exists())
