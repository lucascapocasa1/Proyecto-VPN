from rest_framework import viewsets, permissions
from .models import Matchday, Match, MatchPlayer, MatchEvent
from .serializers import (
    MatchdaySerializer, MatchSerializer, MatchDetailSerializer,
    MatchPlayerSerializer, MatchEventSerializer,
)


class MatchdayViewSet(viewsets.ModelViewSet):
    queryset = Matchday.objects.select_related("season", "division").all()
    serializer_class = MatchdaySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class MatchViewSet(viewsets.ModelViewSet):
    queryset = Match.objects.select_related(
        "season", "division", "matchday",
        "home_club_season__club", "away_club_season__club",
    ).all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return MatchDetailSerializer
        return MatchSerializer


class MatchPlayerViewSet(viewsets.ModelViewSet):
    queryset = MatchPlayer.objects.select_related(
        "match", "player", "club_season__club"
    ).all()
    serializer_class = MatchPlayerSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class MatchEventViewSet(viewsets.ModelViewSet):
    queryset = MatchEvent.objects.select_related(
        "match", "match_player__player", "match_player__club_season__club"
    ).all()
    serializer_class = MatchEventSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
