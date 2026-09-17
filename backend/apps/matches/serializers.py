from rest_framework import serializers
from .models import Matchday, Match, MatchPlayer, MatchEvent


class MatchdaySerializer(serializers.ModelSerializer):
    season_name = serializers.CharField(source="season.name", read_only=True)
    division_name = serializers.CharField(source="division.name", read_only=True)

    class Meta:
        model = Matchday
        fields = [
            "id", "season", "division", "number", "name", "date",
            "season_name", "division_name",
        ]
        read_only_fields = ["id"]


class MatchEventSerializer(serializers.ModelSerializer):
    player_nickname = serializers.CharField(
        source="match_player.player.nickname", read_only=True, default=None
    )
    display_name = serializers.CharField(source="match_player.display_name", read_only=True)
    club_name = serializers.CharField(
        source="match_player.club_season.club.name", read_only=True
    )

    class Meta:
        model = MatchEvent
        fields = [
            "id", "match", "match_player", "event_type", "minute",
            "player_nickname", "display_name", "club_name", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class MatchPlayerSerializer(serializers.ModelSerializer):
    player_nickname = serializers.CharField(
        source="player.nickname", read_only=True, default=None
    )
    club_name = serializers.CharField(source="club_season.club.name", read_only=True)

    class Meta:
        model = MatchPlayer
        fields = [
            "id", "match", "player", "club_season", "display_name",
            "is_starter", "player_nickname", "club_name", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class MatchSerializer(serializers.ModelSerializer):
    home_club_name = serializers.CharField(
        source="home_club_season.club.name", read_only=True
    )
    away_club_name = serializers.CharField(
        source="away_club_season.club.name", read_only=True
    )
    season_name = serializers.CharField(source="season.name", read_only=True)
    division_name = serializers.CharField(source="division.name", read_only=True)
    matchday_name = serializers.CharField(source="matchday.name", read_only=True, default=None)

    class Meta:
        model = Match
        fields = [
            "id", "season", "division", "matchday",
            "home_club_season", "away_club_season",
            "home_goals", "away_goals",
            "date", "time", "status",
            "home_club_name", "away_club_name",
            "season_name", "division_name", "matchday_name",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, data):
        if data.get("home_club_season") == data.get("away_club_season"):
            raise serializers.ValidationError("Local y visitante deben ser diferentes.")
        return data


class MatchDetailSerializer(serializers.ModelSerializer):
    home_club_name = serializers.CharField(
        source="home_club_season.club.name", read_only=True
    )
    away_club_name = serializers.CharField(
        source="away_club_season.club.name", read_only=True
    )
    season_name = serializers.CharField(source="season.name", read_only=True)
    division_name = serializers.CharField(source="division.name", read_only=True)
    matchday_name = serializers.CharField(source="matchday.name", read_only=True, default=None)
    match_players = MatchPlayerSerializer(many=True, read_only=True)
    events = MatchEventSerializer(many=True, read_only=True)

    class Meta:
        model = Match
        fields = [
            "id", "season", "division", "matchday",
            "home_club_season", "away_club_season",
            "home_goals", "away_goals",
            "date", "time", "status",
            "home_club_name", "away_club_name",
            "season_name", "division_name", "matchday_name",
            "match_players", "events",
            "created_at", "updated_at",
        ]
