from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Country, Game, CompetitionFormat, League, Season, Division
from .serializers import (
    CountrySerializer, GameSerializer, CompetitionFormatSerializer,
    LeagueSerializer, SeasonSerializer, SeasonListSerializer, DivisionSerializer,
)
from apps.accounts.permissions import IsSuperAdmin, IsAdminLiga


class CountryViewSet(viewsets.ModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    filterset_fields = ["code"]
    search_fields = ["name", "code"]
    ordering_fields = ["name", "code"]
    tags = ["Countries"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [IsSuperAdmin()]


class GameViewSet(viewsets.ModelViewSet):
    queryset = Game.objects.all()
    serializer_class = GameSerializer
    filterset_fields = ["year"]
    search_fields = ["name"]
    ordering_fields = ["name", "year"]
    tags = ["Games"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [IsSuperAdmin()]


class CompetitionFormatViewSet(viewsets.ModelViewSet):
    queryset = CompetitionFormat.objects.all()
    serializer_class = CompetitionFormatSerializer
    search_fields = ["name"]
    ordering_fields = ["name"]
    tags = ["Games"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [IsSuperAdmin()]


class LeagueViewSet(viewsets.ModelViewSet):
    queryset = League.objects.select_related("country").all()
    serializer_class = LeagueSerializer
    filterset_fields = ["country"]
    search_fields = ["name"]
    ordering_fields = ["name"]
    tags = ["Leagues"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [IsAdminLiga()]


class SeasonViewSet(viewsets.ModelViewSet):
    queryset = Season.objects.select_related(
        "league", "game", "format"
    ).prefetch_related("divisions").all()

    filterset_fields = ["league", "game", "status"]
    search_fields = ["name"]
    ordering_fields = ["name", "number", "status"]
    tags = ["Seasons"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [IsAdminLiga()]

    def get_serializer_class(self):
        if self.action == "list":
            return SeasonListSerializer
        return SeasonSerializer


class DivisionViewSet(viewsets.ModelViewSet):
    queryset = Division.objects.select_related("season").all()
    serializer_class = DivisionSerializer
    filterset_fields = ["season", "order"]
    search_fields = ["name"]
    ordering_fields = ["name", "order"]
    tags = ["Seasons"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [IsAdminLiga()]
