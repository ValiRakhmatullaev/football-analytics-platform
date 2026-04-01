import unittest
from dataclasses import dataclass
from typing import Tuple

from video_analytics.football_events import FootballEventDetector, FrameInfo


@dataclass
class Track:
    track_id: int
    bbox: Tuple[float, float, float, float]
    confidence: float
    class_id: int
    class_name: str
    frame_id: int


def _bbox_centered(cx: float, cy: float, size: float = 10.0):
    half = size / 2.0
    return (cx - half, cy - half, cx + half, cy + half)


class FootballEventDetectorGoalTests(unittest.TestCase):
    def setUp(self):
        self.w = 1280
        self.h = 720
        self.detector = FootballEventDetector(
            goal_line_top_ratio=0.045,
            goal_line_bottom_ratio=0.955,
            goal_mouth_left_ratio=0.25,
            goal_mouth_right_ratio=0.75,
            goal_min_speed_threshold=30.0,
            ball_control_px=150.0,
            temporal_frames=8,
            goal_cooldown_frames=10,
        )

    def _frame_info(self, t: float, frame_id: int) -> FrameInfo:
        return FrameInfo(
            timestamp_sec=t,
            frame_id=frame_id,
            fps=25.0,
            width=self.w,
            height=self.h,
        )

    def _tracks(self, ball_x: float, ball_y: float, player_x: float, player_y: float, frame_id: int):
        ball = Track(
            track_id=1,
            bbox=_bbox_centered(ball_x, ball_y, size=8.0),
            confidence=0.9,
            class_id=32,
            class_name="ball",
            frame_id=frame_id,
        )
        player = Track(
            track_id=10,
            bbox=_bbox_centered(player_x, player_y, size=40.0),
            confidence=0.9,
            class_id=0,
            class_name="person",
            frame_id=frame_id,
        )
        return [ball, player]

    def test_goal_emitted_when_crosses_line_inside_goal_mouth_with_speed(self):
        top_line = self.h * 0.045
        x_in_mouth = self.w * 0.5

        prev_tracks = None
        events_all = []

        # Warm-up frames (detector needs a small history before it starts emitting events)
        tracks0 = self._tracks(x_in_mouth, top_line + 40, x_in_mouth, top_line + 60, frame_id=0)
        events_all.extend(self.detector.detect_events(tracks0, prev_tracks, self._frame_info(0.0, 0)))
        prev_tracks = tracks0

        tracks1 = self._tracks(x_in_mouth, top_line + 25, x_in_mouth, top_line + 60, frame_id=1)
        events_all.extend(self.detector.detect_events(tracks1, prev_tracks, self._frame_info(0.1, 1)))
        prev_tracks = tracks1

        # Frame 2: ball on the pitch (just below the goal line)
        tracks2 = self._tracks(x_in_mouth, top_line + 10, x_in_mouth, top_line + 60, frame_id=2)
        events_all.extend(self.detector.detect_events(tracks2, prev_tracks, self._frame_info(0.2, 2)))
        prev_tracks = tracks2

        # Frame 3: ball crosses the line (just above the line) with enough speed
        tracks3 = self._tracks(x_in_mouth, top_line - 10, x_in_mouth, top_line + 60, frame_id=3)
        events_all.extend(self.detector.detect_events(tracks3, prev_tracks, self._frame_info(0.3, 3)))

        goals = [e for e in events_all if e.event_type == "goal"]
        self.assertEqual(len(goals), 1)
        self.assertEqual(goals[0].metadata.get("goal_line"), "top")

    def test_goal_not_emitted_when_crosses_line_outside_goal_mouth(self):
        top_line = self.h * 0.045
        x_outside_mouth = self.w * 0.05

        prev_tracks = None
        events_all = []

        tracks0 = self._tracks(x_outside_mouth, top_line + 40, x_outside_mouth, top_line + 60, frame_id=0)
        events_all.extend(self.detector.detect_events(tracks0, prev_tracks, self._frame_info(0.0, 0)))
        prev_tracks = tracks0

        tracks1 = self._tracks(x_outside_mouth, top_line + 25, x_outside_mouth, top_line + 60, frame_id=1)
        events_all.extend(self.detector.detect_events(tracks1, prev_tracks, self._frame_info(0.1, 1)))
        prev_tracks = tracks1

        tracks2 = self._tracks(x_outside_mouth, top_line + 10, x_outside_mouth, top_line + 60, frame_id=2)
        events_all.extend(self.detector.detect_events(tracks2, prev_tracks, self._frame_info(0.2, 2)))
        prev_tracks = tracks2

        tracks3 = self._tracks(x_outside_mouth, top_line - 10, x_outside_mouth, top_line + 60, frame_id=3)
        events_all.extend(self.detector.detect_events(tracks3, prev_tracks, self._frame_info(0.3, 3)))

        goals = [e for e in events_all if e.event_type == "goal"]
        self.assertEqual(len(goals), 0)

    def test_goal_not_emitted_when_crossing_speed_too_low(self):
        top_line = self.h * 0.045
        x_in_mouth = self.w * 0.5

        prev_tracks = None
        events_all = []

        # Warm-up + very slow movement across the line over long time => low speed
        tracks0 = self._tracks(x_in_mouth, top_line + 40, x_in_mouth, top_line + 60, frame_id=0)
        events_all.extend(self.detector.detect_events(tracks0, prev_tracks, self._frame_info(0.0, 0)))
        prev_tracks = tracks0

        tracks1 = self._tracks(x_in_mouth, top_line + 25, x_in_mouth, top_line + 60, frame_id=1)
        events_all.extend(self.detector.detect_events(tracks1, prev_tracks, self._frame_info(0.5, 1)))
        prev_tracks = tracks1

        tracks2 = self._tracks(x_in_mouth, top_line + 1, x_in_mouth, top_line + 60, frame_id=2)
        events_all.extend(self.detector.detect_events(tracks2, prev_tracks, self._frame_info(1.0, 2)))
        prev_tracks = tracks2

        tracks3 = self._tracks(x_in_mouth, top_line - 1, x_in_mouth, top_line + 60, frame_id=3)
        events_all.extend(self.detector.detect_events(tracks3, prev_tracks, self._frame_info(2.5, 3)))

        goals = [e for e in events_all if e.event_type == "goal"]
        self.assertEqual(len(goals), 0)


if __name__ == "__main__":
    unittest.main()
