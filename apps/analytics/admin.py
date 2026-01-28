from django.contrib import admin
from apps.analytics.models import VideoUpload, VideoClip


@admin.register(VideoUpload)
class VideoUploadAdmin(admin.ModelAdmin):
    list_display = ['file_name', 'status', 'events_count', 'uploaded_at', 'match']
    list_filter = ['status', 'uploaded_at']
    search_fields = ['file_name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'uploaded_at', 'processed_at']


@admin.register(VideoClip)
class VideoClipAdmin(admin.ModelAdmin):
    list_display = ['title', 'clip_type', 'duration_seconds', 'timestamp_ms', 'video_upload', 'created_at']
    list_filter = ['clip_type', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
