from django.urls import path, include
from django.http import JsonResponse
from django.db import connection
from rest_framework.routers import DefaultRouter
from .views import AuthViewSet, UserViewSet, LeagueAdminViewSet, ClubAdminViewSet


def health_check(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        db_status = "ok"
    except Exception:
        db_status = "error"

    status = "ok" if db_status == "ok" else "degraded"
    return JsonResponse({"status": status, "db": db_status})


router = DefaultRouter()
router.register("auth", AuthViewSet, basename="auth")
router.register("users", UserViewSet, basename="users")
router.register("league-admins", LeagueAdminViewSet, basename="league-admins")
router.register("club-admins", ClubAdminViewSet, basename="club-admins")

urlpatterns = [
    path("health/", health_check, name="health_check"),
    path("", include(router.urls)),
]
