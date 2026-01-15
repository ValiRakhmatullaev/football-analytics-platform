from uuid import UUID
from typing import Dict

from django.apps import apps

from apps.analytics.services.team_metrics import (
    team_possession,
    event_tempo,
    team_turnovers,
)
from apps.analytics.services.player_metrics import player_events_per_90
from apps.analytics.services.normalization import normalize_player_metrics
from apps.analytics.services.player_index import calculate_epi


def get_match_overview(match_id: UUID) -> Dict:
    """
    Aggregate key analytics for Match Overview dashboard.
    """

    MatchTeam = apps.get_model("competitions", "MatchTeam")
    Player = apps.get_model("players", "Player")

    participants = MatchTeam.objects.filter(match_id=match_id)

    # --- Team-level metrics ---
    possession = team_possession(match_id)
    turnovers = team_turnovers(match_id)
    tempo = event_tempo(match_id)

    # --- Player-level metrics (for EPI aggregation) ---
    events_per_90 = player_events_per_90(match_id)

    # Map player -> position
    players = Player.objects.filter(id__in=events_per_90.keys())
    position_map = {p.id: p.primary_position for p in players}

    normalized = normalize_player_metrics(
        player_values={
            pid: {"events_per_90": val}
            for pid, val in events_per_90.items()
        },
        position_map=position_map,
    )

    epi = calculate_epi(normalized)

    # Average EPI per team
    epi_by_team: Dict[UUID, list] = {}

    for player_id, data in epi.items():
        for mt in participants:
            if mt.team_id not in epi_by_team:
                epi_by_team[mt.team_id] = []
            epi_by_team[mt.team_id].append(data["epi"])

    epi_avg_by_team = {
        team_id: int(sum(values) / len(values))
        for team_id, values in epi_by_team.items()
        if values
    }

    # Build response
    teams_data = {}

    for mt in participants:
        side = mt.side
        team_id = mt.team_id

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
