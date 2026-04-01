# Football Video Analytics MVP

Transforms 10-minute football video clips into structured events compatible with the Django backend.

## Overview

This MVP system processes football match videos and extracts:
- **Events**: Passes, Shots, Turnovers, Recoveries
- **Spatial Data**: Normalized pitch coordinates (0-100)
- **Temporal Data**: Timestamps in milliseconds
- **Confidence Scores**: Detection confidence (0.0-1.0)

## Architecture

```
video_analytics/
├── video_processor.py       # Video loading and frame extraction
├── event_detector.py        # Event detection (passes, shots, etc.)
├── advanced_detector.py     # YOLO + BoT-SORT, imgsz=1280, conf=0.25–0.3
├── football_events.py      # detect_events(): shot, goal, pass, save (rule-based + temporal)
├── event_log.py            # Export events to CSV/JSON
├── video_annotation.py     # Draw events/tracks on frames
├── pipeline_advanced.py    # Full pipeline: detect → events → log + annotated video
├── pitch_calibration.py    # Pitch coordinate mapping
├── data_exporter.py        # Django-compatible export
├── pipeline.py             # Main orchestration (legacy)
└── requirements.txt        # Dependencies (ultralytics, opencv)
```

## Installation

1. Install dependencies:
```bash
pip install -r video_analytics/requirements.txt
```

2. Ensure you have OpenCV installed:
```bash
pip install opencv-python numpy
```

## Usage

### Basic Usage (Python)

```python
from video_analytics.pipeline import VideoAnalyticsPipeline

# Initialize pipeline
pipeline = VideoAnalyticsPipeline(
    video_path="/path/to/video.mp4",
    match_id="your-match-uuid",  # Optional
    period=2,  # 2nd half
    video_start_offset_ms=3600000,  # 60:00 in milliseconds
    fps_sample=1.0  # Sample 1 frame per second
)

# Run pipeline
result = pipeline.run()

# Check results
print(f"Detected {result['events_count']} events")
print(f"Output: {result['output_file']}")
```

### Advanced pipeline (YOLO + BoT-SORT + event detection)

Детекция объектов (YOLO, опционально модель Roboflow для футбола), трекинг BoT-SORT, распознавание событий (shot, goal, pass, save), лог в CSV/JSON и аннотированное видео:

```bash
pip install -r video_analytics/requirements.txt
# Опционально: скачать модель Roboflow и задать ROBOFLOW_FOOTBALL_MODEL_PATH или --model

python -m video_analytics.pipeline_advanced /path/to/video.mp4 \
    --output-dir ./analytics_output \
    --imgsz 1280 --conf 0.28 \
    --fps-sample 5 \
    --draw-tracks
```

В коде:

```python
from video_analytics.pipeline_advanced import VideoAnalyticsPipelineAdvanced
from video_analytics.advanced_detector import AdvancedDetector, Track
from video_analytics.football_events import FootballEventDetector, FrameInfo

detector = AdvancedDetector(model_path=None, imgsz=1280, conf=0.28, tracker="botsort.yaml")
event_detector = FootballEventDetector(temporal_frames=8)

# В цикле по кадрам:
detections, tracks = detector.detect_frame(frame, frame_id)
frame_info = FrameInfo(timestamp_sec=ts, frame_id=frame_id, fps=fps, width=w, height=h)
events = event_detector.detect_events(tracks, prev_tracks, frame_info)
# events: список DetectedEventRecord (event_type, timestamp_ms, player_track_id, ...)
```

Лог событий: `{stem}_events.json`, `{stem}_events.csv`. Аннотированное видео: `{stem}_annotated.mp4`.

### Command Line (legacy pipeline)

```bash
python -m video_analytics.pipeline /path/to/video.mp4 \
    --match-id "your-match-uuid" \
    --period 2 \
    --offset-ms 3600000 \
    --fps-sample 1.0
```

### Export to Django

```python
# After running pipeline
pipeline.export_to_django(
    team_mapping={"team1": "uuid-1", "team2": "uuid-2"},
    player_mapping={"player1": "uuid-3", ...}
)
```

## Output Format

Events are exported as JSON with the following structure:

```json
{
  "exported_at": "2026-01-26T12:00:00",
  "match_id": "uuid",
  "period": 2,
  "video_start_offset_ms": 3600000,
  "total_events": 45,
  "events": [
    {
      "event_type": "pass",
      "timestamp_ms": 3605000,
      "period": 2,
      "x": 45.2,
      "y": 60.8,
      "confidence": 0.75,
      "outcome": "unknown",
      "team_id": null,
      "player_id": null
    }
  ]
}
```

## Event Detection

### Current MVP Implementation

- **Pass Detection**: Based on rapid ball movement
- **Shot Detection**: Ball movement toward goal area
- **Turnover Detection**: Sudden direction change
- **Recovery Detection**: (To be implemented)

### Future Enhancements

- YOLO-based player and ball detection
- Deep learning event classification
- Player tracking and identification
- Team possession detection
- More accurate coordinate mapping

## Pitch Calibration

For accurate coordinate mapping, calibrate the pitch:

```python
# Define 4 corner points of the pitch in the video
pitch_corners = [
    (x1, y1),  # Top-left
    (x2, y2),  # Top-right
    (x3, y3),  # Bottom-right
    (x4, y4)   # Bottom-left
]

pipeline.run(calibrate_pitch=True, pitch_corners=pitch_corners)
```

## Integration with Django Backend

The exported events are compatible with the Django `Event` model:

- `event_type`: "pass", "shot", "turnover", "recovery"
- `timestamp_ms`: Milliseconds from match start
- `period`: 1 (1st half) or 2 (2nd half)
- `x`, `y`: Normalized pitch coordinates (0-100)
- `confidence`: Detection confidence (0.0-1.0)
- `outcome`: "success", "fail", "unknown"

## Limitations (MVP)

1. **Simple Detection**: Uses heuristics, not ML models
2. **No Player ID**: Player identification not implemented
3. **No Team ID**: Team detection not implemented
4. **Basic Ball Detection**: Color-based, may miss ball in some conditions
5. **No Tracking**: No player/ball tracking across frames

## Next Steps

1. Integrate YOLO for object detection
2. Implement player tracking
3. Add team color detection
4. Improve ball detection accuracy
5. Add more event types (tackles, interceptions, etc.)
6. Implement confidence thresholding
7. Add video visualization output

## Troubleshooting

### No events detected
- Check video quality and lighting
- Adjust `fps_sample` (try 0.5 or 2.0)
- Verify ball is visible in video

### Incorrect coordinates
- Calibrate pitch using corner points
- Check video resolution and aspect ratio

### Import errors
- Ensure all dependencies are installed
- Check Python version (3.8+)
