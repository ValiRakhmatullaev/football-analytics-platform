import uuid

from django.db import models


class Team(models.Model):
    """
    Football team or club.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=50)
    competition = models.ForeignKey(
        "competitions.Competition",   # ❗ string reference
        on_delete=models.PROTECT,
        related_name="teams",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "teams"
        unique_together = ("competition", "name")
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name
