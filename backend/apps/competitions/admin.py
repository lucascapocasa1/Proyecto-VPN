from django.contrib import admin
from .models import Country, Game, CompetitionFormat, League, Season, Division


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ["name", "code"]
    search_fields = ["name", "code"]


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ["name", "year"]
    ordering = ["-year"]


@admin.register(CompetitionFormat)
class CompetitionFormatAdmin(admin.ModelAdmin):
    list_display = ["name", "format_type", "has_playoffs"]
    list_filter = ["format_type", "has_playoffs"]


@admin.register(League)
class LeagueAdmin(admin.ModelAdmin):
    list_display = ["name", "country"]
    list_filter = ["country"]
    search_fields = ["name"]


class DivisionInline(admin.TabularInline):
    model = Division
    extra = 0
    fields = ["name", "order", "max_clubs", "has_relegation"]


@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ["name", "league", "game", "status", "number"]
    list_filter = ["status", "league", "game"]
    search_fields = ["name", "league__name"]
    inlines = [DivisionInline]


@admin.register(Division)
class DivisionAdmin(admin.ModelAdmin):
    list_display = [
        "name", "season", "order", "max_clubs",
        "playoff_zone_start", "playoff_zone_end",
        "promotion_zone_start", "promotion_zone_end",
        "relegation_zone_start", "relegation_zone_end",
        "has_relegation",
    ]
    list_filter = ["season", "has_relegation"]
    search_fields = ["name"]
