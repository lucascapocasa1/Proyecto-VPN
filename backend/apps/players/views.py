from rest_framework import viewsets, permissions
from .models import Player, PlayerIdentityHistory, PlayerClubHistory
from .serializers import (
    PlayerSerializer, PlayerDetailSerializer,
    PlayerIdentityHistorySerializer, PlayerClubHistorySerializer,
)


class PlayerViewSet(viewsets.ModelViewSet):
    queryset = Player.objects.select_related("country").all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return PlayerDetailSerializer
        return PlayerSerializer


class PlayerIdentityHistoryViewSet(viewsets.ModelViewSet):
    queryset = PlayerIdentityHistory.objects.select_related("player", "changed_by").all()
    serializer_class = PlayerIdentityHistorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class PlayerClubHistoryViewSet(viewsets.ModelViewSet):
    queryset = PlayerClubHistory.objects.select_related(
        "player", "club_season__club", "club_season__season", "club_season__division"
    ).all()
    serializer_class = PlayerClubHistorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
