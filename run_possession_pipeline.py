#!/usr/bin/env python3
"""
Запуск пайплайна аналитики с модулем possession (TeamAssigner + Player_ball_assigner).
Улучшенная детекция: владение мячом и команда по кадрам.

Пример:
  python run_possession_pipeline.py path/to/video.mp4
  python run_possession_pipeline.py path/to/video.mp4 --no-video --fps-sample 3
"""

import sys
import argparse
from pathlib import Path

# Корень проекта
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main():
    parser = argparse.ArgumentParser(
        description="Football video analytics with possession (YOLO + BoT-SORT + TeamAssigner + Player_ball_assigner)"
    )
    parser.add_argument("video_path", type=str, help="Путь к входному видео")
    parser.add_argument("--output-dir", "-o", type=str, default=None, help="Каталог для JSON/CSV и аннотированного видео")
    parser.add_argument("--model", "-m", type=str, default=None, help="Путь к YOLO .pt модели (футбол)")
    parser.add_argument("--imgsz", type=int, default=1280, help="Размер входа YOLO (по умолчанию 1280)")
    parser.add_argument("--conf", type=float, default=0.28, help="Порог уверенности (по умолчанию 0.28)")
    parser.add_argument("--fps-sample", type=float, default=5.0, help="Обрабатывать кадров в секунду (по умолчанию 5)")
    parser.add_argument("--no-video", action="store_true", help="Не писать аннотированное видео")
    parser.add_argument("--draw-tracks", action="store_true", help="Рисовать боксы треков на видео")
    args = parser.parse_args()

    video_path = Path(args.video_path)
    if not video_path.exists():
        print(f"Ошибка: файл не найден: {video_path}")
        return 1

    print("=" * 60)
    print("Пайплайн аналитики + possession (TeamAssigner, Player_ball_assigner)")
    print("=" * 60)
    print(f"Видео: {video_path}")
    print(f"Модель: {args.model or 'по умолчанию (YOLOv8n / Roboflow)'}")
    print(f"FPS сэмпл: {args.fps_sample}")
    print()

    try:
        from video_analytics.pipeline_advanced import VideoAnalyticsPipelineAdvanced
    except ImportError as e:
        print(f"Ошибка импорта: {e}")
        print("Установите зависимости: pip install -r video_analytics/requirements.txt")
        return 1

    pipeline = VideoAnalyticsPipelineAdvanced(
        video_path=str(video_path),
        output_dir=args.output_dir,
        model_path=args.model,
        imgsz=args.imgsz,
        conf=args.conf,
        fps_sample=args.fps_sample,
        write_annotated_video=not args.no_video,
        write_tracks=args.draw_tracks,
    )

    result = pipeline.run()

    if not result.get("success"):
        print("Пайплайн завершился с ошибкой:", result.get("error", "неизвестно"))
        return 1

    print()
    print("Результат:")
    print(f"  Событий: {result['events_count']}")
    print(f"  JSON:    {result.get('events_json', '—')}")
    print(f"  CSV:     {result.get('events_csv', '—')}")
    if result.get("annotated_video"):
        print(f"  Видео:   {result['annotated_video']}")
    stats = result.get("statistics", {})
    if stats.get("events_by_type"):
        print("  По типам:", stats["events_by_type"])
    if stats.get("total_passes") is not None:
        print(f"  Пасов:   {stats['total_passes']}")
    if stats.get("possession_team_1_pct") is not None:
        print(f"  Владение: команда 1 — {stats['possession_team_1_pct']}%, команда 2 — {stats['possession_team_2_pct']}%")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
