from rest_framework import viewsets, permissions, filters, status
from rest_framework.response import Response
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from .models import Player, PlayerIdentityHistory, PlayerClubHistory, Transfer
from .serializers import (
    PlayerSerializer, PlayerDetailSerializer,
    PlayerIdentityHistorySerializer, PlayerClubHistorySerializer,
    TransferSerializer,
)
from apps.accounts.permissions import IsSuperAdmin, IsAdminLiga, IsAdminClub, IsOwnerOrAdmin


class PlayerViewSet(viewsets.ModelViewSet):
    queryset = Player.objects.select_related("country").all()
    filterset_fields = ["country", "platform", "is_active"]
    search_fields = ["nickname"]
    ordering_fields = ["nickname", "created_at"]
    tags = ["Players"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [IsAdminLiga()]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return PlayerDetailSerializer
        return PlayerSerializer


class PlayerIdentityHistoryViewSet(viewsets.ModelViewSet):
    queryset = PlayerIdentityHistory.objects.select_related(
        "player", "changed_by"
    ).all()
    serializer_class = PlayerIdentityHistorySerializer
    filterset_fields = ["player"]
    ordering_fields = ["changed_at"]
    tags = ["Players"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [IsAdminLiga()]

    def perform_create(self, serializer):
        serializer.save(changed_by=self.request.user)


class PlayerClubHistoryViewSet(viewsets.ModelViewSet):
    queryset = PlayerClubHistory.objects.select_related(
        "player", "club_season__club", "club_season__season", "club_season__division"
    ).all()
    serializer_class = PlayerClubHistorySerializer
    filterset_fields = ["player", "club_season"]
    ordering_fields = ["joined_at"]
    tags = ["Players"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [IsAdminLiga()]


class TransferViewSet(viewsets.ModelViewSet):
    queryset = Transfer.objects.select_related(
        "player",
        "from_club_season__club", "from_club_season__division", "from_club_season__season",
        "to_club_season__club", "to_club_season__division", "to_club_season__season",
        "registered_by",
    ).all()
    serializer_class = TransferSerializer
    filterset_fields = ["player", "date"]
    search_fields = ["player__nickname"]
    ordering_fields = ["date", "created_at"]
    tags = ["Transfers"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [IsAdminLiga()]

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        season = self.request.query_params.get("season")
        if season:
            queryset = queryset.filter(to_club_season__season_id=season)
        return queryset

    def perform_create(self, serializer):
        serializer.save(registered_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        transfer = self.get_object()
        latest = (
            Transfer.objects.filter(player=transfer.player)
            .order_by("-date", "-id")
            .first()
        )
        if latest and latest.pk != transfer.pk:
            return Response(
                {"error": "Solo se puede eliminar la transferencia más reciente del jugador."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            new_stint = PlayerClubHistory.objects.filter(
                player=transfer.player,
                club_season=transfer.to_club_season,
                left_at=None,
            ).first()
            if new_stint is None:
                return Response(
                    {"error": "No se encontró el stint abierto en el club destino."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            new_stint.delete()
            if transfer.from_club_season_id:
                old_stint = (
                    PlayerClubHistory.objects.filter(
                        player=transfer.player,
                        club_season=transfer.from_club_season,
                        left_at__isnull=False,
                    )
                    .order_by("-joined_at")
                    .first()
                )
                if old_stint:
                    old_stint.left_at = None
                    old_stint.save(update_fields=["left_at"])
            transfer.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
