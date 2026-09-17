from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, LeagueAdmin, ClubAdmin


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["username", "email", "role", "is_active", "created_at"]
    list_filter = ["role", "is_active", "created_at"]
    search_fields = ["username", "email"]
    ordering = ["-created_at"]

    fieldsets = BaseUserAdmin.fieldsets + (
        ("Rol y Permisos", {"fields": ("role",)}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Rol y Permisos", {"fields": ("role",)}),
    )


@admin.register(LeagueAdmin)
class LeagueAdminAdmin(admin.ModelAdmin):
    list_display = ["user", "league", "created_at"]
    list_filter = ["league", "created_at"]
    search_fields = ["user__username", "league__name"]
    raw_id_fields = ["user", "league"]


@admin.register(ClubAdmin)
class ClubAdminAdmin(admin.ModelAdmin):
    list_display = ["user", "club", "created_at"]
    list_filter = ["club", "created_at"]
    search_fields = ["user__username", "club__name"]
    raw_id_fields = ["user", "club"]
