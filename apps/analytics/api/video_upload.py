"""Video upload and processing API endpoints."""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status as http_status
from django.core.files.storage import default_storage
from django.conf import settings
from django.utils import timezone
import uuid
import os
import sys
import subprocess
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from apps.analytics.models import VideoUpload, VideoClip
from apps.competitions.models import Match, MatchTeam
from apps.teams.models import Team
from apps.events.models import Event


class VideoUploadAPIView(APIView):
    """Upload a video file."""
    
    def post(self, request):
        video_file = request.FILES.get('video')
        if not video_file:
            return Response({'error': 'No video file provided'}, status=http_status.HTTP_400_BAD_REQUEST)
        
        # Save file to media/videos/
        media_root = Path(settings.MEDIA_ROOT)
        videos_dir = media_root / 'videos'
        videos_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        video_id = uuid.uuid4()
        file_ext = Path(video_file.name).suffix
        filename = f"{video_id}{file_ext}"
        file_path = videos_dir / filename
        
        # Save file
        with open(file_path, 'wb+') as destination:
            for chunk in video_file.chunks():
                destination.write(chunk)
        
        # Get video metadata using OpenCV
        try:
            import cv2
            cap = cv2.VideoCapture(str(file_path))
            if cap.isOpened():
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                duration = total_frames / fps if fps > 0 else 0
                cap.release()
            else:
                duration = width = height = fps = None
        except Exception:
            duration = width = height = fps = None
        
        # Create VideoUpload record
        video_upload = VideoUpload.objects.create(
            id=video_id,
            file_name=video_file.name,
            file_path=str(file_path.relative_to(media_root)),
            file_size=video_file.size,
            duration_seconds=duration,
            width=width,
            height=height,
            fps=fps,
            status=VideoUpload.Status.UPLOADED,
        )
        
        # Create match if requested
        match_id = None
        if request.POST.get('create_match') == 'true':
            team1_name = request.POST.get('team1_name', 'Team 1')
            team2_name = request.POST.get('team2_name', 'Team 2')
            
            # Create teams
            team1, _ = Team.objects.get_or_create(name=team1_name)
            team2, _ = Team.objects.get_or_create(name=team2_name)
            
            # Create match
            match = Match.objects.create(
                kickoff_time=timezone.now(),
            )
            MatchTeam.objects.create(match=match, team=team1, side='home')
            MatchTeam.objects.create(match=match, team=team2, side='away')
            
            video_upload.match = match
            video_upload.period = int(request.POST.get('period', 1))
            video_upload.save()
            match_id = str(match.id)
        
        return Response({
            'id': str(video_upload.id),
            'file_name': video_upload.file_name,
            'status': video_upload.status,
            'file_size': video_upload.file_size,
            'uploaded_at': video_upload.uploaded_at.isoformat() if video_upload.uploaded_at else None,
            'match_id': match_id,
            'duration_seconds': duration,
        }, status=http_status.HTTP_201_CREATED)


class VideoProcessAPIView(APIView):
    """Process a video to detect events and create clips."""
    
    def post(self, request, video_id):
        try:
            video_upload = VideoUpload.objects.get(id=video_id)
        except VideoUpload.DoesNotExist:
            return Response({'error': 'Video not found'}, status=http_status.HTTP_404_NOT_FOUND)
        
        video_upload.status = VideoUpload.Status.PROCESSING
        video_upload.save()
        
        try:
            # Run AI pipeline
            from video_analytics.pipeline_advanced import VideoAnalyticsPipelineAdvanced
            
            media_root = Path(settings.MEDIA_ROOT)
            video_path = media_root / video_upload.file_path
            output_dir = media_root / 'analytics' / str(video_id)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            pipeline = VideoAnalyticsPipelineAdvanced(
                video_path=str(video_path),
                output_dir=str(output_dir),
                fps_sample=2.0,
                write_annotated_video=False,
                write_tracks=False,
            )
            
            result = pipeline.run()
            
            if not result.get('success'):
                raise Exception(result.get('error', 'Pipeline failed'))
            
            # Load detected events
            events_json_path = Path(result['events_json'])
            with open(events_json_path, 'r') as f:
                detected_events = json.load(f)
            
            # Create Event records and clips
            clips_created = 0
            for event_data in detected_events:
                event_type = event_data.get('event_type', 'other')
                timestamp_ms = event_data.get('timestamp_ms', 0)
                confidence = event_data.get('confidence', 0.0)
                
                # Create Event record
                event = None
                if video_upload.match:
                    ball_x = event_data.get('ball_x', 0)
                    ball_y = event_data.get('ball_y', 0)
                    width = video_upload.width or 1920
                    height = video_upload.height or 1080
                    
                    event = Event.objects.create(
                        match=video_upload.match,
                        event_type=event_type,
                        period=video_upload.period or 1,
                        timestamp_ms=video_upload.video_start_offset_ms + timestamp_ms,
                        x=round((ball_x / width) * 100, 2),
                        y=round((ball_y / height) * 100, 2),
                    )
                
                # Create video clip for goals and shots
                if event_type in ['goal', 'shot']:
                    clip_created = self._create_clip(
                        video_upload=video_upload,
                        event=event,
                        event_data=event_data,
                        video_path=video_path,
                        output_dir=output_dir,
                    )
                    if clip_created:
                        clips_created += 1
            
            video_upload.status = VideoUpload.Status.COMPLETED
            video_upload.events_count = len(detected_events)
            video_upload.json_output_path = str(events_json_path.relative_to(media_root))
            video_upload.processed_at = timezone.now()
            video_upload.save()
            
            return Response({
                'status': 'completed',
                'events_count': len(detected_events),
                'clips_created': clips_created,
            })
            
        except Exception as e:
            video_upload.status = VideoUpload.Status.FAILED
            video_upload.processing_error = str(e)
            video_upload.save()
            return Response({'error': str(e)}, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _create_clip(self, video_upload, event, event_data, video_path, output_dir):
        """Create a video clip using OpenCV (no ffmpeg dependency)."""
        import cv2
        try:
            timestamp_sec = event_data.get('timestamp_sec', 0)
            event_type = event_data.get('event_type', 'other')
            
            # Clip timing: 3 seconds before event, 3 seconds after
            start_time = max(0, timestamp_sec - 3)
            clip_duration = 6
            
            # Generate clip filename
            clip_id = uuid.uuid4()
            clip_filename = f"clip_{clip_id}.mp4"
            clip_path = output_dir / clip_filename
            
            # Create clip with OpenCV
            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                raise Exception(f"Cannot open video: {video_path}")
            
            fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            start_frame = int(start_time * fps)
            end_frame = int((start_time + clip_duration) * fps)
            
            fourcc = cv2.VideoWriter_fourcc(*'avc1')
            out = cv2.VideoWriter(str(clip_path), fourcc, fps, (width, height))
            
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            for frame_idx in range(start_frame, end_frame):
                ret, frame = cap.read()
                if not ret:
                    break
                out.write(frame)
            
            out.release()
            cap.release()
            
            if not clip_path.exists() or clip_path.stat().st_size == 0:
                raise Exception("Clip file is empty")
            
            clip_size = clip_path.stat().st_size
            
            # Create VideoClip record
            media_root = Path(settings.MEDIA_ROOT)
            VideoClip.objects.create(
                id=clip_id,
                video_upload=video_upload,
                event=event,
                clip_type=event_type,
                title=f"{event_type.title()} at {int(timestamp_sec)}s",
                file_path=str(clip_path.relative_to(media_root)),
                file_size=clip_size,
                duration_seconds=clip_duration,
                start_time_seconds=start_time,
                end_time_seconds=start_time + clip_duration,
                timestamp_ms=event_data.get('timestamp_ms', 0),
                confidence=event_data.get('confidence', 0.0),
            )
            
            return True
        except Exception as e:
            print(f"Failed to create clip: {e}")
            import traceback
            traceback.print_exc()
            return False


class VideoStatusAPIView(APIView):
    """Get video processing status."""
    
    def get(self, request, video_id):
        try:
            video_upload = VideoUpload.objects.get(id=video_id)
            return Response({
                'id': str(video_upload.id),
                'status': video_upload.status,
                'events_count': video_upload.events_count,
                'file_name': video_upload.file_name,
            })
        except VideoUpload.DoesNotExist:
            return Response({'error': 'Video not found'}, status=http_status.HTTP_404_NOT_FOUND)
