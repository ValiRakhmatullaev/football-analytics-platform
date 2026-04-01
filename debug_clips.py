import os, sys, json
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.dev'
import django
django.setup()
import cv2
from apps.analytics.models import VideoUpload
from pathlib import Path
from django.conf import settings

v = VideoUpload.objects.order_by('-uploaded_at').first()
media_root = Path(settings.MEDIA_ROOT)
video_path = media_root / v.file_path
output_dir = media_root / 'analytics' / str(v.id)

# Test different codecs
codecs = [('avc1', '.mp4'), ('H264', '.mp4'), ('XVID', '.avi'), ('mp4v', '.mp4')]
for codec_name, ext in codecs:
    clip_path = output_dir / f"test_{codec_name}{ext}"
    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*codec_name)
    out = cv2.VideoWriter(str(clip_path), fourcc, fps, (w, h))
    cap.set(cv2.CAP_PROP_POS_FRAMES, 17)
    for i in range(150):
        ret, frame = cap.read()
        if not ret:
            break
        out.write(frame)
    out.release()
    cap.release()
    sz = clip_path.stat().st_size if clip_path.exists() else 0
    print(f"{codec_name}{ext}: {sz} bytes")
