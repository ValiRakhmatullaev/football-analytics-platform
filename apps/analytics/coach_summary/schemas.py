from dataclasses import dataclass
from typing import List


# ============================================================
# Coach Summary — Output Schemas (Domain-level)
# ============================================================

@dataclass
class SnapshotSchema:
    """
    High-level snapshot of team performance over a period.
    """

    # Matches & results
    matches_played: int
    wins: int
    draws: int
    losses: int

    # Goals
    goals_for: int
    goals_against: int

    # Points
    points: int
    points_per_match: float

    # Recent form (e.g. ["W", "D", "L"])
    form: List[str]
