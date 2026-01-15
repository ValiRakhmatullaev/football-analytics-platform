import uuid

from django.db import models


class Competition(models.Model):
    """
    A football competition or league (e.g. Uzbekistan Super League).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    country = models.CharField(max_length=100)
    level = models.PositiveSmallIntegerField(
        help_text="Competition level within country (1 = top tier)"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "competitions"
        ordering = ["country", "level", "name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.country})"


class Season(models.Model):
    """
    A specific season of a competition (e.g. 2024/25).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    competition = models.ForeignKey(
        Competition,
        on_delete=models.PROTECT,
        related_name="seasons",
    )
    name = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "seasons"
        unique_together = ("competition", "name")
        ordering = ["-start_date"]

    def __str__(self) -> str:
        return f"{self.competition.name} {self.name}"


class Match(models.Model):
    """
    A single football match.
    """

    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        IN_PROGRESS = "in_progress", "In progress"
        FINISHED = "finished", "Finished"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    season = models.ForeignKey(
        Season,
        on_delete=models.PROTECT,
        related_name="matches",
    )
    kickoff_time = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "matches"
        ordering = ["kickoff_time"]

    def __str__(self) -> str:
        return f"Match {self.id} ({self.kickoff_time})"


class MatchTeam(models.Model):
    """
    Team participation in a match.
    """

    class Side(models.TextChoices):
        HOME = "home", "Home"
        AWAY = "away", "Away"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    match = models.ForeignKey(
        Match,
        on_delete=models.CASCADE,
        related_name="participants",
    )
    team = models.ForeignKey(
        "teams.Team",          # ❗ string reference — НИКАКИХ импортов
        on_delete=models.PROTECT,
        related_name="matches",
    )
    side = models.CharField(
        max_length=10,
        choices=Side.choices,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "match_teams"
        unique_together = ("match", "team")
