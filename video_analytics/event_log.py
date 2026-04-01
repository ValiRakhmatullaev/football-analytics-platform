"""
Сохранение лога событий в CSV и JSON.
Формат: timestamp, event_type, player_track_id, target_track_id, frame_id, confidence, metadata.
"""

import csv
import json
from pathlib import Path
from typing import List, Any, Dict

from video_analytics.football_events import DetectedEventRecord


def save_events_json(events: List[DetectedEventRecord], path: str | Path) -> None:
    """Сохраняет список событий в JSON (массив объектов)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = [e.to_dict() for e in events]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_events_csv(events: List[DetectedEventRecord], path: str | Path) -> None:
    """Сохраняет список событий в CSV (timestamp, event_type, player_track_id, target_track_id, frame_id, confidence, ball_x, ball_y)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = ["timestamp_sec", "timestamp_ms", "frame_id", "event_type", "player_track_id", "target_track_id", "ball_x", "ball_y", "confidence"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        for e in events:
            row = e.to_dict()
            w.writerow({k: row.get(k) for k in keys})
