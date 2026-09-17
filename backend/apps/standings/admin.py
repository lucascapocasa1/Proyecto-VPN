from django.contrib import admin
from .models import Standing
from .zones import get_zone, get_zone_display


@admin.register(Standing)
class StandingAdmin(admin.ModelAdmin):
    list_display = [
        "position", "club_name", "season", "division",
        "played", "won", "drawn", "lost",
        "goals_for", "goals_against", "goal_difference", "points",
        "zone_display",
    ]
    list_filter = ["season", "division"]
    search_fields = ["club_season__club__name"]
    raw_id_fields = ["season", "division", "club_season"]
    ordering = ["season", "division", "position"]
    list_select_related = ["club_season__club", "season", "division"]

    def club_name(self, obj):
        return obj.club_season.club.name
    club_name.short_description = "Club"

    def zone_display(self, obj):
        zone = get_zone(obj)
        return get_zone_display(zone)
    zone_display.short_description = "Zona"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
