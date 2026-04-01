"""Re-process existing videos to create clips using the fixed OpenCV-based clip creation."""
import os, sys, json, uuid
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.dev'
import django
django.setup()
import cv2
from apps.analytics.models import VideoUpload, VideoClip
from pathlib import Path
from django.conf import settings

media_root = Path(settings.MEDIA_ROOT)

for v in VideoUpload.objects.filter(status='completed'):
    print(f"\n=== Processing video: {v.id} ({v.file_name}) ===")
    video_path = media_root / v.file_path
    if not video_path.exists():
        print(f"  Video file not found: {video_path}")
        continue

    output_dir = media_root / 'analytics' / str(v.id)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find events JSON
    events = []
    json_files = list(output_dir.glob('*_events.json'))
    if json_files:
        with open(json_files[0]) as f:
            events = json.load(f)
        print(f"  Found {len(events)} events in {json_files[0].name}")
    else:
        print("  No events JSON found, skipping")
        continue

    # Delete old clips
    old_clips = v.clips.count()
    if old_clips > 0:
        v.clips.all().delete()
        print(f"  Deleted {old_clips} old clips")

    clips_created = 0
    for event_data in events:
        event_type = event_data.get('event_type', 'other')
        if event_type not in ['goal', 'shot']:
            continue

        timestamp_sec = event_data.get('timestamp_sec', 0)
        start_time = max(0, timestamp_sec - 3)
        clip_duration = 6

        clip_id = uuid.uuid4()
        clip_path = output_dir / f"clip_{clip_id}.mp4"

        cap = cv2.VideoCapture(str(video_path))
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        start_frame = int(start_time * fps)
        end_frame = int((start_time + clip_duration) * fps)

        fourcc = cv2.VideoWriter_fourcc(*'avc1')
        out = cv2.VideoWriter(str(clip_path), fourcc, fps, (w, h))
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        written = 0
        for i in range(start_frame, end_frame):
            ret, frame = cap.read()
            if not ret:
                break
            out.write(frame)
            written += 1
        out.release()
        cap.release()

        if clip_path.exists() and clip_path.stat().st_size > 0:
            VideoClip.objects.create(
                id=clip_id,
                video_upload=v,
                clip_type=event_type,
                title=f"{event_type.title()} at {int(timestamp_sec)}s",
                file_path=str(clip_path.relative_to(media_root)),
                file_size=clip_path.stat().st_size,
                duration_seconds=clip_duration,
                start_time_seconds=start_time,
                end_time_seconds=start_time + clip_duration,
                timestamp_ms=event_data.get('timestamp_ms', 0),
                confidence=event_data.get('confidence', 0.0),
            )
            clips_created += 1
            print(f"  Created clip: {event_type} at {timestamp_sec}s ({written} frames, {clip_path.stat().st_size} bytes)")
        else:
            print(f"  FAILED clip: {event_type} at {timestamp_sec}s")

    print(f"  Total clips created: {clips_created}")

print("\nDone!")
