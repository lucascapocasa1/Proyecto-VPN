from rest_framework import serializers
from django.core.validators import MinValueValidator, MaxValueValidator
from .models import Matchday, Match, MatchPlayer, MatchEvent, MatchPerformance


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
        home = data.get(
            "home_club_season",
            self.instance.home_club_season if self.instance else None,
        )
        away = data.get(
            "away_club_season",
            self.instance.away_club_season if self.instance else None,
        )
        if home is not None and away is not None and home == away:
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


class MatchPerformanceSerializer(serializers.ModelSerializer):
    match = serializers.IntegerField(source="match_player.match_id", read_only=True)
    player = serializers.IntegerField(
        source="match_player.player_id", read_only=True, default=None
    )
    player_nickname = serializers.CharField(
        source="match_player.player.nickname", read_only=True, default=None
    )
    display_name = serializers.CharField(
        source="match_player.display_name", read_only=True
    )
    club_name = serializers.CharField(
        source="match_player.club_season.club.name", read_only=True
    )
    match_date = serializers.DateField(
        source="match_player.match.date", read_only=True, default=None
    )
    home_club_name = serializers.CharField(
        source="match_player.match.home_club_season.club.name", read_only=True
    )
    away_club_name = serializers.CharField(
        source="match_player.match.away_club_season.club.name", read_only=True
    )
    home_goals = serializers.IntegerField(
        source="match_player.match.home_goals", read_only=True, default=None
    )
    away_goals = serializers.IntegerField(
        source="match_player.match.away_goals", read_only=True, default=None
    )
    rival_name = serializers.SerializerMethodField()

    rating = serializers.DecimalField(
        max_digits=3, decimal_places=1, coerce_to_string=False,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
    )
    distance_km = serializers.DecimalField(
        max_digits=4, decimal_places=1, coerce_to_string=False, default=0,
        validators=[MinValueValidator(0), MaxValueValidator(999.9)],
    )
    sprint_distance_km = serializers.DecimalField(
        max_digits=4, decimal_places=1, coerce_to_string=False, default=0,
        validators=[MinValueValidator(0), MaxValueValidator(999.9)],
    )

    class Meta:
        model = MatchPerformance
        fields = [
            "id", "match_player", "match", "player", "player_nickname",
            "display_name", "club_name", "match_date",
            "home_club_name", "away_club_name", "home_goals", "away_goals",
            "rival_name",
            "rating", "goals", "assists", "shots", "shot_accuracy_pct",
            "passes", "pass_accuracy_pct", "dribbles", "dribble_success_pct",
            "tackles", "tackle_success_pct", "offsides", "fouls",
            "possession_won", "possession_lost", "minutes_played",
            "distance_km", "sprint_distance_km",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_rival_name(self, obj):
        match = obj.match_player.match
        if obj.match_player.club_season_id == match.home_club_season_id:
            return match.away_club_season.club.name
        return match.home_club_season.club.name

    def validate_match_player(self, value):
        if value.player_id is None:
            raise serializers.ValidationError("Los BOT no tienen rendimiento.")
        return value
