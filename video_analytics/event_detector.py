"""
Event detection module for identifying football events (passes, shots, turnovers, recoveries).
Uses computer vision and heuristics to detect events from video frames.
"""

import cv2
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Event types matching Django Event model."""
    PASS = "pass"
    SHOT = "shot"
    TURNOVER = "turnover"
    RECOVERY = "recovery"
    FREE_KICK = "free_kick"
    PENALTY = "penalty"
    CORNER = "corner"


@dataclass
class DetectedEvent:
    """
    Detected event from video analysis.
    Compatible with Django Event model structure.
    """
    event_type: EventType
    timestamp_ms: int  # Milliseconds from video start
    x: Optional[float] = None  # Normalized pitch x (0-100)
    y: Optional[float] = None  # Normalized pitch y (0-100)
    confidence: float = 0.0  # Detection confidence (0.0-1.0)
    team_id: Optional[str] = None  # Team identifier (to be mapped to Django Team)
    player_id: Optional[str] = None  # Player identifier (to be mapped to Django Player)
    outcome: str = "unknown"  # "success", "fail", "unknown"
    metadata: Dict = None  # Additional event metadata

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class EventDetector:
    """
    Detects football events from video frames using computer vision.
    MVP implementation uses simple heuristics and can be enhanced with ML models.
    """

    def __init__(self, ball_detector=None, player_detector=None):
        """
        Initialize event detector.

        Args:
            ball_detector: Optional ball detection model/function
            player_detector: Optional player detection model/function
        """
        self.ball_detector = ball_detector
        self.player_detector = player_detector

        # State tracking for event detection
        self.previous_frame: Optional[np.ndarray] = None
        self.ball_positions: List[Tuple[float, float, float]] = []  # (x, y, timestamp)
        self.player_positions: List[Dict] = []
        # Cooldown: не выдавать повторный удар в течение N секунд (один удар = одно событие)
        self._last_shot_timestamp: Optional[float] = None
        self.shot_cooldown_seconds: float = 3.0

    def detect_ball(self, frame: np.ndarray) -> Optional[Tuple[float, float, float]]:
        """
        Detect ball position in frame.
        Improved version with multiple color ranges and better filtering.

        Args:
            frame: Input frame (BGR)

        Returns:
            Tuple of (x, y, confidence) or None if not detected
        """
        # MVP: Improved color-based ball detection
        # Supports multiple ball colors: orange, yellow, white, black

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        height, width = frame.shape[:2]

        # Multiple color ranges for different ball types
        masks = []
        
        # Orange/yellow ball (most common)
        lower_orange = np.array([5, 50, 50])  # More lenient lower bound
        upper_orange = np.array([25, 255, 255])
        masks.append(cv2.inRange(hsv, lower_orange, upper_orange))
        
        # Yellow ball
        lower_yellow = np.array([20, 50, 50])
        upper_yellow = np.array([35, 255, 255])
        masks.append(cv2.inRange(hsv, lower_yellow, upper_yellow))
        
        # White ball (in bright conditions)
        lower_white = np.array([0, 0, 200])
        upper_white = np.array([180, 30, 255])
        masks.append(cv2.inRange(hsv, lower_white, upper_white))
        
        # Black/dark ball (shadows)
        lower_black = np.array([0, 0, 0])
        upper_black = np.array([180, 255, 50])
        masks.append(cv2.inRange(hsv, lower_black, upper_black))

        # Combine all masks
        mask = masks[0]
        for m in masks[1:]:
            mask = cv2.bitwise_or(mask, m)

        # Morphological operations to clean up
        kernel = np.ones((3, 3), np.uint8)  # Smaller kernel for better detection
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        # Remove noise with median blur
        mask = cv2.medianBlur(mask, 5)

        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return None

        # Filter contours by size and shape
        valid_contours = []
        for contour in contours:
            area = cv2.contourArea(contour)
            # More lenient size filter (ball can be very small or larger in different videos)
            if area < 20 or area > 5000:  # Increased upper bound
                continue
            
            # Check circularity
            perimeter = cv2.arcLength(contour, True)
            if perimeter == 0:
                continue
            circularity = 4 * np.pi * area / (perimeter * perimeter)
            
            # More lenient circularity check
            if circularity > 0.3:  # Lowered threshold
                valid_contours.append((contour, area, circularity))

        if not valid_contours:
            return None

        # Select best candidate (most circular, reasonable size)
        best_contour, best_area, best_circularity = max(
            valid_contours, 
            key=lambda x: x[2] * (1.0 if 50 <= x[1] <= 500 else 0.7)  # Prefer medium-sized
        )

        # Get center
        M = cv2.moments(best_contour)
        if M["m00"] == 0:
            return None

        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])

        # Calculate confidence (more lenient)
        confidence = min(1.0, best_circularity * 0.8)  # Increased multiplier
        
        # Lower confidence threshold
        if confidence < 0.2:  # Lowered from 0.3
            return None

        return (cx, cy, confidence)

    def detect_players(self, frame: np.ndarray) -> List[Dict]:
        """
        Detect players in frame.

        Args:
            frame: Input frame (BGR)

        Returns:
            List of player detections with position and team info
        """
        # MVP: Simple player detection using color-based team separation
        # In production, use YOLO or specialized player detection model

        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Detect players by finding vertical blobs (simplified)
        # This is a placeholder - real implementation needs proper player detection

        players = []
        # TODO: Implement proper player detection
        # For MVP, return empty list or use simple heuristics

        return players

    def detect_pass(self, ball_positions: List[Tuple[float, float, float]], 
                   frame_width: int, frame_height: int) -> Optional[DetectedEvent]:
        """
        Detect pass event based on ball movement.
        Improved with lower thresholds.

        Args:
            ball_positions: Recent ball positions [(x, y, timestamp), ...]
            frame_width: Frame width
            frame_height: Frame height

        Returns:
            DetectedEvent if pass detected, None otherwise
        """
        if len(ball_positions) < 2:  # Lowered from 3
            return None

        # Check for rapid ball movement (pass characteristic)
        recent_positions = ball_positions[-5:]  # Last 5 positions
        if len(recent_positions) < 2:
            return None

        # Calculate velocity
        positions = np.array([(p[0], p[1]) for p in recent_positions])
        velocities = np.diff(positions, axis=0)
        speeds = np.linalg.norm(velocities, axis=1)

        # Pass typically has high velocity (lowered threshold)
        avg_speed = np.mean(speeds)
        if avg_speed < 10:  # Lowered from 20
            return None

        # Get position at start of movement
        start_pos = recent_positions[0]
        timestamp_ms = int(start_pos[2] * 1000)

        # Normalize coordinates (will be normalized properly by pitch calibrator)
        x_norm = (start_pos[0] / frame_width) * 100.0
        y_norm = (start_pos[1] / frame_height) * 100.0

        confidence = min(0.8, avg_speed / 30.0)  # Adjusted confidence calculation

        return DetectedEvent(
            event_type=EventType.PASS,
            timestamp_ms=timestamp_ms,
            x=x_norm,
            y=y_norm,
            confidence=confidence,
            outcome="unknown"
        )

    def detect_shot(self, ball_positions: List[Tuple[float, float, float]],
                   frame_width: int, frame_height: int) -> Optional[DetectedEvent]:
        """
        Detect shot event based on ball movement toward goal.
        Improved with lower thresholds.

        Args:
            ball_positions: Recent ball positions
            frame_width: Frame width
            frame_height: Frame height

        Returns:
            DetectedEvent if shot detected, None otherwise
        """
        if len(ball_positions) < 3:  # Lowered from 5
            return None

        recent_positions = ball_positions[-8:]  # Reduced from 10
        if len(recent_positions) < 2:  # Lowered from 3
            return None

        # Check for movement toward goal area
        positions = np.array([(p[0], p[1]) for p in recent_positions])
        
        # Goal is typically at top or bottom of frame
        # Check if ball is moving toward goal line
        y_positions = positions[:, 1]
        y_velocity = np.mean(np.diff(y_positions))

        # High velocity toward goal (lowered threshold)
        if abs(y_velocity) < 8:  # Lowered from 15
            return None

        # Check if near goal area (top or bottom 25% of frame)
        current_y = positions[-1, 1]
        goal_area_threshold = frame_height * 0.25
        near_goal = current_y < goal_area_threshold or current_y > (frame_height - goal_area_threshold)

        if not near_goal:
            return None

        # Позицию берём с конца траектории (мяч ближе к воротам) — для корректной классификации гола в клиппере
        end_pos = recent_positions[-1]
        timestamp_ms = int(end_pos[2] * 1000)

        x_norm = (end_pos[0] / frame_width) * 100.0
        y_norm = (end_pos[1] / frame_height) * 100.0

        # Improved confidence calculation based on multiple factors
        # 1. Velocity component (how fast ball is moving)
        velocity_confidence = min(0.6, abs(y_velocity) / 25.0)
        
        # 2. Distance to goal (closer = higher confidence)
        distance_to_goal = min(
            current_y / frame_height,
            (frame_height - current_y) / frame_height
        )
        distance_confidence = (1.0 - distance_to_goal) * 0.3  # Max 0.3 boost
        
        # 3. Consistency of movement (straight line = higher confidence)
        if len(positions) >= 3:
            # Calculate direction consistency
            directions = np.diff(positions, axis=0)
            direction_angles = np.arctan2(directions[:, 1], directions[:, 0])
            angle_std = np.std(direction_angles)
            consistency_confidence = max(0, 0.2 - angle_std)  # Lower std = higher confidence
        else:
            consistency_confidence = 0.1
        
        # Combine all factors
        base_confidence = velocity_confidence + distance_confidence + consistency_confidence
        base_confidence = min(0.85, base_confidence)
        
        # Boost for very close to goal line (top/bottom 8%)
        very_close_to_goal = current_y < frame_height * 0.08 or current_y > frame_height * 0.92
        if very_close_to_goal:
            base_confidence = min(0.95, base_confidence * 1.15)  # Boost by 15%
        
        confidence = base_confidence

        return DetectedEvent(
            event_type=EventType.SHOT,
            timestamp_ms=timestamp_ms,
            x=x_norm,
            y=y_norm,
            confidence=confidence,
            outcome="unknown"
        )

    def detect_turnover(self, ball_positions: List[Tuple[float, float, float]],
                       frame_width: int, frame_height: int) -> Optional[DetectedEvent]:
        """
        Detect turnover (ball possession change).

        Args:
            ball_positions: Recent ball positions
            frame_width: Frame width
            frame_height: Frame height

        Returns:
            DetectedEvent if turnover detected, None otherwise
        """
        # MVP: Simplified - detect sudden direction change
        if len(ball_positions) < 5:
            return None

        recent_positions = ball_positions[-8:]
        if len(recent_positions) < 4:
            return None

        positions = np.array([(p[0], p[1]) for p in recent_positions])
        velocities = np.diff(positions, axis=0)
        
        # Check for significant direction change
        if len(velocities) < 2:
            return None

        # Calculate angle change
        angles = np.arctan2(velocities[:, 1], velocities[:, 0])
        angle_changes = np.diff(angles)
        angle_changes = np.abs(angle_changes)
        angle_changes = np.minimum(angle_changes, 2 * np.pi - angle_changes)  # Wrap to [0, pi]

        # Large angle change indicates turnover
        max_angle_change = np.max(angle_changes)
        if max_angle_change < np.pi / 3:  # 60 degrees
            return None

        pos = recent_positions[len(recent_positions) // 2]
        timestamp_ms = int(pos[2] * 1000)

        x_norm = (pos[0] / frame_width) * 100.0
        y_norm = (pos[1] / frame_height) * 100.0

        return DetectedEvent(
            event_type=EventType.TURNOVER,
            timestamp_ms=timestamp_ms,
            x=x_norm,
            y=y_norm,
            confidence=0.5,
            outcome="unknown"
        )

    def process_frame(self, frame: np.ndarray, timestamp: float, 
                     frame_width: int, frame_height: int) -> List[DetectedEvent]:
        """
        Process a single frame and detect events.
        Improved version with fallback detection methods.

        Args:
            frame: Input frame
            timestamp: Timestamp in seconds
            frame_width: Frame width
            frame_height: Frame height

        Returns:
            List of detected events
        """
        events = []

        # Detect ball
        ball_detection = self.detect_ball(frame)
        if ball_detection:
            x, y, conf = ball_detection
            self.ball_positions.append((x, y, timestamp))
            # Keep only recent positions (last 5 seconds for better tracking)
            self.ball_positions = [p for p in self.ball_positions if timestamp - p[2] < 5.0]

        # Detect events based on ball movement
        if len(self.ball_positions) >= 2:  # Lowered from 3 to 2
            # Try to detect pass
            pass_event = self.detect_pass(self.ball_positions, frame_width, frame_height)
            if pass_event:
                events.append(pass_event)

            # Try to detect shot (с cooldown — один удар за окно 5 сек)
            shot_event = self.detect_shot(self.ball_positions, frame_width, frame_height)
            if shot_event:
                if self._last_shot_timestamp is None or (timestamp - self._last_shot_timestamp) >= self.shot_cooldown_seconds:
                    events.append(shot_event)
                    self._last_shot_timestamp = timestamp

            # Try to detect turnover
            turnover_event = self.detect_turnover(self.ball_positions, frame_width, frame_height)
            if turnover_event:
                events.append(turnover_event)
            
            # Try to detect set pieces (free kicks, penalties, corners)
            set_piece_event = self.detect_set_piece(self.ball_positions, frame_width, frame_height, frame)
            if set_piece_event:
                events.append(set_piece_event)

        # Fallback: Detect events based on frame differences (motion detection)
        # This works even if ball is not detected
        if self.previous_frame is not None:
            motion_events = self.detect_events_from_motion(
                self.previous_frame, frame, timestamp, frame_width, frame_height
            )
            events.extend(motion_events)

        self.previous_frame = frame.copy()

        return events

    def detect_set_piece(self, ball_positions: List[Tuple[float, float, float]],
                        frame_width: int, frame_height: int, frame: np.ndarray) -> Optional[DetectedEvent]:
        """
        Detect set piece events (free kicks, penalties, corners).
        Based on ball position near corners/edges and sudden stops.

        Args:
            ball_positions: Recent ball positions
            frame_width: Frame width
            frame_height: Frame height
            frame: Current frame for additional analysis

        Returns:
            DetectedEvent if set piece detected, None otherwise
        """
        if len(ball_positions) < 3:
            return None

        recent_positions = ball_positions[-5:]
        if len(recent_positions) < 2:
            return None

        positions = np.array([(p[0], p[1]) for p in recent_positions])
        current_pos = positions[-1]
        
        # Check if ball is near corners (corner kicks)
        corner_threshold = 0.1  # 10% from edges
        is_near_corner = (
            (current_pos[0] < frame_width * corner_threshold and 
             (current_pos[1] < frame_height * corner_threshold or 
              current_pos[1] > frame_height * (1 - corner_threshold))) or
            (current_pos[0] > frame_width * (1 - corner_threshold) and 
             (current_pos[1] < frame_height * corner_threshold or 
              current_pos[1] > frame_height * (1 - corner_threshold)))
        )
        
        # Check if ball is near edges (free kicks)
        edge_threshold = 0.05  # 5% from edges
        is_near_edge = (
            current_pos[0] < frame_width * edge_threshold or
            current_pos[0] > frame_width * (1 - edge_threshold) or
            current_pos[1] < frame_height * edge_threshold or
            current_pos[1] > frame_height * (1 - edge_threshold)
        )
        
        # Check for sudden stop (ball stopped moving - set piece setup)
        if len(positions) >= 3:
            velocities = np.diff(positions, axis=0)
            speeds = np.linalg.norm(velocities, axis=1)
            recent_speed = np.mean(speeds[-2:]) if len(speeds) >= 2 else 0
            
            # Ball stopped or moving very slowly
            if recent_speed < 5 and is_near_edge:
                # Determine type based on position
                x_norm = (current_pos[0] / frame_width) * 100.0
                y_norm = (current_pos[1] / frame_height) * 100.0
                
                timestamp_ms = int(recent_positions[-1][2] * 1000)
                
                # Corner kick - near corner (more strict)
                if is_near_corner and (x_norm < 12.0 or x_norm > 88.0):
                    return DetectedEvent(
                        event_type=EventType.CORNER,
                        timestamp_ms=timestamp_ms,
                        x=x_norm,
                        y=y_norm,
                        confidence=0.65,  # Higher confidence for corners
                        outcome="unknown"
                    )
                
                # Penalty - near center of goal line (more strict)
                elif (y_norm < 12.0 or y_norm > 88.0) and 42.0 < x_norm < 58.0:
                    return DetectedEvent(
                        event_type=EventType.PENALTY,
                        timestamp_ms=timestamp_ms,
                        x=x_norm,
                        y=y_norm,
                        confidence=0.7,  # Higher confidence for penalties
                        outcome="unknown"
                    )
                
                # Free kick - near edge but not corner (more strict)
                elif is_near_edge and not is_near_corner:
                    # Free kicks are usually along sidelines or near penalty area
                    is_along_sideline = (x_norm < 8.0 or x_norm > 92.0) and 20.0 < y_norm < 80.0
                    is_near_penalty_area = (y_norm < 18.0 or y_norm > 82.0) and 30.0 < x_norm < 70.0
                    
                    if is_along_sideline or is_near_penalty_area:
                        return DetectedEvent(
                            event_type=EventType.FREE_KICK,
                            timestamp_ms=timestamp_ms,
                            x=x_norm,
                            y=y_norm,
                            confidence=0.6,  # Higher confidence
                            outcome="unknown"
                        )
        
        return None

    def detect_events_from_motion(self, prev_frame: np.ndarray, curr_frame: np.ndarray,
                                  timestamp: float, frame_width: int, frame_height: int) -> List[DetectedEvent]:
        """
        Detect events based on motion between frames.
        Fallback method when ball detection fails.

        Args:
            prev_frame: Previous frame
            curr_frame: Current frame
            timestamp: Current timestamp
            frame_width: Frame width
            frame_height: Frame height

        Returns:
            List of detected events
        """
        events = []

        # Convert to grayscale
        prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
        curr_gray = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2GRAY)

        # Calculate frame difference
        diff = cv2.absdiff(prev_gray, curr_gray)
        _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)

        # Find motion regions
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return events

        # Find largest motion region (likely ball or player movement)
        largest_contour = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest_contour)

        # Filter by size (significant motion)
        if area < 100:  # Too small
            return events

        # Get center of motion
        M = cv2.moments(largest_contour)
        if M["m00"] == 0:
            return events

        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])

        # Normalize coordinates
        x_norm = (cx / frame_width) * 100.0
        y_norm = (cy / frame_height) * 100.0

        # Calculate motion intensity
        motion_intensity = area / (frame_width * frame_height)

        # Detect pass if motion is significant and in middle/forward areas
        if motion_intensity > 0.001 and 30 < y_norm < 70:  # Middle area
            events.append(DetectedEvent(
                event_type=EventType.PASS,
                timestamp_ms=int(timestamp * 1000),
                x=x_norm,
                y=y_norm,
                confidence=min(0.5, motion_intensity * 100),  # Lower confidence for motion-based
                outcome="unknown"
            ))

        # Detect shot if motion is near goal areas
        if motion_intensity > 0.001 and (y_norm < 20 or y_norm > 80):
            events.append(DetectedEvent(
                event_type=EventType.SHOT,
                timestamp_ms=int(timestamp * 1000),
                x=x_norm,
                y=y_norm,
                confidence=min(0.4, motion_intensity * 80),
                outcome="unknown"
            ))

        return events
