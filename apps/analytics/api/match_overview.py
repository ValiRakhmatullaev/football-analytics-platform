from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.players.models import Appearance
from apps.competitions.models import Match
from apps.events.models import Event


def serialize_appearance(app: Appearance):
    player = app.player
    return {
        "id": str(player.id),  # UUID -> string
        "full_name": f"{player.first_name} {player.last_name}",
        "position": player.primary_position,
        "minutes_played": app.minutes_played,
        "started": app.started,
    }


class MatchOverviewAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, match_id):
        # --- Match ---
        match = get_object_or_404(Match, id=match_id)

        match_block = {
            "id": str(match.id),
            "kickoff_time": match.kickoff_time.isoformat() if match.kickoff_time else None,
            "status": match.status,
        }

        # --- Score (placeholder) ---
        score_block = {
            "home": 0,
            "away": 0,
        }

        # --- Teams ---
        participants = match.participants.select_related("team")

        home_team = None
        away_team = None

        for p in participants:
            if p.side == "home":
                home_team = p.team
            elif p.side == "away":
                away_team = p.team

        # --- Appearances (PLAYERS) ---
        home_appearances = Appearance.objects.filter(
            match=match,
            team=home_team,
        ).select_related("player")

        away_appearances = Appearance.objects.filter(
            match=match,
            team=away_team,
        ).select_related("player")

        # --- Events ---
        events = Event.objects.filter(match=match)

        home_events = events.filter(team=home_team)
        away_events = events.filter(team=away_team)

        total_events = home_events.count() + away_events.count()

        def possession_pct(team_events_count, total):
            if total == 0:
                return 0.0
            return round((team_events_count / total) * 100, 1)

        home_possession = possession_pct(home_events.count(), total_events)
        away_possession = possession_pct(away_events.count(), total_events)

        home_turnovers = home_events.filter(event_type="turnover").count()
        away_turnovers = away_events.filter(event_type="turnover").count()

        MATCH_DURATION_MIN = 90
        tempo = round(total_events / MATCH_DURATION_MIN, 2) if total_events else 0.0

        teams_block = {
            "home": {
                "team_id": str(home_team.id) if home_team else None,
                "name": home_team.name if home_team else None,
                "metrics": {
                    "possession_pct": home_possession,
                    "turnovers": home_turnovers,
                    "tempo": tempo,
                },
                "confidence": "high",
                "players": [
                    serialize_appearance(app) for app in home_appearances
                ],
            },
            "away": {
                "team_id": str(away_team.id) if away_team else None,
                "name": away_team.name if away_team else None,
                "metrics": {
                    "possession_pct": away_possession,
                    "turnovers": away_turnovers,
                    "tempo": tempo,
                },
                "confidence": "high",
                "players": [
                    serialize_appearance(app) for app in away_appearances
                ],
            },
        }

        # --- Key insights ---
        key_insights = []

        if home_possession > 55:
            key_insights.append({
                "code": "POSSESSION_ADVANTAGE",
                "text": "Команда чаще контролировала мяч."
            })

        if tempo < 0.2:
            key_insights.append({
                "code": "LOW_TEMPO",
                "text": "Темп игры был ниже среднего."
            })

        # --- Final response ---
        return Response({
            "match": match_block,
            "score": score_block,
            "teams": teams_block,
            "key_insights": key_insights,
            "top_players": [],
            "limitations": [
                "Анализ выполнен на основе событий без видео.",
                "Некоторые метрики являются оценочными.",
            ],
        })
