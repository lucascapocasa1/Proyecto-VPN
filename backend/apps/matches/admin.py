from django.contrib import admin
from .models import Matchday, Match, MatchPlayer, MatchEvent, MatchPerformance


@admin.register(Matchday)
class MatchdayAdmin(admin.ModelAdmin):
    list_display = ["name", "season", "division", "number", "date"]
    list_filter = ["season", "division"]
    search_fields = ["name"]


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = [
        "home_club_season", "away_club_season",
        "home_goals", "away_goals",
        "status", "date", "division",
    ]
    list_filter = ["status", "season", "division"]
    search_fields = [
        "home_club_season__club__name",
        "away_club_season__club__name",
    ]
    raw_id_fields = [
        "season", "division", "matchday",
        "home_club_season", "away_club_season",
    ]


class MatchEventInline(admin.TabularInline):
    model = MatchEvent
    extra = 0
    fields = ["match_player", "event_type", "minute"]


@admin.register(MatchPlayer)
class MatchPlayerAdmin(admin.ModelAdmin):
    list_display = ["display_name", "match", "club_season", "player", "is_starter"]
    list_filter = ["club_season__season"]
    search_fields = ["display_name", "player__nickname"]
    raw_id_fields = ["match", "player", "club_season"]
    inlines = [MatchEventInline]


@admin.register(MatchEvent)
class MatchEventAdmin(admin.ModelAdmin):
    list_display = ["event_type", "match_player", "match", "minute"]
    list_filter = ["event_type", "match__status"]
    search_fields = ["match_player__display_name"]
    raw_id_fields = ["match", "match_player"]


@admin.register(MatchPerformance)
class MatchPerformanceAdmin(admin.ModelAdmin):
    list_display = [
        "match_player", "rating", "goals", "assists",
        "minutes_played", "distance_km",
    ]
    list_filter = ["match_player__match__status"]
    search_fields = ["match_player__display_name", "match_player__player__nickname"]
    raw_id_fields = ["match_player"]
