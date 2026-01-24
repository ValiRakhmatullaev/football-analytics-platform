from typing import Dict, Tuple
from uuid import UUID

from django.apps import apps


# ============================================================
# Domain logic (pure functions, no Django dependencies)
# ============================================================

def calculate_team_possession(
    team_event_counts: Dict[UUID, int],
    total_events: int,
) -> Dict[UUID, float]:
    """
    Calculate possession percentage per team.
    """

    if total_events == 0:
        return {}

    return {
        team_id: round((count / total_events) * 100, 1)
        for team_id, count in team_event_counts.items()
    }


def calculate_event_tempo(
    total_events: int,
    duration_minutes: int = 90,
) -> float:
    """
    Calculate match tempo as events per minute.
    """

    if total_events == 0 or duration_minutes <= 0:
        return 0.0

    return round(total_events / duration_minutes, 2)


def calculate_team_turnovers(
    team_event_counts: Dict[UUID, int],
) -> Dict[UUID, int]:
    """
    Return turnovers per team (identity function for clarity).
    """

    return dict(team_event_counts)


# ============================================================
# Infrastructure layer (Django ORM, data loading)
# ============================================================

def load_team_ball_control_events(
    match_id: UUID,
) -> Tuple[Dict[UUID, int], int]:
    """
    Load ball-control events (passes + shots) per team.
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

    team_event_counts: Dict[UUID, int] = {}

    for event in events:
        team_event_counts[event.team_id] = (
            team_event_counts.get(event.team_id, 0) + 1
        )

    return team_event_counts, events.count()


def load_total_events_count(match_id: UUID) -> int:
    """
    Load total number of events in a match.
    """

    Event = apps.get_model("events", "Event")

    return Event.objects.filter(match_id=match_id).count()


def load_team_turnovers(match_id: UUID) -> Dict[UUID, int]:
    """
    Load turnovers per team.
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


# ============================================================
# Application / Use-case layer (public API)
# ============================================================

def team_possession(match_id: UUID) -> Dict[UUID, float]:
    """
    Application use-case: team possession (%).
    """

    team_event_counts, total_events = load_team_ball_control_events(match_id)

    return calculate_team_possession(
        team_event_counts=team_event_counts,
        total_events=total_events,
    )


def event_tempo(match_id: UUID) -> float:
    """
    Application use-case: match tempo (events per minute).
    """

    total_events = load_total_events_count(match_id)

    # MVP assumption: standard 90-minute match
    return calculate_event_tempo(
        total_events=total_events,
        duration_minutes=90,
    )


def team_turnovers(match_id: UUID) -> Dict[UUID, int]:
    """
    Application use-case: turnovers per team.
    """

    team_event_counts = load_team_turnovers(match_id)

    return calculate_team_turnovers(team_event_counts)
