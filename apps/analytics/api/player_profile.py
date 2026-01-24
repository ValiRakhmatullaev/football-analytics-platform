from uuid import UUID
from config.permissions import IsScout

from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.competitions.models import Match
from apps.players.models import Player

from apps.analytics.services.player_match_profile import (
    PlayerMatchProfileService,
)


class PlayerMatchProfileAPIView(APIView):
    """
    Player Match Profile API.

    Returns full analytical profile of a player in a given match:
    - match context
    - event summary
    - position-aware metrics
    - timeline
    - phase metrics
    - explainable insights
    """

    permission_classes = []

    def get(self, request, match_id: UUID, player_id: UUID):
        # --------------------------------------------------
        # Load core entities
        # --------------------------------------------------
        match = get_object_or_404(Match, id=match_id)
        player = get_object_or_404(Player, id=player_id)

        # --------------------------------------------------
        # Use-case (business logic)
        # --------------------------------------------------
        service = PlayerMatchProfileService(
            match=match,
            player=player,
        )
        profile_data = service.build()

        # --------------------------------------------------
        # Final response (service-defined contract)
        # --------------------------------------------------
        return Response({
            "player": {
                "id": str(player.id),
                "full_name": f"{player.first_name} {player.last_name}",
                "position": player.primary_position,
            },
            **profile_data,
        })
