from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from .models import Player, PlayerIdentityHistory, PlayerClubHistory, Transfer


class PlayerIdentityHistorySerializer(serializers.ModelSerializer):
    changed_by_username = serializers.CharField(source="changed_by.username", read_only=True, default=None)

    class Meta:
        model = PlayerIdentityHistory
        fields = ["id", "nickname", "changed_at", "changed_by", "changed_by_username", "reason"]
        read_only_fields = ["id"]


class PlayerClubHistorySerializer(serializers.ModelSerializer):
    club_name = serializers.CharField(source="club_season.club.name", read_only=True)
    club = serializers.IntegerField(source="club_season.club_id", read_only=True)
    player_nickname = serializers.CharField(source="player.nickname", read_only=True)
    season_name = serializers.CharField(source="club_season.season.name", read_only=True)
    division_name = serializers.CharField(source="club_season.division.name", read_only=True)
    game_name = serializers.CharField(source="club_season.season.game.name", read_only=True, default=None)
    is_current = serializers.BooleanField(read_only=True)
    stats = serializers.SerializerMethodField()

    class Meta:
        model = PlayerClubHistory
        fields = [
            "id", "player", "club_season", "joined_at", "left_at",
            "club_name", "club", "player_nickname", "season_name",
            "division_name", "game_name",
            "is_current", "stats",
        ]
        read_only_fields = ["id"]

    def get_stats(self, obj):
        from apps.statistics.services import get_player_stats_by_club_season, EMPTY_CLUB_STATS

        cache = getattr(self, "_stats_cache", None)
        if cache is None:
            cache = {}
            self._stats_cache = cache
        if obj.player_id not in cache:
            cache[obj.player_id] = get_player_stats_by_club_season(obj.player)
        return cache[obj.player_id].get(obj.club_season_id, dict(EMPTY_CLUB_STATS))


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


class TransferSerializer(serializers.ModelSerializer):
    player_name = serializers.CharField(source="player.nickname", read_only=True)
    from_club_name = serializers.CharField(
        source="from_club_season.club.name", read_only=True, default=None
    )
    from_division_name = serializers.CharField(
        source="from_club_season.division.name", read_only=True, default=None
    )
    from_season_name = serializers.CharField(
        source="from_club_season.season.name", read_only=True, default=None
    )
    to_club_name = serializers.CharField(source="to_club_season.club.name", read_only=True)
    to_division_name = serializers.CharField(
        source="to_club_season.division.name", read_only=True
    )
    to_season_name = serializers.CharField(
        source="to_club_season.season.name", read_only=True
    )
    registered_by_username = serializers.CharField(
        source="registered_by.username", read_only=True, default=None
    )
    from_club = serializers.SerializerMethodField()
    to_club = serializers.SerializerMethodField()

    class Meta:
        model = Transfer
        fields = [
            "id", "player", "from_club_season", "to_club_season", "date",
            "registered_by", "created_at",
            "player_name", "from_club_name", "from_division_name", "from_season_name",
            "to_club_name", "to_division_name", "to_season_name",
            "registered_by_username", "from_club", "to_club",
        ]
        read_only_fields = ["id", "from_club_season", "registered_by", "created_at"]

    def get_from_club(self, obj):
        return obj.from_club_season.club_id if obj.from_club_season_id else None

    def get_to_club(self, obj):
        return obj.to_club_season.club_id

    def validate(self, data):
        player = data["player"]
        to = data["to_club_season"]
        open_stints = PlayerClubHistory.objects.filter(player=player, left_at=None)
        count = open_stints.count()
        if count == 0:
            raise serializers.ValidationError("El jugador no tiene club actual.")
        if count > 1:
            raise serializers.ValidationError(
                "El jugador tiene más de un club actual (datos inconsistentes)."
            )
        current = open_stints.get()
        if current.club_season_id == to.id:
            raise serializers.ValidationError("El destino debe ser un club distinto al actual.")
        if current.club_season.season_id != to.season_id:
            raise serializers.ValidationError(
                "El destino debe pertenecer a la misma temporada que el club actual."
            )
        return data

    @transaction.atomic
    def create(self, validated_data):
        player = validated_data["player"]
        current = PlayerClubHistory.objects.select_for_update().get(
            player=player, left_at=None
        )
        now = timezone.now()
        current.left_at = now
        current.save(update_fields=["left_at"])
        PlayerClubHistory.objects.create(
            player=player,
            club_season=validated_data["to_club_season"],
            joined_at=now,
        )
        validated_data["from_club_season"] = current.club_season
        return Transfer.objects.create(**validated_data)
