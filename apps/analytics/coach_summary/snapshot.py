from typing import Dict, List
from uuid import UUID

from django.apps import apps
from django.db.models import QuerySet

from apps.competitions.models import Match
from apps.events.models import Event


def build_snapshot(
    team_id: UUID,
    matches: QuerySet[Match],
) -> Dict:
    """
    Builds snapshot based on match results.
    Goals are calculated from Event table (event_type='goal').
    """

    wins = draws = losses = 0
    goals_for = goals_against = 0
    form: List[str] = []

    for match in matches.order_by("kickoff_time"):
        match_events = Event.objects.filter(match=match)

        gf = match_events.filter(
            team_id=team_id,
            event_type="goal",
        ).count()

        ga = match_events.exclude(
            team_id=team_id
        ).filter(
            event_type="goal",
        ).count()

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

    return {
        "matches_played": matches_played,
        "wins": wins,
        "draws": draws,
        "losses": losses,
        "goals_for": goals_for,
        "goals_against": goals_against,
        "points": points,
        "points_per_match": ppm,
        "form": form,
    }
