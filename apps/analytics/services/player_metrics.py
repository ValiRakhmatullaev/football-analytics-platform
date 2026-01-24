from typing import Dict, Tuple
from uuid import UUID

from django.apps import apps


# ============================================================
# Domain logic (pure, reusable, testable)
# ============================================================

def calculate_events_per_90(
    minutes_by_player: Dict[UUID, int],
    event_counts: Dict[UUID, int],
) -> Dict[UUID, float]:
    """
    Pure domain function.
    Calculates events per 90 minutes for each player.
    """

    per_90: Dict[UUID, float] = {}

    for player_id, minutes in minutes_by_player.items():
        if minutes <= 0:
            continue

        count = event_counts.get(player_id, 0)
        per_90[player_id] = round((count / minutes) * 90, 2)

    return per_90


# ============================================================
# Infrastructure layer (Django ORM, data access)
# ============================================================

def load_match_player_events(
    match_id: UUID,
) -> Tuple[Dict[UUID, int], Dict[UUID, int]]:
    """
    Loads minutes played and event counts per player from DB.
    Django-specific infrastructure code.
    """

    Event = apps.get_model("events", "Event")
    Appearance = apps.get_model("players", "Appearance")

    appearances = Appearance.objects.filter(
        match_id=match_id,
        minutes_played__gt=0,
    )

    minutes_by_player: Dict[UUID, int] = {
        app.player_id: app.minutes_played
        for app in appearances
    }

    if not minutes_by_player:
        return {}, {}

    events = Event.objects.filter(
        match_id=match_id,
        player_id__in=minutes_by_player.keys(),
    )

    event_counts: Dict[UUID, int] = {}

    for event in events:
        event_counts[event.player_id] = event_counts.get(event.player_id, 0) + 1

    return minutes_by_player, event_counts


# ============================================================
# Application / Use-case layer
# ============================================================

def player_events_per_90(match_id: UUID) -> Dict[UUID, float]:
    """
    Application-level use case.
    Orchestrates data loading and domain calculation.
    Public API for analytics layer.
    """

    minutes_by_player, event_counts = load_match_player_events(match_id)

    if not minutes_by_player:
        return {}

    return calculate_events_per_90(
        minutes_by_player=minutes_by_player,
        event_counts=event_counts,
    )
