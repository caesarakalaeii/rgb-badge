#!/usr/bin/env python3
"""
Bad Apple Frame Converter for 10x10 LED Matrix
Converts Bad Apple video to compressed binary format for ESP32

Requirements:
    pip install opencv-python numpy pillow requests tqdm
"""

import os
import sys
import cv2
import numpy as np
import struct
import requests
from pathlib import Path
from tqdm import tqdm

# Configuration
MATRIX_WIDTH = 10
MATRIX_HEIGHT = 10
TARGET_FPS = 20  # ESP32 can handle ~20 FPS comfortably
THRESHOLD = 128  # Brightness threshold for black/white conversion

# Bad Apple video sources (tried in order)
BAD_APPLE_URLS = [
    "https://archive.org/download/bad-apple-video/bad_apple.mp4",
    "https://ia601501.us.archive.org/10/items/bad-apple-video/bad_apple.mp4",
]
VIDEO_FILE = "bad_apple.mp4"
OUTPUT_DIR = "bad_apple_data"
OUTPUT_FILE = "bad_apple_frames.bin"
HEADER_FILE = "bad_apple_frames.h"


def download_video():
    """Download Bad Apple video if not present"""
    if os.path.exists(VIDEO_FILE):
        print(f"✓ Video file already exists: {VIDEO_FILE}")
        file_size = os.path.getsize(VIDEO_FILE)
        if file_size < 1000000:  # Less than 1MB is suspicious
            print(f"  Warning: File size seems small ({file_size} bytes)")
            response = input("  Use it anyway? (y/n): ").strip().lower()
            if response != 'y':
                os.remove(VIDEO_FILE)
                print("  Deleted. Will try downloading again.")
            else:
                return True
        return True

    # Try yt-dlp first (if available)
    if try_ytdlp_download():
        return True

    # Try direct download from multiple sources
    print("Downloading Bad Apple video...")
    print("This may take a few minutes (~16MB)...")

    for url in BAD_APPLE_URLS:
        print(f"\nTrying: {url}")
        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))

            with open(VIDEO_FILE, 'wb') as f, tqdm(
                desc="Downloading",
                total=total_size,
                unit='iB',
                unit_scale=True
            ) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    size = f.write(chunk)
                    pbar.update(size)

            print(f"✓ Download complete: {VIDEO_FILE}")
            return True

        except Exception as e:
            print(f"✗ Failed: {e}")
            if os.path.exists(VIDEO_FILE):
                os.remove(VIDEO_FILE)
            continue

    # All downloads failed
    print("\n" + "="*60)
    print("✗ Automatic download failed from all sources")
    print("="*60)
    print("\nPlease download manually:")
    print("\nOption 1: YouTube")
    print("  Search: 'Bad Apple Touhou original'")
    print("  Or try: https://www.youtube.com/watch?v=FtutLA63Cp8")
    print(f"  Save as: {os.path.abspath(VIDEO_FILE)}")
    print("\nOption 2: Archive.org (retry later)")
    print("  https://archive.org/details/bad-apple-video")
    print("\nOption 3: Use yt-dlp")
    print("  pip install yt-dlp")
    print("  yt-dlp -o bad_apple.mp4 'https://www.youtube.com/watch?v=FtutLA63Cp8'")
    print("\nThen run this script again.")
    return False


def try_ytdlp_download():
    """Try to download using yt-dlp if available"""
    try:
        import subprocess

        # Check if yt-dlp is available
        result = subprocess.run(['which', 'yt-dlp'],
                              capture_output=True, text=True)
        if result.returncode != 0:
            return False

        print("Found yt-dlp, attempting YouTube download...")

        # Download from YouTube
        youtube_url = "https://www.youtube.com/watch?v=FtutLA63Cp8"
        cmd = [
            'yt-dlp',
            '-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            '-o', VIDEO_FILE,
            youtube_url
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0 and os.path.exists(VIDEO_FILE):
            print(f"✓ Downloaded via yt-dlp: {VIDEO_FILE}")
            return True
        else:
            print(f"✗ yt-dlp failed: {result.stderr}")
            return False

    except Exception as e:
        return False


def extract_frames(video_path):
    """Extract and convert frames to 10x10 binary format"""
    print(f"\nProcessing video: {video_path}")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"✗ Error: Cannot open video file {video_path}")
        return None

    # Get video properties
    original_fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / original_fps

    print(f"Original FPS: {original_fps:.2f}")
    print(f"Total frames: {total_frames}")
    print(f"Duration: {duration:.2f} seconds")

    # Calculate frame skip for target FPS
    frame_skip = int(original_fps / TARGET_FPS)
    expected_frames = total_frames // frame_skip

    print(f"\nConverting to {MATRIX_WIDTH}x{MATRIX_HEIGHT} at {TARGET_FPS} FPS")
    print(f"Frame skip: {frame_skip} (reading every {frame_skip}th frame)")
    print(f"Expected output frames: {expected_frames}")

    frames_data = []
    frame_count = 0
    processed_count = 0

    with tqdm(total=expected_frames, desc="Processing frames") as pbar:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Only process every Nth frame
            if frame_count % frame_skip == 0:
                # Convert to grayscale
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                # Resize to 10x10
                resized = cv2.resize(gray, (MATRIX_WIDTH, MATRIX_HEIGHT),
                                   interpolation=cv2.INTER_AREA)

                # Apply threshold to get binary image
                _, binary = cv2.threshold(resized, THRESHOLD, 255, cv2.THRESH_BINARY)

                # Convert to binary array (1 bit per pixel)
                frame_binary = (binary > 0).astype(np.uint8)

                # Pack into bytes (8 pixels per byte)
                frame_bytes = pack_frame_to_bytes(frame_binary)
                frames_data.append(frame_bytes)

                processed_count += 1
                pbar.update(1)

            frame_count += 1

    cap.release()

    print(f"\n✓ Processed {processed_count} frames")
    return frames_data, processed_count


def pack_frame_to_bytes(frame_binary):
    """Pack 10x10 binary frame into bytes (13 bytes for 100 pixels)"""
    # Flatten the 10x10 array to 100 pixels
    pixels = frame_binary.flatten()

    # Pack 8 pixels per byte
    packed = []
    for i in range(0, len(pixels), 8):
        byte_val = 0
        for bit_pos in range(8):
            if i + bit_pos < len(pixels) and pixels[i + bit_pos]:
                byte_val |= (1 << (7 - bit_pos))
        packed.append(byte_val)

    return bytes(packed)


def save_binary_file(frames_data, num_frames):
    """Save frames as binary file"""
    output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"\nSaving binary file: {output_path}")

    with open(output_path, 'wb') as f:
        # Write header: num_frames (uint16), fps (uint8), width (uint8), height (uint8)
        header = struct.pack('<HBBBx', num_frames, TARGET_FPS, MATRIX_WIDTH, MATRIX_HEIGHT)
        f.write(header)

        # Write all frames
        for frame_bytes in frames_data:
            f.write(frame_bytes)

    file_size = os.path.getsize(output_path)
    bytes_per_frame = 13  # (10x10 = 100 bits = 12.5 bytes, rounded to 13)

    print(f"✓ Saved {num_frames} frames")
    print(f"  File size: {file_size:,} bytes ({file_size/1024:.2f} KB)")
    print(f"  Bytes per frame: {bytes_per_frame}")
    print(f"  Header size: {len(header)} bytes")


def generate_header_file(num_frames):
    """Generate C header file for easy inclusion"""
    header_path = os.path.join(OUTPUT_DIR, HEADER_FILE)

    with open(header_path, 'w') as f:
        f.write(f"""// Bad Apple Frame Data
// Auto-generated by bad_apple_converter.py
//
// Frame format: {MATRIX_WIDTH}x{MATRIX_HEIGHT} monochrome
// Total frames: {num_frames}
// Target FPS: {TARGET_FPS}

#ifndef BAD_APPLE_FRAMES_H
#define BAD_APPLE_FRAMES_H

#define BA_FRAME_COUNT {num_frames}
#define BA_FPS {TARGET_FPS}
#define BA_WIDTH {MATRIX_WIDTH}
#define BA_HEIGHT {MATRIX_HEIGHT}
#define BA_BYTES_PER_FRAME 13  // 100 pixels / 8 bits per byte = 12.5, rounded to 13
#define BA_FRAME_MS {1000 // TARGET_FPS}  // Milliseconds per frame

// File to load: bad_apple_frames.bin
// Use SPIFFS or LittleFS to store this file on ESP32
// File structure:
//   Header (6 bytes): num_frames(2), fps(1), width(1), height(1), padding(1)
//   Frames: {num_frames} frames × 13 bytes each

#endif // BAD_APPLE_FRAMES_H
""")

    print(f"✓ Generated header: {header_path}")


def create_sample_frames():
    """Create sample frames visualization"""
    import PIL.Image as Image

    sample_output = os.path.join(OUTPUT_DIR, "sample_frames.png")

    cap = cv2.VideoCapture(VIDEO_FILE)
    frames_to_show = 8
    samples = []

    frame_positions = [0, 500, 1000, 1500, 2000, 3000, 4000, 5000]

    for pos in frame_positions:
        cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
        ret, frame = cap.read()
        if ret:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            resized = cv2.resize(gray, (MATRIX_WIDTH, MATRIX_HEIGHT),
                               interpolation=cv2.INTER_AREA)
            _, binary = cv2.threshold(resized, THRESHOLD, 255, cv2.THRESH_BINARY)

            # Scale up for visibility (10x10 -> 100x100)
            scaled = cv2.resize(binary, (100, 100), interpolation=cv2.INTER_NEAREST)
            samples.append(scaled)

    cap.release()

    if samples:
        # Create grid
        rows = [np.hstack(samples[:4]), np.hstack(samples[4:])]
        grid = np.vstack(rows)

        cv2.imwrite(sample_output, grid)
        print(f"✓ Sample frames preview: {sample_output}")


def main():
    print("=" * 60)
    print("Bad Apple Frame Converter for 10x10 LED Matrix")
    print("=" * 60)

    # Step 1: Download video if needed
    if not download_video():
        sys.exit(1)

    # Step 2: Extract and convert frames
    frames_data, num_frames = extract_frames(VIDEO_FILE)
    if frames_data is None:
        sys.exit(1)

    # Step 3: Save binary file
    save_binary_file(frames_data, num_frames)

    # Step 4: Generate header file
    generate_header_file(num_frames)

    # Step 5: Create sample preview
    create_sample_frames()

    print("\n" + "=" * 60)
    print("✓ Conversion complete!")
    print("=" * 60)
    print(f"\nOutput files in '{OUTPUT_DIR}/':")
    print(f"  - {OUTPUT_FILE}  (upload to ESP32)")
    print(f"  - {HEADER_FILE}  (include in code)")
    print(f"  - sample_frames.png  (preview)")
    print("\nNext steps:")
    print(f"  1. Upload {OUTPUT_FILE} to ESP32 SPIFFS/LittleFS")
    print("  2. Flash the bad_apple.ino sketch")
    print("  3. Enjoy the show!")


if __name__ == "__main__":
    main()
