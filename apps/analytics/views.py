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

        if not team_id:
            raise ValidationError("team_id is required")
        
        if not match_ids:
            raise ValidationError("match_ids[] is required (at least one match_id)")

        # Filter out empty strings
        match_ids = [mid for mid in match_ids if mid and mid.strip()]

        if not match_ids:
            raise ValidationError("match_ids[] cannot be empty")

        # Validate UUIDs
        try:
            team_uuid = UUID(team_id)
            match_uuids = [UUID(mid) for mid in match_ids]
        except ValueError as e:
            raise ValidationError(f"Invalid UUID format: {str(e)}")

        summary = get_coach_summary(
            team_id=team_uuid,
            match_ids=match_uuids,
        )

        return Response(summary)
