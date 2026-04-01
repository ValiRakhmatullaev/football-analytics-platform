"""
Assign ball to nearest player within distance (Football-Game-Possession-Traking).
"""

from video_analytics.possession.utils_bbox import get_center_of_bbox, measure_distance


class Player_ball_assigner:
    def __init__(self):
        self.max_player_ball_distance = 70

    def ball_assigner(self, ball_bbox, players):
        ball_position = get_center_of_bbox(ball_bbox)
        minimum_distance = 99999
        assigned_player = -1

        for player_id, player in players.items():
            player_bbox = player["bbox"]
            distance_left = measure_distance((player_bbox[0], player_bbox[-1]), ball_position)
            distance_right = measure_distance((player_bbox[2], player_bbox[-1]), ball_position)
            distance = min(distance_left, distance_right)

            if distance < self.max_player_ball_distance:
                if distance < minimum_distance:
                    minimum_distance = distance
                    assigned_player = player_id

        return assigned_player
