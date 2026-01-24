from typing import Dict
from uuid import UUID

from django.apps import apps


# ============================================================
# DOMAIN LOGIC (pure)
# ============================================================

def calculate_usage(
    players_used: int,
    starts: int,
) -> Dict:
    """
    Calculate team usage metrics.
    """

    return {
        "players_used": players_used,
        "starts": starts,
    }


# ============================================================
# INFRASTRUCTURE (Django ORM)
# ============================================================

def load_usage_data(team_id: UUID, matches) -> Dict:
    Appearance = apps.get_model("players", "Appearance")

    qs = Appearance.objects.filter(
        team_id=team_id,
        match__in=matches,
    )

    used_qs = qs.filter(minutes_played__gt=0)

    return {
        "players_used": used_qs.values("player_id").distinct().count(),
        "starts": used_qs.count(),
    }


# ============================================================
# APPLICATION / USE-CASE
# ============================================================

def build_usage(team_id: UUID, matches) -> Dict:
    """
    Build usage block for Coach Summary.
    """

    data = load_usage_data(team_id, matches)

    return calculate_usage(
        players_used=data["players_used"],
        starts=data["starts"],
    )
