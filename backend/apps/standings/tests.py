from django.test import TestCase
from apps.test_helpers.base import BaseTestCase
from apps.matches.models import Matchday, Match, MatchPlayer, MatchEvent
from apps.standings.models import Standing
from apps.standings.services import recalculate_standings, recalculate_all_standings
from apps.standings.zones import get_zone, ZoneType
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
        self.segunda = Division.objects.create(
            name="Segunda", season=self.season, order=2, max_clubs=20,
            playoff_zone_start=2, playoff_zone_end=9,
            promotion_zone_start=1, promotion_zone_end=1,
            relegation_zone_start=18, relegation_zone_end=20,
        )
        self.clubs = []
        for i in range(12):
            club = Club.objects.create(
                name=f"Club {i+1}", short_name=f"C{i+1}", country=self.argentina,
            )
            self.clubs.append(club)

    def test_champion_zone(self):
        cs = ClubSeason.objects.create(
            club=self.clubs[0], season=self.season, division=self.segunda,
        )
        standing = Standing.objects.create(
            season=self.season, division=self.segunda, club_season=cs, position=1,
        )
        zone = get_zone(standing)
        self.assertEqual(zone, ZoneType.CHAMPION)

    def test_playoff_zone(self):
        cs = ClubSeason.objects.create(
            club=self.clubs[0], season=self.season, division=self.segunda,
        )
        standing = Standing.objects.create(
            season=self.season, division=self.segunda, club_season=cs, position=5,
        )
        zone = get_zone(standing)
        self.assertEqual(zone, ZoneType.PLAYOFF)

    def test_normal_zone(self):
        cs = ClubSeason.objects.create(
            club=self.clubs[0], season=self.season, division=self.segunda,
        )
        standing = Standing.objects.create(
            season=self.season, division=self.segunda, club_season=cs, position=12,
        )
        zone = get_zone(standing)
        self.assertEqual(zone, ZoneType.NORMAL)
