from typing import Dict
from uuid import UUID

from django.apps import apps


def team_possession(match_id: UUID) -> Dict[UUID, float]:
    """
    Calculate team possession as percentage of ball-control events.

    Possession is approximated by count of ball-control events
    (passes + shots) per team.
    """

    Event = apps.get_model("events", "Event")

    BALL_CONTROL_EVENTS = {
        Event.Type.PASS,
        Event.Type.SHOT,
    }

    events = Event.objects.filter(
        match_id=match_id,
        event_type__in=BALL_CONTROL_EVENTS,
    )

    total_events = events.count()
    if total_events == 0:
        return {}

    team_event_counts: Dict[UUID, int] = {}

    for event in events:
        team_event_counts[event.team_id] = (
            team_event_counts.get(event.team_id, 0) + 1
        )

    return {
        team_id: round((count / total_events) * 100, 1)
        for team_id, count in team_event_counts.items()
    }

from django.apps import apps


def event_tempo(match_id):
    """
    Calculate match tempo as number of events per minute.
    """

    Event = apps.get_model("events", "Event")
    Match = apps.get_model("competitions", "Match")

    total_events = Event.objects.filter(match_id=match_id).count()

    match = Match.objects.get(id=match_id)

    # MVP допущение: стандартный матч 90 минут
    duration_minutes = 90

    if total_events == 0:
        return 0.0

    return round(total_events / duration_minutes, 2)

from typing import Dict
from uuid import UUID

from django.apps import apps


def team_turnovers(match_id: UUID) -> Dict[UUID, int]:
    """
    Count turnovers per team in a match.
    """

    Event = apps.get_model("events", "Event")

    events = Event.objects.filter(
        match_id=match_id,
        event_type=Event.Type.TURNOVER,
    )

    turnovers: Dict[UUID, int] = {}

    for event in events:
        turnovers[event.team_id] = turnovers.get(event.team_id, 0) + 1

    return turnovers
