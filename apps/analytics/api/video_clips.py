"""Video clips API."""
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import FileResponse, Http404
from django.conf import settings
from pathlib import Path

from apps.analytics.models import VideoUpload, VideoClip


class VideoClipsListAPIView(APIView):
    """List video clips for a video."""
    
    def get(self, request, video_id):
        try:
            video_upload = VideoUpload.objects.get(id=video_id)
        except VideoUpload.DoesNotExist:
            return Response({'error': 'Video not found'}, status=404)
        
        # Get filter by type if provided
        clip_type = request.GET.get('type')
        
        clips = video_upload.clips.all()
        if clip_type and clip_type != 'all':
            clips = clips.filter(clip_type=clip_type)
        
        clips_data = []
        for clip in clips:
            clips_data.append({
                'id': str(clip.id),
                'clip_type': clip.clip_type,
                'title': clip.title,
                'description': clip.description,
                'duration_seconds': clip.duration_seconds,
                'timestamp_ms': clip.timestamp_ms,
                'confidence': clip.confidence,
                'video_url': f'/media/{clip.file_path}',
                'thumbnail_url': f'/media/{clip.thumbnail_path}' if clip.thumbnail_path else None,
            })
        
        return Response(clips_data)


class VideoClipVideoAPIView(APIView):
    """Serve clip video file."""
    
    def get(self, request, clip_id):
        try:
            clip = VideoClip.objects.get(id=clip_id)
        except VideoClip.DoesNotExist:
            raise Http404("Clip not found")
        
        media_root = Path(settings.MEDIA_ROOT)
        clip_path = media_root / clip.file_path
        
        if not clip_path.exists():
            raise Http404("Clip file not found")
        
        return FileResponse(open(clip_path, 'rb'), content_type='video/mp4')


class VideoClipThumbnailAPIView(APIView):
    """Serve clip thumbnail."""
    
    def get(self, request, clip_id):
        try:
            clip = VideoClip.objects.get(id=clip_id)
        except VideoClip.DoesNotExist:
            raise Http404("Clip not found")
        
        if not clip.thumbnail_path:
            raise Http404("Thumbnail not available")
        
        media_root = Path(settings.MEDIA_ROOT)
        thumb_path = media_root / clip.thumbnail_path
        
        if not thumb_path.exists():
            raise Http404("Thumbnail file not found")
        
        return FileResponse(open(thumb_path, 'rb'), content_type='image/jpeg')


class VideoClipsByTypeAPIView(APIView):
    """List clips by type."""
    
    def get(self, request, video_id):
        # Same as VideoClipsListAPIView but with type filter
        return VideoClipsListAPIView().get(request, video_id)
