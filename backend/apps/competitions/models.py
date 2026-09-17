from django.db import models
from django.core.exceptions import ValidationError


class Country(models.Model):
    """Represents a country."""

    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=2, unique=True, help_text="ISO 3166-1 alpha-2")
    flag_url = models.URLField(blank=True, null=True)

    class Meta:
        verbose_name = "País"
        verbose_name_plural = "Países"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Game(models.Model):
    """Represents a game edition (EA FC 26, EA FC 27, etc.)."""

    name = models.CharField(max_length=50)
    year = models.IntegerField()

    class Meta:
        verbose_name = "Juego"
        verbose_name_plural = "Juegos"
        ordering = ["-year"]

    def __str__(self):
        return self.name


class CompetitionFormat(models.Model):
    """Defines the format of a competition."""

    class FormatType(models.TextChoices):
        ROUND_ROBIN = "ROUND_ROBIN", "Liga (Todos contra todos)"
        DOUBLE_ROUND_ROBIN = "DOUBLE_ROUND_ROBIN", "Liga doble (Ida y vuelta)"
        CUSTOM = "CUSTOM", "Personalizado"

    name = models.CharField(max_length=100)
    format_type = models.CharField(
        max_length=20,
        choices=FormatType.choices,
    )
    has_playoffs = models.BooleanField(default=False)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Formato de Competición"
        verbose_name_plural = "Formatos de Competición"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.get_format_type_display()})"


class League(models.Model):
    """Represents a league within a country."""

    name = models.CharField(max_length=100)
    country = models.ForeignKey(
        Country,
        on_delete=models.CASCADE,
        related_name="leagues",
    )

    class Meta:
        verbose_name = "Liga"
        verbose_name_plural = "Ligas"
        unique_together = [["name", "country"]]
        ordering = ["country", "name"]

    def __str__(self):
        return f"{self.name} ({self.country.code})"


class Season(models.Model):
    """Represents a season within a league and game."""

    class Status(models.TextChoices):
        UPCOMING = "UPCOMING", "Próxima"
        ACTIVE = "ACTIVE", "Activa"
        FINISHED = "FINISHED", "Finalizada"

    name = models.CharField(max_length=100)
    league = models.ForeignKey(
        League,
        on_delete=models.CASCADE,
        related_name="seasons",
    )
    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name="seasons",
    )
    number = models.IntegerField(blank=True, null=True)
    format = models.ForeignKey(
        CompetitionFormat,
        on_delete=models.PROTECT,
        related_name="seasons",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.UPCOMING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Temporada"
        verbose_name_plural = "Temporadas"
        unique_together = [["league", "name"]]
        ordering = ["league", "-created_at"]

    def __str__(self):
        return f"{self.name} - {self.league.name}"


class Division(models.Model):
    """Represents a division within a season."""

    name = models.CharField(max_length=100)
    season = models.ForeignKey(
        Season,
        on_delete=models.CASCADE,
        related_name="divisions",
    )
    order = models.IntegerField(help_text="Order within the season (1=first, 2=second, etc.)")
    max_clubs = models.IntegerField(default=20)

    # Zone configuration
    playoff_zone_start = models.IntegerField(blank=True, null=True)
    playoff_zone_end = models.IntegerField(blank=True, null=True)
    promotion_zone_start = models.IntegerField(blank=True, null=True)
    promotion_zone_end = models.IntegerField(blank=True, null=True)
    relegation_zone_start = models.IntegerField(blank=True, null=True)
    relegation_zone_end = models.IntegerField(blank=True, null=True)
    has_relegation = models.BooleanField(default=True)

    class Meta:
        verbose_name = "División"
        verbose_name_plural = "Divisiones"
        unique_together = [["season", "order"]]
        ordering = ["season", "order"]

    def __str__(self):
        return f"{self.name} - {self.season.name}"

    def clean(self):
        if self.has_relegation is False:
            if self.relegation_zone_start is not None or self.relegation_zone_end is not None:
                raise ValidationError(
                    "Una división sin descenso no debe tener zona de descenso configurada."
                )
