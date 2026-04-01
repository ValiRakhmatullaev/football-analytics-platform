"""Video annotation API endpoints."""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status as http_status
from django.http import FileResponse, Http404
from django.conf import settings
from pathlib import Path
import json

from apps.analytics.models import VideoUpload, VideoClip


class VideoAnnotationDataAPIView(APIView):
    """Return annotation data for a video (video meta + events + clips)."""

    def get(self, request, video_id):
        try:
            video = VideoUpload.objects.get(id=video_id)
        except VideoUpload.DoesNotExist:
            return Response({'error': 'Video not found'}, status=http_status.HTTP_404_NOT_FOUND)

        media_root = Path(settings.MEDIA_ROOT)

        # Video metadata
        video_meta = {
            'source_url': f'/api/analytics/videos/{video_id}/source/',
            'duration_seconds': video.duration_seconds or 0,
            'width': video.width or 1920,
            'height': video.height or 1080,
            'file_name': video.file_name,
        }

        # Load raw events from JSON
        raw_events = []
        if video.json_output_path:
            json_path = media_root / video.json_output_path
            if json_path.exists():
                with open(json_path, 'r') as f:
                    events_data = json.load(f)
                for e in events_data:
                    raw_events.append({
                        'event_type': e.get('event_type', 'unknown'),
                        'timestamp_ms': e.get('timestamp_ms', 0),
                        'x': round((e.get('ball_x', 0) / (video.width or 1920)) * 100, 2) if e.get('ball_x') else None,
                        'y': round((e.get('ball_y', 0) / (video.height or 1080)) * 100, 2) if e.get('ball_y') else None,
                        'confidence': e.get('confidence', 0),
                    })

        # Clips
        clips_data = []
        for clip in video.clips.all():
            clips_data.append({
                'id': str(clip.id),
                'clip_type': clip.clip_type,
                'title': clip.title,
                'description': clip.description or '',
                'start_time_seconds': clip.start_time_seconds,
                'end_time_seconds': clip.end_time_seconds,
                'timestamp_ms': clip.timestamp_ms,
                'duration_seconds': clip.duration_seconds,
                'confidence': clip.confidence,
            })

        return Response({
            'video': video_meta,
            'events': raw_events,
            'clips': clips_data,
            'overlays': [],
        })


class VideoSourceAPIView(APIView):
    """Serve the original source video file."""

    def get(self, request, video_id):
        try:
            video = VideoUpload.objects.get(id=video_id)
        except VideoUpload.DoesNotExist:
            raise Http404("Video not found")

        media_root = Path(settings.MEDIA_ROOT)
        video_path = media_root / video.file_path

        if not video_path.exists():
            raise Http404("Video file not found")

        response = FileResponse(open(video_path, 'rb'), content_type='video/mp4')
        response['Content-Disposition'] = f'inline; filename="{video.file_name}"'
        return response


class VideoExportAnnotationsAPIView(APIView):
    """Export annotations as JSON."""

    def get(self, request, video_id):
        try:
            video = VideoUpload.objects.get(id=video_id)
        except VideoUpload.DoesNotExist:
            return Response({'error': 'Video not found'}, status=http_status.HTTP_404_NOT_FOUND)

        clips_data = []
        for clip in video.clips.all():
            clips_data.append({
                'id': str(clip.id),
                'clip_type': clip.clip_type,
                'title': clip.title,
                'description': clip.description or '',
                'start_time_seconds': clip.start_time_seconds,
                'end_time_seconds': clip.end_time_seconds,
                'timestamp_ms': clip.timestamp_ms,
                'confidence': clip.confidence,
            })

        return Response({
            'video_id': str(video_id),
            'file_name': video.file_name,
            'clips': clips_data,
        })


class VideoOverlaysAPIView(APIView):
    """Save/load overlays (arrows, circles, etc.) for a video."""

    def get(self, request, video_id):
        return Response({'overlays': []})

    def post(self, request, video_id):
        overlays = request.data.get('overlays', [])
        return Response({'overlays': overlays})


class ClipUpdateAPIView(APIView):
    """Update a clip's trim or description."""

    def patch(self, request, clip_id):
        try:
            clip = VideoClip.objects.get(id=clip_id)
        except VideoClip.DoesNotExist:
            return Response({'error': 'Clip not found'}, status=http_status.HTTP_404_NOT_FOUND)

        if 'start_time_seconds' in request.data:
            clip.start_time_seconds = request.data['start_time_seconds']
        if 'end_time_seconds' in request.data:
            clip.end_time_seconds = request.data['end_time_seconds']
        if 'description' in request.data:
            clip.description = request.data['description']

        clip.duration_seconds = clip.end_time_seconds - clip.start_time_seconds
        clip.save()

        return Response({
            'start_time_seconds': clip.start_time_seconds,
            'end_time_seconds': clip.end_time_seconds,
            'duration_seconds': clip.duration_seconds,
            'description': clip.description,
        })
