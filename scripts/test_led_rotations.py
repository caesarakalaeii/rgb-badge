#!/usr/bin/env python3
"""
Test script to verify LED rotations for 2×2 block pattern
Places only the first 2×2 block (4 LEDs) for visual verification

Usage in KiCad Scripting Console:
    exec(open('scripts/test_led_rotations.py').read())
"""

import pcbnew

# Matrix configuration (same as main script)
PITCH_X = 1.5625  # mm
PITCH_Y = 1.625   # mm
START_X = 10.0  # mm
START_Y = 10.0  # mm
LED_PREFIX = "D"

# Standard footprint orientation (0°) has pins: 4 3 / 2 1
BLOCK_ROTATIONS = {
    (True, True):   270,   # Top-left:     pins 2,4 / 1,3 → VDD/GND face right+down
    (False, True):  180,   # Top-right:    pins 1,2 / 3,4 → VDD/GND face left+down
    (True, False):    0,   # Bottom-left:  pins 4,3 / 2,1 → VDD/GND face right+up
    (False, False):  90,   # Bottom-right: pins 3,1 / 4,2 → VDD/GND face left+up
}

def get_led_by_number(board, led_num):
    """Get LED footprint by number"""
    ref = f"{LED_PREFIX}{led_num}"
    for fp in board.GetFootprints():
        if fp.GetReference() == ref:
            return fp
    return None

def test_rotations():
    """Test first 2×2 block (D1, D2, D41, D42 for serpentine, or adjust for your numbering)"""
    board = pcbnew.GetBoard()

    print("\n=== Testing 2×2 LED Block Rotations ===\n")
    print("Expected pattern (pins at each corner):")
    print("  D1  (col 0, row 0): 2 4 / 1 3  →  270° rotation")
    print("  D2  (col 1, row 0): 1 2 / 3 4  →  180° rotation")
    print("  D41 (col 0, row 1): 4 3 / 2 1  →    0° rotation")
    print("  D42 (col 1, row 1): 3 1 / 4 2  →   90° rotation")
    print("\n")

    # Test LEDs: first 2×2 block
    # For serpentine: D1, D2 (row 0), D80, D79 (row 1 reversed)
    # But for testing, let's place based on physical position
    test_leds = [
        (1, 0, 0, 270),   # D1: col 0, row 0 → 270°
        (2, 1, 0, 180),   # D2: col 1, row 0 → 180°
        (41, 0, 1, 0),    # D41: col 0, row 1 → 0° (assuming 40 LEDs per row)
        (42, 1, 1, 90),   # D42: col 1, row 1 → 90°
    ]

    for led_num, col, row, expected_rot in test_leds:
        fp = get_led_by_number(board, led_num)
        if not fp:
            print(f"⚠ Warning: {LED_PREFIX}{led_num} not found")
            continue

        # Calculate position
        x_mm = START_X + (col * PITCH_X)
        y_mm = START_Y + (row * PITCH_Y)

        # Set position and rotation
        x_nm = pcbnew.FromMM(x_mm)
        y_nm = pcbnew.FromMM(y_mm)
        fp.SetPosition(pcbnew.VECTOR2I(x_nm, y_nm))
        fp.SetOrientationDegrees(expected_rot)

        print(f"✓ Placed {LED_PREFIX}{led_num} at ({x_mm:.3f}, {y_mm:.3f}) with {expected_rot}° rotation")

    pcbnew.Refresh()

    print("\n=== Verification Steps ===")
    print("1. Zoom in on the first 2×2 block of LEDs")
    print("2. Check pin positions match the expected pattern above")
    print("3. Verify VDD (pin 2) and GND (pin 3) face toward the center")
    print("4. If correct, run the full placement script")
    print("5. If incorrect, adjust BLOCK_ROTATIONS dict and re-run this test")
    print("\nDone!")

if __name__ == "__main__":
    test_rotations()
