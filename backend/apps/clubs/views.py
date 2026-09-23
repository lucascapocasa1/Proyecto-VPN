from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Club, ClubSeason, ClubTitle
from .serializers import ClubSerializer, ClubSeasonSerializer, ClubTitleSerializer, ClubDetailSerializer
from apps.accounts.permissions import IsSuperAdmin, IsAdminLiga, IsAdminClub, CanManageClub


class ClubViewSet(viewsets.ModelViewSet):
    queryset = Club.objects.select_related("country").all()
    filterset_fields = ["country", "is_active"]
    search_fields = ["name", "short_name"]
    ordering_fields = ["name", "created_at"]
    tags = ["Clubs"]
    tags = ["Clubs"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [CanManageClub()]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ClubDetailSerializer
        return ClubSerializer


class ClubSeasonViewSet(viewsets.ModelViewSet):
    queryset = ClubSeason.objects.select_related(
        "club", "season", "division"
    ).all()
    filterset_fields = ["club", "season", "division", "status"]
    ordering_fields = ["created_at"]
    tags = ["Clubs"]
    tags = ["Clubs"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [IsAdminLiga()]


class ClubTitleViewSet(viewsets.ModelViewSet):
    queryset = ClubTitle.objects.select_related(
        "club", "season", "division", "awarded_by"
    ).all()
    serializer_class = ClubTitleSerializer
    filterset_fields = ["club", "season", "division", "title_type"]
    search_fields = ["name"]
    ordering_fields = ["awarded_at", "name"]
    tags = ["Clubs"]
    tags = ["Clubs"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [IsAdminLiga()]

    def perform_create(self, serializer):
        serializer.save(awarded_by=self.request.user)
