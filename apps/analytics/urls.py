from django.urls import path

from apps.analytics.api.match_list import MatchListAPIView
from apps.analytics.api.match_overview import MatchOverviewAPIView
from apps.analytics.api.player_profile import PlayerMatchProfileAPIView
from apps.analytics.api.video_upload import (
    VideoUploadAPIView,
    VideoProcessAPIView,
    VideoStatusAPIView,
)
from apps.analytics.api.video_json import VideoJSONDownloadAPIView
from apps.analytics.api.video_info import VideoInfoAPIView, VideoListAPIView
from apps.analytics.api.video_match import VideoCreateMatchAPIView
from apps.analytics.api.video_clips import (
    VideoClipsListAPIView,
    VideoClipVideoAPIView,
    VideoClipThumbnailAPIView,
    VideoClipsByTypeAPIView,
)
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
    # Video upload endpoints
    path(
        "videos/upload/",
        VideoUploadAPIView.as_view(),
        name="video-upload",
    ),
    path(
        "videos/<uuid:video_id>/process/",
        VideoProcessAPIView.as_view(),
        name="video-process",
    ),
    path(
        "videos/<uuid:video_id>/status/",
        VideoStatusAPIView.as_view(),
        name="video-status",
    ),
    path(
        "videos/<uuid:video_id>/json/",
        VideoJSONDownloadAPIView.as_view(),
        name="video-json-download",
    ),
    path(
        "videos/",
        VideoListAPIView.as_view(),
        name="video-list",
    ),
    path(
        "videos/<uuid:video_id>/info/",
        VideoInfoAPIView.as_view(),
        name="video-info",
    ),
    path(
        "videos/<uuid:video_id>/create-match/",
        VideoCreateMatchAPIView.as_view(),
        name="video-create-match",
    ),
    # Video clips endpoints
    path(
        "videos/<uuid:video_id>/clips/",
        VideoClipsListAPIView.as_view(),
        name="video-clips-list",
    ),
    path(
        "clips/<uuid:clip_id>/video/",
        VideoClipVideoAPIView.as_view(),
        name="clip-video",
    ),
    path(
        "clips/<uuid:clip_id>/thumbnail/",
        VideoClipThumbnailAPIView.as_view(),
        name="clip-thumbnail",
    ),
]
