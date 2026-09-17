from rest_framework import viewsets, permissions
from .models import Country, Game, CompetitionFormat, League, Season, Division
from .serializers import (
    CountrySerializer, GameSerializer, CompetitionFormatSerializer,
    LeagueSerializer, SeasonSerializer, SeasonListSerializer, DivisionSerializer,
)
from apps.accounts.permissions import IsSuperAdmin, IsAdminLiga


class CountryViewSet(viewsets.ModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [IsSuperAdmin()]


class GameViewSet(viewsets.ModelViewSet):
    queryset = Game.objects.all()
    serializer_class = GameSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [IsSuperAdmin()]


class CompetitionFormatViewSet(viewsets.ModelViewSet):
    queryset = CompetitionFormat.objects.all()
    serializer_class = CompetitionFormatSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [IsSuperAdmin()]


class LeagueViewSet(viewsets.ModelViewSet):
    queryset = League.objects.select_related("country").all()
    serializer_class = LeagueSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [IsAdminLiga()]


class SeasonViewSet(viewsets.ModelViewSet):
    queryset = Season.objects.select_related("league", "game", "format").prefetch_related("divisions").all()

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

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [IsAdminLiga()]
