from typing import List
from uuid import UUID

from django.db.models import QuerySet

from apps.competitions.models import Match
from apps.events.models import Event

from apps.analytics.coach_summary.summary import build_explainable_summary


def get_coach_summary(
    team_id: UUID,
    match_ids: List[UUID],
) -> dict:
    """
    Orchestrates coach summary calculation.
    """

    matches: QuerySet[Match] = Match.objects.filter(id__in=match_ids)

    events: QuerySet[Event] = Event.objects.filter(
        match__in=matches
    )

    return build_explainable_summary(
        team_id=team_id,
        matches=matches,
        events=events,
    )
