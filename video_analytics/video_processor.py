"""
Video processing module for frame extraction and basic analysis.
Handles video loading, frame extraction, and temporal sampling.
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Iterator, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class VideoProcessor:
    """
    Processes video files to extract frames and metadata.
    """

    def __init__(self, video_path: str, fps_sample: float = 1.0):
        """
        Initialize video processor.

        Args:
            video_path: Path to input video file
            fps_sample: Frames per second to sample (default: 1.0 = 1 frame per second)
        """
        self.video_path = Path(video_path)
        if not self.video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        self.fps_sample = fps_sample
        self.cap: Optional[cv2.VideoCapture] = None
        self.video_fps: float = 0.0
        self.total_frames: int = 0
        self.duration_seconds: float = 0.0
        self.width: int = 0
        self.height: int = 0

    def __enter__(self):
        """Context manager entry."""
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def open(self):
        """Open video file and read metadata."""
        self.cap = cv2.VideoCapture(str(self.video_path))
        if not self.cap.isOpened():
            raise IOError(f"Failed to open video: {self.video_path}")

        self.video_fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.duration_seconds = self.total_frames / self.video_fps if self.video_fps > 0 else 0
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        logger.info(
            f"Video opened: {self.video_path.name} | "
            f"FPS: {self.video_fps:.2f} | "
            f"Duration: {self.duration_seconds:.2f}s | "
            f"Resolution: {self.width}x{self.height}"
        )

    def close(self):
        """Close video file."""
        if self.cap:
            self.cap.release()
            self.cap = None

    def get_frame_at_time(self, timestamp_seconds: float) -> Optional[np.ndarray]:
        """
        Get frame at specific timestamp.

        Args:
            timestamp_seconds: Timestamp in seconds from video start

        Returns:
            Frame as numpy array (BGR format) or None if failed
        """
        if not self.cap or not self.cap.isOpened():
            self.open()

        frame_number = int(timestamp_seconds * self.video_fps)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)

        ret, frame = self.cap.read()
        if not ret:
            return None

        return frame

    def iter_frames(self, start_time: float = 0.0, end_time: Optional[float] = None) -> Iterator[Tuple[float, np.ndarray]]:
        """
        Iterator over frames sampled at specified FPS.

        Args:
            start_time: Start time in seconds (default: 0.0)
            end_time: End time in seconds (None = end of video)

        Yields:
            Tuple of (timestamp_seconds, frame_array)
        """
        if not self.cap or not self.cap.isOpened():
            self.open()

        if end_time is None:
            end_time = self.duration_seconds

        frame_interval = int(self.video_fps / self.fps_sample) if self.fps_sample > 0 else 1
        start_frame = int(start_time * self.video_fps)
        end_frame = int(end_time * self.video_fps)

        self.cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

        current_frame = start_frame
        while current_frame < end_frame:
            ret, frame = self.cap.read()
            if not ret:
                break

            timestamp = current_frame / self.video_fps
            yield timestamp, frame

            # Skip frames to match sampling rate
            for _ in range(frame_interval - 1):
                ret = self.cap.read()[0]
                if not ret:
                    break
                current_frame += 1

            current_frame += frame_interval

    def get_metadata(self) -> dict:
        """
        Get video metadata.

        Returns:
            Dictionary with video metadata
        """
        return {
            "path": str(self.video_path),
            "fps": self.video_fps,
            "total_frames": self.total_frames,
            "duration_seconds": self.duration_seconds,
            "width": self.width,
            "height": self.height,
            "fps_sample": self.fps_sample,
        }
