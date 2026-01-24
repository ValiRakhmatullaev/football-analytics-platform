from uuid import UUID
#from config.permissions import IsAnalyst

from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.competitions.models import Match
from apps.players.models import Appearance

from apps.analytics.services.match_dashboard import get_match_overview


def serialize_appearance(app: Appearance):
    player = app.player
    return {
        "id": str(player.id),
        "full_name": f"{player.first_name} {player.last_name}",
        "position": player.primary_position,
        "minutes_played": app.minutes_played,
        "started": app.started,
    }


class MatchOverviewAPIView(APIView):
    permission_classes = [] #IsAnalyst]
    def get(self, request, match_id: UUID):
        # --------------------------------------------------
        # Match (metadata only)
        # --------------------------------------------------
        match = get_object_or_404(Match, id=match_id)

        match_block = {
            "id": str(match.id),
            "kickoff_time": (
                match.kickoff_time.isoformat()
                if match.kickoff_time else None
            ),
            "status": match.status,
        }

        # --------------------------------------------------
        # Analytics core (USE-CASE)
        # --------------------------------------------------
        analytics = get_match_overview(match_id)

        # --------------------------------------------------
        # Teams & players (UI layer)
        # --------------------------------------------------
        participants = match.participants.select_related("team")

        teams_block = {}

        for p in participants:
            team = p.team
            side = p.side

            appearances = (
                Appearance.objects
                .filter(match=match, team=team)
                .select_related("player")
            )

            teams_block[side] = {
                "team_id": str(team.id),
                "name": team.name,
                "metrics": {
                    "possession_pct": analytics["teams"]
                    .get(side, {})
                    .get("possession", 0.0),
                    "turnovers": analytics["teams"]
                    .get(side, {})
                    .get("turnovers", 0),
                    "epi_avg": analytics["teams"]
                    .get(side, {})
                    .get("epi_avg"),
                    "tempo": analytics["tempo"],
                },
                "confidence": "high",
                "players": [
                    serialize_appearance(app) for app in appearances
                ],
            }

        # --------------------------------------------------
        # Final response
        # --------------------------------------------------
        return Response({
            "match": match_block,
            "score": {
                "home": 0,
                "away": 0,
            },
            "teams": teams_block,
            "key_insights": [],  # подключим позже из services
            "top_players": [],
            "limitations": [
                "Анализ выполнен на основе событий без видео.",
                "Некоторые метрики являются оценочными.",
            ],
        })
