from typing import Dict, Iterable
from uuid import UUID

from django.apps import apps
from django.db.models import Sum


# ============================================================
# CONSTANTS (Domain knowledge)
# ============================================================

HIGH_LOAD_THRESHOLD = 0.85
MEDIUM_LOAD_THRESHOLD = 0.6
MATCH_DURATION_MIN = 90


# ============================================================
# DOMAIN LOGIC (pure)
# ============================================================

def calculate_team_load(
    total_minutes: int,
    players_used: int,
    matches_count: int,
) -> Dict:
    """
    Calculate team load level based on minutes distribution.
    """

    expected_minutes = players_used * matches_count * MATCH_DURATION_MIN

    load_ratio = (
        total_minutes / expected_minutes
        if expected_minutes > 0
        else 0
    )

    if load_ratio >= HIGH_LOAD_THRESHOLD:
        level = "high"
    elif load_ratio >= MEDIUM_LOAD_THRESHOLD:
        level = "medium"
    else:
        level = "low"

    return {
        "total_minutes": total_minutes,
        "expected_minutes": expected_minutes,
        "players_used": players_used,
        "load_ratio": round(load_ratio, 2),
        "load_level": level,
    }


# ============================================================
# INFRASTRUCTURE (Django ORM)
# ============================================================

def load_team_minutes(team_id: UUID, matches) -> int:
    Appearance = apps.get_model("players", "Appearance")

    return (
        Appearance.objects
        .filter(team_id=team_id, match__in=matches)
        .aggregate(total=Sum("minutes_played"))["total"]
        or 0
    )


def load_players_used(team_id: UUID, matches) -> int:
    Appearance = apps.get_model("players", "Appearance")

    return (
        Appearance.objects
        .filter(
            team_id=team_id,
            match__in=matches,
            minutes_played__gt=0,
        )
        .values("player_id")
        .distinct()
        .count()
    )


def count_matches(matches: Iterable) -> int:
    if hasattr(matches, "count"):
        return matches.count()
    return len(list(matches))


# ============================================================
# APPLICATION / USE-CASE
# ============================================================

def build_load(team_id: UUID, matches) -> Dict:
    """
    Build team load analytics block for Coach Summary.
    """

    total_minutes = load_team_minutes(team_id, matches)
    players_used = load_players_used(team_id, matches)
    matches_count = count_matches(matches)

    return calculate_team_load(
        total_minutes=total_minutes,
        players_used=players_used,
        matches_count=matches_count,
    )
