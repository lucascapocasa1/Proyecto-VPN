from django.utils import timezone
from rest_framework.test import APIClient
from apps.test_helpers.base import BaseTestCase
from apps.accounts.models import User, LeagueAdmin, ClubAdmin
from apps.players.models import Player, PlayerIdentityHistory, PlayerClubHistory, Transfer
from apps.clubs.models import Club, ClubSeason
from apps.competitions.models import Season


class PlayerCreationTest(BaseTestCase):
    """Test player creation and basic operations."""

    def test_player_creation(self):
        player = Player.objects.create(
            nickname="newplayer",
            platform="PC",
            country=self.argentina,
        )
        self.assertEqual(player.nickname, "newplayer")
        self.assertEqual(player.platform, "PC")
        self.assertTrue(player.is_active)

    def test_player_nickname_unique(self):
        with self.assertRaises(Exception):
            Player.objects.create(
                nickname="player1",  # Already exists
                platform="PC",
            )

    def test_player_platform_optional(self):
        player = Player.objects.create(nickname="noplatform")
        self.assertIsNone(player.platform)

    def test_player_without_country(self):
        player = Player.objects.create(nickname="nocountry", platform="XBOX")
        self.assertIsNone(player.country)


class NicknameChangeTest(BaseTestCase):
    """Test nickname change rules."""

    def test_nickname_change_records_history(self):
        player = self.players[0]
        old_nickname = player.nickname

        PlayerIdentityHistory.objects.create(
            player=player,
            nickname=old_nickname,
            changed_at=timezone.now(),
            changed_by=self.superadmin,
            reason="Cambio solicitado",
        )

        player.nickname = "new_nickname"
        player.save()

        player.refresh_from_db()
        self.assertEqual(player.nickname, "new_nickname")

        history = PlayerIdentityHistory.objects.filter(player=player)
        self.assertEqual(history.count(), 1)
        self.assertEqual(history.first().nickname, old_nickname)

    def test_player_id_unchanged_after_nickname_change(self):
        player = self.players[0]
        original_id = player.id

        player.nickname = "changed_nickname"
        player.save()

        player.refresh_from_db()
        self.assertEqual(player.id, original_id)

    def test_multiple_nickname_changes(self):
        player = self.players[0]

        for i in range(3):
            PlayerIdentityHistory.objects.create(
                player=player,
                nickname=f"old_nick_{i}",
                changed_at=timezone.now(),
                changed_by=self.superadmin,
            )
            player.nickname = f"new_nick_{i}"
            player.save()

        history = PlayerIdentityHistory.objects.filter(player=player)
        self.assertEqual(history.count(), 3)


class PlayerClubHistoryTest(BaseTestCase):
    """Test player club history."""

    def test_current_club_detection(self):
        history = PlayerClubHistory.objects.filter(player=self.players[0]).first()
        self.assertIsNotNone(history)
        self.assertTrue(history.is_current)

    def test_club_change(self):
        player = self.players[0]
        old_history = PlayerClubHistory.objects.filter(player=player).first()
        old_history.left_at = timezone.now()
        old_history.save()

        new_history = PlayerClubHistory.objects.create(
            player=player,
            club_season=self.club_seasons[1],
            joined_at=timezone.now(),
        )

        self.assertTrue(new_history.is_current)
        self.assertFalse(old_history.is_current)

    def test_multiple_clubs_history(self):
        player = self.players[0]
        old_history = PlayerClubHistory.objects.filter(player=player).first()
        old_history.left_at = timezone.now()
        old_history.save()

        PlayerClubHistory.objects.create(
            player=player,
            club_season=self.club_seasons[1],
            joined_at=timezone.now(),
        )

        history = PlayerClubHistory.objects.filter(player=player)
        self.assertEqual(history.count(), 2)


class TransferApiTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.client.force_authenticate(self.superadmin)

    def test_create_transfer_moves_player(self):
        resp = self.client.post(
            "/api/transfers/",
            {"player": self.players[0].id, "to_club_season": self.club_seasons[1].id},
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.data)

        transfer = Transfer.objects.get(pk=resp.data["id"])
        self.assertEqual(transfer.from_club_season, self.club_seasons[0])
        self.assertEqual(transfer.to_club_season, self.club_seasons[1])
        self.assertEqual(transfer.registered_by, self.superadmin)

        old = PlayerClubHistory.objects.get(
            player=self.players[0], club_season=self.club_seasons[0]
        )
        self.assertIsNotNone(old.left_at)
        new = PlayerClubHistory.objects.get(
            player=self.players[0], club_season=self.club_seasons[1]
        )
        self.assertIsNone(new.left_at)

    def test_same_club_rejected(self):
        resp = self.client.post(
            "/api/transfers/",
            {"player": self.players[0].id, "to_club_season": self.club_seasons[0].id},
            format="json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_player_without_club_rejected(self):
        resp = self.client.post(
            "/api/transfers/",
            {"player": self.players[20].id, "to_club_season": self.club_seasons[1].id},
            format="json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_destination_other_season_rejected(self):
        season2 = Season.objects.create(
            name="Temporada 2", league=self.league,
            game=self.ea_fc_26, number=2, format=self.liga_format,
            status=Season.Status.UPCOMING,
        )
        other_cs = ClubSeason.objects.create(
            club=self.clubs[0], season=season2, division=self.primera,
        )
        resp = self.client.post(
            "/api/transfers/",
            {"player": self.players[0].id, "to_club_season": other_cs.id},
            format="json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_anonymous_can_list(self):
        anon = APIClient()
        resp = anon.get("/api/transfers/")
        self.assertEqual(resp.status_code, 200)

    def test_player_role_cannot_create(self):
        self.client.force_authenticate(self.player_user)
        resp = self.client.post(
            "/api/transfers/",
            {"player": self.players[0].id, "to_club_season": self.club_seasons[1].id},
            format="json",
        )
        self.assertEqual(resp.status_code, 403)

    def test_admin_liga_can_create(self):
        self.client.force_authenticate(self.admin_liga_user)
        resp = self.client.post(
            "/api/transfers/",
            {"player": self.players[0].id, "to_club_season": self.club_seasons[1].id},
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.data)

    def test_delete_latest_reverts(self):
        resp = self.client.post(
            "/api/transfers/",
            {"player": self.players[0].id, "to_club_season": self.club_seasons[1].id},
            format="json",
        )
        transfer_id = resp.data["id"]

        del_resp = self.client.delete(f"/api/transfers/{transfer_id}/")
        self.assertEqual(del_resp.status_code, 204)
        self.assertEqual(Transfer.objects.count(), 0)

        old = PlayerClubHistory.objects.get(
            player=self.players[0], club_season=self.club_seasons[0]
        )
        self.assertIsNone(old.left_at)
        self.assertFalse(
            PlayerClubHistory.objects.filter(
                player=self.players[0], club_season=self.club_seasons[1]
            ).exists()
        )

    def test_delete_older_rejected(self):
        resp1 = self.client.post(
            "/api/transfers/",
            {"player": self.players[0].id, "to_club_season": self.club_seasons[1].id},
            format="json",
        )
        resp2 = self.client.post(
            "/api/transfers/",
            {"player": self.players[0].id, "to_club_season": self.club_seasons[2].id},
            format="json",
        )
        self.assertEqual(resp2.status_code, 201, resp2.data)

        del_resp = self.client.delete(f"/api/transfers/{resp1.data['id']}/")
        self.assertEqual(del_resp.status_code, 400)
        self.assertEqual(Transfer.objects.count(), 2)

    def test_season_filter(self):
        self.client.post(
            "/api/transfers/",
            {"player": self.players[0].id, "to_club_season": self.club_seasons[1].id},
            format="json",
        )
        resp = self.client.get(f"/api/transfers/?season={self.season.id}")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["count"], 1)

        other = Season.objects.create(
            name="Otra", league=self.league,
            game=self.ea_fc_26, format=self.liga_format,
        )
        resp = self.client.get(f"/api/transfers/?season={other.id}")
        self.assertEqual(resp.data["count"], 0)
