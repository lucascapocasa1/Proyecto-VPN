from rest_framework import viewsets, permissions
from .models import Club, ClubSeason, ClubTitle
from .serializers import ClubSerializer, ClubSeasonSerializer, ClubTitleSerializer, ClubDetailSerializer
from apps.accounts.permissions import IsSuperAdmin, IsAdminLiga, IsAdminClub, CanManageClub


class ClubViewSet(viewsets.ModelViewSet):
    queryset = Club.objects.select_related("country").all()

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [CanManageClub()]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ClubDetailSerializer
        return ClubSerializer


class ClubSeasonViewSet(viewsets.ModelViewSet):
    queryset = ClubSeason.objects.select_related("club", "season", "division").all()
    serializer_class = ClubSeasonSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [IsAdminLiga()]


class ClubTitleViewSet(viewsets.ModelViewSet):
    queryset = ClubTitle.objects.select_related("club", "season", "division", "awarded_by").all()
    serializer_class = ClubTitleSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [IsAdminLiga()]
