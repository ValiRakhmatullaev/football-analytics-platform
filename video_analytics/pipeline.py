"""
Main video analytics pipeline.
Orchestrates video processing, event detection, and data export.
"""

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
import sys

from video_analytics.video_processor import VideoProcessor
from video_analytics.event_detector import EventDetector, DetectedEvent
from video_analytics.pitch_calibration import PitchCalibrator
from video_analytics.data_exporter import DjangoEventExporter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VideoAnalyticsPipeline:
    """
    Main pipeline for processing football video and extracting events.
    """

    def __init__(
        self,
        video_path: str,
        match_id: Optional[str] = None,
        period: int = 2,
        video_start_offset_ms: int = 0,
        fps_sample: float = 1.0,
        output_dir: Optional[str] = None
    ):
        """
        Initialize pipeline.

        Args:
            video_path: Path to input video file
            match_id: Django Match UUID (optional)
            period: Match period (1=1st half, 2=2nd half)
            video_start_offset_ms: Offset in milliseconds (e.g., 3600000 for 60:00)
            fps_sample: Frames per second to sample
            output_dir: Output directory for results
        """
        self.video_path = Path(video_path)
        self.match_id = match_id
        self.period = period
        self.video_start_offset_ms = video_start_offset_ms
        self.fps_sample = fps_sample
        self.output_dir = Path(output_dir) if output_dir else self.video_path.parent / "analytics_output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.video_processor: Optional[VideoProcessor] = None
        self.event_detector = EventDetector()
        self.pitch_calibrator = PitchCalibrator()
        self.exporter = DjangoEventExporter(match_id=match_id, period=period)

        # Results
        self.detected_events: List[DetectedEvent] = []
        self.processing_stats: Dict[str, Any] = {}

    def run(self, calibrate_pitch: bool = False, pitch_corners: Optional[List] = None) -> Dict[str, Any]:
        """
        Run the complete pipeline.

        Args:
            calibrate_pitch: Whether to calibrate pitch (requires pitch_corners)
            pitch_corners: List of 4 corner points for calibration

        Returns:
            Dictionary with processing results and statistics
        """
        logger.info("=" * 70)
        logger.info("Starting Video Analytics Pipeline")
        logger.info("=" * 70)
        logger.info(f"Video: {self.video_path}")
        logger.info(f"Match ID: {self.match_id}")
        logger.info(f"Period: {self.period}")
        logger.info(f"Video start offset: {self.video_start_offset_ms}ms")
        logger.info(f"Sampling rate: {self.fps_sample} fps")
        logger.info("")

        try:
            # Step 1: Open video and get metadata
            logger.info("Step 1: Opening video...")
            self.video_processor = VideoProcessor(
                str(self.video_path),
                fps_sample=self.fps_sample
            )
            self.video_processor.open()
            metadata = self.video_processor.get_metadata()
            logger.info(f"Video duration: {metadata['duration_seconds']:.2f}s")
            logger.info(f"Resolution: {metadata['width']}x{metadata['height']}")
            logger.info("")

            # Step 2: Calibrate pitch (if requested)
            if calibrate_pitch and pitch_corners:
                logger.info("Step 2: Calibrating pitch...")
                # Get a sample frame for calibration
                sample_frame = self.video_processor.get_frame_at_time(metadata['duration_seconds'] / 2)
                if sample_frame is not None:
                    success = self.pitch_calibrator.calibrate_from_corners(
                        sample_frame,
                        pitch_corners,
                        output_size=(metadata['width'], metadata['height'])
                    )
                    if success:
                        logger.info("Pitch calibration successful")
                    else:
                        logger.warning("Pitch calibration failed, using fallback")
                logger.info("")

            # Step 3: Process frames and detect events
            logger.info("Step 3: Processing frames and detecting events...")
            frame_count = 0
            event_count = 0

            for timestamp, frame in self.video_processor.iter_frames():
                frame_count += 1

                # Detect events in this frame
                events = self.event_detector.process_frame(
                    frame,
                    timestamp,
                    metadata['width'],
                    metadata['height']
                )

                # Normalize coordinates using pitch calibrator
                for event in events:
                    if event.x is not None and event.y is not None:
                        # Convert from pixel-normalized to pitch-normalized
                        # (In MVP, they're the same, but calibrator can refine)
                        if self.pitch_calibrator.is_calibrated():
                            event.x, event.y = self.pitch_calibrator.pixel_to_normalized(
                                event.x * metadata['width'] / 100.0,
                                event.y * metadata['height'] / 100.0,
                                metadata['width'],
                                metadata['height']
                            )

                    self.detected_events.append(event)
                    event_count += 1

                if frame_count % 10 == 0:
                    logger.info(f"Processed {frame_count} frames, detected {event_count} events...")

            logger.info(f"Processing complete: {frame_count} frames, {event_count} events detected")
            logger.info("")

            # Step 4: Export results
            logger.info("Step 4: Exporting results...")
            output_json = self.output_dir / f"{self.video_path.stem}_events.json"
            self.exporter.export_to_json(
                self.detected_events,
                str(output_json),
                video_start_offset_ms=self.video_start_offset_ms,
                metadata={
                    "video_path": str(self.video_path),
                    "video_metadata": metadata,
                    "pitch_calibrated": self.pitch_calibrator.is_calibrated(),
                }
            )
            logger.info(f"Results exported to: {output_json}")
            logger.info("")

            # Step 5: Generate statistics
            stats = self._generate_statistics()
            self.processing_stats = stats

            logger.info("=" * 70)
            logger.info("Pipeline Complete")
            logger.info("=" * 70)
            logger.info(f"Total events detected: {len(self.detected_events)}")
            logger.info(f"Events by type: {stats['events_by_type']}")
            logger.info(f"Average confidence: {stats['avg_confidence']:.3f}")
            logger.info("")

            return {
                "success": True,
                "events_count": len(self.detected_events),
                "output_file": str(output_json),
                "statistics": stats,
            }

        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "events_count": len(self.detected_events),
            }

        finally:
            if self.video_processor:
                self.video_processor.close()

    def _generate_statistics(self) -> Dict[str, Any]:
        """Generate processing statistics."""
        if not self.detected_events:
            return {
                "events_by_type": {},
                "avg_confidence": 0.0,
                "total_events": 0,
            }

        events_by_type = {}
        total_confidence = 0.0

        for event in self.detected_events:
            event_type = event.event_type.value
            events_by_type[event_type] = events_by_type.get(event_type, 0) + 1
            total_confidence += event.confidence

        avg_confidence = total_confidence / len(self.detected_events) if self.detected_events else 0.0

        return {
            "events_by_type": events_by_type,
            "avg_confidence": avg_confidence,
            "total_events": len(self.detected_events),
        }

    def export_to_django(self, team_mapping: Optional[Dict[str, str]] = None,
                        player_mapping: Optional[Dict[str, str]] = None) -> bool:
        """
        Export detected events directly to Django database.

        Args:
            team_mapping: Mapping from detected team_id to Django Team UUID
            player_mapping: Mapping from detected player_id to Django Player UUID

        Returns:
            True if successful
        """
        if not self.match_id:
            logger.error("match_id required for Django export")
            return False

        try:
            self.exporter.export_to_django(
                self.detected_events,
                video_start_offset_ms=self.video_start_offset_ms,
                team_mapping=team_mapping,
                player_mapping=player_mapping
            )
            return True
        except Exception as e:
            logger.error(f"Django export failed: {e}")
            return False


def main():
    """Main entry point for command-line usage."""
    import argparse

    parser = argparse.ArgumentParser(description="Football Video Analytics Pipeline")
    parser.add_argument("video_path", help="Path to input video file")
    parser.add_argument("--match-id", help="Django Match UUID")
    parser.add_argument("--period", type=int, default=2, help="Match period (1 or 2)")
    parser.add_argument("--offset-ms", type=int, default=0,
                       help="Video start offset in milliseconds (e.g., 3600000 for 60:00)")
    parser.add_argument("--fps-sample", type=float, default=1.0,
                       help="Frames per second to sample (default: 1.0)")
    parser.add_argument("--output-dir", help="Output directory for results")

    args = parser.parse_args()

    pipeline = VideoAnalyticsPipeline(
        video_path=args.video_path,
        match_id=args.match_id,
        period=args.period,
        video_start_offset_ms=args.offset_ms,
        fps_sample=args.fps_sample,
        output_dir=args.output_dir
    )

    result = pipeline.run()
    
    if result["success"]:
        print(f"\n✓ Success! Detected {result['events_count']} events")
        print(f"  Output: {result['output_file']}")
        sys.exit(0)
    else:
        print(f"\n✗ Failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
