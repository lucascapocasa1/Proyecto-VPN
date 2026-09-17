from rest_framework import viewsets, permissions
from .models import Player, PlayerIdentityHistory, PlayerClubHistory
from .serializers import (
    PlayerSerializer, PlayerDetailSerializer,
    PlayerIdentityHistorySerializer, PlayerClubHistorySerializer,
)
from apps.accounts.permissions import IsSuperAdmin, IsAdminLiga, IsAdminClub, IsOwnerOrAdmin


class PlayerViewSet(viewsets.ModelViewSet):
    queryset = Player.objects.select_related("country").all()

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
    queryset = PlayerIdentityHistory.objects.select_related("player", "changed_by").all()
    serializer_class = PlayerIdentityHistorySerializer

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

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [IsSuperAdmin()]
