from typing import Dict
from uuid import UUID

from django.apps import apps


def player_events_per_90(match_id: UUID) -> Dict[UUID, float]:
    """
    Calculate events per 90 minutes for each player in a match.
    """

    Event = apps.get_model("events", "Event")
    Appearance = apps.get_model("players", "Appearance")

    # Minutes played per player
    appearances = Appearance.objects.filter(match_id=match_id)

    minutes_by_player: Dict[UUID, int] = {
        app.player_id: app.minutes_played
        for app in appearances
        if app.minutes_played > 0
    }

    if not minutes_by_player:
        return {}

    # Event counts per player
    events = Event.objects.filter(
        match_id=match_id,
        player_id__in=minutes_by_player.keys(),
    )

    event_counts: Dict[UUID, int] = {}

    for event in events:
        event_counts[event.player_id] = event_counts.get(event.player_id, 0) + 1

    # Normalize per 90
    per_90: Dict[UUID, float] = {}

    for player_id, minutes in minutes_by_player.items():
        count = event_counts.get(player_id, 0)
        per_90[player_id] = round((count / minutes) * 90, 2)

    return per_90
