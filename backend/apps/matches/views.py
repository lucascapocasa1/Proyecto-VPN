from django.core.cache import cache
from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Matchday, Match, MatchPlayer, MatchEvent
from .serializers import (
    MatchdaySerializer, MatchSerializer, MatchDetailSerializer,
    MatchPlayerSerializer, MatchEventSerializer,
)
from apps.accounts.permissions import IsSuperAdmin, IsAdminLiga, CanManageLeague
from apps.standings.services import recalculate_standings


def _refresh_derived(match):
    recalculate_standings(match.season, match.division)
    cache.clear()


class MatchdayViewSet(viewsets.ModelViewSet):
    queryset = Matchday.objects.select_related("season", "division").all()
    serializer_class = MatchdaySerializer
    filterset_fields = ["season", "division"]
    ordering_fields = ["number", "date"]
    tags = ["Matches"]
    tags = ["Matches"]

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
    tags = ["Matches"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [IsAdminLiga()]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return MatchDetailSerializer
        return MatchSerializer

    def perform_create(self, serializer):
        match = serializer.save()
        _refresh_derived(match)

    def perform_update(self, serializer):
        match = serializer.save()
        _refresh_derived(match)

    def perform_destroy(self, instance):
        match = instance
        super().perform_destroy(instance)
        _refresh_derived(match)


class MatchPlayerViewSet(viewsets.ModelViewSet):
    queryset = MatchPlayer.objects.select_related(
        "match", "player", "club_season__club"
    ).all()
    serializer_class = MatchPlayerSerializer
    filterset_fields = ["match", "player", "club_season"]
    tags = ["Matches"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [IsAdminLiga()]

    def perform_create(self, serializer):
        serializer.save()
        cache.clear()

    def perform_update(self, serializer):
        serializer.save()
        cache.clear()

    def perform_destroy(self, instance):
        super().perform_destroy(instance)
        cache.clear()


class MatchEventViewSet(viewsets.ModelViewSet):
    queryset = MatchEvent.objects.select_related(
        "match", "match_player__player", "match_player__club_season__club"
    ).all()
    serializer_class = MatchEventSerializer
    filterset_fields = ["match", "match_player", "event_type"]
    ordering_fields = ["minute"]
    tags = ["Matches"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [IsAdminLiga()]

    def perform_create(self, serializer):
        serializer.save()
        cache.clear()

    def perform_update(self, serializer):
        serializer.save()
        cache.clear()

    def perform_destroy(self, instance):
        super().perform_destroy(instance)
        cache.clear()
