from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.competitions.models import Match
from apps.players.models import Player
from apps.analytics.services.player_match_profile import PlayerMatchProfileService
from apps.analytics.serializers.player_profile import PlayerMatchProfileSerializer


class PlayerMatchProfileAPIView(APIView):
    permission_classes = []

    def get(self, request, match_id, player_id):
        # 1. Получаем матч и игрока
        match = get_object_or_404(Match, id=match_id)
        player = get_object_or_404(Player, id=player_id)

        # 2. Сервис (бизнес-логика)
        service = PlayerMatchProfileService(match=match, player=player)
        profile_data = service.build()

        # 3. Payload под сериализатор
        payload = {
            "player": player,
            **profile_data,
        }

        # 4. Сериализация
        serializer = PlayerMatchProfileSerializer(payload)
        return Response(serializer.data)
