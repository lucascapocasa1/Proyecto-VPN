from rest_framework import serializers
from .models import Player, PlayerIdentityHistory, PlayerClubHistory


class PlayerIdentityHistorySerializer(serializers.ModelSerializer):
    changed_by_username = serializers.CharField(source="changed_by.username", read_only=True, default=None)

    class Meta:
        model = PlayerIdentityHistory
        fields = ["id", "nickname", "changed_at", "changed_by", "changed_by_username", "reason"]
        read_only_fields = ["id"]


class PlayerClubHistorySerializer(serializers.ModelSerializer):
    club_name = serializers.CharField(source="club_season.club.name", read_only=True)
    season_name = serializers.CharField(source="club_season.season.name", read_only=True)
    division_name = serializers.CharField(source="club_season.division.name", read_only=True)
    is_current = serializers.BooleanField(read_only=True)

    class Meta:
        model = PlayerClubHistory
        fields = [
            "id", "player", "club_season", "joined_at", "left_at",
            "club_name", "season_name", "division_name", "is_current",
        ]
        read_only_fields = ["id"]


class PlayerSerializer(serializers.ModelSerializer):
    country_name = serializers.CharField(source="country.name", read_only=True, default=None)

    class Meta:
        model = Player
        fields = [
            "id", "nickname", "platform", "position", "country", "country_name",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class PlayerDetailSerializer(serializers.ModelSerializer):
    country_name = serializers.CharField(source="country.name", read_only=True, default=None)
    identity_history = PlayerIdentityHistorySerializer(many=True, read_only=True)
    club_history = PlayerClubHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Player
        fields = [
            "id", "nickname", "platform", "position", "country", "country_name",
            "is_active", "identity_history", "club_history",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
