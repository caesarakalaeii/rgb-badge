#!/usr/bin/env python3
"""
LED Matrix Auto-Placement Script for KiCad PCB
Place 64×40 LED matrix with precise pitch

Usage in KiCad Scripting Console:
    exec(open('scripts/place_led_matrix.py').read())
"""

import pcbnew

# Matrix configuration from README.md
COLS = 64
ROWS = 40
PITCH_X = 1.5625  # mm
PITCH_Y = 1.625   # mm

# Starting position (top-left corner) - adjust as needed
START_X = 10.0  # mm from board origin
START_Y = 10.0  # mm from board origin

# LED reference prefix (e.g., "D" for D1, D2, etc.)
LED_PREFIX = "D"

def place_led_matrix():
    """Place LEDs in a 64×40 matrix pattern"""

    board = pcbnew.GetBoard()

    # Get all footprints
    footprints = board.GetFootprints()

    # Filter LED footprints and sort by reference number
    led_footprints = []
    for fp in footprints:
        ref = fp.GetReference()
        if ref.startswith(LED_PREFIX):
            try:
                # Extract number from reference (e.g., LED123 -> 123)
                num = int(ref[len(LED_PREFIX):])
                led_footprints.append((num, fp))
            except ValueError:
                print(f"Warning: Could not parse number from {ref}")

    # Sort by reference number
    led_footprints.sort(key=lambda x: x[0])

    total_leds = COLS * ROWS
    if len(led_footprints) != total_leds:
        print(f"Warning: Found {len(led_footprints)} LEDs, expected {total_leds}")
        response = input(f"Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return

    # Place LEDs in row-major order (left to right, top to bottom)
    print(f"Placing {len(led_footprints)} LEDs in {COLS}×{ROWS} matrix...")
    print(f"Pitch: {PITCH_X}mm × {PITCH_Y}mm")
    print(f"Starting position: ({START_X}, {START_Y})")

    for idx, (led_num, fp) in enumerate(led_footprints):
        # Calculate row and column (0-indexed)
        row = idx // COLS
        col = idx % COLS

        # Calculate position in mm
        x_mm = START_X + (col * PITCH_X)
        y_mm = START_Y + (row * PITCH_Y)

        # Convert to KiCad internal units (nanometers)
        x_nm = pcbnew.FromMM(x_mm)
        y_nm = pcbnew.FromMM(y_mm)

        # Set position
        fp.SetPosition(pcbnew.VECTOR2I(x_nm, y_nm))

        # Progress indicator
        if (idx + 1) % 100 == 0:
            print(f"  Placed {idx + 1}/{len(led_footprints)} LEDs...")

    print(f"✓ Successfully placed {len(led_footprints)} LEDs")

    # Calculate total board dimensions
    total_width = (COLS - 1) * PITCH_X
    total_height = (ROWS - 1) * PITCH_Y
    print(f"\nMatrix dimensions:")
    print(f"  Width: {total_width:.3f} mm ({COLS} columns)")
    print(f"  Height: {total_height:.3f} mm ({ROWS} rows)")
    print(f"  End position: ({START_X + total_width:.3f}, {START_Y + total_height:.3f})")

    # Refresh the board
    pcbnew.Refresh()
    print("\nDone! Board refreshed.")

if __name__ == "__main__":
    place_led_matrix()
