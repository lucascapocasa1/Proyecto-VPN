from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Player, PlayerIdentityHistory, PlayerClubHistory
from .serializers import (
    PlayerSerializer, PlayerDetailSerializer,
    PlayerIdentityHistorySerializer, PlayerClubHistorySerializer,
)
from apps.accounts.permissions import IsSuperAdmin, IsAdminLiga, IsAdminClub, IsOwnerOrAdmin


class PlayerViewSet(viewsets.ModelViewSet):
    queryset = Player.objects.select_related("country").all()
    filterset_fields = ["country", "platform", "is_active"]
    search_fields = ["nickname"]
    ordering_fields = ["nickname", "created_at"]
    tags = ["Players"]
    tags = ["Players"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        if self.action in ["update", "partial_update"]:
            return [IsSuperAdmin()]
        return [IsSuperAdmin()]

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
    tags = ["Players"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [IsSuperAdmin()]

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
    tags = ["Players"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [IsSuperAdmin()]
