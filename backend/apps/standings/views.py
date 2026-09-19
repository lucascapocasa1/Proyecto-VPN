from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from django.core.cache import cache
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Standing
from .serializers import StandingSerializer
from .services import recalculate_standings, recalculate_all_standings
from apps.competitions.models import Season
from apps.accounts.permissions import IsSuperAdmin, IsAdminLiga


class StandingViewSet(viewsets.ModelViewSet):
    queryset = Standing.objects.select_related(
        "season", "division", "club_season__club"
    ).all()
    serializer_class = StandingSerializer
    filterset_fields = ["season", "division", "club_season"]
    ordering_fields = ["position", "points", "goal_difference"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        if self.action == "recalculate":
            return [IsAdminLiga()]
        return [IsSuperAdmin()]

    @action(detail=False, methods=["post"])
    def recalculate(self, request):
        season_id = request.data.get("season_id")
        division_id = request.data.get("division_id")

        if not season_id:
            return Response(
                {"error": "season_id es requerido"},
                status=400,
            )

        try:
            season = Season.objects.get(pk=season_id)
        except Season.DoesNotExist:
            return Response(
                {"error": "Temporada no encontrada"},
                status=404,
            )

        if division_id:
            from apps.competitions.models import Division
            try:
                division = Division.objects.get(pk=division_id, season=season)
            except Division.DoesNotExist:
                return Response(
                    {"error": "División no encontrada"},
                    status=404,
                )
            standings = recalculate_standings(season, division)
            cache_key = f"standings_{season_id}_{division_id}"
            cache.delete(cache_key)
            return Response({
                "message": f"Recalculadas {len(standings)} posiciones",
                "count": len(standings),
            })
        else:
            results = recalculate_all_standings(season)
            total = sum(len(s) for s in results.values())
            for div_id in results:
                cache.delete(f"standings_{season_id}_{div_id}")
            return Response({
                "message": f"Recalculadas {total} posiciones en {len(results)} divisiones",
                "count": total,
            })
