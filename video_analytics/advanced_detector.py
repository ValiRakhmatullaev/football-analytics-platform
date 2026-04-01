"""
Детекция объектов для футбольного видео: YOLO + BoT-SORT.
Поддержка модели Roboflow/HuggingFace для футбола, imgsz=1280, conf=0.25–0.3.
Совместимость: ultralytics, supervision (опционально), opencv.
"""

import cv2
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from pathlib import Path
import os
import logging

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    logging.warning("Ultralytics YOLO not available. Install: pip install ultralytics")

# Опционально: ByteTrack как запасной трекер (если не использовать встроенный BoT-SORT)
BYTETRACK_AVAILABLE = False
try:
    try:
        from byte_tracker import BYTETracker
    except ImportError:
        from yolox.tracker.byte_tracker import BYTETracker
    BYTETRACK_AVAILABLE = True
except ImportError:
    pass

logger = logging.getLogger(__name__)

# Имена классов для футбольной модели Roboflow (players, ball, goalkeeper, referee)
ROBOFLOW_CLASS_NAMES = ["player", "ball", "goalkeeper", "referee"]
# COCO: person=0, sports ball=32
COCO_PERSON_ID = 0
COCO_BALL_ID = 32


@dataclass
class Detection:
    """Один объект детекции."""
    bbox: Tuple[float, float, float, float]  # x1, y1, x2, y2
    confidence: float
    class_id: int
    class_name: str


@dataclass
class Track:
    """Трекируемый объект с ID между кадрами."""
    track_id: int
    bbox: Tuple[float, float, float, float]
    confidence: float
    class_id: int
    class_name: str
    frame_id: int
    team_id: Optional[int] = None
    has_ball: bool = False


@dataclass
class BallControl:
    """Контроль мяча в кадре."""
    frame_id: int
    controlling_player_id: Optional[int] = None
    controlling_team: Optional[int] = None
    ball_position: Optional[Tuple[float, float]] = None
    distance_to_player: Optional[float] = None


def _load_football_model(model_path: Optional[str] = None) -> Optional[Any]:
    """
    Загрузка YOLO-модели: приоритет футбольная модель (Roboflow/HF или .pt), иначе yolov8n.
    """
    if not YOLO_AVAILABLE:
        return None
    # 1) Явный путь к .pt (например скачанный с Roboflow)
    if model_path and Path(model_path).exists():
        try:
            model = YOLO(model_path)
            logger.info(f"Loaded YOLO model from {model_path}")
            return model
        except Exception as e:
            logger.warning(f"Failed to load {model_path}: {e}")
    # 2) Roboflow из переменной окружения (путь к .pt после download)
    roboflow_pt = os.environ.get("ROBOFLOW_FOOTBALL_MODEL_PATH")
    if roboflow_pt and Path(roboflow_pt).exists():
        try:
            model = YOLO(roboflow_pt)
            logger.info(f"Loaded Roboflow football model from {roboflow_pt}")
            return model
        except Exception as e:
            logger.warning(f"Failed to load Roboflow model: {e}")
    # 3) Попытка загрузить из Roboflow API (нужен api_key)
    try:
        from roboflow import Roboflow
        api_key = os.environ.get("ROBOFLOW_API_KEY")
        if api_key:
            rf = Roboflow(api_key=api_key)
            # Популярный датасет: football-players-detection
            proj = rf.workspace("roboflow-jvuqo").project("football-players-detection-3zvbc")
            ver = proj.version(2)  # или другая версия
            ver.download("yolov8")
            # После download модель обычно в текущей папке
            pt_path = Path("football-players-detection-3zvbc-2/train/weights/best.pt")
            if not pt_path.exists():
                pt_path = Path(ver.location) / "weights" / "best.pt" if hasattr(ver, "location") else None
            if pt_path and Path(pt_path).exists():
                model = YOLO(str(pt_path))
                logger.info("Loaded football model from Roboflow")
                return model
    except Exception as e:
        logger.debug(f"Roboflow load skipped: {e}")
    # 4) Fallback — базовая YOLOv8n (person + sports ball в COCO)
    try:
        model = YOLO("yolov8n.pt")
        logger.info("Using pretrained YOLOv8n (person + ball from COCO)")
        return model
    except Exception as e:
        logger.error(f"YOLO load failed: {e}")
        return None


class AdvancedDetector:
    """
    Детектор на YOLO + встроенный BoT-SORT (ultralytics).
    Параметры: imgsz=1280, conf=0.25–0.3, трекинг через model.track(..., tracker="botsort.yaml").
    """

    # Для COCO: person=0, sports ball=32
    PERSON_CLASS = 0
    BALL_CLASS = 32
    # Маппинг имён классов футбольной модели -> person/ball
    FOOTBALL_PERSON_IDS = {0, 1, 3}  # player, goalkeeper, referee -> person
    FOOTBALL_BALL_ID = 2  # ball

    def __init__(
        self,
        model_path: Optional[str] = None,
        use_custom_ball: bool = True,
        imgsz: int = 1280,
        conf: float = 0.28,
        iou: float = 0.45,
        tracker: str = "botsort.yaml",
    ):
        """
        Args:
            model_path: путь к .pt модели (Roboflow/HF или своя).
            use_custom_ball: доп. цветовая детекция мяча если YOLO не нашёл.
            imgsz: размер входа YOLO (1280 для лучшего качества).
            conf: порог уверенности (0.25–0.3).
            iou: IoU для NMS.
            tracker: "botsort.yaml" (по умолчанию) или "bytetrack.yaml".
        """
        self.use_custom_ball = use_custom_ball
        self.imgsz = imgsz
        self.conf = conf
        self.iou = iou
        self.tracker_name = tracker
        self.model = _load_football_model(model_path)
        self._is_football_model = False
        self._model_names: Dict[int, str] = {}
        if self.model and hasattr(self.model, "names"):
            names = self.model.names
            if isinstance(names, dict):
                self._model_names = {int(k): str(v) for k, v in names.items()}
            else:
                self._model_names = {i: str(n) for i, n in enumerate(names)}
            if any("ball" in n.lower() or "player" in n.lower() or "person" in n.lower() for n in self._model_names.values()):
                self._is_football_model = True
                logger.info("Football model: class names %s", list(self._model_names.values()))

    def _class_id_to_person_ball(self, class_id: int) -> Tuple[int, str]:
        """Приводит class_id к единому виду: person (0) или ball (32). По имени класса, чтобы работало с любой моделью."""
        if self._is_football_model and self._model_names:
            name = self._model_names.get(class_id, "").lower()
            if "ball" in name or "мяч" in name:
                return COCO_BALL_ID, "ball"
            return COCO_PERSON_ID, "person"
        if class_id == self.BALL_CLASS:
            return COCO_BALL_ID, "ball"
        if class_id == self.PERSON_CLASS:
            return COCO_PERSON_ID, "person"
        name = (self.model.names.get(class_id, "unknown") if self.model else "unknown")
        return class_id, str(name)

    def detect_ball_color(self, frame: np.ndarray, bbox: Optional[Tuple] = None) -> Optional[Detection]:
        """Цветовая детекция мяча (оранжевый/жёлтый/белый) как fallback."""
        roi = frame
        offset_x, offset_y = 0, 0
        if bbox:
            x1, y1, x2, y2 = map(int, bbox)
            roi = frame[y1:y2, x1:x2]
            offset_x, offset_y = x1, y1
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        h, w = roi.shape[:2]
        masks = []
        masks.append(cv2.inRange(hsv, np.array([5, 50, 50]), np.array([25, 255, 255])))
        masks.append(cv2.inRange(hsv, np.array([20, 50, 50]), np.array([35, 255, 255])))
        masks.append(cv2.inRange(hsv, np.array([0, 0, 200]), np.array([180, 30, 255])))
        mask = masks[0]
        for m in masks[1:]:
            mask = cv2.bitwise_or(mask, m)
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.medianBlur(mask, 5)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 20 or area > 5000:
                continue
            perimeter = cv2.arcLength(contour, True)
            if perimeter == 0:
                continue
            circularity = 4 * np.pi * area / (perimeter * perimeter)
            if circularity < 0.3:
                continue
            M = cv2.moments(contour)
            if M["m00"] == 0:
                continue
            cx = int(M["m10"] / M["m00"]) + offset_x
            cy = int(M["m01"] / M["m00"]) + offset_y
            x1 = max(0, cx - 12)
            y1 = max(0, cy - 12)
            x2 = min(frame.shape[1], cx + 12)
            y2 = min(frame.shape[0], cy + 12)
            conf = min(1.0, circularity * 0.8)
            if conf < 0.2:
                continue
            return Detection(bbox=(float(x1), float(y1), float(x2), float(y2)), confidence=conf, class_id=COCO_BALL_ID, class_name="ball")
        return None

    def detect_frame(self, frame: np.ndarray, frame_id: int) -> Tuple[List[Detection], List[Track]]:
        """
        Детекция + трекинг за один вызов (YOLO track с BoT-SORT).
        Возвращает (detections, tracks) для текущего кадра.
        """
        detections: List[Detection] = []
        tracks: List[Track] = []

        if not self.model:
            return detections, tracks

        try:
            # persist=True чтобы track_id сохранялись между вызовами
            results = self.model.track(
                frame,
                imgsz=self.imgsz,
                conf=self.conf,
                iou=self.iou,
                tracker=self.tracker_name,
                persist=True,
                verbose=False,
            )
        except Exception as e:
            logger.error(f"YOLO track failed: {e}")
            return detections, tracks

        for result in results:
            if result.boxes is None:
                continue
            boxes = result.boxes
            xyxy = boxes.xyxy.cpu().numpy()
            conf = boxes.conf.cpu().numpy()
            cls = boxes.cls.cpu().numpy()
            ids = boxes.id.cpu().numpy() if boxes.id is not None else np.arange(len(boxes))

            for i in range(len(boxes)):
                x1, y1, x2, y2 = xyxy[i]
                c = float(conf[i])
                class_id = int(cls[i])
                tid = int(ids[i]) if np.isscalar(ids[i]) else int(ids[i].item())
                cid_unified, cname = self._class_id_to_person_ball(class_id)
                if cid_unified != COCO_PERSON_ID and cid_unified != COCO_BALL_ID:
                    continue
                detections.append(Detection(bbox=(float(x1), float(y1), float(x2), float(y2)), confidence=c, class_id=cid_unified, class_name=cname))
                tracks.append(Track(track_id=tid, bbox=(float(x1), float(y1), float(x2), float(y2)), confidence=c, class_id=cid_unified, class_name=cname, frame_id=frame_id))

        # Fallback: цветовая детекция мяча если не найден
        if self.use_custom_ball and not any(d.class_id == COCO_BALL_ID for d in detections):
            ball_det = self.detect_ball_color(frame)
            if ball_det:
                detections.append(ball_det)
                # Мячу даём синтетический track_id (отрицательный или большой), чтобы не путать с игроками
                synthetic_ball_id = 900000 + frame_id
                tracks.append(Track(track_id=synthetic_ball_id, bbox=ball_det.bbox, confidence=ball_det.confidence, class_id=COCO_BALL_ID, class_name="ball", frame_id=frame_id))

        return detections, tracks

    def get_ball_control(self, tracks: List[Track], ball_control_threshold_px: float = 80.0) -> Optional[BallControl]:
        """Определяет игрока, ближайшего к мячу (контроль мяча)."""
        ball_track = None
        player_tracks = []
        for t in tracks:
            if t.class_id == COCO_BALL_ID:
                ball_track = t
            elif t.class_id == COCO_PERSON_ID:
                player_tracks.append(t)
        if not ball_track or not player_tracks:
            return None
        bx = (ball_track.bbox[0] + ball_track.bbox[2]) / 2
        by = (ball_track.bbox[1] + ball_track.bbox[3]) / 2
        best_dist = float("inf")
        best_player = None
        for p in player_tracks:
            px = (p.bbox[0] + p.bbox[2]) / 2
            py = (p.bbox[1] + p.bbox[3]) / 2
            d = np.sqrt((bx - px) ** 2 + (by - py) ** 2)
            if d < best_dist:
                best_dist = d
                best_player = p
        if best_dist <= ball_control_threshold_px:
            return BallControl(frame_id=ball_track.frame_id, controlling_player_id=best_player.track_id if best_player else None, controlling_team=None, ball_position=(bx, by), distance_to_player=best_dist)
        return None
