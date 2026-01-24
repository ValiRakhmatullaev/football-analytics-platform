from typing import Dict, List, Any
from uuid import UUID

from django.apps import apps
from django.shortcuts import get_object_or_404


# ============================================================
# CONSTANTS (Domain knowledge)
# ============================================================

INSIGHT_RULES = {
    "ATTACK_FOCUS": {
        "phase": "attack",
        "min_events": 5,
        "text": "Игрок был наиболее активен в атаке, участвуя в розыгрышах мяча большую часть матча.",
    },
    "LOW_DEFENSIVE_INVOLVEMENT": {
        "phase": "defence",
        "max_events": 1,
        "text": "Оборонительное участие игрока было ограниченным.",
    },
    "DISCIPLINE_ISSUE": {
        "phase": "discipline",
        "min_events": 1,
        "text": "Игрок получал дисциплинарные санкции в этом матче.",
    },
    "LOW_SAMPLE_SIZE": {
        "type": "minutes",
        "max_minutes": 10,
        "text": "Игрок провёл на поле слишком мало времени для надёжных аналитических выводов.",
    },
    "HIGH_INVOLVEMENT": {
        "metric": "passes",
        "min_value": 30,
        "text": "Игрок был активно вовлечён в игру через большое количество передач.",
    },
}

EVENT_DESCRIPTIONS = {
    "pass": "Short pass in build-up phase",
    "shot": "Shot attempt",
    "goal": "Goal scored",
    "assist": "Assist provided",
    "tackle": "Defensive tackle",
    "interception": "Interception",
    "yellow_card": "Yellow card received",
    "red_card": "Red card received",
}

EVENT_PHASES = {
    "pass": "attack",
    "shot": "attack",
    "goal": "attack",
    "assist": "attack",
    "tackle": "defence",
    "interception": "defence",
    "clearance": "defence",
    "turnover": "transition",
    "yellow_card": "discipline",
    "red_card": "discipline",
    "corner": "set_piece",
    "free_kick": "set_piece",
    "penalty": "set_piece",
}

PHASE_EVENT_COUNTERS = {
    "attack": {
        "passes": ["pass"],
        "shots": ["shot"],
        "goals": ["goal"],
        "assists": ["assist"],
    },
    "defence": {
        "tackles": ["tackle"],
        "interceptions": ["interception"],
        "clearances": ["clearance"],
    },
    "transition": {
        "turnovers": ["turnover"],
    },
    "discipline": {
        "cards": ["yellow_card", "red_card"],
    },
    "set_piece": {
        "set_piece_actions": ["corner", "free_kick", "penalty"],
    },
}


# ============================================================
# DOMAIN FUNCTIONS (pure logic)
# ============================================================

def build_timeline(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    timeline = []

    for event in events:
        minute = None
        if event["timestamp_ms"] is not None:
            minute = (event["timestamp_ms"] // 60000) + 1

        timeline.append({
            "minute": minute,
            "type": event["event_type"],
            "phase": EVENT_PHASES.get(event["event_type"], "other"),
            "description": EVENT_DESCRIPTIONS.get(
                event["event_type"], "Match action"
            ),
        })

    return timeline


def calculate_phase_metrics(timeline: List[Dict[str, Any]]) -> Dict[str, Dict]:
    phase_data: Dict[str, Dict] = {}

    for item in timeline:
        phase = item["phase"]
        minute = item["minute"]

        if phase not in phase_data:
            phase_data[phase] = {
                "events": 0,
                "_minutes": set(),
            }

        phase_data[phase]["events"] += 1
        if minute is not None:
            phase_data[phase]["_minutes"].add(minute)

    for phase, counters in PHASE_EVENT_COUNTERS.items():
        if phase not in phase_data:
            continue
        for counter_name in counters.keys():
            phase_data[phase][counter_name] = 0

    for item in timeline:
        phase = item["phase"]
        event_type = item["type"]

        if phase not in PHASE_EVENT_COUNTERS:
            continue

        for metric, types in PHASE_EVENT_COUNTERS[phase].items():
            if event_type in types:
                phase_data[phase][metric] += 1

    for phase in phase_data:
        phase_data[phase]["minutes_active"] = len(
            phase_data[phase].pop("_minutes")
        )

    return phase_data


def calculate_confidence(events: int, minutes: int) -> str:
    if events >= 5 and minutes >= 10:
        return "high"
    if events >= 3 and minutes >= 5:
        return "medium"
    return "low"


def generate_insights(
    appearance_minutes: int,
    events_summary: Dict[str, int],
    phase_metrics: Dict[str, Dict],
) -> List[Dict[str, Any]]:
    insights = []

    for code, rule in INSIGHT_RULES.items():
        if rule.get("type") == "minutes":
            if appearance_minutes <= rule["max_minutes"]:
                insights.append({
                    "code": code,
                    "text": rule["text"],
                    "confidence": "high",
                    "sources": {
                        "minutes_played": appearance_minutes,
                        "threshold_minutes": rule["max_minutes"],
                    },
                })

    for code, rule in INSIGHT_RULES.items():
        if "phase" in rule:
            phase = rule["phase"]
            data = phase_metrics.get(phase)
            if not data:
                continue

            events_count = data.get("events", 0)

            if (
                ("min_events" in rule and events_count >= rule["min_events"])
                or
                ("max_events" in rule and events_count <= rule["max_events"])
            ):
                insights.append({
                    "code": code,
                    "text": rule["text"],
                    "confidence": calculate_confidence(
                        events_count,
                        data.get("minutes_active", 0),
                    ),
                    "sources": {
                        "phase": phase,
                        "events": events_count,
                        "minutes_active": data.get("minutes_active", 0),
                    },
                })

        if "metric" in rule:
            metric = rule["metric"]
            value = events_summary.get(metric, 0)

            if value >= rule.get("min_value", 0):
                insights.append({
                    "code": code,
                    "text": rule["text"],
                    "confidence": "high" if value >= 40 else "medium",
                    "sources": {
                        "metric": metric,
                        "value": value,
                    },
                })

    return insights


def position_metrics(position: str, events: Dict[str, int]) -> List[Dict[str, Any]]:
    if position == "FW":
        return [
            {"key": "involvement", "value": events["passes"]},
            {"key": "shooting_activity", "value": events["shots"]},
            {"key": "goal_output", "value": events["goals"]},
        ]
    if position == "MF":
        return [
            {"key": "passing_volume", "value": events["passes"]},
            {
                "key": "defensive_actions",
                "value": events["tackles"] + events["interceptions"],
            },
        ]
    if position == "DF":
        return [
            {
                "key": "defensive_actions",
                "value": events["tackles"] + events["interceptions"],
            },
            {"key": "build_up_involvement", "value": events["passes"]},
        ]
    if position == "GK":
        return [
            {"key": "distribution", "value": events["passes"]},
        ]
    return []


# ============================================================
# INFRASTRUCTURE (Django ORM)
# ============================================================

def load_appearance(match, player):
    Appearance = apps.get_model("players", "Appearance")
    return get_object_or_404(Appearance, match=match, player=player)


def load_player_events(match, player) -> List[Dict[str, Any]]:
    Event = apps.get_model("events", "Event")

    qs = (
        Event.objects
        .filter(match=match, player=player)
        .order_by("timestamp_ms", "created_at")
    )

    return list(
        qs.values("event_type", "timestamp_ms")
    )


def load_events_summary(match, player) -> Dict[str, int]:
    Event = apps.get_model("events", "Event")

    qs = Event.objects.filter(match=match, player=player)

    return {
        "goals": qs.filter(event_type="goal").count(),
        "assists": qs.filter(event_type="assist").count(),
        "passes": qs.filter(event_type="pass").count(),
        "shots": qs.filter(event_type="shot").count(),
        "tackles": qs.filter(event_type="tackle").count(),
        "interceptions": qs.filter(event_type="interception").count(),
        "yellow_cards": qs.filter(event_type="yellow_card").count(),
        "red_cards": qs.filter(event_type="red_card").count(),
    }


# ============================================================
# APPLICATION SERVICE (public API)
# ============================================================

class PlayerMatchProfileService:
    def __init__(self, match, player):
        self.match = match
        self.player = player
        self.appearance = load_appearance(match, player)

    def build(self) -> Dict[str, Any]:
        events_summary = load_events_summary(self.match, self.player)
        raw_events = load_player_events(self.match, self.player)

        timeline = build_timeline(raw_events)
        phase_metrics = calculate_phase_metrics(timeline)

        return {
            "match_context": {
                "match_id": str(self.match.id),
                "minutes_played": self.appearance.minutes_played,
                "started": self.appearance.started,
            },
            "events": events_summary,
            "metrics": position_metrics(
                self.player.primary_position,
                events_summary,
            ),
            "timeline": timeline,
            "phase_metrics": phase_metrics,
            "insights": generate_insights(
                self.appearance.minutes_played,
                events_summary,
                phase_metrics,
            ),
        }
