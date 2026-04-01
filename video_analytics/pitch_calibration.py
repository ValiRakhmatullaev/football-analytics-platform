"""
Pitch calibration module for mapping pixel coordinates to normalized pitch coordinates (0-100).
Handles perspective transformation and coordinate normalization.
"""

import cv2
import numpy as np
from typing import Tuple, Optional, List
import logging

logger = logging.getLogger(__name__)


class PitchCalibrator:
    """
    Calibrates pitch coordinates from video frames.
    Maps pixel coordinates to normalized pitch coordinates (0-100).
    """

    def __init__(self, pitch_length_m: float = 105.0, pitch_width_m: float = 68.0):
        """
        Initialize pitch calibrator.

        Args:
            pitch_length_m: Standard pitch length in meters (default: 105m)
            pitch_width_m: Standard pitch width in meters (default: 68m)
        """
        self.pitch_length_m = pitch_length_m
        self.pitch_width_m = pitch_width_m
        self.transform_matrix: Optional[np.ndarray] = None
        self.inverse_transform_matrix: Optional[np.ndarray] = None
        self.calibrated = False

    def calibrate_from_corners(
        self,
        frame: np.ndarray,
        corners: List[Tuple[float, float]],
        output_size: Tuple[int, int] = (1050, 680)
    ) -> bool:
        """
        Calibrate using four corner points of the pitch.

        Args:
            frame: Input frame
            corners: List of 4 corner points [(x1, y1), (x2, y2), (x3, y3), (x4, y4)]
                    Order: top-left, top-right, bottom-right, bottom-left
            output_size: Output size for perspective transform (width, height)

        Returns:
            True if calibration successful
        """
        if len(corners) != 4:
            logger.error("Need exactly 4 corner points for calibration")
            return False

        # Source points (pixel coordinates in frame)
        src_points = np.float32(corners)

        # Destination points (normalized to output size)
        # Top-left, top-right, bottom-right, bottom-left
        dst_points = np.float32([
            [0, 0],
            [output_size[0], 0],
            [output_size[0], output_size[1]],
            [0, output_size[1]]
        ])

        # Calculate perspective transform matrix
        self.transform_matrix = cv2.getPerspectiveTransform(src_points, dst_points)
        self.inverse_transform_matrix = cv2.getPerspectiveTransform(dst_points, src_points)
        self.calibrated = True

        logger.info("Pitch calibration completed")
        return True

    def calibrate_auto(self, frame: np.ndarray) -> bool:
        """
        Automatic calibration using edge detection and line detection.
        This is a simplified MVP approach - can be enhanced with ML models.

        Args:
            frame: Input frame

        Returns:
            True if calibration successful (simplified - always returns False for MVP)
        """
        # TODO: Implement automatic pitch detection using:
        # - Edge detection (Canny)
        # - Line detection (HoughLines)
        # - Field line detection
        # - Corner detection

        logger.warning("Auto calibration not implemented in MVP - use manual calibration")
        return False

    def pixel_to_normalized(self, x: float, y: float, frame_width: int, frame_height: int) -> Tuple[float, float]:
        """
        Convert pixel coordinates to normalized pitch coordinates (0-100).

        Args:
            x: Pixel x coordinate
            y: Pixel y coordinate
            frame_width: Frame width in pixels
            frame_height: Frame height in pixels

        Returns:
            Tuple of (normalized_x, normalized_y) in range 0-100
        """
        if not self.calibrated:
            # Fallback: simple normalization based on frame dimensions
            # Assumes pitch fills most of the frame
            normalized_x = (x / frame_width) * 100.0
            normalized_y = (y / frame_height) * 100.0
            return normalized_x, normalized_y

        # Transform pixel to normalized coordinates using perspective transform
        # For MVP, we'll use a simplified approach
        # In production, use the transform matrix for accurate mapping

        # Apply perspective transform
        point = np.array([[[x, y]]], dtype=np.float32)
        transformed = cv2.perspectiveTransform(point, self.transform_matrix)[0][0]

        # Normalize to 0-100 range
        # Assuming output_size from calibration
        normalized_x = (transformed[0] / 1050.0) * 100.0
        normalized_y = (transformed[1] / 680.0) * 100.0

        # Clamp to valid range
        normalized_x = max(0.0, min(100.0, normalized_x))
        normalized_y = max(0.0, min(100.0, normalized_y))

        return normalized_x, normalized_y

    def is_calibrated(self) -> bool:
        """Check if calibrator is calibrated."""
        return self.calibrated

    def get_transform_matrix(self) -> Optional[np.ndarray]:
        """Get perspective transform matrix."""
        return self.transform_matrix
