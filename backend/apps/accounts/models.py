from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """User model with role-based access control."""

    class Role(models.TextChoices):
        SUPERADMIN = "SUPERADMIN", "Super Administrador"
        ADMIN_LIGA = "ADMIN_LIGA", "Administrador de Liga"
        ADMIN_CLUB = "ADMIN_CLUB", "Administrador de Club"
        PLAYER = "PLAYER", "Jugador"
        USER = "USER", "Usuario"

    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.USER,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class LeagueAdmin(models.Model):
    """Association between User and League for admin permissions."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="league_administrations",
    )
    league = models.ForeignKey(
        "competitions.League",
        on_delete=models.CASCADE,
        related_name="administrators",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Administrador de Liga"
        verbose_name_plural = "Administradores de Liga"
        unique_together = [["user", "league"]]

    def __str__(self):
        return f"{self.user.username} - {self.league.name}"


class ClubAdmin(models.Model):
    """Association between User and Club for admin permissions."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="club_administrations",
    )
    club = models.ForeignKey(
        "clubs.Club",
        on_delete=models.CASCADE,
        related_name="administrators",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Administrador de Club"
        verbose_name_plural = "Administradores de Club"
        unique_together = [["user", "club"]]

    def __str__(self):
        return f"{self.user.username} - {self.club.name}"
