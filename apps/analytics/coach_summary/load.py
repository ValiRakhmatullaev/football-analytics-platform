from typing import Dict
from uuid import UUID

from django.apps import apps


def build_load(team_id: UUID, matches) -> Dict:
    Appearance = apps.get_model("players", "Appearance")

    minutes_qs = Appearance.objects.filter(
        team_id=team_id,
        match__in=matches,
    ).values_list("minutes_played", flat=True)

    total_minutes = sum(minutes_qs) if minutes_qs else 0

    if total_minutes > 900:
        level = "high"
    elif total_minutes > 600:
        level = "medium"
    else:
        level = "low"

    return {
        "total_minutes": total_minutes,
        "load_level": level,
    }
