from typing import Dict, List
from uuid import UUID

from django.apps import apps
from django.db.models import QuerySet

from apps.competitions.models import Match

from apps.analytics.coach_summary.schemas import SnapshotSchema


# ============================================================
# DOMAIN LOGIC (pure)
# ============================================================

def calculate_snapshot_from_results(
    results: List[Dict],
) -> SnapshotSchema:
    """
    Build snapshot metrics from per-match results.
    """

    wins = draws = losses = 0
    goals_for = goals_against = 0
    form: List[str] = []

    for r in results:
        gf = r["goals_for"]
        ga = r["goals_against"]

        goals_for += gf
        goals_against += ga

        if gf > ga:
            wins += 1
            form.append("W")
        elif gf == ga:
            draws += 1
            form.append("D")
        else:
            losses += 1
            form.append("L")

    matches_played = len(form)
    points = wins * 3 + draws
    ppm = round(points / matches_played, 2) if matches_played else 0.0

    return SnapshotSchema(
        matches_played=matches_played,
        wins=wins,
        draws=draws,
        losses=losses,
        goals_for=goals_for,
        goals_against=goals_against,
        points=points,
        points_per_match=ppm,
        form=form,
    )


# ============================================================
# INFRASTRUCTURE (Django ORM)
# ============================================================

def load_match_goal_counts(
    team_id: UUID,
    matches: QuerySet[Match],
) -> List[Dict]:
    """
    Load goals for / against per match from Event table.
    """

    Event = apps.get_model("events", "Event")

    results: List[Dict] = []

    for match in matches.order_by("kickoff_time"):
        match_events = Event.objects.filter(
            match=match,
            event_type="goal",
        )

        goals_for = match_events.filter(team_id=team_id).count()
        goals_against = match_events.exclude(team_id=team_id).count()

        results.append({
            "match_id": match.id,
            "goals_for": goals_for,
            "goals_against": goals_against,
        })

    return results


# ============================================================
# APPLICATION / USE-CASE
# ============================================================

def build_snapshot(
    team_id: UUID,
    matches: QuerySet[Match],
) -> Dict:
    """
    Build team performance snapshot for Coach Summary.
    """

    results = load_match_goal_counts(team_id, matches)
    snapshot = calculate_snapshot_from_results(results)

    # Service layer returns plain dict (API-ready)
    return snapshot.__dict__
