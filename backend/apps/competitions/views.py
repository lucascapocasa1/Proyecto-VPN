from rest_framework import viewsets, permissions
from .models import Country, Game, CompetitionFormat, League, Season, Division
from .serializers import (
    CountrySerializer, GameSerializer, CompetitionFormatSerializer,
    LeagueSerializer, SeasonSerializer, SeasonListSerializer, DivisionSerializer,
)


class CountryViewSet(viewsets.ModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class GameViewSet(viewsets.ModelViewSet):
    queryset = Game.objects.all()
    serializer_class = GameSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class CompetitionFormatViewSet(viewsets.ModelViewSet):
    queryset = CompetitionFormat.objects.all()
    serializer_class = CompetitionFormatSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class LeagueViewSet(viewsets.ModelViewSet):
    queryset = League.objects.select_related("country").all()
    serializer_class = LeagueSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class SeasonViewSet(viewsets.ModelViewSet):
    queryset = Season.objects.select_related("league", "game", "format").prefetch_related("divisions").all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.action == "list":
            return SeasonListSerializer
        return SeasonSerializer


class DivisionViewSet(viewsets.ModelViewSet):
    queryset = Division.objects.select_related("season").all()
    serializer_class = DivisionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
