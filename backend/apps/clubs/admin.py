from django.contrib import admin
from .models import Club, ClubSeason, ClubTitle


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ["name", "short_name", "country", "is_active", "founded_date"]
    list_filter = ["country", "is_active"]
    search_fields = ["name", "short_name"]


@admin.register(ClubSeason)
class ClubSeasonAdmin(admin.ModelAdmin):
    list_display = ["club", "season", "division", "status"]
    list_filter = ["status", "season", "division"]
    search_fields = ["club__name", "season__name"]
    raw_id_fields = ["club", "season", "division"]


@admin.register(ClubTitle)
class ClubTitleAdmin(admin.ModelAdmin):
    list_display = ["name", "club", "season", "division", "title_type", "awarded_at", "awarded_by"]
    list_filter = ["title_type", "season"]
    search_fields = ["name", "club__name"]
    raw_id_fields = ["club", "season", "division", "awarded_by"]
