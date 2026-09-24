from decimal import Decimal
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.test import APIClient
from apps.test_helpers.base import BaseTestCase
from apps.competitions.models import Season
from apps.matches.models import Matchday, Match, MatchPlayer, MatchEvent, MatchPerformance
from apps.matches.services.ocr import (
    extract_first_number,
    extract_selected_player,
    extract_valoracion,
    levenshtein,
    match_player,
    parse_stats,
    validate_stats,
)
from apps.standings.models import Standing


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


class MatchApiPermissionTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.matchday = Matchday.objects.create(
            season=self.season, division=self.primera,
            number=1, name="Jornada 1", date=timezone.now().date(),
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

    def test_anonymous_can_list_and_retrieve(self):
        resp = self.client.get("/api/matches/")
        self.assertEqual(resp.status_code, 200)
        detail = self.client.get(f"/api/matches/{self.match.id}/")
        self.assertEqual(detail.status_code, 200)
        self.assertIn("events", detail.data)
        self.assertIn("match_players", detail.data)

    def test_anonymous_cannot_update(self):
        resp = self.client.patch(
            f"/api/matches/{self.match.id}/", {"home_goals": 0}, format="json"
        )
        self.assertIn(resp.status_code, (401, 403))

    def test_player_role_cannot_update(self):
        self.client.force_authenticate(self.player_user)
        resp = self.client.patch(
            f"/api/matches/{self.match.id}/", {"home_goals": 9}, format="json"
        )
        self.assertEqual(resp.status_code, 403)

    def test_player_role_cannot_create_event(self):
        self.client.force_authenticate(self.player_user)
        resp = self.client.post(
            "/api/match-events/",
            {
                "match": self.match.id,
                "match_player": self.home_mp.id,
                "event_type": "GOAL",
                "minute": 10,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 403)

    def test_admin_liga_update_recalculates_standings(self):
        self.client.force_authenticate(self.admin_liga_user)
        resp = self.client.patch(
            f"/api/matches/{self.match.id}/",
            {"home_goals": 1, "away_goals": 1},
            format="json",
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        self.match.refresh_from_db()
        self.assertEqual(self.match.home_goals, 1)

        home = Standing.objects.get(
            season=self.season, division=self.primera,
            club_season=self.club_seasons[0],
        )
        away = Standing.objects.get(
            season=self.season, division=self.primera,
            club_season=self.club_seasons[1],
        )
        self.assertEqual(home.played, 1)
        self.assertEqual(home.points, 1)
        self.assertEqual(away.points, 1)

    def test_create_match_recalculates_standings(self):
        self.client.force_authenticate(self.superadmin)
        resp = self.client.post(
            "/api/matches/",
            {
                "season": self.season.id,
                "division": self.primera.id,
                "matchday": self.matchday.id,
                "home_club_season": self.club_seasons[2].id,
                "away_club_season": self.club_seasons[3].id,
                "home_goals": 3,
                "away_goals": 0,
                "status": "FINISHED",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.data)

        new_home = Standing.objects.get(
            season=self.season, division=self.primera,
            club_season=self.club_seasons[2],
        )
        self.assertEqual(new_home.points, 3)

        first_home = Standing.objects.get(
            season=self.season, division=self.primera,
            club_season=self.club_seasons[0],
        )
        self.assertEqual(first_home.played, 1)
        self.assertEqual(first_home.points, 3)

    def test_admin_liga_event_crud(self):
        self.client.force_authenticate(self.admin_liga_user)
        create = self.client.post(
            "/api/match-events/",
            {
                "match": self.match.id,
                "match_player": self.home_mp.id,
                "event_type": "GOAL",
                "minute": 23,
            },
            format="json",
        )
        self.assertEqual(create.status_code, 201, create.data)

        upd = self.client.patch(
            f"/api/match-events/{create.data['id']}/", {"minute": 24}, format="json"
        )
        self.assertEqual(upd.status_code, 200)

        dele = self.client.delete(f"/api/match-events/{create.data['id']}/")
        self.assertEqual(dele.status_code, 204)


class MatchPerformanceTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.matchday = Matchday.objects.create(
            season=self.season, division=self.primera,
            number=1, name="Jornada 1", date=timezone.now().date(),
        )
        self.match = Match.objects.create(
            season=self.season, division=self.primera, matchday=self.matchday,
            home_club_season=self.club_seasons[0],
            away_club_season=self.club_seasons[1],
            home_goals=2, away_goals=1, status=Match.Status.FINISHED,
        )
        # players[0] has stint in club_seasons[0] (home); MatchPlayer only for players[0].
        self.home_mp = MatchPlayer.objects.create(
            match=self.match, player=self.players[0],
            club_season=self.club_seasons[0],
            display_name=self.players[0].nickname,
        )
        # players[1] has stint in club_seasons[1] but NO MatchPlayer yet (auto-create path).

    def test_performance_creation(self):
        perf = MatchPerformance.objects.create(
            match_player=self.home_mp, rating=Decimal("7.5"), goals=1
        )
        self.assertEqual(perf.rating, Decimal("7.5"))
        self.assertEqual(perf.match_player, self.home_mp)
        self.assertEqual(perf.match_player.performance, perf)

    def test_bot_performance_fails_clean(self):
        bot_mp = MatchPlayer.objects.create(
            match=self.match, player=None, club_season=self.club_seasons[0],
            display_name="BOT",
        )
        perf = MatchPerformance(match_player=bot_mp, rating=Decimal("5.0"))
        with self.assertRaises(ValidationError):
            perf.clean()

    def test_rating_out_of_range_fails(self):
        perf = MatchPerformance(match_player=self.home_mp, rating=Decimal("11.0"))
        with self.assertRaises(ValidationError):
            perf.full_clean()

    def test_pct_out_of_range_fails(self):
        perf = MatchPerformance(
            match_player=self.home_mp, rating=Decimal("5.0"),
            pass_accuracy_pct=150,
        )
        with self.assertRaises(ValidationError):
            perf.full_clean()

    def test_anonymous_can_list_and_retrieve(self):
        MatchPerformance.objects.create(match_player=self.home_mp, rating=Decimal("7.5"))
        resp = self.client.get("/api/match-performances/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["count"], 1)
        detail = self.client.get(f"/api/match-performances/{resp.data['results'][0]['id']}/")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.data["rival_name"], "Club 2")

    def test_filter_by_match(self):
        MatchPerformance.objects.create(match_player=self.home_mp, rating=Decimal("7.5"))
        resp = self.client.get(f"/api/match-performances/?match={self.match.id}")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["count"], 1)
        other = self.client.get("/api/match-performances/?match=9999")
        self.assertEqual(other.data["count"], 0)

    def test_anonymous_cannot_create(self):
        resp = self.client.post(
            "/api/match-performances/",
            {"match_player": self.home_mp.id, "rating": 7.5},
            format="json",
        )
        self.assertIn(resp.status_code, (401, 403))

    def test_player_role_cannot_create(self):
        self.client.force_authenticate(self.player_user)
        resp = self.client.post(
            "/api/match-performances/",
            {"match_player": self.home_mp.id, "rating": 7.5},
            format="json",
        )
        self.assertEqual(resp.status_code, 403)

    def test_admin_single_create(self):
        self.client.force_authenticate(self.admin_liga_user)
        resp = self.client.post(
            "/api/match-performances/",
            {"match_player": self.home_mp.id, "rating": 7.5, "goals": 1},
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertEqual(resp.data["player"], self.players[0].id)
        self.assertEqual(resp.data["rival_name"], "Club 2")
        self.assertEqual(resp.data["home_goals"], 2)

    def test_bot_single_create_rejected(self):
        bot_mp = MatchPlayer.objects.create(
            match=self.match, player=None, club_season=self.club_seasons[0],
            display_name="BOT",
        )
        self.client.force_authenticate(self.admin_liga_user)
        resp = self.client.post(
            "/api/match-performances/",
            {"match_player": bot_mp.id, "rating": 5.0},
            format="json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_batch_creates_performance_and_auto_match_player(self):
        self.client.force_authenticate(self.admin_liga_user)
        resp = self.client.post(
            f"/api/matches/{self.match.id}/performances/batch/",
            [{"player": self.players[1].id, "rating": 6.5, "goals": 0}],
            format="json",
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(len(resp.data), 1)

        mp = MatchPlayer.objects.get(match=self.match, player=self.players[1])
        self.assertEqual(mp.club_season, self.club_seasons[1])
        self.assertEqual(mp.display_name, self.players[1].nickname)
        self.assertTrue(hasattr(mp, "performance"))
        self.assertEqual(mp.performance.rating, Decimal("6.5"))

    def test_batch_upsert_updates_existing(self):
        self.client.force_authenticate(self.admin_liga_user)
        first = self.client.post(
            f"/api/matches/{self.match.id}/performances/batch/",
            [{"player": self.players[0].id, "rating": 7.0, "goals": 2}],
            format="json",
        )
        self.assertEqual(first.status_code, 200, first.data)

        second = self.client.post(
            f"/api/matches/{self.match.id}/performances/batch/",
            [{"player": self.players[0].id, "rating": 8.5}],
            format="json",
        )
        self.assertEqual(second.status_code, 200, second.data)

        self.assertEqual(
            MatchPerformance.objects.filter(match_player__match=self.match).count(), 1
        )
        perf = MatchPerformance.objects.get(match_player=self.home_mp)
        self.assertEqual(perf.rating, Decimal("8.5"))
        self.assertEqual(perf.goals, 2)

    def test_batch_rejects_foreign_player_and_rolls_back(self):
        self.client.force_authenticate(self.admin_liga_user)
        resp = self.client.post(
            f"/api/matches/{self.match.id}/performances/batch/",
            [
                {"player": self.players[1].id, "rating": 6.5},
                {"player": self.players[2].id, "rating": 7.0},
            ],
            format="json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("errors", resp.data)
        self.assertEqual(MatchPerformance.objects.count(), 0)
        self.assertFalse(
            MatchPlayer.objects.filter(match=self.match, player=self.players[1]).exists()
        )

    def test_batch_invalid_rating_rejected(self):
        self.client.force_authenticate(self.admin_liga_user)
        resp = self.client.post(
            f"/api/matches/{self.match.id}/performances/batch/",
            [{"player": self.players[0].id, "rating": 15}],
            format="json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(MatchPerformance.objects.count(), 0)

    def test_batch_requires_admin(self):
        resp = self.client.post(
            f"/api/matches/{self.match.id}/performances/batch/",
            [{"player": self.players[0].id, "rating": 7.0}],
            format="json",
        )
        self.assertIn(resp.status_code, (401, 403))

        self.client.force_authenticate(self.player_user)
        resp = self.client.post(
            f"/api/matches/{self.match.id}/performances/batch/",
            [{"player": self.players[0].id, "rating": 7.0}],
            format="json",
        )
        self.assertEqual(resp.status_code, 403)

    def test_player_history_endpoint(self):
        MatchPerformance.objects.create(
            match_player=self.home_mp, rating=Decimal("7.5"), goals=1,
            distance_km=Decimal("10.2"),
        )
        resp = self.client.get(f"/api/players/{self.players[0].id}/performances/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["count"], 1)
        row = resp.data["results"][0]
        self.assertEqual(row["rival_name"], "Club 2")
        self.assertEqual(row["home_club_name"], "Club 1")
        self.assertEqual(row["home_goals"], 2)
        self.assertEqual(row["distance_km"], Decimal("10.2"))
        self.assertEqual(row["player_nickname"], self.players[0].nickname)

        empty = self.client.get(f"/api/players/{self.players[5].id}/performances/")
        self.assertEqual(empty.data["count"], 0)

    def test_player_history_season_filter(self):
        MatchPerformance.objects.create(match_player=self.home_mp, rating=Decimal("7.5"))
        resp = self.client.get(
            f"/api/players/{self.players[0].id}/performances/?season={self.season.id}"
        )
        self.assertEqual(resp.data["count"], 1)
        resp_other = self.client.get(
            f"/api/players/{self.players[0].id}/performances/?season=9999"
        )
        self.assertEqual(resp_other.data["count"], 0)


STATS_SAMPLE = """Calificación 8.4 7.9
Goles 2 1
Asistencias 1 0
Tiros 5 3
Precisión en los tiros (%) 60 40
Pases 42 38
Precisión en los pases (%) 85 90
Regates 3 2
Tasa de éxito de los regates (%) 66 50
Entradas 4 5
Tasa de éxito en entradas (%) 75 60
Fueras de lugar 1 0
Faltas cometidas 2 3
Posesión ganada 6 5
Posesión perdida 4 7
Minutos jugados 90 90
Distancia recorrida (km) 10.5 9.8
Distancia en carrera (km) 2.1 1.8
"""


class OcrParserTest(BaseTestCase):
    """Tests unitarios del parser OCR (sin Tesseract)."""

    def test_levenshtein(self):
        self.assertEqual(levenshtein("kitten", "sitting"), 3)
        self.assertEqual(levenshtein("", "abc"), 3)
        self.assertEqual(levenshtein("same", "same"), 0)

    def test_extract_first_number_fixes_ocr_misreads(self):
        self.assertEqual(extract_first_number("Goles  O) 2"), 0.0)
        self.assertEqual(extract_first_number("Goles  Lo) 2"), 0.0)
        self.assertEqual(extract_first_number("Minutos O 90"), 0.0)
        self.assertEqual(extract_first_number("Pases 42 38"), 42.0)
        self.assertEqual(extract_first_number("Distancia 10.5 9.8"), 10.5)
        self.assertIsNone(extract_first_number("Asist."))

    def test_extract_valoracion_with_mirror_6_9_fix(self):
        self.assertEqual(extract_valoracion("Calificación 8.4 7.9"), 8.4)
        # OCR confunde 9.9 ↔ 6.9: debe preferir el segundo valor
        self.assertEqual(extract_valoracion("Calificación 9.9 6.9"), 6.9)
        # Sin decimales con punto: fallback a coma decimal
        self.assertEqual(extract_valoracion("rating 7,2"), 7.2)

    def test_extract_selected_player_skips_noise(self):
        text = "mci\nlucasyjoaqui 6.9\nres"
        self.assertEqual(extract_selected_player(text), "lucasyjoaqui")
        self.assertIsNone(extract_selected_player("mci\nres\ndc"))

    def test_match_player_fuzzy(self):
        roster = [
            {"player": 7, "nickname": "lucasyjoaqui", "aliases": {"lucasyjoaqui"}},
            {"player": 8, "nickname": "Charly", "aliases": {"charly"}},
        ]
        self.assertEqual(match_player("lucasyjoaqui", roster)["player"], 7)
        # typo de 1 edición
        self.assertEqual(match_player("lucasyjoacul", roster)["player"], 7)
        self.assertIsNone(match_player("zzzzzzzzzzzzzz", roster))

    def test_parse_stats_full_panel(self):
        stats = parse_stats(STATS_SAMPLE)
        self.assertEqual(stats["rating"], 8.4)
        self.assertEqual(stats["goals"], 2)
        self.assertEqual(stats["assists"], 1)
        self.assertEqual(stats["shots"], 5)
        self.assertEqual(stats["shot_accuracy_pct"], 60)
        self.assertEqual(stats["passes"], 42)
        self.assertEqual(stats["pass_accuracy_pct"], 85)
        self.assertEqual(stats["dribbles"], 3)
        self.assertEqual(stats["dribble_success_pct"], 66)
        self.assertEqual(stats["tackles"], 4)
        self.assertEqual(stats["tackle_success_pct"], 75)
        self.assertEqual(stats["offsides"], 1)
        self.assertEqual(stats["fouls"], 2)
        self.assertEqual(stats["possession_won"], 6)
        self.assertEqual(stats["possession_lost"], 4)
        self.assertEqual(stats["minutes_played"], 90)
        self.assertEqual(stats["distance_km"], 10.5)
        self.assertEqual(stats["sprint_distance_km"], 2.1)

    def test_parse_stats_rating_from_name_panel_priority(self):
        stats = parse_stats(STATS_SAMPLE, name_text="mci lucasyjoaqui 6.9")
        self.assertEqual(stats["rating"], 6.9)

    def test_parse_stats_clamps_ranges(self):
        stats = parse_stats(
            "Calificación 8.4\nPrecisión en los pases (%) 150\n"
            "Minutos jugados 200\nDistancia recorrida (km) 1500.0"
        )
        self.assertEqual(stats["pass_accuracy_pct"], 100)
        self.assertEqual(stats["minutes_played"], 130)
        self.assertEqual(stats["distance_km"], 999.9)

    def test_validate_stats_warnings(self):
        self.assertEqual(validate_stats(parse_stats(STATS_SAMPLE)), [])
        empty = parse_stats("sin datos")
        warnings = validate_stats(empty)
        self.assertEqual(len(warnings), 2)


class OcrAnalyzeEndpointTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.matchday = Matchday.objects.create(
            season=self.season, division=self.primera,
            number=1, name="Jornada 1", date=timezone.now().date(),
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
        self.url = f"/api/matches/{self.match.id}/performances/analyze/"
        self.fake_image = SimpleUploadedFile(
            "captura.png", b"fake-png-bytes", content_type="image/png"
        )

    def _fake_result(self, player=None):
        return [{
            "filename": "captura.png",
            "success": True,
            "detected_name": "nada",
            "player": player,
            "player_nickname": None,
            "stats": {"rating": 7.5, "goals": 1, "assists": 0, "passes": 30},
            "warnings": [],
            "errors": [],
            "ocr_debug": {"name_text": "", "stats_text": ""},
        }]

    def test_requires_admin(self):
        resp = self.client.post(self.url, {"images": [self.fake_image]})
        self.assertIn(resp.status_code, (401, 403))
        self.client.force_authenticate(self.player_user)
        resp = self.client.post(self.url, {"images": [self.fake_image]})
        self.assertEqual(resp.status_code, 403)

    def test_no_images_rejected(self):
        self.client.force_authenticate(self.admin_liga_user)
        resp = self.client.post(self.url, {}, format="multipart")
        self.assertEqual(resp.status_code, 400)

    def test_non_image_rejected(self):
        self.client.force_authenticate(self.admin_liga_user)
        bad = SimpleUploadedFile("notas.txt", b"hola", content_type="text/plain")
        resp = self.client.post(self.url, {"images": [bad]})
        self.assertEqual(resp.status_code, 400)

    def test_too_many_images_rejected(self):
        self.client.force_authenticate(self.admin_liga_user)
        files = [
            SimpleUploadedFile(f"i{n}.png", b"x", content_type="image/png")
            for n in range(31)
        ]
        resp = self.client.post(self.url, {"images": files})
        self.assertEqual(resp.status_code, 400)

    @patch("apps.matches.views.ocr_analyze_images")
    def test_analyze_returns_results(self, mock_analyze):
        mock_analyze.return_value = self._fake_result(self.players[0].id)
        self.client.force_authenticate(self.admin_liga_user)
        resp = self.client.post(self.url, {"images": [self.fake_image]})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["total"], 1)
        self.assertEqual(resp.data["exitosos"], 1)
        self.assertEqual(resp.data["results"][0]["player"], self.players[0].id)
        # El servicio recibe el plantel del partido (match_players + stints)
        roster = mock_analyze.call_args[0][1]
        self.assertTrue(any(r["player"] == self.players[0].id for r in roster))

    @patch("apps.matches.views.ocr_analyze_images")
    def test_analyze_tesseract_unavailable_503(self, mock_analyze):
        from apps.matches.services.ocr import TesseractNotAvailable

        mock_analyze.side_effect = TesseractNotAvailable("no tesseract")
        self.client.force_authenticate(self.admin_liga_user)
        resp = self.client.post(self.url, {"images": [self.fake_image]})
        self.assertEqual(resp.status_code, 503)

    @patch("apps.matches.views.ocr_analyze_images")
    def test_analyze_malformed_input_400(self, mock_analyze):
        mock_analyze.side_effect = ValueError("Máximo 30 imágenes por solicitud.")
        self.client.force_authenticate(self.admin_liga_user)
        resp = self.client.post(self.url, {"images": [self.fake_image]})
        self.assertEqual(resp.status_code, 400)
