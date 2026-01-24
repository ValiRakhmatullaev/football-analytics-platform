from rest_framework.views import APIView
from rest_framework.response import Response

from apps.competitions.models import Match


class MatchListAPIView(APIView):
    """
    GET /api/analytics/matches/
    """

    def get(self, request):
        matches = (
            Match.objects
            .order_by("-kickoff_time")
            .values("id", "kickoff_time", "status")
        )

        return Response(list(matches))
