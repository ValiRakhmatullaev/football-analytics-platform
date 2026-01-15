from rest_framework import serializers
from apps.players.models import Player
from apps.players.models import Appearance


class PlayerMatchProfileSerializer(serializers.Serializer):
    player = serializers.SerializerMethodField()
    match_context = serializers.DictField()
    events = serializers.DictField()
    metrics = serializers.ListField()
    timeline = serializers.ListField()
    phase_metrics = serializers.DictField()
    insights = serializers.ListField()



    def get_player(self, obj):
        player: Player = obj["player"]

        # Appearance для ЭТОГО матча уже проверен в сервисе
        appearance = player.appearances.get(match_id=obj["match_context"]["match_id"])

        return {
            "id": str(player.id),
            "full_name": f"{player.first_name} {player.last_name}",
            "position": player.primary_position,
            "team": {
                "id": str(appearance.team.id),
                "name": appearance.team.name,
            },
        }
