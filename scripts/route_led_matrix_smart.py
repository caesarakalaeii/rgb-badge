#!/usr/bin/env python3
"""
Smart LED Matrix Router for KiCad PCB
Routes data traces with proper net assignment and via usage

Usage in KiCad Scripting Console:
    exec(open('scripts/route_led_matrix_smart.py').read())
"""

import pcbnew

# Matrix configuration
COLS = 64
ROWS = 40
PITCH_X = 1.5625  # mm
PITCH_Y = 1.625   # mm
START_X = 10.0
START_Y = 10.0

# Routing configuration
TRACE_WIDTH = 0.1   # mm - narrower for tight spacing
VIA_DRILL = 0.3     # mm
VIA_SIZE = 0.6      # mm

# Layer definitions
LAYER_TOP = pcbnew.F_Cu
LAYER_BOTTOM = pcbnew.B_Cu

# LED prefix
LED_PREFIX = "D"

# 8-lane configuration
LANES = 8
COLS_PER_LANE = COLS // LANES
PIXELS_PER_LANE = COLS_PER_LANE * ROWS


def get_pad_by_number(footprint, pad_number):
    """Get a specific pad object from footprint"""
    for pad in footprint.Pads():
        if pad.GetName() == str(pad_number):
            return pad
    return None


def create_track_with_net(board, start_pos, end_pos, width_mm, layer, net):
    """Create a track with proper net assignment"""
    track = pcbnew.PCB_TRACK(board)
    track.SetStart(start_pos)
    track.SetEnd(end_pos)
    track.SetWidth(pcbnew.FromMM(width_mm))
    track.SetLayer(layer)
    if net:
        track.SetNet(net)
    board.Add(track)
    return track


def create_via_with_net(board, position, drill_mm, size_mm, net):
    """Create a via with proper net assignment"""
    via = pcbnew.PCB_VIA(board)
    via.SetPosition(position)
    via.SetDrill(pcbnew.FromMM(drill_mm))
    via.SetWidth(pcbnew.FromMM(size_mm))
    if net:
        via.SetNet(net)
    board.Add(via)
    return via


def get_footprint_by_ref(board, reference):
    """Get footprint by reference designator"""
    for fp in board.GetFootprints():
        if fp.GetReference() == reference:
            return fp
    return None


def route_with_via_if_needed(board, start_pad, end_pad, width_mm,
                              current_row, current_col, next_row, next_col):
    """
    Route between two pads, using vias and bottom layer only for row transitions.
    With rotated LEDs on odd rows, most routing is simple horizontal traces.
    Returns number of segments created.
    """
    start_pos = start_pad.GetPosition()
    end_pos = end_pad.GetPosition()
    net = start_pad.GetNet()

    segments = 0

    # Calculate routing distance
    dx_mm = abs(pcbnew.ToMM(end_pos.x - start_pos.x))
    dy_mm = abs(pcbnew.ToMM(end_pos.y - start_pos.y))

    # Determine if this is a row transition (serpentine wrap-around)
    is_row_transition = (current_row != next_row)

    if not is_row_transition:
        # Same row: simple horizontal routing on top layer
        # With rotated LEDs, DOUT and DIN are naturally aligned
        create_track_with_net(board, start_pos, end_pos, width_mm, LAYER_TOP, net)
        segments += 1

    else:
        # Row transition (serpentine wrap): Use bottom layer to avoid obstacles
        # This happens at the end of each row when wrapping to the next

        # Via at start (top to bottom)
        create_via_with_net(board, start_pos, VIA_DRILL, VIA_SIZE, net)
        segments += 1

        # Track on bottom layer
        create_track_with_net(board, start_pos, end_pos, width_mm, LAYER_BOTTOM, net)
        segments += 1

        # Via at end (bottom to top)
        create_via_with_net(board, end_pos, VIA_DRILL, VIA_SIZE, net)
        segments += 1

    return segments


def get_led_row_col(led_idx, serpentine=True):
    """
    Calculate the row and column for an LED in serpentine pattern.
    Returns (row, col) for the LED's physical position.
    """
    # For 8-lane serpentine
    lane = (led_idx // PIXELS_PER_LANE) % LANES
    pixel_in_lane = led_idx % PIXELS_PER_LANE

    row = pixel_in_lane // COLS_PER_LANE
    col_in_lane = pixel_in_lane % COLS_PER_LANE

    # Serpentine: reverse direction on odd rows
    if serpentine and row % 2 == 1:
        col_in_lane = COLS_PER_LANE - 1 - col_in_lane

    col = lane * COLS_PER_LANE + col_in_lane

    return (row, col)


def route_data_lanes_smart(board, led_footprints):
    """
    Smart routing with proper net assignment and via usage
    """
    print("Smart routing data traces with net assignment...")

    PAD_DIN = 4
    PAD_DOUT = 1

    total_segments = 0
    errors = 0

    # Route each connection
    for idx in range(len(led_footprints) - 1):
        led_num, current_fp = led_footprints[idx]
        next_num, next_fp = led_footprints[idx + 1]

        # Get pads
        dout_pad = get_pad_by_number(current_fp, PAD_DOUT)
        din_pad = get_pad_by_number(next_fp, PAD_DIN)

        if not dout_pad or not din_pad:
            print(f"  Warning: Missing pads for {LED_PREFIX}{led_num} -> {LED_PREFIX}{next_num}")
            errors += 1
            continue

        # Calculate row/col positions for routing decision
        current_row, current_col = get_led_row_col(idx)
        next_row, next_col = get_led_row_col(idx + 1)

        # Route with intelligence
        segs = route_with_via_if_needed(
            board, dout_pad, din_pad, TRACE_WIDTH,
            current_row, current_col, next_row, next_col
        )
        total_segments += segs

        # Progress indicator
        if (idx + 1) % 100 == 0:
            print(f"  Routed {idx + 1}/{len(led_footprints)-1} connections ({total_segments} segments)...")

    print(f"\n✓ Created {total_segments} routing segments")
    if errors > 0:
        print(f"⚠ {errors} connections had errors")

    return total_segments


def main():
    """Main routing function"""
    board = pcbnew.GetBoard()

    # Get LED footprints
    footprints = board.GetFootprints()
    led_footprints = []

    for fp in footprints:
        ref = fp.GetReference()
        if ref.startswith(LED_PREFIX):
            try:
                num = int(ref[len(LED_PREFIX):])
                led_footprints.append((num, fp))
            except ValueError:
                pass

    led_footprints.sort(key=lambda x: x[0])

    print(f"\nFound {len(led_footprints)} LEDs")
    print(f"Trace width: {TRACE_WIDTH}mm")
    print(f"Via size: {VIA_SIZE}mm / {VIA_DRILL}mm drill")
    print(f"\nRouting strategy (optimized for rotated LEDs):")
    print(f"  - Same row: Simple horizontal trace on top layer")
    print(f"    (LEDs rotated on odd rows align DOUT→DIN naturally)")
    print(f"  - Row transitions: Via to bottom layer to avoid obstacles")
    print(f"  - All tracks assigned to proper nets")
    print(f"  - Expected: ~{COLS_PER_LANE * LANES * (ROWS-1) * 3} vias (row transitions only)\n")

    response = input("Start routing? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled")
        return

    # Route data lanes
    route_data_lanes_smart(board, led_footprints)

    # Refresh board
    pcbnew.Refresh()
    print("\n✓ Done! Board refreshed.")
    print("\nNext steps:")
    print("  1. Add GND plane on In1.Cu")
    print("  2. Add VDD plane on In2.Cu")
    print("  3. Fill zones and run DRC")


if __name__ == "__main__":
    main()
