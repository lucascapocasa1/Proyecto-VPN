from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Standing
from .serializers import StandingSerializer
from .services import recalculate_standings, recalculate_all_standings
from apps.competitions.models import Season


class StandingViewSet(viewsets.ModelViewSet):
    queryset = Standing.objects.select_related(
        "season", "division", "club_season__club"
    ).all()
    serializer_class = StandingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @action(detail=False, methods=["post"], permission_classes=[permissions.IsAdminUser])
    def recalculate(self, request):
        season_id = request.data.get("season_id")
        division_id = request.data.get("division_id")

        if not season_id:
            return Response(
                {"error": "season_id es requerido"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            season = Season.objects.get(pk=season_id)
        except Season.DoesNotExist:
            return Response(
                {"error": "Temporada no encontrada"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if division_id:
            from apps.competitions.models import Division
            try:
                division = Division.objects.get(pk=division_id, season=season)
            except Division.DoesNotExist:
                return Response(
                    {"error": "División no encontrada"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            standings = recalculate_standings(season, division)
            return Response({
                "message": f"Recalculadas {len(standings)} posiciones",
                "count": len(standings),
            })
        else:
            results = recalculate_all_standings(season)
            total = sum(len(s) for s in results.values())
            return Response({
                "message": f"Recalculadas {total} posiciones en {len(results)} divisiones",
                "count": total,
            })
