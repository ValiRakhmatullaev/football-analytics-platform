"""
Example usage of the Video Analytics Pipeline.

This script demonstrates how to process a 10-minute video clip
and extract events compatible with the Django backend.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from video_analytics.pipeline import VideoAnalyticsPipeline


def example_basic_usage():
    """Basic example: Process video and export to JSON."""
    
    # Path to your 10-minute video clip
    video_path = "/Users/valijonrakhmatullaev/PyCharmMiscProject/second_half_60-70.mp4"
    
    # Initialize pipeline
    # For a 10-minute clip starting at 60:00 (1 hour = 3600000 ms)
    pipeline = VideoAnalyticsPipeline(
        video_path=video_path,
        match_id=None,  # Set to Django Match UUID if available
        period=2,  # 2nd half
        video_start_offset_ms=3600000,  # 60:00 in milliseconds
        fps_sample=1.0,  # Sample 1 frame per second (adjust for speed/accuracy tradeoff)
        output_dir=None  # Will create analytics_output/ in video directory
    )
    
    # Run pipeline
    print("Starting video analysis...")
    result = pipeline.run()
    
    if result["success"]:
        print(f"\n✓ Success!")
        print(f"  Detected {result['events_count']} events")
        print(f"  Output file: {result['output_file']}")
        print(f"  Statistics: {result['statistics']}")
    else:
        print(f"\n✗ Failed: {result.get('error', 'Unknown error')}")


def example_with_pitch_calibration():
    """Example with pitch calibration for accurate coordinates."""
    
    video_path = "/Users/valijonrakhmatullaev/PyCharmMiscProject/second_half_60-70.mp4"
    
    pipeline = VideoAnalyticsPipeline(
        video_path=video_path,
        match_id=None,
        period=2,
        video_start_offset_ms=3600000,
        fps_sample=1.0
    )
    
    # Define pitch corners in pixel coordinates
    # You need to manually identify these points in your video
    # Order: top-left, top-right, bottom-right, bottom-left
    pitch_corners = [
        (100, 50),   # Top-left corner of pitch
        (900, 50),   # Top-right corner of pitch
        (900, 630),  # Bottom-right corner of pitch
        (100, 630)   # Bottom-left corner of pitch
    ]
    
    # Run with calibration
    result = pipeline.run(
        calibrate_pitch=True,
        pitch_corners=pitch_corners
    )
    
    if result["success"]:
        print(f"Detected {result['events_count']} events with calibrated coordinates")


def example_django_export():
    """Example: Export directly to Django database."""
    
    import os
    import django
    
    # Setup Django (adjust path as needed)
    sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    django.setup()
    
    video_path = "/Users/valijonrakhmatullaev/PyCharmMiscProject/second_half_60-70.mp4"
    match_id = "your-match-uuid-here"  # Replace with actual Match UUID
    
    pipeline = VideoAnalyticsPipeline(
        video_path=video_path,
        match_id=match_id,
        period=2,
        video_start_offset_ms=3600000,
        fps_sample=1.0
    )
    
    # Run pipeline
    result = pipeline.run()
    
    if result["success"]:
        # Export to Django
        # You'll need to map detected team/player IDs to Django UUIDs
        team_mapping = {
            # "detected_team_1": "django-team-uuid-1",
            # "detected_team_2": "django-team-uuid-2",
        }
        
        player_mapping = {
            # "detected_player_1": "django-player-uuid-1",
            # ...
        }
        
        success = pipeline.export_to_django(
            team_mapping=team_mapping,
            player_mapping=player_mapping
        )
        
        if success:
            print("Events exported to Django database")
        else:
            print("Failed to export to Django")


if __name__ == "__main__":
    print("Video Analytics Pipeline - Example Usage")
    print("=" * 70)
    print()
    
    # Run basic example
    example_basic_usage()
    
    # Uncomment to try other examples:
    # example_with_pitch_calibration()
    # example_django_export()
