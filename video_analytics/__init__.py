"""
Football Video Analytics MVP
Transforms 10-minute video clips into structured events compatible with Django backend.
Продвинутый пайплайн: YOLO + BoT-SORT, detect_events (shot/goal/pass/save), лог CSV/JSON.
"""

__version__ = "0.1.0"

# Детекция событий (не требует cv2/ultralytics)
from video_analytics.football_events import FootballEventDetector, FrameInfo, DetectedEventRecord

# IO helpers (не требуют cv2)
from video_analytics.event_log import save_events_json, save_events_csv

# Опциональные зависимости (opencv / ultralytics)
try:
    from video_analytics.advanced_detector import AdvancedDetector, Detection, Track, BallControl
except Exception:  # noqa: BLE001
    AdvancedDetector = None
    Detection = None
    Track = None
    BallControl = None

try:
    from video_analytics.video_annotation import draw_events_on_frame, draw_tracks_on_frame
except Exception:  # noqa: BLE001
    draw_events_on_frame = None
    draw_tracks_on_frame = None
