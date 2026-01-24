from django.shortcuts import render

# Create your views here.
from uuid import UUID

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from apps.analytics.coach_summary.service import get_coach_summary


class CoachSummaryView(APIView):
    """
    GET /api/coach-summary/?team_id=&match_ids=
    """

    def get(self, request):
        team_id = request.query_params.get("team_id")
        match_ids = request.query_params.getlist("match_ids")

        if not team_id or not match_ids:
            raise ValidationError(
                "team_id and match_ids[] are required"
            )

        summary = get_coach_summary(
            team_id=UUID(team_id),
            match_ids=[UUID(mid) for mid in match_ids],
        )

        return Response(summary)
