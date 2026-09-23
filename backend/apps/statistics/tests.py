from django.utils import timezone
from apps.test_helpers.base import BaseTestCase
from apps.matches.models import Matchday, Match, MatchPlayer, MatchEvent
from apps.statistics.services import (
    get_player_statistics,
    get_player_stats_by_club_season,
    get_top_scorers,
    get_top_assists,
    get_top_mvp,
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
