from typing import Dict, Any
from uuid import UUID

from django.apps import apps
from django.db.models import QuerySet, Avg

from apps.competitions.models import Match


# ============================================================
# CONSTANTS (Domain knowledge)
# ============================================================

MATCH_DURATION_MIN = 90


# ============================================================
# DOMAIN UTILS (pure)
# ============================================================

def safe_divide(a: float, b: float) -> float:
    return a / b if b else 0.0


def label_by_thresholds(value: float, thresholds: Dict[str, tuple]) -> str:
    for label, (min_v, max_v) in thresholds.items():
        if min_v <= value < max_v:
            return label
    return list(thresholds.keys())[-1]


# ============================================================
# DOMAIN METRICS (pure)
# ============================================================

def evaluate_ppda(
    opponent_passes: int,
    defensive_actions: int,
) -> Dict[str, Any]:
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


def evaluate_possession(
    team_passes: int,
    opponent_passes: int,
) -> Dict[str, Any]:
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


def evaluate_defensive_line(
    avg_x: float,
) -> Dict[str, Any]:
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


def evaluate_tempo(
    team_passes: int,
    matches_count: int,
) -> Dict[str, Any]:
    total_minutes = matches_count * MATCH_DURATION_MIN
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


# ============================================================
# INFRASTRUCTURE (Django ORM)
# ============================================================

def load_ppda_data(
    team_id: UUID,
    matches: QuerySet[Match],
) -> tuple[int, int]:
    Event = apps.get_model("events", "Event")

    opponent_passes = (
        Event.objects
        .filter(
            match__in=matches,
            event_type="pass",
            x__gte=40,
        )
        .exclude(team_id=team_id)
        .count()
    )

    defensive_actions = (
        Event.objects
        .filter(
            match__in=matches,
            team_id=team_id,
            event_type__in=["tackle", "interception", "foul"],
            x__gte=40,
        )
        .count()
    )

    return opponent_passes, defensive_actions


def load_pass_counts(
    team_id: UUID,
    matches: QuerySet[Match],
) -> tuple[int, int]:
    Event = apps.get_model("events", "Event")

    team_passes = (
        Event.objects
        .filter(
            match__in=matches,
            team_id=team_id,
            event_type="pass",
        )
        .count()
    )

    opponent_passes = (
        Event.objects
        .filter(
            match__in=matches,
            event_type="pass",
        )
        .exclude(team_id=team_id)
        .count()
    )

    return team_passes, opponent_passes


def load_defensive_line_x(
    team_id: UUID,
    matches: QuerySet[Match],
) -> float:
    Event = apps.get_model("events", "Event")

    return (
        Event.objects
        .filter(
            match__in=matches,
            team_id=team_id,
            event_type__in=["tackle", "interception"],
        )
        .aggregate(avg_x=Avg("x"))
        .get("avg_x")
        or 0.0
    )


# ============================================================
# APPLICATION / USE-CASE
# ============================================================

def build_tactical_identity(
    team_id: UUID,
    matches: QuerySet[Match],
) -> Dict[str, Any]:
    """
    Build tactical identity block for Coach Summary.
    This describes HOW the team plays, not how well.
    """

    opponent_passes, defensive_actions = load_ppda_data(team_id, matches)
    team_passes, opponent_passes_all = load_pass_counts(team_id, matches)
    avg_def_line_x = load_defensive_line_x(team_id, matches)

    return {
        "ppda": evaluate_ppda(opponent_passes, defensive_actions),
        "possession": evaluate_possession(
            team_passes,
            opponent_passes_all,
        ),
        "defensive_line": evaluate_defensive_line(avg_def_line_x),
        "tempo": evaluate_tempo(
            team_passes,
            matches.count(),
        ),
    }
