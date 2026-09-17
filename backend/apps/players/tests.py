from django.utils import timezone
from apps.test_helpers.base import BaseTestCase
from apps.accounts.models import User, LeagueAdmin, ClubAdmin
from apps.players.models import Player, PlayerIdentityHistory, PlayerClubHistory
from apps.clubs.models import Club, ClubSeason


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
