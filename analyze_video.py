"""Analyze videoplayback.mp4 and register in backend DB with clips."""
import os, sys, json, uuid
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.dev'
import django
django.setup()
import cv2
import shutil
from pathlib import Path
from django.conf import settings
from django.utils import timezone
from apps.analytics.models import VideoUpload, VideoClip
from apps.competitions.models import Match, MatchTeam
from apps.teams.models import Team

media_root = Path(settings.MEDIA_ROOT)
src = Path('videoplayback.mp4')

# 1. Copy video to media
videos_dir = media_root / 'videos'
videos_dir.mkdir(parents=True, exist_ok=True)
video_id = uuid.uuid4()
dest = videos_dir / f'{video_id}.mp4'
shutil.copy2(src, dest)
print(f'Video copied: {dest}')

# 2. Get metadata
cap = cv2.VideoCapture(str(dest))
fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
duration = frames / fps
cap.release()
print(f'Metadata: {duration:.0f}s, {w}x{h} @ {fps}fps')

# 3. Create match + teams (with required Season and Competition)
from apps.competitions.models import Competition, Season
from datetime import date
comp, _ = Competition.objects.get_or_create(
    name='Video Analysis',
    defaults={'country': 'Unknown', 'level': 1}
)
season, _ = Season.objects.get_or_create(
    competition=comp, name='2024-25',
    defaults={'start_date': date(2024, 8, 1), 'end_date': date(2025, 6, 30)}
)
team1, _ = Team.objects.get_or_create(
    name='Home Team',
    defaults={'short_name': 'HOM', 'competition': comp}
)
team2, _ = Team.objects.get_or_create(
    name='Away Team',
    defaults={'short_name': 'AWY', 'competition': comp}
)
match = Match.objects.create(season=season, kickoff_time=timezone.now())
MatchTeam.objects.create(match=match, team=team1, side='home')
MatchTeam.objects.create(match=match, team=team2, side='away')

# 4. Create VideoUpload record
video_upload = VideoUpload.objects.create(
    id=video_id,
    file_name='videoplayback.mp4',
    file_path=str(dest.relative_to(media_root)),
    file_size=src.stat().st_size,
    duration_seconds=duration,
    width=w, height=h, fps=fps,
    status=VideoUpload.Status.PROCESSING,
    match=match, period=1,
)
print(f'VideoUpload created: {video_id}')

# 5. Run AI pipeline
print('\n=== Running AI pipeline (this will take a few minutes) ===')
sys.path.insert(0, '.')
from video_analytics.pipeline_advanced import VideoAnalyticsPipelineAdvanced

output_dir = media_root / 'analytics' / str(video_id)
output_dir.mkdir(parents=True, exist_ok=True)

pipeline = VideoAnalyticsPipelineAdvanced(
    video_path=str(dest),
    output_dir=str(output_dir),
    fps_sample=2.0,
    write_annotated_video=False,
    write_tracks=False,
)
result = pipeline.run()

if not result.get('success'):
    print(f'FAILED: {result.get("error")}')
    video_upload.status = VideoUpload.Status.FAILED
    video_upload.processing_error = result.get('error', '')
    video_upload.save()
    sys.exit(1)

# 6. Load events
events_json_path = Path(result['events_json'])
with open(events_json_path) as f:
    detected_events = json.load(f)

print(f'\nDetected {len(detected_events)} events:')
stats = {}
for e in detected_events:
    t = e.get('event_type', '?')
    stats[t] = stats.get(t, 0) + 1
for t, c in sorted(stats.items()):
    print(f'  {t}: {c}')

# 7. Create clips for goals and shots
print('\n=== Creating clips ===')
clips_created = 0
for event_data in detected_events:
    event_type = event_data.get('event_type', 'other')
    if event_type not in ['goal', 'shot']:
        continue

    timestamp_sec = event_data.get('timestamp_sec', 0)
    start_time = max(0, timestamp_sec - 3)
    clip_duration = 6

    clip_id = uuid.uuid4()
    clip_path = output_dir / f'clip_{clip_id}.mp4'

    cap = cv2.VideoCapture(str(dest))
    start_frame = int(start_time * fps)
    end_frame = int((start_time + clip_duration) * fps)
    fourcc = cv2.VideoWriter_fourcc(*'avc1')
    out = cv2.VideoWriter(str(clip_path), fourcc, fps, (w, h))
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    for i in range(end_frame - start_frame):
        ret, frame = cap.read()
        if not ret:
            break
        out.write(frame)
    out.release()
    cap.release()

    if clip_path.exists() and clip_path.stat().st_size > 0:
        VideoClip.objects.create(
            id=clip_id,
            video_upload=video_upload,
            clip_type=event_type,
            title=f'{event_type.title()} at {int(timestamp_sec // 60)}:{int(timestamp_sec % 60):02d}',
            file_path=str(clip_path.relative_to(media_root)),
            file_size=clip_path.stat().st_size,
            duration_seconds=clip_duration,
            start_time_seconds=start_time,
            end_time_seconds=start_time + clip_duration,
            timestamp_ms=event_data.get('timestamp_ms', 0),
            confidence=event_data.get('confidence', 0.0),
        )
        clips_created += 1
        print(f'  Clip: {event_type} at {int(timestamp_sec)}s ({clip_path.stat().st_size} bytes)')

# 8. Update video status
video_upload.status = VideoUpload.Status.COMPLETED
video_upload.events_count = len(detected_events)
video_upload.json_output_path = str(events_json_path.relative_to(media_root))
video_upload.processed_at = timezone.now()
video_upload.save()

print(f'\n=== DONE ===')
print(f'Video ID: {video_id}')
print(f'Events: {len(detected_events)}')
print(f'Clips created: {clips_created}')
print(f'Statistics: {result.get("statistics", {})}')
print(f'\nView clips: http://localhost:3000/videos/{video_id}/clips')
print(f'Annotate:   http://localhost:3000/videos/{video_id}/annotate')
