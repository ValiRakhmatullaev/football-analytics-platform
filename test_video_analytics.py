#!/usr/bin/env python3
"""
Test script for Video Analytics Pipeline.
Tests with the 10-minute video clip from cut_video.py
"""

import sys
from pathlib import Path

# Add video_analytics to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from video_analytics.pipeline import VideoAnalyticsPipeline


def main():
    """Test the video analytics pipeline with the user's video."""
    
    # Check dependencies first
    print("=" * 70)
    print("Testing Video Analytics Pipeline")
    print("=" * 70)
    print()
    
    # Check for required dependencies
    print("Checking dependencies...")
    try:
        import cv2
        import numpy as np
        print(f"✓ OpenCV {cv2.__version__} installed")
        print(f"✓ NumPy {np.__version__} installed")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print()
        print("Please install dependencies first:")
        print("  python3 -m pip install opencv-python numpy")
        print()
        print("Or run the setup script:")
        print("  bash setup_video_analytics.sh")
        return 1
    
    print()
    
    # Video path from cut_video.py output
    video_path = "/Users/valijonrakhmatullaev/PyCharmMiscProject/second_half_60-70.mp4"
    
    print(f"Video: {video_path}")
    print()
    
    # Check if video exists
    if not Path(video_path).exists():
        print(f"❌ ERROR: Video file not found: {video_path}")
        print("\nPlease ensure:")
        print("1. The video file exists at the specified path")
        print("2. You've run cut_video.py to create the 10-minute clip")
        print("3. The path is correct")
        return 1
    
    print("✓ Video file found")
    print()
    
    # Initialize pipeline
    # For a 10-minute clip starting at 60:00 (1 hour = 3600000 ms)
    print("Initializing pipeline...")
    try:
        # Use workspace directory for output (to avoid permission issues)
        output_dir = PROJECT_ROOT / "analytics_output"
        pipeline = VideoAnalyticsPipeline(
            video_path=video_path,
            match_id=None,  # No Django match ID for testing
            period=2,  # 2nd half
            video_start_offset_ms=3600000,  # 60:00 in milliseconds
            fps_sample=1.0,  # Sample 1 frame per second (fast for testing)
            output_dir=str(output_dir)  # Use workspace directory
        )
        print("✓ Pipeline initialized")
        print()
    except Exception as e:
        print(f"❌ ERROR initializing pipeline: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Run pipeline
    print("Running video analysis...")
    print("This may take a few minutes depending on video length...")
    print()
    
    try:
        result = pipeline.run()
        
        print()
        print("=" * 70)
        
        if result["success"]:
            print("✓ SUCCESS!")
            print()
            print(f"Detected {result['events_count']} events")
            print(f"Output file: {result['output_file']}")
            print()
            
            # Print statistics
            stats = result.get('statistics', {})
            if stats:
                print("Statistics:")
                events_by_type = stats.get('events_by_type', {})
                if events_by_type:
                    for event_type, count in events_by_type.items():
                        print(f"  {event_type}: {count}")
                else:
                    print("  No events detected by type")
                
                avg_conf = stats.get('avg_confidence', 0)
                print(f"  Average confidence: {avg_conf:.3f}")
            print()
            
            # Show output file location
            output_file = Path(result['output_file'])
            if output_file.exists():
                file_size = output_file.stat().st_size / 1024  # KB
                print(f"Output JSON file size: {file_size:.2f} KB")
                print()
                print("You can now:")
                print("1. Review the JSON file to see detected events")
                print("2. Import events to Django using the management command")
                print("3. Adjust detection parameters if needed")
            else:
                print("⚠ Warning: Output file not found")
            
            return 0
        else:
            print("❌ FAILED")
            print()
            error = result.get('error', 'Unknown error')
            print(f"Error: {error}")
            print()
            print("Troubleshooting:")
            print("1. Check that OpenCV is installed: pip install opencv-python")
            print("2. Verify video file is not corrupted")
            print("3. Check video format is supported (MP4, AVI, etc.)")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠ Interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR during processing: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
