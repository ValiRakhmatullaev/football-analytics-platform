from typing import List, Dict, Any
from uuid import UUID

from django.db.models import QuerySet

from apps.competitions.models import Match
from apps.events.models import Event


POSSESSION_THRESHOLD = 55
HIGH_PRESS_THRESHOLD = 15


def build_strengths(
    team_id: UUID,
    matches: QuerySet[Match],
    events: QuerySet[Event],
) -> List[Dict[str, Any]]:
    """
    Builds list of team strengths based on events.
    """

    strengths: List[Dict[str, Any]] = []

    scoped_events = events.filter(match__in=matches)

    # ---------------------------------
    # Possession control (passes proxy)
    # ---------------------------------
    team_passes = scoped_events.filter(
        team_id=team_id,
        event_type="pass",
    ).count()

    opponent_passes = scoped_events.exclude(
        team_id=team_id
    ).filter(
        event_type="pass",
    ).count()

    total_passes = team_passes + opponent_passes

    if total_passes > 0:
        possession_pct = (team_passes / total_passes) * 100

        if possession_pct >= POSSESSION_THRESHOLD:
            strengths.append({
                "code": "POSSESSION_CONTROL",
                "text": "Команда контролирует мяч большую часть времени.",
                "evidence": {
                    "possession_pct": round(possession_pct, 1),
                },
            })

    # ---------------------------------
    # High pressing activity
    # ---------------------------------
    high_def_actions = scoped_events.filter(
        team_id=team_id,
        event_type__in=["tackle", "interception"],
        x__gte=60,
    ).count()

    if high_def_actions >= HIGH_PRESS_THRESHOLD:
        strengths.append({
            "code": "HIGH_PRESS_ACTIVITY",
            "text": "Активные оборонительные действия высоко на поле.",
            "evidence": {
                "def_actions_high_zone": high_def_actions,
            },
        })

    return strengths
