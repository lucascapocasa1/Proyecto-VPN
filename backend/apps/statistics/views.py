from rest_framework import viewsets, permissions
from django.core.cache import cache
from django.conf import settings
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
    get_performance_leaderboard,
    get_performance_by_position,
    get_player_match_series,
    PERFORMANCE_METRICS,
)
from .serializers import (
    PlayerStatsSerializer,
    TopScorerSerializer,
    TopAssistSerializer,
    TopMVPSerializer,
)

STATISTICS_CACHE = getattr(settings, "STATISTICS_CACHE_TIMEOUT", 600)


def _int_param(request, name, default, lo, hi):
    try:
        value = int(request.query_params.get(name, default))
    except (TypeError, ValueError):
        return default
    return max(lo, min(hi, value))


def _resolve_season_division(request):
    season = division = None
    season_id = request.query_params.get("season_id")
    division_id = request.query_params.get("division_id")
    if season_id:
        try:
            season = Season.objects.get(pk=season_id)
        except (Season.DoesNotExist, ValueError):
            return None, None, {"error": "Temporada no encontrada"}, 404
    if division_id:
        try:
            division = Division.objects.get(pk=division_id)
        except (Division.DoesNotExist, ValueError):
            return None, None, {"error": "División no encontrada"}, 404
    return season, division, None, None


class StatisticsViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.AllowAny]
    serializer_class = TopScorerSerializer
    tags = ["Statistics"]

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

        cache_key = f"stats_player_{player_id}_{season_id}_{division_id}"
        cached = cache.get(cache_key)
        if cached:
            return Response(cached)

        season = None
        division = None
        if season_id:
            season = Season.objects.get(pk=season_id)
        if division_id:
            division = Division.objects.get(pk=division_id)

        stats = get_player_statistics(player, season=season, division=division)
        result = {
            "player": {"id": player.id, "nickname": player.nickname},
            "stats": stats,
        }
        cache.set(cache_key, result, STATISTICS_CACHE)
        return Response(result)

    @action(detail=False, methods=["get"])
    def player_history(self, request):
        player_id = request.query_params.get("player_id")
        if not player_id:
            return Response({"error": "player_id es requerido"}, status=400)

        try:
            player = Player.objects.get(pk=player_id)
        except Player.DoesNotExist:
            return Response({"error": "Jugador no encontrado"}, status=404)

        cache_key = f"stats_history_{player_id}"
        cached = cache.get(cache_key)
        if cached:
            return Response(cached)

        history = get_player_statistics_by_season(player)
        result = {
            "player": {"id": player.id, "nickname": player.nickname},
            "history": [
                {
                    "season": {"id": h["season"].id, "name": h["season"].name},
                    "stats": h["stats"],
                }
                for h in history
            ],
        }
        cache.set(cache_key, result, STATISTICS_CACHE)
        return Response(result)

    @action(detail=False, methods=["get"])
    def top_scorers(self, request):
        season_id = request.query_params.get("season_id")
        division_id = request.query_params.get("division_id")
        limit = int(request.query_params.get("limit", 10))

        cache_key = f"stats_scorers_{season_id}_{division_id}_{limit}"
        cached = cache.get(cache_key)
        if cached:
            return Response(cached)

        season = None
        division = None
        if season_id:
            season = Season.objects.get(pk=season_id)
        if division_id:
            division = Division.objects.get(pk=division_id)

        scorers = get_top_scorers(season=season, division=division, limit=limit)
        cache.set(cache_key, scorers, STATISTICS_CACHE)
        return Response(scorers)

    @action(detail=False, methods=["get"])
    def top_assists(self, request):
        season_id = request.query_params.get("season_id")
        division_id = request.query_params.get("division_id")
        limit = int(request.query_params.get("limit", 10))

        cache_key = f"stats_assists_{season_id}_{division_id}_{limit}"
        cached = cache.get(cache_key)
        if cached:
            return Response(cached)

        season = None
        division = None
        if season_id:
            season = Season.objects.get(pk=season_id)
        if division_id:
            division = Division.objects.get(pk=division_id)

        assists = get_top_assists(season=season, division=division, limit=limit)
        cache.set(cache_key, assists, STATISTICS_CACHE)
        return Response(assists)

    @action(detail=False, methods=["get"])
    def top_mvp(self, request):
        season_id = request.query_params.get("season_id")
        division_id = request.query_params.get("division_id")
        limit = int(request.query_params.get("limit", 10))

        cache_key = f"stats_mvp_{season_id}_{division_id}_{limit}"
        cached = cache.get(cache_key)
        if cached:
            return Response(cached)

        season = None
        division = None
        if season_id:
            season = Season.objects.get(pk=season_id)
        if division_id:
            division = Division.objects.get(pk=division_id)

        mvp = get_top_mvp(season=season, division=division, limit=limit)
        cache.set(cache_key, mvp, STATISTICS_CACHE)
        return Response(mvp)

    @action(detail=False, methods=["get"])
    def performance_leaderboard(self, request):
        """Ranking por cualquier metrica de MatchPerformance (avg o sum)."""
        metric = request.query_params.get("metric", "rating")
        agg = request.query_params.get("agg", "avg")
        if metric not in PERFORMANCE_METRICS:
            return Response(
                {"error": f"Métrica inválida: {metric}",
                 "allowed": list(PERFORMANCE_METRICS)},
                status=400,
            )
        if agg not in ("avg", "sum"):
            return Response({"error": "agg debe ser 'avg' o 'sum'"}, status=400)

        limit = _int_param(request, "limit", 10, 1, 50)
        min_matches = _int_param(request, "min_matches", 1, 1, 200)

        season, division, error, status = _resolve_season_division(request)
        if error:
            return Response(error, status=status)

        cache_key = (
            f"stats_perf_lb_{metric}_{agg}_"
            f"{request.query_params.get('season_id')}_"
            f"{request.query_params.get('division_id')}_{limit}_{min_matches}"
        )
        cached = cache.get(cache_key)
        if cached:
            return Response(cached)

        rows = get_performance_leaderboard(
            metric=metric, agg=agg, season=season, division=division,
            limit=limit, min_matches=min_matches,
        )
        cache.set(cache_key, rows, STATISTICS_CACHE)
        return Response(rows)

    @action(detail=False, methods=["get"])
    def performance_by_position(self, request):
        """Promedios de metricas clave por posicion (ARQ/DEF/MED/DEL)."""
        season, division, error, status = _resolve_season_division(request)
        if error:
            return Response(error, status=status)

        cache_key = (
            f"stats_perf_pos_"
            f"{request.query_params.get('season_id')}_"
            f"{request.query_params.get('division_id')}"
        )
        cached = cache.get(cache_key)
        if cached:
            return Response(cached)

        rows = get_performance_by_position(season=season, division=division)
        cache.set(cache_key, rows, STATISTICS_CACHE)
        return Response(rows)

    @action(detail=False, methods=["get"])
    def player_match_series(self, request):
        """Serie por partido de un jugador (rating fisico + eventos)."""
        player_id = request.query_params.get("player_id")
        if not player_id:
            return Response({"error": "player_id es requerido"}, status=400)
        try:
            player = Player.objects.get(pk=player_id)
        except (Player.DoesNotExist, ValueError):
            return Response({"error": "Jugador no encontrado"}, status=404)

        cache_key = f"stats_series_{player_id}"
        cached = cache.get(cache_key)
        if cached:
            return Response(cached)

        series = get_player_match_series(player)
        cache.set(cache_key, series, STATISTICS_CACHE)
        return Response(series)
