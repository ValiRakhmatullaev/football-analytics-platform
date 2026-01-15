import uuid

from django.db import models


class Event(models.Model):
    """
    Atomic football event within a match.
    """

    class Type(models.TextChoices):
        PASS = "pass", "Pass"
        SHOT = "shot", "Shot"
        TURNOVER = "turnover", "Turnover"
        RECOVERY = "recovery", "Recovery"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    match = models.ForeignKey(
        "competitions.Match",
        on_delete=models.CASCADE,
        related_name="events",
    )
    team = models.ForeignKey(
        "teams.Team",
        on_delete=models.PROTECT,
        related_name="events",
    )
    player = models.ForeignKey(
        "players.Player",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
    )

    event_type = models.CharField(
        max_length=20,
        choices=Type.choices,
    )

    # Time context
    timestamp_ms = models.PositiveIntegerField(
        help_text="Milliseconds from match start"
    )
    period = models.PositiveSmallIntegerField(
        help_text="Match period (1=1st half, 2=2nd half, etc.)"
    )

    # Spatial context (normalized pitch coordinates)
    x = models.FloatField(
        null=True,
        blank=True,
        help_text="X coordinate on pitch (0-100)",
    )
    y = models.FloatField(
        null=True,
        blank=True,
        help_text="Y coordinate on pitch (0-100)",
    )

    # CV / data confidence
    confidence = models.FloatField(
        null=True,
        blank=True,
        help_text="Event confidence score (0.0–1.0)",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "events"
        ordering = ["timestamp_ms"]
        indexes = [
            models.Index(fields=["match", "event_type"]),
            models.Index(fields=["player"]),
        ]

    def __str__(self) -> str:
        return f"{self.event_type} @ {self.timestamp_ms}ms"

    # Optional secondary participant (e.g. pass receiver)
    secondary_player = models.ForeignKey(
        "players.Player",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="secondary_events",
    )

    # Link to related event (e.g. pass -> reception)
    related_event = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="derived_events",
    )

    class Outcome(models.TextChoices):
        SUCCESS = "success", "Success"
        FAIL = "fail", "Fail"
        UNKNOWN = "unknown", "Unknown"

    outcome = models.CharField(
        max_length=10,
        choices=Outcome.choices,
        default=Outcome.UNKNOWN,
    )
