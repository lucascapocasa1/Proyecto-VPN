from django.contrib import admin
from .models import Player, PlayerIdentityHistory, PlayerClubHistory


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ["nickname", "platform", "country", "user", "is_active", "created_at"]
    list_filter = ["platform", "country", "is_active"]
    search_fields = ["nickname"]
    raw_id_fields = ["user", "country"]


@admin.register(PlayerIdentityHistory)
class PlayerIdentityHistoryAdmin(admin.ModelAdmin):
    list_display = ["player", "nickname", "changed_at", "changed_by"]
    list_filter = ["changed_at"]
    search_fields = ["player__nickname", "nickname"]
    raw_id_fields = ["player", "changed_by"]


@admin.register(PlayerClubHistory)
class PlayerClubHistoryAdmin(admin.ModelAdmin):
    list_display = ["player", "club_season", "joined_at", "left_at", "is_current"]
    list_filter = ["club_season__season"]
    search_fields = ["player__nickname", "club_season__club__name"]
    raw_id_fields = ["player", "club_season"]
