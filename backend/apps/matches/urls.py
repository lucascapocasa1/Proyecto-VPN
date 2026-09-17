from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MatchdayViewSet, MatchViewSet, MatchPlayerViewSet, MatchEventViewSet

router = DefaultRouter()
router.register("matchdays", MatchdayViewSet, basename="matchdays")
router.register("matches", MatchViewSet, basename="matches")
router.register("match-players", MatchPlayerViewSet, basename="match-players")
router.register("match-events", MatchEventViewSet, basename="match-events")

urlpatterns = [
    path("", include(router.urls)),
]
