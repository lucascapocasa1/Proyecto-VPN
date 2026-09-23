from django.test import TestCase
from apps.test_helpers.base import BaseTestCase
from apps.matches.models import Matchday, Match, MatchPlayer, MatchEvent
from apps.standings.models import Standing
from apps.standings.services import recalculate_standings, recalculate_all_standings
from apps.standings.zones import get_zone, get_zone_display, ZoneType
from apps.clubs.models import Club, ClubSeason


class StandingsRecalculationTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.matchday = Matchday.objects.create(
            season=self.season, division=self.primera,
            number=1, name="Jornada 1",
        )

    def test_empty_standings(self):
        standings = recalculate_standings(self.season, self.primera)
        self.assertEqual(standings.count(), 10)

    def test_win_gives_3_points(self):
        Match.objects.create(
            season=self.season, division=self.primera, matchday=self.matchday,
            home_club_season=self.club_seasons[0],
            away_club_season=self.club_seasons[1],
            home_goals=2, away_goals=1, status=Match.Status.FINISHED,
        )
        recalculate_standings(self.season, self.primera)

        home = Standing.objects.get(
            season=self.season, division=self.primera,
            club_season=self.club_seasons[0],
        )
        away = Standing.objects.get(
            season=self.season, division=self.primera,
            club_season=self.club_seasons[1],
        )
        self.assertEqual(home.points, 3)
        self.assertEqual(home.won, 1)
        self.assertEqual(away.points, 0)
        self.assertEqual(away.lost, 1)

    def test_draw_gives_1_point(self):
        Match.objects.create(
            season=self.season, division=self.primera, matchday=self.matchday,
            home_club_season=self.club_seasons[0],
            away_club_season=self.club_seasons[1],
            home_goals=1, away_goals=1, status=Match.Status.FINISHED,
        )
        recalculate_standings(self.season, self.primera)

        home = Standing.objects.get(club_season=self.club_seasons[0])
        away = Standing.objects.get(club_season=self.club_seasons[1])
        self.assertEqual(home.points, 1)
        self.assertEqual(home.drawn, 1)
        self.assertEqual(away.points, 1)

    def test_goal_difference(self):
        Match.objects.create(
            season=self.season, division=self.primera, matchday=self.matchday,
            home_club_season=self.club_seasons[0],
            away_club_season=self.club_seasons[1],
            home_goals=3, away_goals=1, status=Match.Status.FINISHED,
        )
        recalculate_standings(self.season, self.primera)

        home = Standing.objects.get(club_season=self.club_seasons[0])
        away = Standing.objects.get(club_season=self.club_seasons[1])
        self.assertEqual(home.goal_difference, 2)
        self.assertEqual(away.goal_difference, -2)

    def test_position_ordering(self):
        Match.objects.create(
            season=self.season, division=self.primera, matchday=self.matchday,
            home_club_season=self.club_seasons[0],
            away_club_season=self.club_seasons[1],
            home_goals=3, away_goals=0, status=Match.Status.FINISHED,
        )
        Match.objects.create(
            season=self.season, division=self.primera, matchday=self.matchday,
            home_club_season=self.club_seasons[2],
            away_club_season=self.club_seasons[3],
            home_goals=1, away_goals=0, status=Match.Status.FINISHED,
        )
        recalculate_standings(self.season, self.primera)

        standings = Standing.objects.filter(
            season=self.season, division=self.primera
        ).order_by("position")

        self.assertEqual(standings[0].club_season, self.club_seasons[0])
        self.assertEqual(standings[0].position, 1)
        self.assertEqual(standings[1].club_season, self.club_seasons[2])
        self.assertEqual(standings[1].position, 2)

    def test_multiple_matches_accumulate_points(self):
        for i in range(5):
            md = Matchday.objects.create(
                season=self.season, division=self.primera,
                number=i + 2, name=f"Jornada {i + 2}",
            )
            Match.objects.create(
                season=self.season, division=self.primera, matchday=md,
                home_club_season=self.club_seasons[0],
                away_club_season=self.club_seasons[i + 1],
                home_goals=2, away_goals=0, status=Match.Status.FINISHED,
            )
        recalculate_standings(self.season, self.primera)

        standings = Standing.objects.filter(
            season=self.season, division=self.primera
        ).order_by("-points")

        top = standings[0]
        self.assertEqual(top.club_season, self.club_seasons[0])
        self.assertEqual(top.points, 15)
        self.assertEqual(top.won, 5)
        self.assertEqual(top.played, 5)


class ZonesTest(TestCase):
    def setUp(self):
        from apps.accounts.models import User
        from apps.competitions.models import Country, Game, CompetitionFormat, League, Season, Division
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
        self.primera = Division.objects.create(
            name="Primera", season=self.season, order=1, max_clubs=20,
            promotion_zone_start=19, promotion_zone_end=19,
            relegation_zone_start=20, relegation_zone_end=20,
        )
        self.segunda = Division.objects.create(
            name="Segunda", season=self.season, order=2, max_clubs=20,
            playoff_zone_start=2, playoff_zone_end=9,
            promotion_zone_start=19, promotion_zone_end=19,
            relegation_zone_start=20, relegation_zone_end=20,
        )
        self.clubs = []
        for i in range(24):
            club = Club.objects.create(
                name=f"Club {i+1}", short_name=f"C{i+1}", country=self.argentina,
            )
            self.clubs.append(club)

    def _standing(self, division, position, offset=0):
        cs = ClubSeason.objects.create(
            club=self.clubs[offset], season=self.season, division=division,
        )
        return Standing.objects.create(
            season=self.season, division=division, club_season=cs, position=position,
        )

    def test_champion_zone(self):
        standing = self._standing(self.segunda, 1)
        self.assertEqual(get_zone(standing), ZoneType.CHAMPION)

    def test_playoff_zone(self):
        standing = self._standing(self.segunda, 5)
        self.assertEqual(get_zone(standing), ZoneType.PLAYOFF)

    def test_normal_zone(self):
        standing = self._standing(self.segunda, 12)
        self.assertEqual(get_zone(standing), ZoneType.NORMAL)

    def test_promotion_zone_segunda(self):
        standing = self._standing(self.segunda, 19, offset=1)
        self.assertEqual(get_zone(standing), ZoneType.PROMOTION)
        self.assertEqual(get_zone_display(ZoneType.PROMOTION), "PROMOCIÓN")

    def test_relegation_zone_segunda(self):
        standing = self._standing(self.segunda, 20, offset=2)
        self.assertEqual(get_zone(standing), ZoneType.RELEGATION)
        self.assertEqual(get_zone_display(ZoneType.RELEGATION), "DESCENSO")

    def test_promotion_zone_primera(self):
        standing = self._standing(self.primera, 19, offset=3)
        self.assertEqual(get_zone(standing), ZoneType.PROMOTION)

    def test_relegation_zone_primera(self):
        standing = self._standing(self.primera, 20, offset=4)
        self.assertEqual(get_zone(standing), ZoneType.RELEGATION)

    def test_primera_has_no_playoff(self):
        standing = self._standing(self.primera, 5, offset=5)
        self.assertEqual(get_zone(standing), ZoneType.NORMAL)

    def test_primera_champion_zone(self):
        standing = self._standing(self.primera, 1, offset=6)
        self.assertEqual(get_zone(standing), ZoneType.CHAMPION)

    def test_zone_displays_match_frontend_keys(self):
        expected = {
            ZoneType.CHAMPION: "CAMPEÓN",
            ZoneType.PLAYOFF: "REDUCIDO",
            ZoneType.PROMOTION: "PROMOCIÓN",
            ZoneType.RELEGATION: "DESCENSO",
            ZoneType.NORMAL: None,
        }
        for zone, display in expected.items():
            self.assertEqual(get_zone_display(zone), display)
