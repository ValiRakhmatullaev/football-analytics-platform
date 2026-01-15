from typing import List, Dict, Any
from uuid import UUID

from django.db.models import QuerySet

from apps.events.models import Event
from apps.competitions.models import Match


def build_weaknesses(
    team_id: UUID,
    matches: QuerySet[Match],
    events: QuerySet[Event],
) -> List[Dict[str, Any]]:

    weaknesses: List[Dict[str, Any]] = []

    # --- High turnovers ---
    turnovers = events.filter(
        team_id=team_id,
        event_type="turnover",
    ).count()

    if turnovers >= 20:
        weaknesses.append({
            "code": "HIGH_TURNOVERS",
            "text": "Команда часто теряет мяч.",
            "evidence": {
                "turnovers": turnovers,
            },
        })

    # --- Low tempo ---
    MATCH_DURATION_MIN = 90
    total_minutes = len(matches) * MATCH_DURATION_MIN

    team_events = events.filter(team_id=team_id).count()

    if total_minutes > 0:
        tempo = team_events / total_minutes

        if tempo < 0.2:
            weaknesses.append({
                "code": "LOW_TEMPO",
                "text": "Низкий темп игры.",
                "evidence": {
                    "events_per_min": round(tempo, 2),
                },
            })

    return weaknesses
