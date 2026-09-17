from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuthViewSet, UserViewSet, LeagueAdminViewSet, ClubAdminViewSet

router = DefaultRouter()
router.register("auth", AuthViewSet, basename="auth")
router.register("users", UserViewSet, basename="users")
router.register("league-admins", LeagueAdminViewSet, basename="league-admins")
router.register("club-admins", ClubAdminViewSet, basename="club-admins")

urlpatterns = [
    path("", include(router.urls)),
]
