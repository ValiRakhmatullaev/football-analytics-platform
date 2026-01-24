from typing import Dict, List
from uuid import UUID

from django.apps import apps

from apps.analytics.services.team_metrics import (
    team_possession,
    event_tempo,
    team_turnovers,
)
from apps.analytics.services.player_metrics import player_events_per_90
from apps.analytics.services.normalization import normalize_player_metrics
from apps.analytics.services.player_index import calculate_epi


# ============================================================
# INFRASTRUCTURE (Django ORM)
# ============================================================

def load_match_participants(match_id: UUID) -> List[Dict]:
    MatchTeam = apps.get_model("competitions", "MatchTeam")

    return list(
        MatchTeam.objects
        .filter(match_id=match_id)
        .values("team_id", "side")
    )


def load_player_positions(player_ids: List[UUID]) -> Dict[UUID, str]:
    Player = apps.get_model("players", "Player")

    return {
        player["id"]: player["primary_position"]
        for player in Player.objects.filter(id__in=player_ids)
        .values("id", "primary_position")
    }


# ============================================================
# DOMAIN / APPLICATION HELPERS
# ============================================================

def average(values: List[int]) -> int | None:
    if not values:
        return None
    return int(sum(values) / len(values))


def calculate_team_epi_averages(
    epi_by_player: Dict[UUID, Dict],
    participants: List[Dict],
) -> Dict[UUID, int]:
    """
    Average EPI per team.
    """

    epi_by_team: Dict[UUID, List[int]] = {}

    # Map player -> team once
    player_to_team: Dict[UUID, UUID] = {}

    for p in participants:
        player_to_team.setdefault(p["team_id"], [])

    # NOTE:
    # Player-team relation must come from MatchTeam ↔ Appearance.
    # MVP assumption: all players belong to both teams equally.
    # (Safe placeholder until appearances are explicitly joined)

    for player_id, data in epi_by_player.items():
        for p in participants:
            epi_by_team.setdefault(p["team_id"], []).append(data["epi"])

    return {
        team_id: average(values)
        for team_id, values in epi_by_team.items()
        if values
    }


# ============================================================
# APPLICATION SERVICE (public API)
# ============================================================

def get_match_overview(match_id: UUID) -> Dict:
    """
    Aggregate key analytics for Match Overview dashboard.
    """

    participants = load_match_participants(match_id)

    # --------------------------------------------------------
    # Team-level metrics
    # --------------------------------------------------------
    possession = team_possession(match_id)
    turnovers = team_turnovers(match_id)
    tempo = event_tempo(match_id)

    # --------------------------------------------------------
    # Player-level metrics → EPI
    # --------------------------------------------------------
    events_per_90 = player_events_per_90(match_id)

    position_map = load_player_positions(list(events_per_90.keys()))

    normalized = normalize_player_metrics(
        player_values={
            pid: {"events_per_90": value}
            for pid, value in events_per_90.items()
        },
        position_map=position_map,
    )

    epi = calculate_epi(normalized)

    epi_avg_by_team = calculate_team_epi_averages(
        epi_by_player=epi,
        participants=participants,
    )

    # --------------------------------------------------------
    # Build response
    # --------------------------------------------------------
    teams_data: Dict[str, Dict] = {}

    for p in participants:
        side = p["side"]
        team_id = p["team_id"]

        teams_data[side] = {
            "team_id": str(team_id),
            "possession": possession.get(team_id, 0.0),
            "turnovers": turnovers.get(team_id, 0),
            "epi_avg": epi_avg_by_team.get(team_id),
        }

    return {
        "match_id": str(match_id),
        "teams": teams_data,
        "tempo": tempo,
    }
