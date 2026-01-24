from typing import Dict, Any
from uuid import UUID

from django.db.models import QuerySet

from apps.competitions.models import Match
from apps.events.models import Event

from apps.analytics.coach_summary.load import build_load
from apps.analytics.coach_summary.usage import build_usage
from apps.analytics.coach_summary.strengths import build_strengths
from apps.analytics.coach_summary.weaknesses import build_weaknesses


WEAKNESS_LABELS = {
    "HIGH_TURNOVERS": "частые потери мяча",
    "LOW_TEMPO": "низкий темп игры",
}

STRENGTH_LABELS = {
    "POSSESSION_CONTROL": "контроль мяча",
    "HIGH_PRESS_ACTIVITY": "активный высокий прессинг",
}


def build_explainable_summary(
    team_id: UUID,
    matches: QuerySet[Match],
    events: QuerySet[Event],
) -> Dict[str, Any]:
    """
    Aggregates usage, load, strengths and weaknesses
    into a single explainable summary.
    """

    # -------------------------------
    # Edge case: no data
    # -------------------------------
    if not matches.exists():
        return {
            "meta": {"matches_count": 0},
            "load": {},
            "usage": {},
            "strengths": [],
            "weaknesses": [],
            "text": "Недостаточно данных для формирования аналитического отчёта.",
        }

    # -------------------------------
    # Core blocks
    # -------------------------------
    usage = build_usage(team_id, matches)
    load = build_load(team_id, matches)
    strengths = build_strengths(team_id, matches, events)
    weaknesses = build_weaknesses(team_id, matches, events)

    # -------------------------------
    # Human-readable text
    # -------------------------------
    sentences = []

    # Load
    load_level = load.get("load_level")
    if load_level == "high":
        sentences.append("Команда испытывает высокую игровую нагрузку.")
    elif load_level == "medium":
        sentences.append("Нагрузка команды находится на среднем уровне.")
    else:
        sentences.append("Нагрузка команды относительно низкая.")

    # Usage
    players_used = usage.get("players_used", 0)
    sentences.append(
        f"В анализируемых матчах использовано игроков: {players_used}."
    )

    # Strengths
    if strengths:
        strength_labels = [
            STRENGTH_LABELS.get(s["code"], s["code"])
            for s in strengths
        ]
        sentences.append(
            f"Сильные стороны команды: {', '.join(strength_labels)}."
        )

    # Weaknesses
    if weaknesses:
        weakness_labels = [
            WEAKNESS_LABELS.get(w["code"], w["code"])
            for w in weaknesses
        ]
        sentences.append(
            f"Зоны для улучшения: {', '.join(weakness_labels)}."
        )

    return {
        "meta": {
            "matches_count": matches.count(),
        },
        "load": load,
        "usage": usage,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "text": " ".join(sentences),
    }
