"""
Обогащение треков данными владения: TeamAssigner + Player_ball_assigner.
Улучшает детекцию: команда игрока и кто владеет мячом в каждом кадре.
"""

from typing import List, Optional, Tuple
from dataclasses import replace
import logging

from video_analytics.advanced_detector import Track
from video_analytics.possession.team_assigner import TeamAssigner
from video_analytics.possession.player_ball_assigner import Player_ball_assigner

try:
    import numpy as np
except ImportError:
    np = None

logger = logging.getLogger(__name__)

COCO_PERSON_ID = 0
COCO_BALL_ID = 32


class PossessionEnricher:
    """
    Обогащает треки (Track) полями team_id и has_ball с помощью
    TeamAssigner и Player_ball_assigner из модуля possession.
    """

    def __init__(self, max_player_ball_distance: float = 70.0):
        self.team_assigner = TeamAssigner()
        self.ball_assigner = Player_ball_assigner()
        if max_player_ball_distance != 70.0:
            self.ball_assigner.max_player_ball_distance = max_player_ball_distance
        self._team_color_initialized = False

    def _player_detections_from_tracks(self, tracks: List[Track]) -> dict:
        out = {}
        for t in tracks:
            if t.class_id == COCO_PERSON_ID:
                out[t.track_id] = {"bbox": list(t.bbox)}
        return out

    def _ball_bbox_from_tracks(self, tracks: List[Track]) -> Optional[List[float]]:
        for t in tracks:
            if t.class_id == COCO_BALL_ID:
                return list(t.bbox)
        return None

    def init_team_colors(self, frame, tracks: List[Track]) -> None:
        """Инициализировать цвета команд по первому кадру с игроками."""
        if self._team_color_initialized:
            return
        player_detections = self._player_detections_from_tracks(tracks)
        if not player_detections:
            return
        try:
            self.team_assigner.assign_team_color(frame, player_detections)
            self._team_color_initialized = True
            logger.info("Possession: team colors initialized from %d players", len(player_detections))
        except Exception as e:
            logger.warning("Possession: failed to init team colors: %s", e)

    def enrich_frame(
        self, frame, tracks: List[Track]
    ) -> List[Track]:
        """
        Обогащает треки кадра: team_id для игроков, has_ball для владеющего мячом.
        Возвращает новый список Track с заполненными team_id и has_ball.
        """
        if not tracks:
            return tracks

        player_detections = self._player_detections_from_tracks(tracks)
        ball_bbox = self._ball_bbox_from_tracks(tracks)

        if not self._team_color_initialized and player_detections:
            self.init_team_colors(frame, tracks)

        assigned_player_id = -1
        if ball_bbox and player_detections and self.ball_assigner:
            try:
                assigned_player_id = self.ball_assigner.ball_assigner(ball_bbox, player_detections)
            except Exception as e:
                logger.debug("Possession: ball_assigner failed: %s", e)

        result = []
        for t in tracks:
            if t.class_id == COCO_BALL_ID:
                result.append(t)
                continue
            if t.class_id == COCO_PERSON_ID:
                team_id = None
                if self._team_color_initialized:
                    try:
                        team_id = self.team_assigner.get_player_team(
                            frame, t.bbox, t.track_id
                        )
                    except Exception as e:
                        logger.debug("Possession: get_player_team failed: %s", e)
                has_ball = t.track_id == assigned_player_id
                result.append(
                    replace(t, team_id=team_id, has_ball=has_ball)
                )
            else:
                result.append(t)
        return result
