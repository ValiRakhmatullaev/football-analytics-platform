from django.urls import path
from apps.analytics.api.player_profile import PlayerMatchProfileAPIView

from apps.analytics.api.match_overview import MatchOverviewAPIView

urlpatterns = [
    path(
        "matches/<uuid:match_id>/overview/",
        MatchOverviewAPIView.as_view(),
        name="match-overview",
    ),
    path(
        "matches/<uuid:match_id>/players/<uuid:player_id>/profile/",
        PlayerMatchProfileAPIView.as_view(),
        name="player-match-profile",
    ),
]
