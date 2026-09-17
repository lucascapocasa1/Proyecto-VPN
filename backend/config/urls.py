from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("apps.accounts.urls")),
    path("api/", include("apps.competitions.urls")),
    path("api/", include("apps.clubs.urls")),
    path("api/", include("apps.players.urls")),
    path("api/", include("apps.matches.urls")),
    path("api/", include("apps.standings.urls")),
    path("api/", include("apps.statistics.urls")),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
