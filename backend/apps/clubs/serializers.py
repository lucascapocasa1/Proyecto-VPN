from django.utils import timezone
from rest_framework import serializers
from .models import Club, ClubSeason, ClubTitle


class ClubSerializer(serializers.ModelSerializer):
    country_name = serializers.CharField(source="country.name", read_only=True)

    class Meta:
        model = Club
        fields = [
            "id", "name", "short_name", "logo", "country",
            "country_name", "founded_date", "is_active", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class ClubSeasonSerializer(serializers.ModelSerializer):
    club_name = serializers.CharField(source="club.name", read_only=True)
    season_name = serializers.CharField(source="season.name", read_only=True)
    division_name = serializers.CharField(source="division.name", read_only=True)

    class Meta:
        model = ClubSeason
        fields = [
            "id", "club", "season", "division", "status",
            "club_name", "season_name", "division_name", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class ClubTitleSerializer(serializers.ModelSerializer):
    club_name = serializers.CharField(source="club.name", read_only=True)
    season_name = serializers.CharField(source="season.name", read_only=True)
    division_name = serializers.CharField(source="division.name", read_only=True, default=None)
    awarded_by_username = serializers.CharField(source="awarded_by.username", read_only=True)
    awarded_at = serializers.DateTimeField(required=False, default=timezone.now)

    class Meta:
        model = ClubTitle
        fields = [
            "id", "club", "season", "division", "title_type",
            "name", "awarded_at", "awarded_by", "notes",
            "club_name", "season_name", "division_name", "awarded_by_username",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "awarded_by"]


class ClubDetailSerializer(serializers.ModelSerializer):
    country_name = serializers.CharField(source="country.name", read_only=True)
    seasons = ClubSeasonSerializer(many=True, read_only=True)
    titles = ClubTitleSerializer(many=True, read_only=True)

    class Meta:
        model = Club
        fields = [
            "id", "name", "short_name", "logo", "country",
            "country_name", "founded_date", "is_active",
            "seasons", "titles", "created_at",
        ]
