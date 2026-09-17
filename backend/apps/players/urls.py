from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PlayerViewSet, PlayerIdentityHistoryViewSet, PlayerClubHistoryViewSet

router = DefaultRouter()
router.register("players", PlayerViewSet, basename="players")
router.register("player-identity-history", PlayerIdentityHistoryViewSet, basename="player-identity-history")
router.register("player-club-history", PlayerClubHistoryViewSet, basename="player-club-history")

urlpatterns = [
    path("", include(router.urls)),
]
