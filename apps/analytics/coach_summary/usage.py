from typing import Dict
from uuid import UUID

from django.apps import apps


def build_usage(team_id: UUID, matches) -> Dict:
    Appearance = apps.get_model("players", "Appearance")

    qs = Appearance.objects.filter(
        team_id=team_id,
        match__in=matches,
    )

    return {
        "players_used": qs.values("player_id").distinct().count(),
        "starts": qs.filter(started=True).count(),
    }
