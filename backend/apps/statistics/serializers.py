from rest_framework import serializers
from apps.players.models import Player


class PlayerStatsSerializer(serializers.ModelSerializer):
    stats = serializers.SerializerMethodField()

    class Meta:
        model = Player
        fields = ["id", "nickname", "stats"]

    def get_stats(self, obj):
        from apps.statistics.services import get_player_statistics
        return get_player_statistics(obj)


class TopScorerSerializer(serializers.Serializer):
    player_id = serializers.IntegerField()
    nickname = serializers.CharField()
    goals = serializers.IntegerField()


class TopAssistSerializer(serializers.Serializer):
    player_id = serializers.IntegerField()
    nickname = serializers.CharField()
    assists = serializers.IntegerField()


class TopMVPSerializer(serializers.Serializer):
    player_id = serializers.IntegerField()
    nickname = serializers.CharField()
    mvp_count = serializers.IntegerField()
