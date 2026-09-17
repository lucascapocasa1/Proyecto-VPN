from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClubViewSet, ClubSeasonViewSet, ClubTitleViewSet

router = DefaultRouter()
router.register("clubs", ClubViewSet, basename="clubs")
router.register("club-seasons", ClubSeasonViewSet, basename="club-seasons")
router.register("club-titles", ClubTitleViewSet, basename="club-titles")

urlpatterns = [
    path("", include(router.urls)),
]
