from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Matchday, Match, MatchPlayer, MatchEvent
from .serializers import (
    MatchdaySerializer, MatchSerializer, MatchDetailSerializer,
    MatchPlayerSerializer, MatchEventSerializer,
)
from apps.accounts.permissions import IsSuperAdmin, IsAdminLiga, CanManageLeague


class MatchdayViewSet(viewsets.ModelViewSet):
    queryset = Matchday.objects.select_related("season", "division").all()
    serializer_class = MatchdaySerializer
    filterset_fields = ["season", "division"]
    ordering_fields = ["number", "date"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [IsAdminLiga()]


class MatchViewSet(viewsets.ModelViewSet):
    queryset = Match.objects.select_related(
        "season", "division", "matchday",
        "home_club_season__club", "away_club_season__club",
    ).all()
    filterset_fields = ["season", "division", "matchday", "status"]
    search_fields = ["home_club_season__club__name", "away_club_season__club__name"]
    ordering_fields = ["date", "status", "created_at"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [IsAdminLiga()]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return MatchDetailSerializer
        return MatchSerializer


class MatchPlayerViewSet(viewsets.ModelViewSet):
    queryset = MatchPlayer.objects.select_related(
        "match", "player", "club_season__club"
    ).all()
    serializer_class = MatchPlayerSerializer
    filterset_fields = ["match", "player", "club_season"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [IsAdminLiga()]


class MatchEventViewSet(viewsets.ModelViewSet):
    queryset = MatchEvent.objects.select_related(
        "match", "match_player__player", "match_player__club_season__club"
    ).all()
    serializer_class = MatchEventSerializer
    filterset_fields = ["match", "match_player", "event_type"]
    ordering_fields = ["minute"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [IsAdminLiga()]
