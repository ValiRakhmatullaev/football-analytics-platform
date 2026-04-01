"""
Аннотация видео: текст и иконки над мячом/игроком при событии.
Совместимость: OpenCV; опционально supervision для боксов.
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional

from video_analytics.football_events import DetectedEventRecord

# Цвета (BGR)
COLORS = {
    "shot": (0, 165, 255),   # оранжевый
    "goal": (0, 255, 0),     # зелёный
    "pass": (255, 255, 0),   # голубой
    "save": (0, 255, 255),   # жёлтый
}
DEFAULT_COLOR = (200, 200, 200)
LABELS = {
    "shot": "SHOT",
    "goal": "GOAL",
    "pass": "PASS",
    "save": "SAVE",
}


def draw_events_on_frame(
    frame: np.ndarray,
    events: List[DetectedEventRecord],
    *,
    draw_at_ball: bool = True,
    font_scale: float = 0.8,
    thickness: int = 2,
) -> np.ndarray:
    """
    Рисует на кадре подписи и иконки для списка событий (в этом кадре).
    Если draw_at_ball — текст над позицией мяча, иначе по центру сверху.
    """
    out = frame.copy()
    h, w = frame.shape[:2]
    for ev in events:
        color = COLORS.get(ev.event_type, DEFAULT_COLOR)
        label = LABELS.get(ev.event_type, ev.event_type.upper())
        if draw_at_ball and ev.ball_xy:
            cx, cy = int(ev.ball_xy[0]), int(ev.ball_xy[1])
            # Текст чуть выше мяча
            tx, ty = cx, max(20, cy - 25)
        else:
            tx, ty = w // 2 - 40, 40
        # Фон для текста
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
        cv2.rectangle(out, (tx - 2, ty - th - 4), (tx + tw + 2, ty + 4), (0, 0, 0), -1)
        cv2.putText(out, label, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness, cv2.LINE_AA)
        # Небольшой круг на мяче при событии
        if draw_at_ball and ev.ball_xy:
            cx, cy = int(ev.ball_xy[0]), int(ev.ball_xy[1])
            cv2.circle(out, (cx, cy), 12, color, 2)
    return out


def draw_tracks_on_frame(
    frame: np.ndarray,
    tracks: List,
    *,
    draw_ball: bool = True,
    draw_players: bool = True,
) -> np.ndarray:
    """
    Рисует боксы треков на кадре (совместим с advanced_detector.Track).
    """
    out = frame.copy()
    for t in tracks:
        x1, y1, x2, y2 = map(int, t.bbox)
        is_ball = getattr(t, "class_id", None) == 32 or getattr(t, "class_name", "") == "ball"
        if is_ball and not draw_ball:
            continue
        if not is_ball and not draw_players:
            continue
        color = (0, 255, 0) if is_ball else (255, 165, 0)
        cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)
        tid = getattr(t, "track_id", None)
        if tid is not None:
            cv2.putText(out, str(tid), (x1, y1 - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)
    return out
