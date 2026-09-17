from django.db import models


class Club(models.Model):
    """Represents a club (historical entity)."""

    name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=20)
    logo = models.ImageField(upload_to="clubs/logos/", blank=True, null=True)
    country = models.ForeignKey(
        "competitions.Country",
        on_delete=models.CASCADE,
        related_name="clubs",
    )
    founded_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Club"
        verbose_name_plural = "Clubes"
        ordering = ["name"]

    def __str__(self):
        return self.name


class ClubSeason(models.Model):
    """Represents a club's participation in a specific season and division."""

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Activo"
        RELEGATED = "RELEGATED", "Descendido"
        PROMOTED = "PROMOTED", "Ascendido"
        WITHDRAWN = "WITHDRAWN", "Retirado"

    club = models.ForeignKey(
        Club,
        on_delete=models.CASCADE,
        related_name="seasons",
    )
    season = models.ForeignKey(
        "competitions.Season",
        on_delete=models.CASCADE,
        related_name="club_seasons",
    )
    division = models.ForeignKey(
        "competitions.Division",
        on_delete=models.CASCADE,
        related_name="club_seasons",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Club por Temporada"
        verbose_name_plural = "Clubes por Temporada"
        unique_together = [["club", "season"]]
        ordering = ["season", "division", "club__name"]

    def __str__(self):
        return f"{self.club.name} - {self.season.name}"


class ClubTitle(models.Model):
    """Represents a title awarded to a club (manual administrative record)."""

    class TitleType(models.TextChoices):
        CHAMPION = "CHAMPION", "Campeón"
        RUNNER_UP = "RUNNER_UP", "Subcampeón"
        PLAYOFF_WINNER = "PLAYOFF_WINNER", "Ganador del Reducido"
        PROMOTION_WINNER = "PROMOTION_WINNER", "Ganador de Promoción"

    club = models.ForeignKey(
        Club,
        on_delete=models.CASCADE,
        related_name="titles",
    )
    season = models.ForeignKey(
        "competitions.Season",
        on_delete=models.CASCADE,
        related_name="club_titles",
    )
    division = models.ForeignKey(
        "competitions.Division",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="club_titles",
    )
    title_type = models.CharField(
        max_length=20,
        choices=TitleType.choices,
    )
    name = models.CharField(max_length=200)
    awarded_at = models.DateTimeField()
    awarded_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="awarded_titles",
    )
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Título de Club"
        verbose_name_plural = "Títulos de Clubes"
        ordering = ["-awarded_at"]

    def __str__(self):
        return f"{self.name} - {self.club.name}"
