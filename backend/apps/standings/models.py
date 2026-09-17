from django.db import models


class Standing(models.Model):
    """Represents the standing for a club in a specific season and division.

    This is derived data - it should be recalculated from Match results.
    """

    season = models.ForeignKey(
        "competitions.Season",
        on_delete=models.CASCADE,
        related_name="standings",
    )
    division = models.ForeignKey(
        "competitions.Division",
        on_delete=models.CASCADE,
        related_name="standings",
    )
    club_season = models.ForeignKey(
        "clubs.ClubSeason",
        on_delete=models.CASCADE,
        related_name="standings",
    )
    played = models.IntegerField(default=0)
    won = models.IntegerField(default=0)
    drawn = models.IntegerField(default=0)
    lost = models.IntegerField(default=0)
    goals_for = models.IntegerField(default=0)
    goals_against = models.IntegerField(default=0)
    goal_difference = models.IntegerField(default=0)
    points = models.IntegerField(default=0)
    position = models.IntegerField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Posición"
        verbose_name_plural = "Tabla de Posiciones"
        unique_together = [["season", "division", "club_season"]]
        ordering = ["season", "division", "position"]

    def __str__(self):
        return f"{self.club_season.club.name} - {self.position}°"
