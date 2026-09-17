from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.players.models import Player
from apps.matches.models import Match
from apps.competitions.models import Season, Division

from .services import (
    get_player_statistics,
    get_player_statistics_by_season,
    get_top_scorers,
    get_top_assists,
    get_top_mvp,
)
from .serializers import (
    PlayerStatsSerializer,
    TopScorerSerializer,
    TopAssistSerializer,
    TopMVPSerializer,
)


class StatisticsViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=["get"])
    def player(self, request):
        player_id = request.query_params.get("player_id")
        if not player_id:
            return Response({"error": "player_id es requerido"}, status=400)

        try:
            player = Player.objects.get(pk=player_id)
        except Player.DoesNotExist:
            return Response({"error": "Jugador no encontrado"}, status=404)

        season_id = request.query_params.get("season_id")
        division_id = request.query_params.get("division_id")

        season = None
        division = None
        if season_id:
            season = Season.objects.get(pk=season_id)
        if division_id:
            division = Division.objects.get(pk=division_id)

        stats = get_player_statistics(player, season=season, division=division)
        return Response({
            "player": {"id": player.id, "nickname": player.nickname},
            "stats": stats,
        })

    @action(detail=False, methods=["get"])
    def player_history(self, request):
        player_id = request.query_params.get("player_id")
        if not player_id:
            return Response({"error": "player_id es requerido"}, status=400)

        try:
            player = Player.objects.get(pk=player_id)
        except Player.DoesNotExist:
            return Response({"error": "Jugador no encontrado"}, status=404)

        history = get_player_statistics_by_season(player)
        return Response({
            "player": {"id": player.id, "nickname": player.nickname},
            "history": [
                {
                    "season": {"id": h["season"].id, "name": h["season"].name},
                    "stats": h["stats"],
                }
                for h in history
            ],
        })

    @action(detail=False, methods=["get"])
    def top_scorers(self, request):
        season_id = request.query_params.get("season_id")
        division_id = request.query_params.get("division_id")
        limit = int(request.query_params.get("limit", 10))

        season = None
        division = None
        if season_id:
            season = Season.objects.get(pk=season_id)
        if division_id:
            division = Division.objects.get(pk=division_id)

        scorers = get_top_scorers(season=season, division=division, limit=limit)
        return Response(scorers)

    @action(detail=False, methods=["get"])
    def top_assists(self, request):
        season_id = request.query_params.get("season_id")
        division_id = request.query_params.get("division_id")
        limit = int(request.query_params.get("limit", 10))

        season = None
        division = None
        if season_id:
            season = Season.objects.get(pk=season_id)
        if division_id:
            division = Division.objects.get(pk=division_id)

        assists = get_top_assists(season=season, division=division, limit=limit)
        return Response(assists)

    @action(detail=False, methods=["get"])
    def top_mvp(self, request):
        season_id = request.query_params.get("season_id")
        division_id = request.query_params.get("division_id")
        limit = int(request.query_params.get("limit", 10))

        season = None
        division = None
        if season_id:
            season = Season.objects.get(pk=season_id)
        if division_id:
            division = Division.objects.get(pk=division_id)

        mvp = get_top_mvp(season=season, division=division, limit=limit)
        return Response(mvp)
