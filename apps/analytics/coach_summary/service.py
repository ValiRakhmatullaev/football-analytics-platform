from uuid import UUID
from typing import Dict

from django.apps import apps

from apps.analytics.coach_summary.snapshot import build_snapshot
from apps.analytics.coach_summary.tactics import build_tactical_identity
from apps.analytics.coach_summary.strengths import build_strengths
from apps.analytics.coach_summary.weaknesses import build_weaknesses
from apps.analytics.coach_summary.load import build_load
from apps.analytics.coach_summary.usage import build_usage



def build_coach_summary(
    team_id: UUID,
    matches_limit: int = 5,
) -> Dict:
    """
    Aggregates full Coach Summary for Coach View.
    Orchestrator only. No analytics logic here.
    """

    Match = apps.get_model("competitions", "Match")
    MatchTeam = apps.get_model("competitions", "MatchTeam")
    Event = apps.get_model("events", "Event")

    # --- 1. Collect recent matches ---
    match_ids = (
        MatchTeam.objects
        .filter(team_id=team_id)
        .order_by("-match__kickoff_time")
        .values_list("match_id", flat=True)[:matches_limit]
    )

    matches = Match.objects.filter(id__in=match_ids)
    events = Event.objects.filter(match_id__in=match_ids)

    # --- 2. Build blocks ---
    snapshot = build_snapshot(team_id, matches)
    tactical_identity = build_tactical_identity(team_id, matches, events)
    strengths = build_strengths(team_id, matches, events)
    weaknesses = build_weaknesses(team_id, matches, events)
    load = build_load(team_id, matches)
    usage = build_usage(team_id, matches)

    # --- 3. Final response ---
    return {
        "team_id": str(team_id),
        "range": f"last_{matches_limit}",
        "snapshot": snapshot,
        "tactical_identity": tactical_identity,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "load": load,
        "usage": usage,
        "confidence": "medium",
        "limitations": [
            "Анализ основан на событийных данных.",
            "Метрики отражают поведение, а не качество.",
        ],
    }
