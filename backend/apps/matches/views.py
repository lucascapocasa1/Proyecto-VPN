from django.core.cache import cache
from django.db import transaction
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
import django_filters
from .models import Matchday, Match, MatchPlayer, MatchEvent, MatchPerformance
from .serializers import (
    MatchdaySerializer, MatchSerializer, MatchDetailSerializer,
    MatchPlayerSerializer, MatchEventSerializer, MatchPerformanceSerializer,
)
from .services.ocr import (
    MAX_IMAGES, MAX_IMAGE_BYTES, TesseractNotAvailable,
    analyze_images as ocr_analyze_images,
)
from apps.accounts.permissions import IsSuperAdmin, IsAdminLiga, CanManageLeague
from apps.standings.services import recalculate_standings


def _refresh_derived(match):
    recalculate_standings(match.season, match.division)
    cache.clear()


def _build_roster(match):
    """Plantel candidato para matchear el apodo OCR: alineación + stints + apodos viejos."""
    from apps.players.models import Player, PlayerClubHistory

    roster = {}

    def _entry(player_id, nickname):
        return roster.setdefault(
            player_id,
            {"player": player_id, "nickname": nickname, "aliases": set()},
        )

    for mp in MatchPlayer.objects.filter(match=match).select_related("player"):
        if mp.player_id is None:
            continue
        entry = _entry(mp.player_id, mp.player.nickname)
        if mp.player.nickname:
            entry["aliases"].add(mp.player.nickname.lower())
        if mp.display_name:
            entry["aliases"].add(mp.display_name.lower())

    stints = PlayerClubHistory.objects.filter(
        club_season_id__in=[match.home_club_season_id, match.away_club_season_id],
    ).select_related("player")
    for stint in stints:
        entry = _entry(stint.player_id, stint.player.nickname)
        if stint.player.nickname:
            entry["aliases"].add(stint.player.nickname.lower())

    if roster:
        players = Player.objects.filter(id__in=roster.keys()).prefetch_related(
            "identity_history"
        )
        for player in players:
            for change in player.identity_history.all():
                if change.nickname:
                    roster[player.id]["aliases"].add(change.nickname.lower())

    return list(roster.values())


PERFORMANCE_STAT_FIELDS = [
    "rating", "goals", "assists", "shots", "shot_accuracy_pct",
    "passes", "pass_accuracy_pct", "dribbles", "dribble_success_pct",
    "tackles", "tackle_success_pct", "offsides", "fouls",
    "possession_won", "possession_lost", "minutes_played",
    "distance_km", "sprint_distance_km",
]


class MatchdayViewSet(viewsets.ModelViewSet):
    queryset = Matchday.objects.select_related("season", "division").all()
    serializer_class = MatchdaySerializer
    filterset_fields = ["season", "division"]
    ordering_fields = ["number", "date"]
    tags = ["Matches"]
    tags = ["Matches"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [IsAdminLiga()]


class MatchViewSet(viewsets.ModelViewSet):
    queryset = Match.objects.select_related(
        "season", "division", "matchday",
        "home_club_season__club", "away_club_season__club",
    ).all()
    filterset_fields = ["season", "division", "matchday", "status"]
    search_fields = ["home_club_season__club__name", "away_club_season__club__name"]
    ordering_fields = ["date", "status", "created_at"]
    tags = ["Matches"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [IsAdminLiga()]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return MatchDetailSerializer
        return MatchSerializer

    def perform_create(self, serializer):
        match = serializer.save()
        _refresh_derived(match)

    def perform_update(self, serializer):
        match = serializer.save()
        _refresh_derived(match)

    def perform_destroy(self, instance):
        match = instance
        super().perform_destroy(instance)
        _refresh_derived(match)

    @action(detail=True, methods=["post"], url_path="performances/batch")
    def performances_batch(self, request, pk=None):
        match = self.get_object()
        items = request.data
        if not isinstance(items, list) or not items:
            return Response(
                {"error": "Se espera una lista de items no vacía."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from apps.players.models import Player, PlayerClubHistory

        errors = []
        results = []

        with transaction.atomic():
            prepared = []
            for index, item in enumerate(items):
                if not isinstance(item, dict):
                    errors.append({"index": index, "error": "Item inválido."})
                    continue

                player_id = item.get("player")
                if not player_id:
                    errors.append({"index": index, "error": "Falta el jugador."})
                    continue
                try:
                    player = Player.objects.get(pk=player_id)
                except (Player.DoesNotExist, ValueError, TypeError):
                    errors.append(
                        {"index": index, "error": f"Jugador {player_id} no existe."}
                    )
                    continue

                mp = MatchPlayer.objects.filter(match=match, player=player).first()
                if mp is None:
                    stints = PlayerClubHistory.objects.filter(
                        player=player,
                        club_season_id__in=[
                            match.home_club_season_id,
                            match.away_club_season_id,
                        ],
                    )
                    stint = (
                        stints.filter(left_at__isnull=True).first()
                        or stints.order_by("-joined_at").first()
                    )
                    if stint is None:
                        errors.append(
                            {
                                "index": index,
                                "player": player.id,
                                "error": "El jugador no tiene stint en los clubes del partido.",
                            }
                        )
                        continue
                    mp = MatchPlayer.objects.create(
                        match=match,
                        player=player,
                        club_season=stint.club_season,
                        display_name=player.nickname,
                        is_starter=True,
                    )

                data = {f: item[f] for f in PERFORMANCE_STAT_FIELDS if f in item}
                data["match_player"] = mp.id
                existing = MatchPerformance.objects.filter(match_player=mp).first()
                serializer = MatchPerformanceSerializer(
                    instance=existing, data=data, partial=existing is not None
                )
                if not serializer.is_valid():
                    errors.append(
                        {"index": index, "player": player.id, "errors": serializer.errors}
                    )
                    continue
                prepared.append(serializer)

            if errors:
                transaction.set_rollback(True)
            else:
                results = [serializer.save() for serializer in prepared]
                cache.clear()

        if errors:
            return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        output = MatchPerformanceSerializer(
            results, many=True, context={"request": request}
        )
        return Response(output.data, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=["post"],
        url_path="performances/analyze",
        parser_classes=[MultiPartParser, FormParser],
    )
    def performances_analyze(self, request, pk=None):
        """Analiza capturas FIFA con OCR y devuelve stats sugeridas (sin persistir).

        Multipart con `images` (≤30, ≤20MB c/u). Las imágenes se descartan
        al terminar. El guardado se hace después vía performances/batch.
        """
        match = self.get_object()
        files = request.FILES.getlist("images")
        if not files:
            return Response(
                {"error": "No se enviaron imágenes."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(files) > MAX_IMAGES:
            return Response(
                {"error": f"Máximo {MAX_IMAGES} imágenes por solicitud."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        images = []
        for f in files:
            if not (f.content_type or "").startswith("image/"):
                return Response(
                    {"error": f"{f.name}: solo se aceptan imágenes."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            raw = f.read()
            if len(raw) > MAX_IMAGE_BYTES:
                return Response(
                    {"error": f"{f.name}: supera {MAX_IMAGE_BYTES // (1024 * 1024)}MB."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            images.append((f.name, raw))

        try:
            results = ocr_analyze_images(images, _build_roster(match))
        except TesseractNotAvailable:
            return Response(
                {"error": "Tesseract no está instalado en el servidor."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        ok = sum(1 for r in results if r.get("success"))
        return Response(
            {
                "total": len(results),
                "exitosos": ok,
                "fallidos": len(results) - ok,
                "results": results,
            },
            status=status.HTTP_200_OK,
        )


class MatchPlayerViewSet(viewsets.ModelViewSet):
    queryset = MatchPlayer.objects.select_related(
        "match", "player", "club_season__club"
    ).all()
    serializer_class = MatchPlayerSerializer
    filterset_fields = ["match", "player", "club_season"]
    tags = ["Matches"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [IsAdminLiga()]

    def perform_create(self, serializer):
        serializer.save()
        cache.clear()

    def perform_update(self, serializer):
        serializer.save()
        cache.clear()

    def perform_destroy(self, instance):
        super().perform_destroy(instance)
        cache.clear()


class MatchEventViewSet(viewsets.ModelViewSet):
    queryset = MatchEvent.objects.select_related(
        "match", "match_player__player", "match_player__club_season__club"
    ).all()
    serializer_class = MatchEventSerializer
    filterset_fields = ["match", "match_player", "event_type"]
    ordering_fields = ["minute"]
    tags = ["Matches"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [IsAdminLiga()]

    def perform_create(self, serializer):
        serializer.save()
        cache.clear()

    def perform_update(self, serializer):
        serializer.save()
        cache.clear()

    def perform_destroy(self, instance):
        super().perform_destroy(instance)
        cache.clear()


class MatchPerformanceFilter(django_filters.FilterSet):
    match = django_filters.NumberFilter(field_name="match_player__match")
    player = django_filters.NumberFilter(field_name="match_player__player")

    class Meta:
        model = MatchPerformance
        fields = ["match", "match_player", "player"]


class MatchPerformanceViewSet(viewsets.ModelViewSet):
    queryset = MatchPerformance.objects.select_related(
        "match_player__player",
        "match_player__club_season__club",
        "match_player__match__home_club_season__club",
        "match_player__match__away_club_season__club",
    ).all()
    serializer_class = MatchPerformanceSerializer
    filterset_class = MatchPerformanceFilter
    ordering_fields = ["rating", "updated_at"]
    tags = ["Matches"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [IsAdminLiga()]

    def perform_create(self, serializer):
        serializer.save()
        cache.clear()

    def perform_update(self, serializer):
        serializer.save()
        cache.clear()

    def perform_destroy(self, instance):
        super().perform_destroy(instance)
        cache.clear()
