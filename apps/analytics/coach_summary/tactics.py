from typing import Dict, Any
from uuid import UUID

from django.db.models import QuerySet, Avg

from apps.competitions.models import Match
from apps.events.models import Event


# =========================
# Utils
# =========================

def safe_divide(a: float, b: float) -> float:
    return a / b if b else 0.0


def label_by_thresholds(value: float, thresholds: dict) -> str:
    for label, (min_v, max_v) in thresholds.items():
        if min_v <= value < max_v:
            return label
    return list(thresholds.keys())[-1]


# =========================
# Public API
# =========================

def build_tactical_identity(
    team_id: UUID,
    matches: QuerySet[Match],
    events: QuerySet[Event],
) -> Dict[str, Any]:
    """
    Fixes factual team behaviour based on events.
    NOT a quality judgment.
    """

    return {
        "ppda": calculate_ppda(team_id, events),
        "possession": calculate_possession(team_id, events),
        "defensive_line": calculate_defensive_line(team_id, events),
        "tempo": calculate_tempo(team_id, events, matches),
    }


# =========================
# Metrics
# =========================

def calculate_ppda(
    team_id: UUID,
    events: QuerySet[Event],
) -> Dict[str, Any]:
    """
    PPDA = opponent passes / team defensive actions
    Calculated in attacking 60% of the pitch
    """

    opponent_passes = events.exclude(
        team_id=team_id
    ).filter(
        event_type="pass",
        x__gte=40,
    ).count()

    defensive_actions = events.filter(
        team_id=team_id,
        event_type__in=["tackle", "interception", "foul"],
        x__gte=40,
    ).count()

    value = safe_divide(opponent_passes, defensive_actions)

    label = label_by_thresholds(
        value,
        {
            "high": (0, 8),
            "medium": (8, 12),
            "low": (12, 10_000),
        },
    )

    explanation = {
        "high": "Aggressive pressing in opponent half",
        "medium": "Moderate pressing intensity",
        "low": "Low pressing, compact defensive shape",
    }[label]

    return {
        "value": round(value, 2),
        "label": label,
        "explanation": explanation,
    }


def calculate_possession(
    team_id: UUID,
    events: QuerySet[Event],
) -> Dict[str, Any]:
    """
    Possession = team passes / total passes
    """

    team_passes = events.filter(
        team_id=team_id,
        event_type="pass",
    ).count()

    opponent_passes = events.exclude(
        team_id=team_id
    ).filter(
        event_type="pass",
    ).count()

    possession = safe_divide(
        team_passes,
        team_passes + opponent_passes,
    ) * 100

    label = label_by_thresholds(
        possession,
        {
            "dominant": (55, 100),
            "balanced": (45, 55),
            "reactive": (0, 45),
        },
    )

    explanation = {
        "dominant": "Controls the game through possession",
        "balanced": "Balanced possession approach",
        "reactive": "Plays mostly without the ball",
    }[label]

    return {
        "value": round(possession, 1),
        "label": label,
        "explanation": explanation,
    }


def calculate_defensive_line(
    team_id: UUID,
    events: QuerySet[Event],
) -> Dict[str, Any]:
    """
    Defensive line height = average X of team defensive actions
    Field assumed 0–100
    """

    avg_x = (
        events.filter(
            team_id=team_id,
            event_type__in=["tackle", "interception"],
        )
        .aggregate(avg_x=Avg("x"))
        .get("avg_x")
        or 0.0
    )

    label = label_by_thresholds(
        avg_x,
        {
            "high": (60, 100),
            "medium": (45, 60),
            "deep": (0, 45),
        },
    )

    explanation = {
        "high": "High defensive line",
        "medium": "Mid-block defensive structure",
        "deep": "Deep defensive block",
    }[label]

    return {
        "value": round(avg_x, 1),
        "label": label,
        "explanation": explanation,
    }


def calculate_tempo(
    team_id: UUID,
    events: QuerySet[Event],
    matches: QuerySet[Match],
) -> Dict[str, Any]:
    """
    Tempo = team passes per minute
    """

    MATCH_DURATION_MIN = 90
    total_minutes = len(matches) * MATCH_DURATION_MIN

    team_passes = events.filter(
        team_id=team_id,
        event_type="pass",
    ).count()

    tempo = safe_divide(team_passes, total_minutes)

    label = label_by_thresholds(
        tempo,
        {
            "fast": (15, 10_000),
            "normal": (11, 15),
            "slow": (0, 11),
        },
    )

    explanation = {
        "fast": "Fast ball circulation",
        "normal": "Normal game tempo",
        "slow": "Slow build-up play",
    }[label]

    return {
        "value": round(tempo, 2),
        "label": label,
        "explanation": explanation,
    }
