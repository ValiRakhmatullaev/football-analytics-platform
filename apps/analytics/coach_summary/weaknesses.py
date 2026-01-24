from typing import List, Dict, Any
from uuid import UUID

from django.apps import apps
from django.db.models import QuerySet, Sum

from apps.competitions.models import Match
from apps.events.models import Event


TURNOVER_THRESHOLD = 20
LOW_TEMPO_THRESHOLD = 0.2


def build_weaknesses(
    team_id: UUID,
    matches: QuerySet[Match],
    events: QuerySet[Event],
) -> List[Dict[str, Any]]:
    """
    Builds list of team weaknesses based on events and tempo.
    """

    weaknesses: List[Dict[str, Any]] = []

    # -----------------------------
    # High turnovers (proxy)
    # -----------------------------
    turnovers = events.filter(
        team_id=team_id,
        event_type__in=["duel", "pass"],
    ).count()

    if turnovers >= TURNOVER_THRESHOLD:
        weaknesses.append({
            "code": "HIGH_TURNOVERS",
            "text": "Команда часто теряет мяч в передачах и единоборствах.",
            "evidence": {
                "turnovers": turnovers,
            },
        })

    # -----------------------------
    # Low tempo (minutes-based)
    # -----------------------------
    Appearance = apps.get_model("players", "Appearance")

    total_minutes = (
        Appearance.objects
        .filter(team_id=team_id, match__in=matches)
        .aggregate(total=Sum("minutes_played"))["total"]
        or 0
    )

    team_events = events.filter(team_id=team_id).count()

    if total_minutes > 0:
        tempo = team_events / total_minutes

        if tempo < LOW_TEMPO_THRESHOLD:
            weaknesses.append({
                "code": "LOW_TEMPO",
                "text": "Команда играет в низком темпе.",
                "evidence": {
                    "events_per_min": round(tempo, 2),
                },
            })

    return weaknesses
