#!/usr/bin/env python3
"""
VIA-Optimized LED Matrix Placement Script for KiCad PCB
Places LEDs in 2×2 blocks with rotations optimized for shared center VIAs
Supports 8 data lanes with serpentine routing within each lane

Layout: 40 columns × 64 rows = 2560 LEDs
- 8 data lanes, each handling 8 rows × 40 columns = 320 LEDs
- Serpentine pattern: left-to-right on even rows, right-to-left on odd rows
- LEDs in 2×2 blocks rotated so VDD/GND pins face center VIA

Target pin arrangement in each 2×2 block (pins facing center VIA):
    2 4 | 1 2
    1 3 | 3 4
    ----V----
    4 3 | 3 1
    2 1 | 4 2

Where: 1=DOUT, 2=VDD, 3=GND, 4=DIN, V=shared VIA

Usage in KiCad Scripting Console:
    exec(open('scripts/place_led_matrix_via_optimized.py').read())
"""

import pcbnew

# Matrix configuration
COLS = 40  # Changed from 64 to 40
ROWS = 64  # Changed from 40 to 64
PITCH_X = 1.5625  # mm (horizontal spacing)
PITCH_Y = 1.625   # mm (vertical spacing)

# Number of data lanes and rows per lane
NUM_LANES = 8
ROWS_PER_LANE = ROWS // NUM_LANES  # 8 rows per lane

# Starting position (adjust to your board origin)
START_X = 10.0  # mm
START_Y = 10.0  # mm

# LED reference prefix
LED_PREFIX = "D"

# ===== ROTATION CONFIGURATION =====
# These rotations create the 2×2 VIA-optimized block pattern
# Adjust these values based on your footprint's standard orientation
#
# Standard WS2812B-1010 orientation (at 0°):
#   Pin 2 (VDD)    Pin 3 (GND)
#   Pin 1 (DOUT)   Pin 4 (DIN)
#
# TODO: Verify and adjust these rotation angles based on actual footprint
# Goal: VDD and GND pins face toward center of each 2×2 block

# Rotation angles for 2×2 block positions (in degrees)
# These are applied based on (col % 2, row % 2) position within each 2×2 block
# Standard footprint orientation (0°) has pins: 4 3 / 2 1
BLOCK_ROTATIONS = {
    # (col_even, row_even): rotation_angle
    (True, True):   270,   # Top-left:     pins 2,4 / 1,3 → VDD/GND face right+down
    (False, True):  180,   # Top-right:    pins 1,2 / 3,4 → VDD/GND face left+down
    (True, False):    0,   # Bottom-left:  pins 4,3 / 2,1 → VDD/GND face right+up
    (False, False):  90,   # Bottom-right: pins 3,1 / 4,2 → VDD/GND face left+up
}


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


def get_via_optimized_rotation(col, row):
    """
    Calculate LED rotation based on position in 2×2 block
    Returns rotation in degrees
    """
    col_even = (col % 2) == 0
    row_even = (row % 2) == 0

    return BLOCK_ROTATIONS.get((col_even, row_even), 0)


def place_8lane_serpentine_via_optimized(led_footprints):
    """
    8-lane serpentine pattern with VIA-optimized 2×2 block rotations
    - 8 data lanes, each handling 8 rows
    - 40 LEDs per row
    - Serpentine within each data lane
    - LEDs rotated in 2×2 blocks for optimal VIA sharing
    """
    PIXELS_PER_LANE = ROWS_PER_LANE * COLS  # 320 pixels per lane

    print(f"  Using VIA-optimized 8-lane serpentine pattern")
    print(f"  Layout: {COLS} columns × {ROWS} rows = {COLS * ROWS} LEDs")
    print(f"  Data lanes: {NUM_LANES} lanes × {PIXELS_PER_LANE} pixels")
    print(f"  Each lane: {ROWS_PER_LANE} rows × {COLS} columns")
    print(f"  2×2 block rotations for shared center VIAs\n")

    for idx, (led_num, fp) in enumerate(led_footprints):
        # Determine which data lane this LED belongs to
        lane = idx // PIXELS_PER_LANE
        pixel_in_lane = idx % PIXELS_PER_LANE

        # Within the lane, calculate row and column
        row_in_lane = pixel_in_lane // COLS
        col = pixel_in_lane % COLS

        # Serpentine: reverse direction on odd rows within each lane
        if row_in_lane % 2 == 1:
            col = COLS - 1 - col

        # Global row position (lane offset + row within lane)
        row = lane * ROWS_PER_LANE + row_in_lane

        # Calculate physical position
        x_mm = START_X + (col * PITCH_X)
        y_mm = START_Y + (row * PITCH_Y)

        # Get rotation for VIA optimization
        rotation = get_via_optimized_rotation(col, row)

        # Set position and rotation
        set_footprint_position(fp, x_mm, y_mm, rotation)

        if (idx + 1) % 100 == 0:
            print(f"  Placed {idx + 1}/{len(led_footprints)} LEDs...")


def set_footprint_position(fp, x_mm, y_mm, rotation=0):
    """Set footprint position and rotation"""
    x_nm = pcbnew.FromMM(x_mm)
    y_nm = pcbnew.FromMM(y_mm)

    fp.SetPosition(pcbnew.VECTOR2I(x_nm, y_nm))

    # Always set rotation to ensure consistent orientation
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

    print(f"\nPlacing {len(led_footprints)} LEDs in VIA-optimized pattern")
    print(f"Matrix: {COLS} columns × {ROWS} rows")
    print(f"Pitch: {PITCH_X}mm × {PITCH_Y}mm")
    print(f"Pattern: 8-lane serpentine with 2×2 block VIA optimization")
    print(f"Starting position: ({START_X}, {START_Y})\n")

    # Place LEDs
    place_8lane_serpentine_via_optimized(led_footprints)

    # Report results
    total_width = (COLS - 1) * PITCH_X
    total_height = (ROWS - 1) * PITCH_Y

    print(f"\n✓ Successfully placed {len(led_footprints)} LEDs")
    print(f"\nMatrix dimensions:")
    print(f"  Width: {total_width:.3f} mm ({COLS} columns)")
    print(f"  Height: {total_height:.3f} mm ({ROWS} rows)")
    print(f"  Total area: {total_width:.1f} × {total_height:.1f} mm")
    print(f"  End position: ({START_X + total_width:.3f}, {START_Y + total_height:.3f})")
    print(f"\n  VIA optimization: LEDs grouped in 2×2 blocks")
    print(f"  - {(COLS // 2) * (ROWS // 2)} shared VIAs possible")
    print(f"  - Each VIA serves 4 LEDs (VDD + GND)")

    # Refresh board
    pcbnew.Refresh()
    print("\nDone! Board refreshed.")
    print("\nNOTE: Verify LED rotations match your footprint pin arrangement.")
    print("      Adjust BLOCK_ROTATIONS dict if needed.")


if __name__ == "__main__":
    place_led_matrix()
