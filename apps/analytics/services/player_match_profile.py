from django.shortcuts import get_object_or_404

from apps.players.models import Appearance
from apps.events.models import Event


# =========================================================
# INSIGHT RULES (3F)
# =========================================================
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


# =========================================================
# EVENT DESCRIPTIONS (3C)
# =========================================================
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


# =========================================================
# EVENT → PHASE (3D)
# =========================================================
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


# =========================================================
# PHASE COUNTERS (3E)
# =========================================================
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


# =========================================================
# SERVICE
# =========================================================
class PlayerMatchProfileService:
    def __init__(self, match, player):
        self.match = match
        self.player = player

        self.appearance = get_object_or_404(
            Appearance,
            match=match,
            player=player,
        )

    # -----------------------------------------------------
    # MATCH CONTEXT
    # -----------------------------------------------------
    def match_context(self):
        return {
            "match_id": str(self.match.id),
            "minutes_played": self.appearance.minutes_played,
            "started": self.appearance.started,
        }

    # -----------------------------------------------------
    # EVENTS SUMMARY
    # -----------------------------------------------------
    def events_summary(self):
        qs = Event.objects.filter(match=self.match, player=self.player)

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

    # -----------------------------------------------------
    # TIMELINE (3C + 3D)
    # -----------------------------------------------------
    def timeline(self):
        qs = (
            Event.objects
            .filter(match=self.match, player=self.player)
            .order_by("timestamp_ms", "created_at")
        )

        timeline = []

        for event in qs:
            minute = None
            if event.timestamp_ms is not None:
                minute = (event.timestamp_ms // 60000) + 1

            timeline.append({
                "minute": minute,
                "type": event.event_type,
                "phase": EVENT_PHASES.get(event.event_type, "other"),
                "description": EVENT_DESCRIPTIONS.get(
                    event.event_type,
                    "Match action"
                ),
            })

        return timeline

    # -----------------------------------------------------
    # PHASE MICRO METRICS (3E)
    # -----------------------------------------------------
    def phase_micro_metrics(self):
        timeline = self.timeline()
        phase_data = {}

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

        for event in timeline:
            phase = event["phase"]
            event_type = event["type"]

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

    # -----------------------------------------------------
    # CONFIDENCE (3G)
    # -----------------------------------------------------
    def calculate_confidence(self, sources):
        events = sources.get("events", 0)
        minutes = sources.get("minutes_active", 0)

        if events >= 5 and minutes >= 10:
            return "high"
        if events >= 3 and minutes >= 5:
            return "medium"
        return "low"

    # -----------------------------------------------------
    # INSIGHTS (3F + 3G)
    # -----------------------------------------------------
    def generate_insights(self, events_summary, phase_metrics):
        insights = []
        # 0. Low sample size (minutes played)
        minutes_played = self.appearance.minutes_played

        for code, rule in INSIGHT_RULES.items():
            if rule.get("type") == "minutes":
                if minutes_played <= rule["max_minutes"]:
                    insights.append({
                        "code": code,
                        "text": rule["text"],
                        "confidence": "high",
                        "sources": {
                            "minutes_played": minutes_played,
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
                    sources = {
                        "phase": phase,
                        "events": events_count,
                        "minutes_active": data.get("minutes_active", 0),
                    }

                    insights.append({
                        "code": code,
                        "text": rule["text"],
                        "confidence": self.calculate_confidence(sources),
                        "sources": sources,
                    })

            if "metric" in rule:
                metric = rule["metric"]
                value = events_summary.get(metric, 0)

                if value >= rule.get("min_value", 0):
                    sources = {
                        "metric": metric,
                        "value": value,
                    }

                    insights.append({
                        "code": code,
                        "text": rule["text"],
                        "confidence": "high" if value >= 40 else "medium",
                        "sources": sources,
                    })

        return insights

    # -----------------------------------------------------
    # POSITION-AWARE METRICS (3B)
    # -----------------------------------------------------
    def fw_metrics(self, events):
        return [
            {
                "key": "involvement",
                "label": "Involvement",
                "value": events["passes"],
                "explanation": "Number of passes shows how often the forward was involved in build-up play",
            },
            {
                "key": "shooting_activity",
                "label": "Shooting activity",
                "value": events["shots"],
                "explanation": "Shots indicate how often the player attempted to finish attacks",
            },
            {
                "key": "goal_output",
                "label": "Goals scored",
                "value": events["goals"],
                "explanation": "Goals represent direct attacking contribution",
            },
        ]

    def mf_metrics(self, events):
        return [
            {
                "key": "passing_volume",
                "label": "Passing volume",
                "value": events["passes"],
                "explanation": "Shows how actively the midfielder distributed the ball",
            },
            {
                "key": "defensive_actions",
                "label": "Defensive actions",
                "value": events["tackles"] + events["interceptions"],
                "explanation": "Sum of tackles and interceptions reflects defensive contribution",
            },
        ]

    def df_metrics(self, events):
        return [
            {
                "key": "defensive_actions",
                "label": "Defensive actions",
                "value": events["tackles"] + events["interceptions"],
                "explanation": "Core defensive contribution through tackles and interceptions",
            },
            {
                "key": "build_up_involvement",
                "label": "Build-up involvement",
                "value": events["passes"],
                "explanation": "Passing volume indicates participation in build-up from the back",
            },
        ]

    def gk_metrics(self, events):
        return [
            {
                "key": "distribution",
                "label": "Distribution",
                "value": events["passes"],
                "explanation": "Number of passes reflects goalkeeper involvement in distribution",
            },
        ]

    def position_metrics(self, events):
        pos = self.player.primary_position

        if pos == "FW":
            return self.fw_metrics(events)
        if pos == "MF":
            return self.mf_metrics(events)
        if pos == "DF":
            return self.df_metrics(events)
        if pos == "GK":
            return self.gk_metrics(events)

        return []

    # -----------------------------------------------------
    # BUILD
    # -----------------------------------------------------
    def build(self):
        events = self.events_summary()
        phase_metrics = self.phase_micro_metrics()

        return {
            "match_context": self.match_context(),
            "events": events,
            "metrics": self.position_metrics(events),
            "timeline": self.timeline(),
            "phase_metrics": phase_metrics,
            "insights": self.generate_insights(events, phase_metrics),
        }
