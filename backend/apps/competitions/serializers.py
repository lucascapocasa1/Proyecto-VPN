from rest_framework import serializers
from .models import Country, Game, CompetitionFormat, League, Season, Division


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ["id", "name", "code", "flag_url"]


class GameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        fields = ["id", "name", "year"]


class CompetitionFormatSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompetitionFormat
        fields = ["id", "name", "format_type", "has_playoffs", "description"]


class DivisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Division
        fields = [
            "id", "name", "season", "order", "max_clubs",
            "playoff_zone_start", "playoff_zone_end",
            "promotion_zone_start", "promotion_zone_end",
            "relegation_zone_start", "relegation_zone_end",
            "has_relegation",
        ]


class LeagueSerializer(serializers.ModelSerializer):
    country_name = serializers.CharField(source="country.name", read_only=True)

    class Meta:
        model = League
        fields = ["id", "name", "country", "country_name"]


class SeasonSerializer(serializers.ModelSerializer):
    league_name = serializers.CharField(source="league.name", read_only=True)
    game_name = serializers.CharField(source="game.name", read_only=True)
    format_name = serializers.CharField(source="format.name", read_only=True)
    divisions = DivisionSerializer(many=True, read_only=True)

    class Meta:
        model = Season
        fields = [
            "id", "name", "league", "game", "number",
            "format", "status", "created_at", "updated_at",
            "league_name", "game_name", "format_name", "divisions",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class SeasonListSerializer(serializers.ModelSerializer):
    league_name = serializers.CharField(source="league.name", read_only=True)
    game_name = serializers.CharField(source="game.name", read_only=True)

    class Meta:
        model = Season
        fields = [
            "id", "name", "league", "game", "number",
            "status", "league_name", "game_name",
        ]
