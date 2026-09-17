from django.db import models


class Player(models.Model):
    """Represents a player (independent of User)."""

    class Platform(models.TextChoices):
        PLAYSTATION = "PLAYSTATION", "PlayStation"
        XBOX = "XBOX", "Xbox"
        PC = "PC", "PC"

    nickname = models.CharField(max_length=50, unique=True)
    platform = models.CharField(
        max_length=20,
        choices=Platform.choices,
        blank=True,
        null=True,
    )
    country = models.ForeignKey(
        "competitions.Country",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="players",
    )
    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="player_profile",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Jugador"
        verbose_name_plural = "Jugadores"
        ordering = ["nickname"]

    def __str__(self):
        return self.nickname


class PlayerIdentityHistory(models.Model):
    """Stores previous nicknames for a player."""

    player = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name="identity_history",
    )
    nickname = models.CharField(max_length=50)
    changed_at = models.DateTimeField()
    changed_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="nickname_changes",
    )
    reason = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        verbose_name = "Historial de Identidad"
        verbose_name_plural = "Historiales de Identidad"
        ordering = ["-changed_at"]

    def __str__(self):
        return f"{self.player.nickname} - {self.nickname}"


class PlayerClubHistory(models.Model):
    """Tracks a player's club history across seasons."""

    player = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name="club_history",
    )
    club_season = models.ForeignKey(
        "clubs.ClubSeason",
        on_delete=models.CASCADE,
        related_name="player_history",
    )
    joined_at = models.DateTimeField()
    left_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "Historial de Club del Jugador"
        verbose_name_plural = "Historiales de Club de Jugadores"
        ordering = ["-joined_at"]

    def __str__(self):
        status = "Actual" if self.left_at is None else "Anterior"
        return f"{self.player.nickname} - {self.club_season.club.name} ({status})"

    @property
    def is_current(self):
        return self.left_at is None
