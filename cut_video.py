#!/usr/bin/env python3
"""
Script to cut exactly 10 minutes from the second half of a football match video
(from 60:00 to 70:00) using ffmpeg with lossless copy (no re-encoding).

Requirements:
- ffmpeg binary must be executable
- Input video file must exist
- Uses absolute paths to avoid working directory issues
"""

import os
import subprocess
import sys
from pathlib import Path


# ============================================================================
# CONFIGURATION - Easy to modify
# ============================================================================

# Path to ffmpeg binary (absolute path)
FFMPEG_BINARY = "/Users/valijonrakhmatullaev/PyCharmMiscProject/ffmpeg_bin/ffmpeg"

# Input video file (absolute path)
INPUT_VIDEO = "/Users/valijonrakhmatullaev/PyCharmMiscProject/ffmpeg_bin/YTDown.com_YouTube_Real-Madrid-vs-FC-Barcelona-3-4-2013-201_Media_6j1Oj5N7kwE_003_480p.mp4"

# Output video file (absolute path)
OUTPUT_VIDEO = "/Users/valijonrakhmatullaev/PyCharmMiscProject/second_half_60-70.mp4"

# Start time: 60 minutes (1 hour) = 3600 seconds
START_TIME = "01:00:00"  # Format: HH:MM:SS

# Duration: 10 minutes = 600 seconds
DURATION = "00:10:00"  # Format: HH:MM:SS


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def print_info(message):
    """Print info message with prefix."""
    print(f"[INFO] {message}")


def print_error(message):
    """Print error message with prefix."""
    print(f"[ERROR] {message}", file=sys.stderr)


def print_success(message):
    """Print success message with prefix."""
    print(f"[SUCCESS] {message}")


def check_file_exists(filepath, description):
    """
    Check if a file exists.
    
    Args:
        filepath: Absolute path to the file
        description: Description of the file for error messages
        
    Returns:
        bool: True if file exists, False otherwise
    """
    if not os.path.isfile(filepath):
        print_error(f"{description} not found: {filepath}")
        return False
    print_info(f"{description} found: {filepath}")
    return True


def check_file_executable(filepath, description):
    """
    Check if a file is executable.
    
    Args:
        filepath: Absolute path to the file
        description: Description of the file for error messages
        
    Returns:
        bool: True if file is executable, False otherwise
    """
    if not os.access(filepath, os.X_OK):
        print_error(f"{description} is not executable: {filepath}")
        return False
    print_info(f"{description} is executable: {filepath}")
    return True


def get_file_size(filepath):
    """
    Get file size in human-readable format.
    
    Args:
        filepath: Absolute path to the file
        
    Returns:
        str: File size in human-readable format (e.g., "123.45 MB")
    """
    try:
        size_bytes = os.path.getsize(filepath)
        # Convert to human-readable format
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
    except OSError as e:
        return f"Error getting size: {e}"


# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    """Main function to cut the video."""
    
    print_info("=" * 70)
    print_info("Football Match Video Cutter - Lossless 10-minute Cut")
    print_info("=" * 70)
    print()
    
    # Print current working directory
    cwd = os.getcwd()
    print_info(f"Current working directory: {cwd}")
    print()
    
    # Check ffmpeg binary
    print_info("Checking ffmpeg binary...")
    if not check_file_exists(FFMPEG_BINARY, "ffmpeg binary"):
        print_error("Please ensure ffmpeg binary exists at the specified path.")
        return 1
    
    if not check_file_executable(FFMPEG_BINARY, "ffmpeg binary"):
        print_error("Please make ffmpeg binary executable: chmod +x " + FFMPEG_BINARY)
        return 1
    
    # Verify ffmpeg version (optional check)
    try:
        result = subprocess.run(
            [FFMPEG_BINARY, "-version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print_info(f"ffmpeg version: {version_line}")
        else:
            print_error("ffmpeg version check failed")
            return 1
    except subprocess.TimeoutExpired:
        print_error("ffmpeg version check timed out")
        return 1
    except Exception as e:
        print_error(f"Error checking ffmpeg version: {e}")
        return 1
    
    print()
    
    # Check input video file
    print_info("Checking input video file...")
    if not check_file_exists(INPUT_VIDEO, "Input video"):
        print_error("Please ensure input video file exists at the specified path.")
        return 1
    
    input_size = get_file_size(INPUT_VIDEO)
    print_info(f"Input video size: {input_size}")
    print()
    
    # Prepare output directory
    output_dir = os.path.dirname(OUTPUT_VIDEO)
    if output_dir and not os.path.exists(output_dir):
        print_info(f"Creating output directory: {output_dir}")
        try:
            os.makedirs(output_dir, exist_ok=True)
        except OSError as e:
            print_error(f"Failed to create output directory: {e}")
            return 1
    
    # Build ffmpeg command
    # Note: -ss before -i is faster (input seeking), but -ss after -i is more accurate
    # For lossless copy with -c copy, we use -ss before -i for speed
    ffmpeg_command = [
        FFMPEG_BINARY,
        "-ss", START_TIME,          # Start time (60 minutes)
        "-i", INPUT_VIDEO,          # Input file
        "-t", DURATION,             # Duration (10 minutes)
        "-c", "copy",               # Copy codecs (no re-encoding)
        "-avoid_negative_ts", "make_zero",  # Handle negative timestamps
        "-y",                       # Overwrite output file if exists
        OUTPUT_VIDEO                # Output file
    ]
    
    # Print command being executed
    print_info("=" * 70)
    print_info("Executing ffmpeg command:")
    print_info(" ".join(ffmpeg_command))
    print_info("=" * 70)
    print()
    
    # Run ffmpeg
    print_info("Processing video (this should be fast with -c copy)...")
    try:
        result = subprocess.run(
            ffmpeg_command,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout (should be much faster with copy)
        )
        
        if result.returncode == 0:
            print_success("Video cutting completed successfully!")
            print()
            
            # Check output file
            if os.path.isfile(OUTPUT_VIDEO):
                output_size = get_file_size(OUTPUT_VIDEO)
                print_info(f"Output video: {OUTPUT_VIDEO}")
                print_info(f"Output video size: {output_size}")
                print_success("Task completed!")
                return 0
            else:
                print_error("Output file was not created, but ffmpeg returned success.")
                return 1
        else:
            print_error("ffmpeg command failed!")
            print_error(f"Return code: {result.returncode}")
            print()
            print_error("STDERR output:")
            print(result.stderr)
            print()
            if result.stdout:
                print_error("STDOUT output:")
                print(result.stdout)
            return 1
            
    except subprocess.TimeoutExpired:
        print_error("ffmpeg command timed out (exceeded 5 minutes)")
        return 1
    except KeyboardInterrupt:
        print_error("Process interrupted by user (Ctrl+C)")
        return 1
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
