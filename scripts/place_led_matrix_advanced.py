#!/usr/bin/env python3
"""
Advanced LED Matrix Auto-Placement Script for KiCad PCB
Supports 8-lane serpentine routing pattern for parallel data distribution

Usage in KiCad Scripting Console:
    exec(open('scripts/place_led_matrix_advanced.py').read())
"""

import pcbnew

# Matrix configuration
COLS = 64
ROWS = 40
PITCH_X = 1.5625  # mm
PITCH_Y = 1.625   # mm

# Starting position (adjust to your board origin)
START_X = 10.0  # mm
START_Y = 10.0  # mm

# LED reference prefix
LED_PREFIX = "D"

# Placement pattern options
PATTERN_ROW_MAJOR = "row_major"          # Left-to-right, top-to-bottom
PATTERN_SERPENTINE = "serpentine"        # Snake pattern (alternate row direction)
PATTERN_8LANE_SERPENTINE = "8lane_serpentine"  # Per README: 8 lanes, each 8×40

# Choose pattern
PLACEMENT_PATTERN = PATTERN_8LANE_SERPENTINE

# Rotation (in degrees, 0 = normal orientation)
LED_ROTATION = 0.0


def get_led_footprints(board):
    """Get all LED footprints sorted by reference number"""
    footprints = board.GetFootprints()
    led_footprints = []

    for fp in footprints:
        ref = fp.GetReference()
        if ref.startswith(LED_PREFIX):
            try:
                num = int(ref[len(LED_PREFIX):])
                led_footprints.append((num, fp))
            except ValueError:
                print(f"Warning: Could not parse number from {ref}")

    led_footprints.sort(key=lambda x: x[0])
    return led_footprints


def place_row_major(led_footprints):
    """Simple row-major placement (left-to-right, top-to-bottom)"""
    for idx, (led_num, fp) in enumerate(led_footprints):
        row = idx // COLS
        col = idx % COLS

        x_mm = START_X + (col * PITCH_X)
        y_mm = START_Y + (row * PITCH_Y)

        set_footprint_position(fp, x_mm, y_mm, row)

        if (idx + 1) % 100 == 0:
            print(f"  Placed {idx + 1}/{len(led_footprints)} LEDs...")


def place_serpentine(led_footprints):
    """Serpentine pattern - alternates direction each row"""
    for idx, (led_num, fp) in enumerate(led_footprints):
        row = idx // COLS
        col = idx % COLS

        # Reverse column order on odd rows
        if row % 2 == 1:
            col = COLS - 1 - col

        x_mm = START_X + (col * PITCH_X)
        y_mm = START_Y + (row * PITCH_Y)

        set_footprint_position(fp, x_mm, y_mm, row)

        if (idx + 1) % 100 == 0:
            print(f"  Placed {idx + 1}/{len(led_footprints)} LEDs...")


def place_8lane_serpentine(led_footprints):
    """
    8-lane pattern per README architecture:
    - 8 parallel data lanes
    - Each lane drives 320 pixels (8 columns × 40 rows)
    - Serpentine within each lane for efficient routing
    - LEDs rotated 180° on odd rows for optimal pin alignment
    """
    LANES = 8
    COLS_PER_LANE = COLS // LANES  # 8 columns per lane
    PIXELS_PER_LANE = COLS_PER_LANE * ROWS  # 320 pixels per lane

    print(f"  Using 8-lane serpentine: {LANES} lanes × {PIXELS_PER_LANE} pixels")
    print(f"  Each lane: {COLS_PER_LANE} columns × {ROWS} rows")
    print(f"  LEDs rotated 180° on odd rows for better routing")

    for idx, (led_num, fp) in enumerate(led_footprints):
        # Determine which lane this LED belongs to
        lane = (idx // PIXELS_PER_LANE) % LANES
        pixel_in_lane = idx % PIXELS_PER_LANE

        # Within the lane, calculate row and column
        row = pixel_in_lane // COLS_PER_LANE
        col_in_lane = pixel_in_lane % COLS_PER_LANE

        # Serpentine: reverse direction on odd rows
        if row % 2 == 1:
            col_in_lane = COLS_PER_LANE - 1 - col_in_lane

        # Global column position
        col = lane * COLS_PER_LANE + col_in_lane

        # Calculate physical position
        x_mm = START_X + (col * PITCH_X)
        y_mm = START_Y + (row * PITCH_Y)

        set_footprint_position(fp, x_mm, y_mm, row)

        if (idx + 1) % 100 == 0:
            print(f"  Placed {idx + 1}/{len(led_footprints)} LEDs...")


def set_footprint_position(fp, x_mm, y_mm, row=None):
    """Set footprint position and rotation"""
    x_nm = pcbnew.FromMM(x_mm)
    y_nm = pcbnew.FromMM(y_mm)

    fp.SetPosition(pcbnew.VECTOR2I(x_nm, y_nm))

    # For serpentine: rotate LEDs 180° on odd rows
    # This aligns DOUT→DIN connections naturally
    rotation = LED_ROTATION
    if PLACEMENT_PATTERN == PATTERN_8LANE_SERPENTINE or PLACEMENT_PATTERN == PATTERN_SERPENTINE:
        if row is not None and row % 2 == 1:
            rotation += 180.0

    if rotation != 0:
        fp.SetOrientationDegrees(rotation)


def place_led_matrix():
    """Main placement function"""
    board = pcbnew.GetBoard()

    led_footprints = get_led_footprints(board)

    total_leds = COLS * ROWS
    if len(led_footprints) != total_leds:
        print(f"Warning: Found {len(led_footprints)} LEDs, expected {total_leds}")
        response = input(f"Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return

    print(f"\nPlacing {len(led_footprints)} LEDs in {COLS}×{ROWS} matrix")
    print(f"Pitch: {PITCH_X}mm × {PITCH_Y}mm")
    print(f"Pattern: {PLACEMENT_PATTERN}")
    print(f"Starting position: ({START_X}, {START_Y})\n")

    # Choose placement pattern
    if PLACEMENT_PATTERN == PATTERN_ROW_MAJOR:
        place_row_major(led_footprints)
    elif PLACEMENT_PATTERN == PATTERN_SERPENTINE:
        place_serpentine(led_footprints)
    elif PLACEMENT_PATTERN == PATTERN_8LANE_SERPENTINE:
        place_8lane_serpentine(led_footprints)
    else:
        print(f"Error: Unknown pattern '{PLACEMENT_PATTERN}'")
        return

    # Report results
    total_width = (COLS - 1) * PITCH_X
    total_height = (ROWS - 1) * PITCH_Y

    print(f"\n✓ Successfully placed {len(led_footprints)} LEDs")
    print(f"\nMatrix dimensions:")
    print(f"  Width: {total_width:.3f} mm ({COLS} columns)")
    print(f"  Height: {total_height:.3f} mm ({ROWS} rows)")
    print(f"  Total area: {total_width:.1f} × {total_height:.1f} mm")
    print(f"  End position: ({START_X + total_width:.3f}, {START_Y + total_height:.3f})")

    # Refresh board
    pcbnew.Refresh()
    print("\nDone! Board refreshed.")


if __name__ == "__main__":
    place_led_matrix()
