"""
Пайплайн продвинутой аналитики футбольного видео.
Детекция (YOLO + BoT-SORT, imgsz=1280, conf=0.25–0.3) → detect_events() → лог CSV/JSON + аннотированное видео.
Совместимость: ultralytics, supervision (опц.), opencv.
"""

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

try:
    import cv2
except ImportError:
    cv2 = None

from video_analytics.video_processor import VideoProcessor
from video_analytics.advanced_detector import AdvancedDetector, Track
from video_analytics.football_events import FootballEventDetector, FrameInfo, DetectedEventRecord
from video_analytics.event_log import save_events_json, save_events_csv
from video_analytics.video_annotation import draw_events_on_frame, draw_tracks_on_frame
from video_analytics.possession_enrichment import PossessionEnricher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class VideoAnalyticsPipelineAdvanced:
    """
    Пайплайн: открытие видео → детекция + трекинг (BoT-SORT) → detect_events → экспорт лога + аннотированное видео.
    """

    def __init__(
        self,
        video_path: str,
        output_dir: Optional[str] = None,
        model_path: Optional[str] = None,
        imgsz: int = 1280,
        conf: float = 0.28,
        fps_sample: float = 5.0,
        write_annotated_video: bool = True,
        write_tracks: bool = False,
    ):
        """
        Args:
            video_path: путь к видео.
            output_dir: каталог для JSON/CSV и аннотированного видео (по умолчанию рядом с видео).
            model_path: путь к .pt модели (Roboflow/HF футбол) или None.
            imgsz: размер входа YOLO (1280).
            conf: порог уверенности (0.25–0.3).
            fps_sample: частота семплирования кадров (кадров/сек).
            write_annotated_video: писать ли видео с аннотациями событий.
            write_tracks: рисовать ли боксы треков на видео.
        """
        self.video_path = Path(video_path)
        self.output_dir = Path(output_dir) if output_dir else self.video_path.parent / "analytics_output"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.model_path = model_path
        self.imgsz = imgsz
        self.conf = conf
        self.fps_sample = fps_sample
        self.write_annotated_video = write_annotated_video
        self.write_tracks = write_tracks

        self.detector = AdvancedDetector(
            model_path=model_path,
            use_custom_ball=True,
            imgsz=imgsz,
            conf=conf,
            tracker="botsort.yaml",
        )
        self.possession_enricher = PossessionEnricher(max_player_ball_distance=70.0)
        self.event_detector = FootballEventDetector(
            temporal_frames=8,
            shot_speed_threshold=70.0,
            pass_speed_threshold=45.0,
            event_cooldown_frames=18,
            goal_cooldown_frames=60,
            save_cooldown_frames=35,
            goal_line_top_ratio=0.045,
            goal_line_bottom_ratio=0.955,
            ball_control_px=120.0,
        )

        self.all_events: List[DetectedEventRecord] = []
        self.possession_team_1_frames: int = 0
        self.possession_team_2_frames: int = 0
        self.video_processor: Optional[VideoProcessor] = None
        self.metadata: Dict[str, Any] = {}

    def run(self) -> Dict[str, Any]:
        """
        Запуск пайплайна: обработка кадров, детекция событий, сохранение лога и (опционально) видео.
        """
        logger.info("Starting advanced video analytics pipeline")
        logger.info("Video: %s", self.video_path)
        logger.info("Output dir: %s", self.output_dir)

        self.video_processor = VideoProcessor(str(self.video_path), fps_sample=self.fps_sample)
        self.video_processor.open()
        meta = self.video_processor.get_metadata()
        self.metadata = meta
        fps = meta["fps"] or 25.0
        w, h = meta["width"], meta["height"]

        # Выходное видео (если нужно)
        out_video: Optional[Any] = None
        if self.write_annotated_video and cv2:
            out_path = self.output_dir / f"{self.video_path.stem}_annotated.mp4"
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            out_video = cv2.VideoWriter(str(out_path), fourcc, fps, (w, h))
            logger.info("Writing annotated video: %s", out_path)

        prev_tracks: Optional[List[Track]] = None
        frame_id = 0

        for timestamp_sec, frame in self.video_processor.iter_frames():
            # Детекция + трекинг
            detections, tracks = self.detector.detect_frame(frame, frame_id)
            # Обогащение владением: team_id, has_ball (TeamAssigner + Player_ball_assigner)
            tracks = self.possession_enricher.enrich_frame(frame, tracks)
            frame_info = FrameInfo(
                timestamp_sec=timestamp_sec,
                frame_id=frame_id,
                fps=fps,
                width=w,
                height=h,
            )
            # События по правилам (tracks, prev_tracks, frame_info)
            events_this_frame = self.event_detector.detect_events(tracks, prev_tracks, frame_info)
            self.all_events.extend(events_this_frame)

            # Владение мячом по кадрам (игрок с has_ball и team_id 1 или 2)
            for t in tracks:
                if getattr(t, "has_ball", False) and getattr(t, "team_id", None) is not None:
                    if t.team_id == 1:
                        self.possession_team_1_frames += 1
                    elif t.team_id == 2:
                        self.possession_team_2_frames += 1
                    break

            # Аннотация кадра
            if self.write_annotated_video and cv2:
                vis = frame.copy()
                if self.write_tracks:
                    vis = draw_tracks_on_frame(vis, tracks, draw_ball=True, draw_players=True)
                vis = draw_events_on_frame(vis, events_this_frame, draw_at_ball=True)
                if out_video is not None:
                    out_video.write(vis)

            prev_tracks = tracks
            frame_id += 1

            if frame_id % 50 == 0:
                logger.info("Processed %d frames, events so far: %d", frame_id, len(self.all_events))

        if out_video is not None:
            out_video.release()
            logger.info("Annotated video saved")

        self.video_processor.close()

        # Сохранение лога событий
        stem = self.video_path.stem
        json_path = self.output_dir / f"{stem}_events.json"
        csv_path = self.output_dir / f"{stem}_events.csv"
        save_events_json(self.all_events, json_path)
        save_events_csv(self.all_events, csv_path)
        logger.info("Events log saved: %s, %s", json_path, csv_path)

        stats = self._stats()
        logger.info("Pipeline finished. Total events: %d. By type: %s", len(self.all_events), stats.get("events_by_type", {}))
        return {
            "success": True,
            "events_count": len(self.all_events),
            "output_dir": str(self.output_dir),
            "events_json": str(json_path),
            "events_csv": str(csv_path),
            "annotated_video": str(self.output_dir / f"{stem}_annotated.mp4") if self.write_annotated_video else None,
            "statistics": stats,
        }

    def _stats(self) -> Dict[str, Any]:
        by_type: Dict[str, int] = {}
        for e in self.all_events:
            by_type[e.event_type] = by_type.get(e.event_type, 0) + 1
        avg_conf = sum(e.confidence for e in self.all_events) / len(self.all_events) if self.all_events else 0.0
        total_passes = by_type.get("pass", 0)
        total_poss = self.possession_team_1_frames + self.possession_team_2_frames
        if total_poss > 0:
            poss_1_pct = round(100.0 * self.possession_team_1_frames / total_poss, 1)
            poss_2_pct = round(100.0 * self.possession_team_2_frames / total_poss, 1)
        else:
            poss_1_pct = poss_2_pct = 0.0
        return {
            "events_by_type": by_type,
            "avg_confidence": round(avg_conf, 4),
            "total_events": len(self.all_events),
            "total_passes": total_passes,
            "possession_team_1_pct": poss_1_pct,
            "possession_team_2_pct": poss_2_pct,
            "possession_team_1_frames": self.possession_team_1_frames,
            "possession_team_2_frames": self.possession_team_2_frames,
        }

    def export_backend_format_json(
        self,
        output_path: str,
        video_start_offset_ms: int = 0,
        match_id: Optional[str] = None,
        period: int = 2,
    ) -> None:
        """
        Сохраняет события в формате, ожидаемом бэкендом и VideoClipper:
        events[].event_type, timestamp_ms, x (0–100), y (0–100), confidence.
        Вызывать после run(). Координаты ball_xy (пиксели) приводятся к нормализованным 0–100.
        """
        from datetime import datetime
        import json
        w = self.metadata.get("width") or 1280
        h = self.metadata.get("height") or 720
        django_events = []
        for e in self.all_events:
            ts_ms = video_start_offset_ms + e.timestamp_ms
            x_norm = round((e.ball_xy[0] / w) * 100.0, 2) if e.ball_xy else 50.0
            y_norm = round((e.ball_xy[1] / h) * 100.0, 2) if e.ball_xy else 50.0
            django_events.append({
                "event_type": e.event_type,
                "timestamp_ms": ts_ms,
                "x": x_norm,
                "y": y_norm,
                "confidence": round(e.confidence, 3),
                "outcome": "unknown",
            })
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "match_id": match_id,
            "period": period,
            "video_start_offset_ms": video_start_offset_ms,
            "total_events": len(django_events),
            "events": django_events,
            "metadata": {"pipeline": "advanced", "video_metadata": self.metadata},
        }
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        logger.info("Exported backend-format JSON to %s (%d events)", output_path, len(django_events))


def main():
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Football video analytics (YOLO + BoT-SORT + event detection)")
    parser.add_argument("video_path", help="Path to input video")
    parser.add_argument("--output-dir", "-o", help="Output directory for JSON/CSV and annotated video")
    parser.add_argument("--model", "-m", help="Path to YOLO .pt model (e.g. Roboflow football)")
    parser.add_argument("--imgsz", type=int, default=1280, help="YOLO input size (default 1280)")
    parser.add_argument("--conf", type=float, default=0.28, help="Confidence threshold (default 0.28)")
    parser.add_argument("--fps-sample", type=float, default=5.0, help="Frames per second to process (default 5)")
    parser.add_argument("--no-video", action="store_true", help="Do not write annotated video")
    parser.add_argument("--draw-tracks", action="store_true", help="Draw track boxes on video")
    args = parser.parse_args()

    pipeline = VideoAnalyticsPipelineAdvanced(
        video_path=args.video_path,
        output_dir=args.output_dir,
        model_path=args.model,
        imgsz=args.imgsz,
        conf=args.conf,
        fps_sample=args.fps_sample,
        write_annotated_video=not args.no_video,
        write_tracks=args.draw_tracks,
    )
    result = pipeline.run()

    if result.get("success"):
        print("Done. Events:", result["events_count"])
        print("JSON:", result["events_json"])
        print("CSV:", result["events_csv"])
        if result.get("annotated_video"):
            print("Video:", result["annotated_video"])
        sys.exit(0)
    else:
        print("Failed:", result.get("error", "Unknown"))
        sys.exit(1)


if __name__ == "__main__":
    main()
