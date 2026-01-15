from typing import List, Dict, Any
from uuid import UUID

from django.db.models import QuerySet

from apps.events.models import Event
from apps.competitions.models import Match


def build_strengths(
    team_id: UUID,
    matches: QuerySet[Match],
    events: QuerySet[Event],
) -> List[Dict[str, Any]]:

    strengths: List[Dict[str, Any]] = []

    # --- Possession control ---
    team_passes = events.filter(
        team_id=team_id,
        event_type="pass",
    ).count()

    opponent_passes = events.exclude(
        team_id=team_id
    ).filter(
        event_type="pass",
    ).count()

    total_passes = team_passes + opponent_passes

    if total_passes > 0:
        possession_pct = (team_passes / total_passes) * 100

        if possession_pct >= 55:
            strengths.append({
                "code": "POSSESSION_CONTROL",
                "text": "Команда контролирует мяч большую часть времени.",
                "evidence": {
                    "possession_pct": round(possession_pct, 1),
                },
            })

    # --- High pressing activity ---
    high_def_actions = events.filter(
        team_id=team_id,
        event_type__in=["tackle", "interception"],
        x__gte=60,
    ).count()

    if high_def_actions >= 15:
        strengths.append({
            "code": "HIGH_PRESS_ACTIVITY",
            "text": "Активные оборонительные действия высоко на поле.",
            "evidence": {
                "def_actions_high_zone": high_def_actions,
            },
        })

    return strengths
