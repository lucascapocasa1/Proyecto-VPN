from datetime import timedelta
from django.utils import timezone
from apps.test_helpers.base import BaseTestCase
from apps.matches.models import Matchday, Match, MatchPlayer, MatchEvent, MatchPerformance
from apps.statistics.services import (
    get_player_statistics,
    get_player_stats_by_club_season,
    get_top_scorers,
    get_top_assists,
    get_top_mvp,
    get_performance_leaderboard,
    get_performance_by_position,
    get_player_match_series,
)


class PlayerStatisticsTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.matchday = Matchday.objects.create(
            season=self.season, division=self.primera,
            number=1, name="Jornada 1",
        )
        self.match = Match.objects.create(
            season=self.season, division=self.primera, matchday=self.matchday,
            home_club_season=self.club_seasons[0],
            away_club_season=self.club_seasons[1],
            home_goals=2, away_goals=1, status=Match.Status.FINISHED,
        )
        self.home_mp = MatchPlayer.objects.create(
            match=self.match, player=self.players[0],
            club_season=self.club_seasons[0],
            display_name=self.players[0].nickname,
        )
        self.away_mp = MatchPlayer.objects.create(
            match=self.match, player=self.players[1],
            club_season=self.club_seasons[1],
            display_name=self.players[1].nickname,
        )

    def test_goals_counted(self):
        MatchEvent.objects.create(
            match=self.match, match_player=self.home_mp,
            event_type=MatchEvent.EventType.GOAL, minute=10,
        )
        MatchEvent.objects.create(
            match=self.match, match_player=self.home_mp,
            event_type=MatchEvent.EventType.GOAL, minute=30,
        )
        stats = get_player_statistics(self.players[0])
        self.assertEqual(stats["goals"], 2)

    def test_assists_counted(self):
        MatchEvent.objects.create(
            match=self.match, match_player=self.home_mp,
            event_type=MatchEvent.EventType.ASSIST, minute=25,
        )
        stats = get_player_statistics(self.players[0])
        self.assertEqual(stats["assists"], 1)

    def test_own_goal_not_counted_for_player(self):
        MatchEvent.objects.create(
            match=self.match, match_player=self.home_mp,
            event_type=MatchEvent.EventType.OWN_GOAL, minute=80,
        )
        stats = get_player_statistics(self.players[0])
        self.assertEqual(stats["goals"], 0)
        self.assertEqual(stats["own_goals"], 1)

    def test_cards_counted(self):
        MatchEvent.objects.create(
            match=self.match, match_player=self.home_mp,
            event_type=MatchEvent.EventType.YELLOW_CARD, minute=30,
        )
        MatchEvent.objects.create(
            match=self.match, match_player=self.home_mp,
            event_type=MatchEvent.EventType.RED_CARD, minute=70,
        )
        stats = get_player_statistics(self.players[0])
        self.assertEqual(stats["yellow_cards"], 1)
        self.assertEqual(stats["red_cards"], 1)

    def test_mvp_counted(self):
        MatchEvent.objects.create(
            match=self.match, match_player=self.home_mp,
            event_type=MatchEvent.EventType.MVP, minute=90,
        )
        stats = get_player_statistics(self.players[0])
        self.assertEqual(stats["mvp"], 1)


class PlayerStatsByClubSeasonTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.matchday = Matchday.objects.create(
            season=self.season, division=self.primera,
            number=1, name="Jornada 1",
        )
        self.match = Match.objects.create(
            season=self.season, division=self.primera, matchday=self.matchday,
            home_club_season=self.club_seasons[0],
            away_club_season=self.club_seasons[1],
            home_goals=2, away_goals=0, status=Match.Status.FINISHED,
        )
        self.mp = MatchPlayer.objects.create(
            match=self.match, player=self.players[0],
            club_season=self.club_seasons[0],
            display_name=self.players[0].nickname,
        )

    def test_grouped_by_club_season(self):
        MatchEvent.objects.create(
            match=self.match, match_player=self.mp,
            event_type=MatchEvent.EventType.GOAL, minute=10,
        )
        MatchEvent.objects.create(
            match=self.match, match_player=self.mp,
            event_type=MatchEvent.EventType.GOAL, minute=30,
        )
        MatchEvent.objects.create(
            match=self.match, match_player=self.mp,
            event_type=MatchEvent.EventType.ASSIST, minute=45,
        )
        MatchEvent.objects.create(
            match=self.match, match_player=self.mp,
            event_type=MatchEvent.EventType.MVP, minute=90,
        )
        result = get_player_stats_by_club_season(self.players[0])
        stats = result.get(self.club_seasons[0].id)
        self.assertIsNotNone(stats)
        self.assertEqual(stats["matches_played"], 1)
        self.assertEqual(stats["goals"], 2)
        self.assertEqual(stats["assists"], 1)
        self.assertEqual(stats["mvp"], 1)
        self.assertEqual(stats["yellow_cards"], 0)

    def test_cards_grouped(self):
        MatchEvent.objects.create(
            match=self.match, match_player=self.mp,
            event_type=MatchEvent.EventType.YELLOW_CARD, minute=20,
        )
        MatchEvent.objects.create(
            match=self.match, match_player=self.mp,
            event_type=MatchEvent.EventType.RED_CARD, minute=80,
        )
        result = get_player_stats_by_club_season(self.players[0])
        stats = result.get(self.club_seasons[0].id)
        self.assertEqual(stats["yellow_cards"], 1)
        self.assertEqual(stats["red_cards"], 1)

    def test_matches_without_events_still_counted(self):
        result = get_player_stats_by_club_season(self.players[0])
        stats = result.get(self.club_seasons[0].id)
        self.assertIsNotNone(stats)
        self.assertEqual(stats["matches_played"], 1)
        self.assertEqual(stats["goals"], 0)

    def test_serializer_returns_stats(self):
        from apps.players.models import PlayerClubHistory
        from apps.players.serializers import PlayerClubHistorySerializer

        pch = PlayerClubHistory.objects.create(
            player=self.players[0],
            club_season=self.club_seasons[0],
            joined_at=timezone.now(),
        )
        serializer = PlayerClubHistorySerializer(pch)
        data = serializer.data
        self.assertIn("stats", data)
        self.assertIn("game_name", data)
        self.assertEqual(data["stats"]["matches_played"], 1)
        self.assertEqual(data["game_name"], "EA FC 26")


class TopScorersTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.matchday = Matchday.objects.create(
            season=self.season, division=self.primera,
            number=1, name="Jornada 1",
        )
        self.match = Match.objects.create(
            season=self.season, division=self.primera, matchday=self.matchday,
            home_club_season=self.club_seasons[0],
            away_club_season=self.club_seasons[1],
            home_goals=3, away_goals=0, status=Match.Status.FINISHED,
        )

    def test_top_scorers_ranking(self):
        mp0 = MatchPlayer.objects.create(
            match=self.match, player=self.players[0],
            club_season=self.club_seasons[0],
            display_name=self.players[0].nickname,
        )
        mp1 = MatchPlayer.objects.create(
            match=self.match, player=self.players[1],
            club_season=self.club_seasons[0],
            display_name=self.players[1].nickname,
        )
        MatchEvent.objects.create(
            match=self.match, match_player=mp0,
            event_type=MatchEvent.EventType.GOAL, minute=10,
        )
        MatchEvent.objects.create(
            match=self.match, match_player=mp0,
            event_type=MatchEvent.EventType.GOAL, minute=30,
        )
        MatchEvent.objects.create(
            match=self.match, match_player=mp1,
            event_type=MatchEvent.EventType.GOAL, minute=50,
        )
        scorers = get_top_scorers(season=self.season, division=self.primera)
        self.assertEqual(len(scorers), 2)
        self.assertEqual(scorers[0]["player_id"], self.players[0].id)
        self.assertEqual(scorers[0]["goals"], 2)


class TopAssistsTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.matchday = Matchday.objects.create(
            season=self.season, division=self.primera,
            number=1, name="Jornada 1",
        )
        self.match = Match.objects.create(
            season=self.season, division=self.primera, matchday=self.matchday,
            home_club_season=self.club_seasons[0],
            away_club_season=self.club_seasons[1],
            home_goals=2, away_goals=0, status=Match.Status.FINISHED,
        )

    def test_top_assists_ranking(self):
        mp0 = MatchPlayer.objects.create(
            match=self.match, player=self.players[0],
            club_season=self.club_seasons[0],
            display_name=self.players[0].nickname,
        )
        mp1 = MatchPlayer.objects.create(
            match=self.match, player=self.players[1],
            club_season=self.club_seasons[0],
            display_name=self.players[1].nickname,
        )
        MatchEvent.objects.create(
            match=self.match, match_player=mp0,
            event_type=MatchEvent.EventType.ASSIST, minute=10,
        )
        MatchEvent.objects.create(
            match=self.match, match_player=mp0,
            event_type=MatchEvent.EventType.ASSIST, minute=30,
        )
        MatchEvent.objects.create(
            match=self.match, match_player=mp1,
            event_type=MatchEvent.EventType.ASSIST, minute=50,
        )
        assists = get_top_assists(season=self.season, division=self.primera)
        self.assertEqual(len(assists), 2)
        self.assertEqual(assists[0]["player_id"], self.players[0].id)
        self.assertEqual(assists[0]["assists"], 2)


class TopMVPTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.matchday = Matchday.objects.create(
            season=self.season, division=self.primera,
            number=1, name="Jornada 1",
        )
        self.match = Match.objects.create(
            season=self.season, division=self.primera, matchday=self.matchday,
            home_club_season=self.club_seasons[0],
            away_club_season=self.club_seasons[1],
            home_goals=1, away_goals=0, status=Match.Status.FINISHED,
        )

    def test_top_mvp_ranking(self):
        mp = MatchPlayer.objects.create(
            match=self.match, player=self.players[0],
            club_season=self.club_seasons[0],
            display_name=self.players[0].nickname,
        )
        MatchEvent.objects.create(
            match=self.match, match_player=mp,
            event_type=MatchEvent.EventType.MVP, minute=90,
        )
        mvp = get_top_mvp(season=self.season, division=self.primera)
        self.assertEqual(len(mvp), 1)
        self.assertEqual(mvp[0]["player_id"], self.players[0].id)
        self.assertEqual(mvp[0]["mvp_count"], 1)


class PerformanceAnalyticsTest(BaseTestCase):
    """Leaderboard generico, promedios por posicion y serie por jugador."""

    def setUp(self):
        super().setUp()
        self.matchday = Matchday.objects.create(
            season=self.season, division=self.primera,
            number=1, name="Jornada 1", date=timezone.now().date(),
        )
        self.match1 = Match.objects.create(
            season=self.season, division=self.primera, matchday=self.matchday,
            home_club_season=self.club_seasons[0],
            away_club_season=self.club_seasons[1],
            home_goals=2, away_goals=1, status=Match.Status.FINISHED,
            date=timezone.now().date() - timedelta(days=7),
        )
        self.match2 = Match.objects.create(
            season=self.season, division=self.primera, matchday=self.matchday,
            home_club_season=self.club_seasons[2],
            away_club_season=self.club_seasons[3],
            home_goals=0, away_goals=0, status=Match.Status.FINISHED,
            date=timezone.now().date(),
        )
        self.pending = Match.objects.create(
            season=self.season, division=self.primera, matchday=self.matchday,
            home_club_season=self.club_seasons[4],
            away_club_season=self.club_seasons[5],
            status=Match.Status.SCHEDULED,
            date=timezone.now().date() + timedelta(days=7),
        )

        self.players[0].position = "DEL"
        self.players[0].save()
        self.players[1].position = "DEF"
        self.players[1].save()

        # player0: 2 partidos (8.0 y 7.0, 2 goles y 1 gol)
        self.p0_m1 = MatchPlayer.objects.create(
            match=self.match1, player=self.players[0],
            club_season=self.club_seasons[0],
            display_name=self.players[0].nickname,
        )
        self.p0_m2 = MatchPlayer.objects.create(
            match=self.match2, player=self.players[0],
            club_season=self.club_seasons[2],
            display_name=self.players[0].nickname,
        )
        # player1: 1 partido (6.0)
        self.p1_m1 = MatchPlayer.objects.create(
            match=self.match1, player=self.players[1],
            club_season=self.club_seasons[1],
            display_name=self.players[1].nickname,
        )
        # BOT en partido finalizado: no debe aparecer
        bot_mp = MatchPlayer.objects.create(
            match=self.match1, player=None,
            club_season=self.club_seasons[1],
            display_name="CPU",
        )
        # Aparicion en partido SCHEDULED: no debe contar
        pending_mp = MatchPlayer.objects.create(
            match=self.pending, player=self.players[1],
            club_season=self.club_seasons[4],
            display_name=self.players[1].nickname,
        )

        MatchPerformance.objects.create(match_player=self.p0_m1, rating=8.0, goals=2)
        MatchPerformance.objects.create(match_player=self.p0_m2, rating=7.0, goals=1)
        MatchPerformance.objects.create(match_player=self.p1_m1, rating=6.0, goals=0)
        MatchPerformance.objects.create(match_player=bot_mp, rating=9.9, goals=5)
        MatchPerformance.objects.create(match_player=pending_mp, rating=9.9, goals=5)

        # Eventos para la serie (goleador = fuente de verdad)
        MatchEvent.objects.create(
            match=self.match1, match_player=self.p0_m1,
            event_type=MatchEvent.EventType.GOAL, minute=10,
        )
        MatchEvent.objects.create(
            match=self.match1, match_player=self.p0_m1,
            event_type=MatchEvent.EventType.GOAL, minute=55,
        )
        MatchEvent.objects.create(
            match=self.match1, match_player=self.p0_m1,
            event_type=MatchEvent.EventType.MVP, minute=90,
        )
        MatchEvent.objects.create(
            match=self.match1, match_player=self.p1_m1,
            event_type=MatchEvent.EventType.YELLOW_CARD, minute=40,
        )
        MatchEvent.objects.create(
            match=self.match2, match_player=self.p0_m2,
            event_type=MatchEvent.EventType.GOAL, minute=12,
        )

    def test_leaderboard_avg_rating(self):
        rows = get_performance_leaderboard(metric="rating", agg="avg", min_matches=1)
        self.assertEqual(rows[0]["player_id"], self.players[0].id)
        self.assertEqual(rows[0]["matches"], 2)
        self.assertEqual(rows[0]["value"], 7.5)
        self.assertEqual(rows[1]["value"], 6.0)

    def test_leaderboard_sum_goals(self):
        rows = get_performance_leaderboard(metric="goals", agg="sum", min_matches=1)
        self.assertEqual(rows[0]["player_id"], self.players[0].id)
        self.assertEqual(rows[0]["value"], 3.0)

    def test_leaderboard_min_matches_excludes_one_appearance(self):
        rows = get_performance_leaderboard(metric="rating", agg="avg", min_matches=2)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["player_id"], self.players[0].id)

    def test_leaderboard_excludes_bot_and_scheduled(self):
        rows = get_performance_leaderboard(metric="goals", agg="sum", min_matches=1)
        player_ids = {r["player_id"] for r in rows}
        # BOT (player_id None) y el partido SCHEDULED (9.9 rating/5 goals) no suman
        self.assertEqual(player_ids, {self.players[0].id, self.players[1].id})
        self.assertLess(rows[0]["value"], 5.0)

    def test_leaderboard_invalid_metric_raises(self):
        with self.assertRaises(ValueError):
            get_performance_leaderboard(metric="password", agg="avg")
        with self.assertRaises(ValueError):
            get_performance_leaderboard(metric="rating", agg="median")

    def test_by_position_returns_four_positions(self):
        rows = get_performance_by_position()
        self.assertEqual([r["position"] for r in rows], ["ARQ", "DEF", "MED", "DEL"])
        by_pos = {r["position"]: r for r in rows}
        self.assertEqual(by_pos["DEL"]["matches"], 2)
        self.assertEqual(by_pos["DEL"]["rating"], 7.5)
        self.assertEqual(by_pos["DEF"]["rating"], 6.0)
        self.assertIsNone(by_pos["ARQ"]["rating"])
        self.assertEqual(by_pos["ARQ"]["matches"], 0)

    def test_player_match_series_chronological_with_events(self):
        series = get_player_match_series(self.players[0])
        self.assertEqual(len(series), 2)
        # orden cronologico: match1 (7 dias atras) primero
        self.assertEqual(series[0]["match"], self.match1.id)
        self.assertEqual(series[1]["match"], self.match2.id)
        self.assertEqual(series[0]["rating"], 8.0)
        self.assertEqual(series[0]["goals"], 2)   # de MatchEvent
        self.assertEqual(series[0]["mvp"], 1)
        self.assertEqual(series[1]["goals"], 1)
        self.assertEqual(series[1]["opponent"], self.club_seasons[3].club.name)

    def test_endpoints_public_and_errors(self):
        resp = self.client.get("/api/statistics/performance_leaderboard/")
        self.assertEqual(resp.status_code, 200)

        resp = self.client.get(
            "/api/statistics/performance_leaderboard/",
            {"metric": "hack", "agg": "avg"},
        )
        self.assertEqual(resp.status_code, 400)

        resp = self.client.get(
            "/api/statistics/performance_leaderboard/",
            {"metric": "rating", "agg": "median"},
        )
        self.assertEqual(resp.status_code, 400)

        resp = self.client.get("/api/statistics/performance_by_position/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 4)

        resp = self.client.get("/api/statistics/player_match_series/")
        self.assertEqual(resp.status_code, 400)

        resp = self.client.get(
            "/api/statistics/player_match_series/",
            {"player_id": self.players[0].id},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 2)

        resp = self.client.get(
            "/api/statistics/performance_leaderboard/",
            {"season_id": 99999},
        )
        self.assertEqual(resp.status_code, 404)
