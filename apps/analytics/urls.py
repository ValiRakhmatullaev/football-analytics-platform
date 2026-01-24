from django.urls import path

from apps.analytics.api.match_list import MatchListAPIView
from apps.analytics.api.match_overview import MatchOverviewAPIView
from apps.analytics.api.player_profile import PlayerMatchProfileAPIView
from apps.analytics.views import CoachSummaryView

urlpatterns = [
    path(
        "matches/",
        MatchListAPIView.as_view(),
        name="match-list",
    ),
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
    path(
        "coach-summary/",
        CoachSummaryView.as_view(),
        name="coach-summary",
    ),
]
