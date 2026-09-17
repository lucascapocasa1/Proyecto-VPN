from django.db import models
from django.core.exceptions import ValidationError


class Matchday(models.Model):
    """Represents a matchday within a season and division."""

    season = models.ForeignKey(
        "competitions.Season",
        on_delete=models.CASCADE,
        related_name="matchdays",
    )
    division = models.ForeignKey(
        "competitions.Division",
        on_delete=models.CASCADE,
        related_name="matchdays",
    )
    number = models.IntegerField()
    name = models.CharField(max_length=100)
    date = models.DateField(blank=True, null=True)

    class Meta:
        verbose_name = "Jornada"
        verbose_name_plural = "Jornadas"
        unique_together = [["season", "division", "number"]]
        ordering = ["season", "division", "number"]

    def __str__(self):
        return f"{self.name} - {self.season.name}"


class Match(models.Model):
    """Represents a match between two clubs."""

    class Status(models.TextChoices):
        SCHEDULED = "SCHEDULED", "Programado"
        IN_PROGRESS = "IN_PROGRESS", "En Juego"
        FINISHED = "FINISHED", "Finalizado"
        POSTPONED = "POSTPONED", "Aplazado"
        CANCELLED = "CANCELLED", "Cancelado"

    season = models.ForeignKey(
        "competitions.Season",
        on_delete=models.PROTECT,
        related_name="matches",
    )
    division = models.ForeignKey(
        "competitions.Division",
        on_delete=models.PROTECT,
        related_name="matches",
    )
    matchday = models.ForeignKey(
        Matchday,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="matches",
    )
    home_club_season = models.ForeignKey(
        "clubs.ClubSeason",
        on_delete=models.PROTECT,
        related_name="home_matches",
    )
    away_club_season = models.ForeignKey(
        "clubs.ClubSeason",
        on_delete=models.PROTECT,
        related_name="away_matches",
    )
    home_goals = models.IntegerField(blank=True, null=True)
    away_goals = models.IntegerField(blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    time = models.TimeField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Partido"
        verbose_name_plural = "Partidos"
        ordering = ["date", "time", "matchday__number"]

    def __str__(self):
        return f"{self.home_club_season.club.name} vs {self.away_club_season.club.name}"

    def clean(self):
        if self.home_club_season == self.away_club_season:
            raise ValidationError("Local y visitante deben ser diferentes.")

        if self.home_club_season.season != self.season:
            raise ValidationError("El club local no pertenece a la temporada del partido.")

        if self.away_club_season.season != self.season:
            raise ValidationError("El club visitante no pertenece a la temporada del partido.")

        if self.home_club_season.division != self.division:
            raise ValidationError("El club local no pertenece a la división del partido.")

        if self.away_club_season.division != self.division:
            raise ValidationError("El club visitante no pertenece a la división del partido.")

        if self.matchday:
            if self.matchday.season != self.season:
                raise ValidationError("La jornada no pertenece a la temporada del partido.")

            if self.matchday.division != self.division:
                raise ValidationError("La jornada no pertenece a la división del partido.")


class MatchPlayer(models.Model):
    """Represents a player who participated in a match."""

    match = models.ForeignKey(
        Match,
        on_delete=models.CASCADE,
        related_name="match_players",
    )
    player = models.ForeignKey(
        "players.Player",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="match_participations",
        help_text="NULL represents a BOT",
    )
    club_season = models.ForeignKey(
        "clubs.ClubSeason",
        on_delete=models.CASCADE,
        related_name="match_players",
    )
    display_name = models.CharField(max_length=100)
    is_starter = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Jugador del Partido"
        verbose_name_plural = "Jugadores del Partido"
        ordering = ["match", "club_season", "-is_starter"]

    def __str__(self):
        return f"{self.display_name} - {self.match}"

    def clean(self):
        match = self.match
        if self.club_season not in (match.home_club_season, match.away_club_season):
            raise ValidationError(
                "El jugador no pertenece a ninguno de los clubes participantes."
            )


class MatchEvent(models.Model):
    """Represents an event that occurred during a match."""

    class EventType(models.TextChoices):
        GOAL = "GOAL", "Gol"
        OWN_GOAL = "OWN_GOAL", "Gol en Contra"
        ASSIST = "ASSIST", "Asistencia"
        YELLOW_CARD = "YELLOW_CARD", "Tarjeta Amarilla"
        RED_CARD = "RED_CARD", "Tarjeta Roja"
        MVP = "MVP", "MVP"

    match = models.ForeignKey(
        Match,
        on_delete=models.CASCADE,
        related_name="events",
    )
    match_player = models.ForeignKey(
        MatchPlayer,
        on_delete=models.CASCADE,
        related_name="events",
    )
    event_type = models.CharField(
        max_length=20,
        choices=EventType.choices,
    )
    minute = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Evento del Partido"
        verbose_name_plural = "Eventos del Partido"
        ordering = ["match", "minute", "event_type"]

    def __str__(self):
        return f"{self.get_event_type_display()} - {self.match_player.display_name}"

    def clean(self):
        if self.match_player.match != self.match:
            raise ValidationError(
                "El jugador no pertenece a este partido."
            )
