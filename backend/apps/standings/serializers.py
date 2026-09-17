from rest_framework import serializers
from .models import Standing
from .zones import get_zone, get_zone_display


class StandingSerializer(serializers.ModelSerializer):
    club_name = serializers.CharField(source="club_season.club.name", read_only=True)
    season_name = serializers.CharField(source="season.name", read_only=True)
    division_name = serializers.CharField(source="division.name", read_only=True)
    zone = serializers.SerializerMethodField()

    class Meta:
        model = Standing
        fields = [
            "id", "season", "division", "club_season",
            "played", "won", "drawn", "lost",
            "goals_for", "goals_against", "goal_difference",
            "points", "position", "updated_at",
            "club_name", "season_name", "division_name", "zone",
        ]

    def get_zone(self, obj):
        zone = get_zone(obj)
        return get_zone_display(zone)
