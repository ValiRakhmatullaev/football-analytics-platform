"""
Advanced event detection based on tracking data.
Detects passes, shots, recoveries, turnovers.
"""

import numpy as np
import cv2
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class Event:
    """Detected event."""
    event_type: str  # "pass", "shot", "recovery", "turnover"
    frame_id: int
    player_id: Optional[int] = None
    team_id: Optional[int] = None
    start_position: Optional[Tuple[float, float]] = None
    end_position: Optional[Tuple[float, float]] = None
    target_player_id: Optional[int] = None
    confidence: float = 0.0
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class AdvancedEventDetector:
    """
    Detects football events from tracking data.
    """
    
    def __init__(
        self,
        ball_control_threshold: float = 2.0,  # meters
        pass_speed_threshold: float = 5.0,  # m/s
        shot_speed_threshold: float = 10.0,  # m/s
        pass_distance_threshold: float = 3.0,  # meters
        control_frames: int = 5,  # frames to consider control
    ):
        """
        Initialize event detector.
        
        Args:
            ball_control_threshold: Max distance for ball control (meters)
            pass_speed_threshold: Min speed for pass (m/s)
            shot_speed_threshold: Min speed for shot (m/s)
            pass_distance_threshold: Min distance for pass (meters)
            control_frames: Frames to maintain control
        """
        self.ball_control_threshold = ball_control_threshold
        self.pass_speed_threshold = pass_speed_threshold
        self.shot_speed_threshold = shot_speed_threshold
        self.pass_distance_threshold = pass_distance_threshold
        self.control_frames = control_frames
        
        # State tracking
        self.ball_control_history: List[Dict] = []  # [{frame_id, player_id, team_id, position}, ...]
        self.player_positions: Dict[int, List[Tuple[float, float]]] = defaultdict(list)
        self.ball_positions: List[Tuple[float, float, int]] = []  # (x, y, frame_id)
    
    def update_ball_control(self, frame_id: int, ball_control: Dict, teams: Dict[int, int]):
        """
        Update ball control history.
        
        Args:
            frame_id: Current frame
            ball_control: Ball control info {player_id, position, distance}
            teams: Mapping of player_id -> team_id
        """
        if ball_control and ball_control.get('player_id'):
            player_id = ball_control['player_id']
            team_id = teams.get(player_id)
            
            self.ball_control_history.append({
                'frame_id': frame_id,
                'player_id': player_id,
                'team_id': team_id,
                'position': ball_control.get('position'),
                'distance': ball_control.get('distance', 0)
            })
            
            # Keep only recent history
            if len(self.ball_control_history) > 100:
                self.ball_control_history = self.ball_control_history[-100:]
    
    def update_positions(self, tracks: List, homography: Optional[np.ndarray] = None):
        """
        Update player and ball positions.
        
        Args:
            tracks: List of tracked objects
            homography: Optional homography matrix for pitch calibration
        """
        for track in tracks:
            x1, y1, x2, y2 = track.bbox
            center = ((x1 + x2) / 2, (y1 + y2) / 2)
            
            # Transform to pitch coordinates if homography available
            if homography is not None:
                try:
                    point = np.array([[center[0], center[1]]], dtype=np.float32)
                    point = point.reshape(-1, 1, 2)
                    transformed = cv2.perspectiveTransform(point, homography)
                    center = (float(transformed[0][0][0]), float(transformed[0][0][1]))
                except:
                    pass
            
            if track.class_name == "ball":
                self.ball_positions.append((center[0], center[1], track.frame_id))
                if len(self.ball_positions) > 100:
                    self.ball_positions = self.ball_positions[-100:]
            else:
                self.player_positions[track.track_id].append((center[0], center[1], track.frame_id))
                if len(self.player_positions[track.track_id]) > 50:
                    self.player_positions[track.track_id] = self.player_positions[track.track_id][-50:]
    
    def detect_pass(self, frame_id: int, current_control: Dict, teams: Dict[int, int]) -> Optional[Event]:
        """
        Detect pass event.
        
        Pass: Player A controls ball, then ball moves to Player B (same team).
        """
        if len(self.ball_control_history) < self.control_frames * 2:
            return None
        
        # Get recent control history
        recent_history = self.ball_control_history[-self.control_frames * 2:]
        
        # Check for control change between players of same team
        if len(recent_history) < 2:
            return None
        
        # Find control transitions
        for i in range(len(recent_history) - 1):
            prev = recent_history[i]
            curr = recent_history[i + 1]
            
            if (prev['player_id'] != curr['player_id'] and
                prev['team_id'] is not None and
                curr['team_id'] is not None and
                prev['team_id'] == curr['team_id']):
                
                # Check ball speed (pass should have significant movement)
                if prev['position'] and curr['position']:
                    dx = curr['position'][0] - prev['position'][0]
                    dy = curr['position'][1] - prev['position'][1]
                    distance = np.sqrt(dx**2 + dy**2)
                    
                    # Estimate speed (assuming ~30 fps)
                    speed = distance * 30  # pixels per second
                    
                    if speed > self.pass_speed_threshold * 10:  # Convert m/s to pixels (rough)
                        return Event(
                            event_type="pass",
                            frame_id=frame_id,
                            player_id=prev['player_id'],
                            team_id=prev['team_id'],
                            start_position=prev['position'],
                            end_position=curr['position'],
                            target_player_id=curr['player_id'],
                            confidence=min(1.0, speed / (self.pass_speed_threshold * 20)),
                            metadata={'speed': speed, 'distance': distance}
                        )
        
        return None
    
    def detect_shot(self, frame_id: int, current_control: Dict, goal_positions: Tuple) -> Optional[Event]:
        """
        Detect shot event.
        
        Shot: Ball moves with high speed toward goal area.
        """
        if len(self.ball_positions) < 5:
            return None
        
        # Get recent ball positions
        recent_positions = [p for p in self.ball_positions if p[2] >= frame_id - 10]
        if len(recent_positions) < 3:
            return None
        
        # Calculate ball velocity
        positions = np.array([(p[0], p[1]) for p in recent_positions])
        velocities = np.diff(positions, axis=0)
        speeds = np.linalg.norm(velocities, axis=1) * 30  # pixels per second
        
        avg_speed = np.mean(speeds)
        
        if avg_speed < self.shot_speed_threshold * 10:  # Convert to pixels
            return None
        
        # Check direction toward goal
        goal_top, goal_bottom = goal_positions
        current_pos = positions[-1]
        
        # Check if moving toward goal
        y_velocity = np.mean(np.diff(positions[:, 1])) * 30
        
        # Goal is typically at top or bottom
        near_goal = (current_pos[1] < goal_top or current_pos[1] > goal_bottom)
        
        if abs(y_velocity) > 5 and near_goal:
            controlling_player = None
            if current_control and current_control.get('player_id'):
                controlling_player = current_control['player_id']
            
            return Event(
                event_type="shot",
                frame_id=frame_id,
                player_id=controlling_player,
                start_position=tuple(positions[0]),
                end_position=tuple(positions[-1]),
                confidence=min(1.0, avg_speed / (self.shot_speed_threshold * 20)),
                metadata={'speed': avg_speed, 'y_velocity': y_velocity}
            )
        
        return None
    
    def detect_recovery(self, frame_id: int, current_control: Dict, teams: Dict[int, int]) -> Optional[Event]:
        """
        Detect recovery (ball won back).
        
        Recovery: Control changes from opponent team to our team.
        """
        if len(self.ball_control_history) < self.control_frames:
            return None
        
        recent_history = self.ball_control_history[-self.control_frames:]
        
        # Check for control change between different teams
        if len(recent_history) < 2:
            return None
        
        for i in range(len(recent_history) - 1):
            prev = recent_history[i]
            curr = recent_history[i + 1]
            
            if (prev['team_id'] is not None and
                curr['team_id'] is not None and
                prev['team_id'] != curr['team_id']):
                
                return Event(
                    event_type="recovery",
                    frame_id=frame_id,
                    player_id=curr['player_id'],
                    team_id=curr['team_id'],
                    start_position=prev.get('position'),
                    end_position=curr.get('position'),
                    confidence=0.7,
                    metadata={'from_team': prev['team_id'], 'to_team': curr['team_id']}
                )
        
        return None
    
    def detect_turnover(self, frame_id: int, current_control: Dict, teams: Dict[int, int], 
                       defensive_third: Tuple) -> Optional[Event]:
        """
        Detect turnover (ball lost).
        
        Turnover: Control changes from our team to opponent team in defensive third.
        """
        if len(self.ball_control_history) < self.control_frames:
            return None
        
        recent_history = self.ball_control_history[-self.control_frames:]
        
        if len(recent_history) < 2:
            return None
        
        for i in range(len(recent_history) - 1):
            prev = recent_history[i]
            curr = recent_history[i + 1]
            
            # Check if in defensive third
            if prev.get('position'):
                y_pos = prev['position'][1]
                if not (defensive_third[0] <= y_pos <= defensive_third[1]):
                    continue
            
            if (prev['team_id'] is not None and
                curr['team_id'] is not None and
                prev['team_id'] != curr['team_id']):
                
                return Event(
                    event_type="turnover",
                    frame_id=frame_id,
                    player_id=prev['player_id'],
                    team_id=prev['team_id'],
                    start_position=prev.get('position'),
                    end_position=curr.get('position'),
                    confidence=0.7,
                    metadata={'from_team': prev['team_id'], 'to_team': curr['team_id']}
                )
        
        return None
    
    def process_frame(
        self,
        frame_id: int,
        tracks: List,
        ball_control: Dict,
        teams: Dict[int, int],
        homography: Optional[np.ndarray] = None,
        goal_positions: Tuple = (0, 100),
        defensive_third: Tuple = (0, 33)
    ) -> List[Event]:
        """
        Process frame and detect events.
        
        Returns:
            List of detected events
        """
        events = []
        
        # Update positions
        self.update_positions(tracks, homography)
        
        # Update ball control
        self.update_ball_control(frame_id, ball_control, teams)
        
        # Detect events
        pass_event = self.detect_pass(frame_id, ball_control, teams)
        if pass_event:
            events.append(pass_event)
        
        shot_event = self.detect_shot(frame_id, ball_control, goal_positions)
        if shot_event:
            events.append(shot_event)
        
        recovery_event = self.detect_recovery(frame_id, ball_control, teams)
        if recovery_event:
            events.append(recovery_event)
        
        turnover_event = self.detect_turnover(frame_id, ball_control, teams, defensive_third)
        if turnover_event:
            events.append(turnover_event)
        
        return events
