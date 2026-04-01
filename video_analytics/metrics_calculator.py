"""
Metrics calculator for team and player analytics.
Calculates all required metrics from tracking data and events.
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class TeamMetrics:
    """Team-level metrics."""
    possession_pct: float  # Владение мячом
    total_shots: int  # Общее количество ударов
    shots_on_target: int  # Удары в створ
    passes: int  # Количество передач
    pass_accuracy_pct: float  # Процент успешных передач
    recoveries: int  # Количество отборов
    turnovers: int  # Количество потерь


@dataclass
class PlayerMetrics:
    """Player-level metrics."""
    activity_index: float  # Активность (нормализованное расстояние)
    pass_score: float  # Пас (передачи вперед - назад) / всего
    pressure_resistance: float  # Устойчивость к прессингу
    zone_dominance: float  # Доминирование в зоне (атакующая треть)


class MetricsCalculator:
    """
    Calculates team and player metrics from tracking data.
    """
    
    def __init__(
        self,
        pitch_length_m: float = 105.0,
        pitch_width_m: float = 68.0,
        fps: float = 30.0,
        control_distance_threshold: float = 2.0,  # meters
        pass_reception_frames: int = 5,  # frames to consider reception
        pressure_radius: float = 2.0,  # meters
    ):
        """
        Initialize metrics calculator.
        
        Args:
            pitch_length_m: Pitch length in meters
            pitch_width_m: Pitch width in meters
            fps: Frames per second
            control_distance_threshold: Max distance for ball control (meters)
            pass_reception_frames: Frames to wait for pass reception
            pressure_radius: Radius for pressure detection (meters)
        """
        self.pitch_length_m = pitch_length_m
        self.pitch_width_m = pitch_width_m
        self.fps = fps
        self.control_distance_threshold = control_distance_threshold
        self.pass_reception_frames = pass_reception_frames
        self.pressure_radius = pressure_radius
        
        # Zone boundaries (normalized 0-100)
        self.defensive_third = (0, 33.33)
        self.middle_third = (33.33, 66.66)
        self.attacking_third = (66.66, 100)
    
    def calculate_team_metrics(
        self,
        ball_control_history: List[Dict],
        events: List[Dict],
        team_id: int,
        total_frames: int
    ) -> TeamMetrics:
        """
        Calculate team metrics.
        
        Args:
            ball_control_history: List of ball control frames
            events: List of detected events
            team_id: Team ID
            total_frames: Total number of frames
            
        Returns:
            TeamMetrics object
        """
        # 1. Possession (Владение мячом)
        team_control_frames = sum(
            1 for control in ball_control_history
            if control.get('team_id') == team_id
        )
        possession_pct = (team_control_frames / total_frames * 100) if total_frames > 0 else 0.0
        
        # 2. Total shots (Общее количество ударов)
        total_shots = sum(
            1 for event in events
            if event.get('event_type') == 'shot' and event.get('team_id') == team_id
        )
        
        # 3. Shots on target (Удары в створ)
        shots_on_target = sum(
            1 for event in events
            if (event.get('event_type') == 'shot' and
                event.get('team_id') == team_id and
                self._is_shot_on_target(event))
        )
        
        # 4. Passes (Количество передач)
        passes = sum(
            1 for event in events
            if event.get('event_type') == 'pass' and event.get('team_id') == team_id
        )
        
        # 5. Pass accuracy (Процент успешных передач)
        successful_passes = sum(
            1 for event in events
            if (event.get('event_type') == 'pass' and
                event.get('team_id') == team_id and
                event.get('metadata', {}).get('successful', False))
        )
        pass_accuracy_pct = (successful_passes / passes * 100) if passes > 0 else 0.0
        
        # 6. Recoveries (Количество отборов)
        recoveries = sum(
            1 for event in events
            if (event.get('event_type') == 'recovery' and
                event.get('team_id') == team_id and
                self._is_in_middle_or_attacking_third(event))
        )
        
        # 7. Turnovers (Количество потерь)
        turnovers = sum(
            1 for event in events
            if (event.get('event_type') == 'turnover' and
                event.get('team_id') == team_id)
        )
        
        return TeamMetrics(
            possession_pct=possession_pct,
            total_shots=total_shots,
            shots_on_target=shots_on_target,
            passes=passes,
            pass_accuracy_pct=pass_accuracy_pct,
            recoveries=recoveries,
            turnovers=turnovers
        )
    
    def calculate_player_metrics(
        self,
        player_id: int,
        team_id: int,
        player_positions: List[Tuple[float, float, int]],  # (x, y, frame_id) in meters
        ball_control_history: List[Dict],
        events: List[Dict],
        touches: List[Dict],
        position_average_distance: Optional[float] = None
    ) -> PlayerMetrics:
        """
        Calculate player metrics.
        
        Args:
            player_id: Player ID
            team_id: Team ID
            player_positions: List of player positions
            ball_control_history: Ball control history
            events: List of events
            touches: List of touches (ball control by player)
            position_average_distance: Average distance for player's position (for normalization)
            
        Returns:
            PlayerMetrics object
        """
        # 1. Activity index (Активность)
        distance_traveled = self._calculate_distance_traveled(player_positions)
        if position_average_distance and position_average_distance > 0:
            activity_index = (distance_traveled / position_average_distance) * 100
        else:
            # Fallback: normalize by match average (assume 10km average)
            activity_index = (distance_traveled / 10000.0) * 100
        
        # 2. Pass score (Пас)
        player_passes = [
            e for e in events
            if e.get('event_type') == 'pass' and e.get('player_id') == player_id
        ]
        
        forward_passes = 0
        backward_passes = 0
        
        for pass_event in player_passes:
            direction = self._get_pass_direction(pass_event)
            if -45 <= direction <= 45:  # Forward
                forward_passes += 1
            elif 135 <= direction <= 225:  # Backward
                backward_passes += 1
        
        total_passes = len(player_passes)
        pass_score = ((forward_passes - backward_passes) / total_passes) if total_passes > 0 else 0.0
        
        # 3. Pressure resistance (Устойчивость к прессингу)
        player_touches = [t for t in touches if t.get('player_id') == player_id]
        total_touches = len(player_touches)
        
        losses_under_pressure = sum(
            1 for event in events
            if (event.get('event_type') == 'turnover' and
                event.get('player_id') == player_id and
                event.get('metadata', {}).get('under_pressure', False))
        )
        
        pressure_resistance = 1.0 - (losses_under_pressure / total_touches) if total_touches > 0 else 0.0
        
        # 4. Zone dominance (Доминирование в зоне)
        attacking_touches = sum(
            1 for touch in player_touches
            if self._is_in_attacking_third(touch.get('position'))
        )
        zone_dominance = (attacking_touches / total_touches * 100) if total_touches > 0 else 0.0
        
        return PlayerMetrics(
            activity_index=activity_index,
            pass_score=pass_score,
            pressure_resistance=pressure_resistance,
            zone_dominance=zone_dominance
        )
    
    def _calculate_distance_traveled(self, positions: List[Tuple[float, float, int]]) -> float:
        """Calculate total distance traveled in meters."""
        if len(positions) < 2:
            return 0.0
        
        total_distance = 0.0
        for i in range(1, len(positions)):
            x1, y1, _ = positions[i-1]
            x2, y2, _ = positions[i]
            distance = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            total_distance += distance
        
        return total_distance
    
    def _is_shot_on_target(self, shot_event: Dict) -> bool:
        """Check if shot is on target."""
        end_position = shot_event.get('end_position')
        if not end_position:
            return False
        
        # Goal is typically at y=0 or y=100 (normalized)
        # Goal width is approximately 7.32m, pitch width is 68m
        # So goal spans from ~46.6% to 53.4% of width (normalized)
        goal_left = 46.6
        goal_right = 53.4
        
        x, y = end_position
        # Check if ball crosses goal line (y near 0 or 100) and within goal width
        if (y < 5 or y > 95) and (goal_left <= x <= goal_right):
            return True
        
        return False
    
    def _is_in_middle_or_attacking_third(self, event: Dict) -> bool:
        """Check if event is in middle or attacking third."""
        position = event.get('start_position') or event.get('end_position')
        if not position:
            return False
        
        _, y = position
        return self.middle_third[0] <= y <= self.attacking_third[1]
    
    def _is_in_attacking_third(self, position: Optional[Tuple[float, float]]) -> bool:
        """Check if position is in attacking third."""
        if not position:
            return False
        
        _, y = position
        return self.attacking_third[0] <= y <= self.attacking_third[1]
    
    def _get_pass_direction(self, pass_event: Dict) -> float:
        """Get pass direction in degrees (0 = forward, 180 = backward)."""
        start_pos = pass_event.get('start_position')
        end_pos = pass_event.get('end_position')
        
        if not start_pos or not end_pos:
            return 0.0
        
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]
        
        # Calculate angle in degrees
        angle = np.degrees(np.arctan2(dy, dx))
        
        # Normalize to 0-360
        if angle < 0:
            angle += 360
        
        return angle
