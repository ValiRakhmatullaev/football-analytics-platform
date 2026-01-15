import uuid

from django.db import models


class Player(models.Model):
    """
    Football player profile.
    """

    class Position(models.TextChoices):
        GK = "GK", "Goalkeeper"
        DF = "DF", "Defender"
        MF = "MF", "Midfielder"
        FW = "FW", "Forward"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    nationality = models.CharField(max_length=100, blank=True)
    primary_position = models.CharField(
        max_length=2,
        choices=Position.choices,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "players"
        ordering = ["last_name", "first_name"]

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"


class Appearance(models.Model):
    """
    Player participation in a specific match.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    player = models.ForeignKey(
        "players.Player",
        on_delete=models.PROTECT,
        related_name="appearances",
    )
    match = models.ForeignKey(
        "competitions.Match",
        on_delete=models.CASCADE,
        related_name="appearances",
    )
    team = models.ForeignKey(
        "teams.Team",
        on_delete=models.PROTECT,
        related_name="appearances",
    )

    minutes_played = models.PositiveSmallIntegerField()
    started = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "appearances"
        unique_together = ("player", "match")
