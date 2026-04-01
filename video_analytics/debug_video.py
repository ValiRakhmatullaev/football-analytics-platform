"""
Debug script to visualize video processing and ball detection.
Helps understand why events might not be detected.
"""

import cv2
import numpy as np
from pathlib import Path
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from video_analytics.video_processor import VideoProcessor
from video_analytics.event_detector import EventDetector


def visualize_ball_detection(frame, detector):
    """Visualize ball detection on a frame."""
    # Detect ball
    ball_detection = detector.detect_ball(frame)
    
    # Create visualization
    vis_frame = frame.copy()
    
    if ball_detection:
        x, y, confidence = ball_detection
        # Draw circle at detected ball position
        cv2.circle(vis_frame, (int(x), int(y)), 20, (0, 255, 0), 2)
        cv2.putText(vis_frame, f"Ball: {confidence:.2f}", 
                   (int(x) + 25, int(y)), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        print(f"  Ball detected at ({x:.1f}, {y:.1f}) with confidence {confidence:.2f}")
    else:
        print("  No ball detected")
    
    return vis_frame


def main():
    """Debug video processing."""
    video_path = "/Users/valijonrakhmatullaev/PyCharmMiscProject/second_half_60-70.mp4"
    
    if not Path(video_path).exists():
        print(f"Video not found: {video_path}")
        return
    
    print("=" * 70)
    print("Video Debug Tool")
    print("=" * 70)
    print(f"Video: {video_path}")
    print()
    
    # Initialize components
    processor = VideoProcessor(video_path, fps_sample=1.0)
    detector = EventDetector()
    
    processor.open()
    metadata = processor.get_metadata()
    
    print(f"Video info:")
    print(f"  Duration: {metadata['duration_seconds']:.2f}s")
    print(f"  Resolution: {metadata['width']}x{metadata['height']}")
    print(f"  FPS: {metadata['fps']:.2f}")
    print()
    
    # Sample a few frames
    print("Sampling frames for analysis...")
    print()
    
    sample_times = [
        metadata['duration_seconds'] * 0.1,  # 10% through
        metadata['duration_seconds'] * 0.5,  # 50% through
        metadata['duration_seconds'] * 0.9,  # 90% through
    ]
    
    output_dir = Path(__file__).parent.parent / "analytics_output" / "debug"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for i, timestamp in enumerate(sample_times):
        print(f"Frame {i+1} at {timestamp:.1f}s:")
        frame = processor.get_frame_at_time(timestamp)
        
        if frame is None:
            print("  Failed to read frame")
            continue
        
        # Visualize ball detection
        vis_frame = visualize_ball_detection(frame, detector)
        
        # Save visualization
        output_file = output_dir / f"frame_{i+1}_t{timestamp:.1f}s.jpg"
        cv2.imwrite(str(output_file), vis_frame)
        print(f"  Saved to: {output_file}")
        print()
    
    processor.close()
    
    print("=" * 70)
    print("Debug complete!")
    print(f"Check output images in: {output_dir}")
    print()
    print("Tips:")
    print("1. If no ball is detected, the video might have:")
    print("   - Poor lighting")
    print("   - Ball not visible (too small/far)")
    print("   - Different ball color than expected")
    print("2. Try adjusting ball detection thresholds in event_detector.py")
    print("3. Consider using ML-based detection (YOLO) for better results")


if __name__ == "__main__":
    main()
