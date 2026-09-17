from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.test_helpers.base import BaseTestCase
from apps.competitions.models import Season
from apps.matches.models import Matchday, Match, MatchPlayer, MatchEvent


class MatchCreationTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.matchday = Matchday.objects.create(
            season=self.season, division=self.primera,
            number=1, name="Jornada 1", date=timezone.now().date(),
        )

    def test_match_creation(self):
        match = Match.objects.create(
            season=self.season, division=self.primera, matchday=self.matchday,
            home_club_season=self.club_seasons[0],
            away_club_season=self.club_seasons[1],
            home_goals=2, away_goals=1, status=Match.Status.FINISHED,
        )
        self.assertEqual(match.home_goals, 2)
        self.assertEqual(match.away_goals, 1)

    def test_match_home_equals_away_fails(self):
        match = Match(
            season=self.season, division=self.primera, matchday=self.matchday,
            home_club_season=self.club_seasons[0],
            away_club_season=self.club_seasons[0],
            status=Match.Status.SCHEDULED,
        )
        with self.assertRaises(ValidationError):
            match.clean()

    def test_match_wrong_season_fails(self):
        season2 = Season.objects.create(
            name="Otra Temporada", league=self.league,
            game=self.ea_fc_26, format=self.liga_format,
            status=Season.Status.UPCOMING,
        )
        match = Match(
            season=season2, division=self.primera,
            home_club_season=self.club_seasons[0],
            away_club_season=self.club_seasons[1],
            status=Match.Status.SCHEDULED,
        )
        with self.assertRaises(ValidationError):
            match.clean()


class MatchPlayerTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.matchday = Matchday.objects.create(
            season=self.season, division=self.primera, number=1, name="Jornada 1",
        )
        self.match = Match.objects.create(
            season=self.season, division=self.primera, matchday=self.matchday,
            home_club_season=self.club_seasons[0],
            away_club_season=self.club_seasons[1],
            status=Match.Status.FINISHED,
        )

    def test_match_player_creation(self):
        mp = MatchPlayer.objects.create(
            match=self.match, player=self.players[0],
            club_season=self.club_seasons[0],
            display_name=self.players[0].nickname,
        )
        self.assertEqual(mp.player, self.players[0])

    def test_bot_creation(self):
        mp = MatchPlayer.objects.create(
            match=self.match, player=None, club_season=self.club_seasons[0],
            display_name="BOT",
        )
        self.assertIsNone(mp.player)
        self.assertEqual(mp.display_name, "BOT")


class MatchEventTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.matchday = Matchday.objects.create(
            season=self.season, division=self.primera, number=1, name="Jornada 1",
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

    def test_goal_event(self):
        event = MatchEvent.objects.create(
            match=self.match, match_player=self.home_mp,
            event_type=MatchEvent.EventType.GOAL, minute=23,
        )
        self.assertEqual(event.event_type, MatchEvent.EventType.GOAL)

    def test_assist_event(self):
        event = MatchEvent.objects.create(
            match=self.match, match_player=self.away_mp,
            event_type=MatchEvent.EventType.ASSIST, minute=45,
        )
        self.assertEqual(event.event_type, MatchEvent.EventType.ASSIST)

    def test_own_goal_event(self):
        event = MatchEvent.objects.create(
            match=self.match, match_player=self.away_mp,
            event_type=MatchEvent.EventType.OWN_GOAL, minute=80,
        )
        self.assertEqual(event.event_type, MatchEvent.EventType.OWN_GOAL)

    def test_card_events(self):
        yellow = MatchEvent.objects.create(
            match=self.match, match_player=self.home_mp,
            event_type=MatchEvent.EventType.YELLOW_CARD, minute=30,
        )
        red = MatchEvent.objects.create(
            match=self.match, match_player=self.away_mp,
            event_type=MatchEvent.EventType.RED_CARD, minute=70,
        )
        self.assertEqual(yellow.event_type, MatchEvent.EventType.YELLOW_CARD)
        self.assertEqual(red.event_type, MatchEvent.EventType.RED_CARD)

    def test_mvp_event(self):
        event = MatchEvent.objects.create(
            match=self.match, match_player=self.home_mp,
            event_type=MatchEvent.EventType.MVP, minute=90,
        )
        self.assertEqual(event.event_type, MatchEvent.EventType.MVP)

    def test_multiple_events_same_match(self):
        MatchEvent.objects.create(
            match=self.match, match_player=self.home_mp,
            event_type=MatchEvent.EventType.GOAL, minute=10,
        )
        MatchEvent.objects.create(
            match=self.match, match_player=self.home_mp,
            event_type=MatchEvent.EventType.GOAL, minute=30,
        )
        MatchEvent.objects.create(
            match=self.match, match_player=self.home_mp,
            event_type=MatchEvent.EventType.ASSIST, minute=25,
        )
        self.assertEqual(MatchEvent.objects.filter(match=self.match).count(), 3)
