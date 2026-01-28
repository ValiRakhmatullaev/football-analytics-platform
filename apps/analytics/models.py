from django.db import models
import uuid


class VideoUpload(models.Model):
    """
    Model for storing video upload metadata.
    """

    class Status(models.TextChoices):
        UPLOADING = "uploading", "Uploading"
        UPLOADED = "uploaded", "Uploaded"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # File information
    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)  # Path to stored video file
    file_size = models.BigIntegerField(help_text="File size in bytes")
    
    # Video metadata
    duration_seconds = models.FloatField(null=True, blank=True)
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    fps = models.FloatField(null=True, blank=True)
    
    # Processing information
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.UPLOADING,
    )
    match = models.ForeignKey(
        "competitions.Match",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="video_uploads",
    )
    period = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Match period (1=1st half, 2=2nd half)"
    )
    video_start_offset_ms = models.PositiveIntegerField(
        default=0,
        help_text="Video start offset in milliseconds from match start"
    )
    
    # Processing results
    events_count = models.IntegerField(default=0)
    processing_error = models.TextField(null=True, blank=True)
    json_output_path = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        help_text="Path to JSON file with detected events"
    )
    
    # Timestamps
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "video_uploads"
        ordering = ["-uploaded_at"]

    def __str__(self) -> str:
        return f"{self.file_name} ({self.status})"


class VideoClip(models.Model):
    """
    Model for storing video clips (highlights) extracted from match video.
    """

    class ClipType(models.TextChoices):
        GOAL = "goal", "Goal"
        SHOT = "shot", "Shot"
        DANGEROUS_MOMENT = "dangerous_moment", "Dangerous Moment"
        PASS = "pass", "Key Pass"
        TACKLE = "tackle", "Tackle"
        SAVE = "save", "Save"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relations
    video_upload = models.ForeignKey(
        VideoUpload,
        on_delete=models.CASCADE,
        related_name="clips",
    )
    event = models.ForeignKey(
        "events.Event",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="video_clips",
        help_text="Related event that triggered this clip"
    )
    
    # Clip information
    clip_type = models.CharField(
        max_length=20,
        choices=ClipType.choices,
    )
    title = models.CharField(
        max_length=255,
        help_text="Human-readable title for the clip"
    )
    description = models.TextField(
        null=True,
        blank=True,
        help_text="Description of what happens in the clip"
    )
    
    # Video file
    file_path = models.CharField(
        max_length=500,
        help_text="Path to clipped video file"
    )
    file_size = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="File size in bytes"
    )
    duration_seconds = models.FloatField(
        help_text="Duration of the clip in seconds"
    )
    
    # Timing
    start_time_seconds = models.FloatField(
        help_text="Start time in original video (seconds)"
    )
    end_time_seconds = models.FloatField(
        help_text="End time in original video (seconds)"
    )
    timestamp_ms = models.PositiveIntegerField(
        help_text="Event timestamp in milliseconds from match start"
    )
    
    # Metadata
    confidence = models.FloatField(
        null=True,
        blank=True,
        help_text="Confidence score for clip importance (0.0-1.0)"
    )
    thumbnail_path = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        help_text="Path to thumbnail image"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "video_clips"
        ordering = ["timestamp_ms"]
        indexes = [
            models.Index(fields=["video_upload", "clip_type"]),
            models.Index(fields=["timestamp_ms"]),
        ]

    def __str__(self) -> str:
        return f"{self.clip_type} @ {self.timestamp_ms}ms - {self.title}"
