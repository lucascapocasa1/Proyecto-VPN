from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StandingViewSet

router = DefaultRouter()
router.register("standings", StandingViewSet, basename="standings")

urlpatterns = [
    path("", include(router.urls)),
]
