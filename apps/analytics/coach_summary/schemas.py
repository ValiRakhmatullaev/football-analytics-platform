from rest_framework import serializers


class SnapshotSerializer(serializers.Serializer):
    # Matches & results
    matches_played = serializers.IntegerField()
    wins = serializers.IntegerField()
    draws = serializers.IntegerField()
    losses = serializers.IntegerField()

    # Goals
    goals_for = serializers.IntegerField()
    goals_against = serializers.IntegerField()

    # Points
    points = serializers.IntegerField()
    points_per_match = serializers.FloatField()

    # Form: W / D / L sequence
    form = serializers.ListField(
        child=serializers.ChoiceField(choices=["W", "D", "L"])
    )
