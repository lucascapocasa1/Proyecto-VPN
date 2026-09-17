from rest_framework import viewsets, permissions
from .models import Club, ClubSeason, ClubTitle
from .serializers import ClubSerializer, ClubSeasonSerializer, ClubTitleSerializer, ClubDetailSerializer


class ClubViewSet(viewsets.ModelViewSet):
    queryset = Club.objects.select_related("country").all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ClubDetailSerializer
        return ClubSerializer


class ClubSeasonViewSet(viewsets.ModelViewSet):
    queryset = ClubSeason.objects.select_related("club", "season", "division").all()
    serializer_class = ClubSeasonSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class ClubTitleViewSet(viewsets.ModelViewSet):
    queryset = ClubTitle.objects.select_related("club", "season", "division", "awarded_by").all()
    serializer_class = ClubTitleSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
