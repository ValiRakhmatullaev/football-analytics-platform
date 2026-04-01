"""
Распознавание футбольных событий по трекингу: rule-based shot, goal, pass, save.
Temporal анализ по 5–10 кадрам (позиции мяча и игроков).
Совместимость: выход в формате timestamp, event_type, track_id для лога CSV/JSON.
"""

from __future__ import annotations

import math
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import deque
import logging

logger = logging.getLogger(__name__)

# Типы событий для лога
EVENT_SHOT = "shot"
EVENT_GOAL = "goal"
EVENT_PASS = "pass"
EVENT_SAVE = "save"

# Классы объектов (совпадают с advanced_detector)
COCO_PERSON_ID = 0
COCO_BALL_ID = 32


@dataclass
class FrameInfo:
    """Метаданные кадра для detect_events."""
    timestamp_sec: float
    frame_id: int
    fps: float
    width: int
    height: int


@dataclass
class TrackLike:
    """Минимальный интерфейс трека (совместим с video_analytics.advanced_detector.Track)."""
    track_id: int
    bbox: Tuple[float, float, float, float]
    class_id: int
    class_name: str
    frame_id: int


@dataclass
class DetectedEventRecord:
    """
    Запись о событии для лога и аннотации видео.
    """
    event_type: str       # "shot", "goal", "pass", "save"
    timestamp_sec: float
    timestamp_ms: int
    frame_id: int
    player_track_id: Optional[int] = None  # игрок, совершивший действие
    target_track_id: Optional[int] = None  # для паса — получатель
    ball_xy: Optional[Tuple[float, float]] = None
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "timestamp_sec": round(self.timestamp_sec, 3),
            "timestamp_ms": self.timestamp_ms,
            "frame_id": self.frame_id,
            "player_track_id": self.player_track_id,
            "target_track_id": self.target_track_id,
            "ball_x": self.ball_xy[0] if self.ball_xy else None,
            "ball_y": self.ball_xy[1] if self.ball_xy else None,
            "confidence": round(self.confidence, 4),
            **self.metadata,
        }


def _center(bbox: Tuple[float, float, float, float]) -> Tuple[float, float]:
    x1, y1, x2, y2 = bbox
    return ((x1 + x2) / 2, (y1 + y2) / 2)


def _distance(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    return float(math.hypot(a[0] - b[0], a[1] - b[1]))


class FootballEventDetector:
    """
    Rule-based детектор событий: удар/гол, пас, сейв.
    Использует temporal анализ (буфер последних 5–10 кадров).
    """

    def __init__(
        self,
        # Линия ворот: мяч ЗА этой линией = внутри ворот (доли высоты кадра: 0 = верх, 1 = низ).
        goal_line_top_ratio: float = 0.03,
        goal_line_bottom_ratio: float = 0.97,
        # Ширина створа ворот по X (доли ширины кадра). Нужна, чтобы не считать голом вылет в аут/угловой.
        goal_mouth_left_ratio: float = 0.30,
        goal_mouth_right_ratio: float = 0.70,
        # Зоны «близко к воротам» для ударов (не для гола).
        goal_zone_top_ratio: float = 0.10,
        goal_zone_bottom_ratio: float = 0.10,
        # Пороги скорости мяча (пиксели в секунду) — будут автоматически масштабироваться по разрешению
        shot_speed_threshold: float = 300.0,
        pass_speed_threshold: float = 100.0,
        # Минимальная скорость мяча для гола
        goal_min_speed_threshold: float = 80.0,
        # Близость мяча к игроку (пиксели) для "контроля"
        ball_control_px: float = 80.0,
        # Минимальное число кадров для траектории
        temporal_frames: int = 8,
        # Подавление повторов одного типа события (кадров обработанных, не оригинальных)
        event_cooldown_frames: int = 60,
        goal_cooldown_frames: int = 200,
        save_cooldown_frames: int = 80,
        # Порог прыжка мяча для обнаружения смены сцены/камеры (доля диагонали кадра)
        scene_cut_jump_ratio: float = 0.35,
    ):
        self.goal_line_top = goal_line_top_ratio
        self.goal_line_bottom = goal_line_bottom_ratio
        self.goal_mouth_left = goal_mouth_left_ratio
        self.goal_mouth_right = goal_mouth_right_ratio
        self.goal_zone_top = goal_zone_top_ratio
        self.goal_zone_bottom = goal_zone_bottom_ratio
        self.shot_speed_threshold = shot_speed_threshold
        self.pass_speed_threshold = pass_speed_threshold
        self.goal_min_speed_threshold = goal_min_speed_threshold
        self.ball_control_px = ball_control_px
        self.temporal_frames = temporal_frames
        self.event_cooldown_frames = event_cooldown_frames
        self.goal_cooldown_frames = goal_cooldown_frames
        self.save_cooldown_frames = save_cooldown_frames
        self.scene_cut_jump_ratio = scene_cut_jump_ratio

        # Буферы для temporal анализа
        self._ball_history: deque = deque(maxlen=32)   # (frame_id, ts, x, y, track_id or None)
        self._ownership_history: deque = deque(maxlen=32)  # (frame_id, track_id or None) — кто ближе к мячу
        self._last_event_frame: Dict[str, int] = {}   # event_type -> frame_id
        self._scene_cut_cooldown: int = 0  # кадров после обнаружения смены сцены

    def _get_ball_track(self, tracks: List[TrackLike]) -> Optional[TrackLike]:
        for t in tracks:
            if t.class_id == COCO_BALL_ID:
                return t
        return None

    def _get_players(self, tracks: List[TrackLike]) -> List[TrackLike]:
        return [t for t in tracks if t.class_id == COCO_PERSON_ID]

    def _ownership(self, ball: TrackLike, players: List[TrackLike]) -> Optional[int]:
        bc = _center(ball.bbox)
        best_id = None
        best_d = float("inf")
        for p in players:
            d = _distance(bc, _center(p.bbox))
            if d < best_d:
                best_d = d
                best_id = p.track_id
        if best_d <= self.ball_control_px:
            return best_id
        return None

    def _ball_speed_px_per_sec(self, fps: float) -> Optional[float]:
        if len(self._ball_history) < 2 or fps <= 0:
            return None
        arr = list(self._ball_history)
        (f0, t0, x0, y0, _), (f1, t1, x1, y1, _) = arr[-2], arr[-1]
        dt = t1 - t0
        if dt <= 0:
            return None
        dist = _distance((x0, y0), (x1, y1))
        return dist / dt  # px/sec

    def _smooth_ball_speed(self, fps: float, n: int = 3) -> Optional[float]:
        """Средняя скорость мяча за последние n замеров — снижает шум."""
        if len(self._ball_history) < n + 1 or fps <= 0:
            return None
        arr = list(self._ball_history)
        speeds = []
        for i in range(-n, 0):
            f0, t0, x0, y0, _ = arr[i - 1]
            f1, t1, x1, y1, _ = arr[i]
            dt = t1 - t0
            if dt <= 0:
                continue
            speeds.append(_distance((x0, y0), (x1, y1)) / dt)
        return sum(speeds) / len(speeds) if speeds else None

    def _detect_scene_cut(self, width: int, height: int) -> bool:
        """Обнаруживает смену сцены/камеры по резкому прыжку позиции мяча."""
        if len(self._ball_history) < 2:
            return False
        arr = list(self._ball_history)
        (_, _, x0, y0, _), (_, _, x1, y1, _) = arr[-2], arr[-1]
        diag = math.hypot(width, height)
        jump = _distance((x0, y0), (x1, y1))
        return jump > diag * self.scene_cut_jump_ratio

    def _ball_trajectory_consistent(self, n: int = 4) -> bool:
        """Проверяет, что мяч двигался в одном направлении последние n кадров (не дёргался)."""
        if len(self._ball_history) < n:
            return False
        arr = list(self._ball_history)
        dy_signs = []
        for i in range(-n + 1, 0):
            dy = arr[i][3] - arr[i - 1][3]
            if abs(dy) > 1:  # порог шума
                dy_signs.append(1 if dy > 0 else -1)
        if len(dy_signs) < 2:
            return False
        # Все движения в одном направлении?
        return all(s == dy_signs[0] for s in dy_signs)

    def _ball_moving_toward_goal(self, height: int) -> Optional[str]:
        """Возвращает 'top' или 'bottom' если мяч летит в сторону соответствующей створки."""
        if len(self._ball_history) < 3:
            return None
        arr = list(self._ball_history)
        ys = [a[3] for a in arr[-5:]]
        if len(ys) < 2:
            return None
        dy = ys[-1] - ys[0]
        top_zone = height * self.goal_zone_top
        bottom_zone = height * (1.0 - self.goal_zone_bottom)
        if dy < 0 and ys[-1] < top_zone * 1.2:
            return "top"
        if dy > 0 and ys[-1] > bottom_zone * 0.8:
            return "bottom"
        return None

    def _in_goal_zone(self, y: float, height: int) -> bool:
        top_zone = height * self.goal_zone_top
        bottom_zone = height * (1.0 - self.goal_zone_bottom)
        return y < top_zone or y > bottom_zone

    def _goal_line_crossing(self, width: int, height: int) -> Optional[str]:
        """
        Гол только при пересечении линии ворот: мяч был на поле и пересёк линию ворот.
        Возвращает "top" или "bottom" если в этом кадре мяч только что зашёл за линию ворот.
        """
        if len(self._ball_history) < 2:
            return None
        arr = list(self._ball_history)
        (_, _, x_prev, y_prev, _), (_, _, x_curr, y_curr, _) = arr[-2], arr[-1]

        mouth_left = width * self.goal_mouth_left
        mouth_right = width * self.goal_mouth_right
        # Требуем, чтобы пересечение происходило в пределах створа ворот по X.
        # Используем текущую точку мяча (после пересечения), чтобы отфильтровать вылеты в аут/угловой.
        if not (mouth_left <= x_curr <= mouth_right):
            return None

        line_top = height * self.goal_line_top
        line_bottom = height * self.goal_line_bottom
        # Верхние ворота: мяч пересёк линию сверху (был на поле y_prev >= line_top, стал за линией y_curr < line_top)
        if y_prev >= line_top and y_curr < line_top:
            return "top"
        # Нижние ворота: мяч пересёк линию снизу (был на поле y_prev <= line_bottom, стал за линией y_curr > line_bottom)
        if y_prev <= line_bottom and y_curr > line_bottom:
            return "bottom"
        return None

    def _check_cooldown(self, event_type: str, frame_id: int) -> bool:
        if event_type == EVENT_GOAL:
            last = self._last_event_frame.get(event_type, -999)
            return frame_id - last >= self.goal_cooldown_frames
        if event_type == EVENT_SAVE:
            last = self._last_event_frame.get(event_type, -999)
            return frame_id - last >= self.save_cooldown_frames
        last = self._last_event_frame.get(event_type, -999)
        return frame_id - last >= self.event_cooldown_frames

    def _commit_event(self, event_type: str, frame_id: int):
        self._last_event_frame[event_type] = frame_id

    def detect_events(
        self,
        tracks: List[TrackLike],
        prev_tracks: Optional[List[TrackLike]],
        frame_info: FrameInfo,
    ) -> List[DetectedEventRecord]:
        """
        Определяет события по текущим и предыдущим трекам и метаданным кадра.
        Правила:
        - Удар/гол: скорость мяча > shot_speed_threshold, траектория в створ, игрок рядом с мячом.
        - Пас: мяч переходит от одного player track_id к другому (по ownership), без критерия удара.
        - Сейв: мяч летит в створ, затем резкая смена владения на вратаря или остановка в зоне ворот.
        """
        events: List[DetectedEventRecord] = []
        fps = frame_info.fps if frame_info.fps > 0 else 25.0
        ts_sec = frame_info.timestamp_sec
        ts_ms = int(frame_info.timestamp_sec * 1000)
        frame_id = frame_info.frame_id
        w, h = frame_info.width, frame_info.height

        ball = self._get_ball_track(tracks)
        players = self._get_players(tracks)

        if ball is None:
            return events

        ball_xy = _center(ball.bbox)
        owner = self._ownership(ball, players)

        # Обновляем буфер (frame_id, timestamp_sec, x, y, ball_track_id)
        self._ball_history.append((frame_id, ts_sec, ball_xy[0], ball_xy[1], ball.track_id))
        self._ownership_history.append((frame_id, owner))

        # Обнаружение смены сцены/камеры (реплей, графика)
        if self._detect_scene_cut(w, h):
            self._scene_cut_cooldown = 6  # пропускаем 6 обработанных кадров (3 сек при 2fps)
            logger.debug(f"Scene cut detected at {ts_sec:.1f}s, cooldown activated")
            return events
        if self._scene_cut_cooldown > 0:
            self._scene_cut_cooldown -= 1
            return events

        # Нужно достаточно кадров для скорости
        if len(self._ball_history) < max(3, self.temporal_frames // 2):
            return events

        speed_px_s = self._smooth_ball_speed(fps, n=3)
        toward_goal = self._ball_moving_toward_goal(h)
        in_goal_zone = self._in_goal_zone(ball_xy[1], h)
        trajectory_ok = self._ball_trajectory_consistent(n=3)

        # —— Гол только при пересечении линии ворот + устойчивая траектория ——
        crossing = self._goal_line_crossing(w, h)
        is_goal_speed_ok = speed_px_s is not None and speed_px_s >= self.goal_min_speed_threshold
        if (
            crossing is not None
            and is_goal_speed_ok
            and trajectory_ok
            and self._check_cooldown(EVENT_GOAL, frame_id)
        ):
            events.append(DetectedEventRecord(
                event_type=EVENT_GOAL,
                timestamp_sec=ts_sec,
                timestamp_ms=ts_ms,
                frame_id=frame_id,
                player_track_id=owner,
                ball_xy=ball_xy,
                confidence=0.9,
                metadata={
                    "goal_line": crossing,
                    "ball_crossed_goal_line": True,
                    "ball_speed_px_s": round(speed_px_s or 0.0, 2),
                },
            ))
            self._commit_event(EVENT_GOAL, frame_id)
            # Также засчитываем как shot cooldown, чтобы не дублировать
            self._commit_event(EVENT_SHOT, frame_id)

        # —— Удар (без гола): высокая скорость + устойчивая траектория к воротам + игрок рядом ——
        if (
            speed_px_s is not None
            and speed_px_s >= self.shot_speed_threshold
            and toward_goal is not None
            and trajectory_ok
            and self._check_cooldown(EVENT_SHOT, frame_id)
        ):
            # Требуем, чтобы был игрок рядом с мячом недавно
            had_player_near = False
            for _fi, _oid in list(self._ownership_history)[-3:]:
                if _oid is not None:
                    had_player_near = True
                    break
            if had_player_near:
                events.append(DetectedEventRecord(
                    event_type=EVENT_SHOT,
                    timestamp_sec=ts_sec,
                    timestamp_ms=ts_ms,
                    frame_id=frame_id,
                    player_track_id=owner,
                    ball_xy=ball_xy,
                    confidence=min(1.0, speed_px_s / (self.shot_speed_threshold * 2)),
                    metadata={"ball_speed_px_s": round(speed_px_s, 2), "goal_direction": toward_goal},
                ))
                self._commit_event(EVENT_SHOT, frame_id)

        # —— Пас: смена владения мячом между двумя разными игроками (по track_id), без удара ——
        if prev_tracks is not None and len(self._ownership_history) >= 2:
            prev_ball = self._get_ball_track(prev_tracks)
            prev_players = self._get_players(prev_tracks)
            prev_owner = None
            if prev_ball and prev_players:
                prev_owner = self._ownership(prev_ball, prev_players)
            if prev_owner is not None and owner is not None and prev_owner != owner:
                # Не считаем пасом если только что зафиксировали удар
                if not events and (speed_px_s is None or speed_px_s < self.shot_speed_threshold):
                    if self._check_cooldown(EVENT_PASS, frame_id):
                        events.append(DetectedEventRecord(
                            event_type=EVENT_PASS,
                            timestamp_sec=ts_sec,
                            timestamp_ms=ts_ms,
                            frame_id=frame_id,
                            player_track_id=prev_owner,
                            target_track_id=owner,
                            ball_xy=ball_xy,
                            confidence=0.6,
                            metadata={"from_track_id": prev_owner, "to_track_id": owner},
                        ))
                        self._commit_event(EVENT_PASS, frame_id)

        # —— Сейв: мяч летел в створ (высокая скорость), затем смена владения в зоне ворот ——
        if (
            in_goal_zone
            and toward_goal
            and trajectory_ok
            and self._check_cooldown(EVENT_SAVE, frame_id)
            and speed_px_s is not None
            and speed_px_s >= self.shot_speed_threshold * 0.8
            and owner is not None
            and len(self._ownership_history) >= 4
        ):
            prev_owns = [x[1] for x in list(self._ownership_history)[-4:-1]]
            if prev_owns[-1] is not None and prev_owns[-1] != owner:
                events.append(DetectedEventRecord(
                    event_type=EVENT_SAVE,
                    timestamp_sec=ts_sec,
                    timestamp_ms=ts_ms,
                    frame_id=frame_id,
                    player_track_id=owner,
                    ball_xy=ball_xy,
                    confidence=0.55,
                    metadata={"ball_speed_px_s": round(speed_px_s or 0, 2)},
                ))
                self._commit_event(EVENT_SAVE, frame_id)

        return events
