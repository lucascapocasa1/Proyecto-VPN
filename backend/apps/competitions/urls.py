from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CountryViewSet, GameViewSet, CompetitionFormatViewSet,
    LeagueViewSet, SeasonViewSet, DivisionViewSet,
)

router = DefaultRouter()
router.register("countries", CountryViewSet, basename="countries")
router.register("games", GameViewSet, basename="games")
router.register("formats", CompetitionFormatViewSet, basename="formats")
router.register("leagues", LeagueViewSet, basename="leagues")
router.register("seasons", SeasonViewSet, basename="seasons")
router.register("divisions", DivisionViewSet, basename="divisions")

urlpatterns = [
    path("", include(router.urls)),
]
