#!/usr/bin/env python3
"""
Combined Test Sample Script: 10×10 LED Matrix with 2 Data Lines
Creates a complete layout including placement, vias, and routing

Features:
- 10×10 LED matrix (100 LEDs total)
- 2 parallel data lanes (50 LEDs each)
- Serpentine routing within each lane
- Optimized LED rotation (180° on odd rows)
- Power vias in 2×2 block centers
- Auto-routing for data and power connections

Usage in KiCad Scripting Console:
    exec(open('scripts/create_test_sample_10x10.py').read())
"""

import pcbnew
import math

# ============================================================================
# CONFIGURATION
# ============================================================================

# Matrix configuration
COLS = 10
ROWS = 10
TOTAL_LEDS = COLS * ROWS
PITCH_X = 1.5625  # mm
PITCH_Y = 1.625   # mm

# Starting position
START_X = 10.0  # mm
START_Y = 10.0  # mm

# LED configuration
LED_PREFIX = "D"

# Data lane configuration (single serpentine chain)
NUM_LANES = 1  # Single continuous serpentine
COLS_PER_LANE = COLS  # All columns in one chain
PIXELS_PER_LANE = COLS * ROWS  # All pixels in one chain

# VIA configuration (for power)
VIA_SIZE = 0.4    # mm (via diameter)
VIA_DRILL = 0.2   # mm (drill diameter)

# Routing configuration
DATA_TRACE_WIDTH = 0.1   # mm (data traces)
POWER_TRACE_WIDTH = 0.25  # mm (power traces)
DATA_VIA_DRILL = 0.3     # mm (for data routing)
DATA_VIA_SIZE = 0.6      # mm (for data routing)

# Layer configuration
LAYER_TOP = pcbnew.F_Cu
LAYER_BOTTOM = pcbnew.B_Cu

# Net names
VDD_NET_NAME = "VDD"
GND_NET_NAME = "GND"

# Optimized 2×2 block rotations for via-centered power distribution
# Each LED in a 2×2 block is rotated so VDD/GND pins face the center via
# Standard footprint (0°) has pins: 4 3 / 2 1 (DIN=4, DOUT=1, VDD=2, GND=3)
BLOCK_ROTATIONS = {
    (True, True):   270,   # Top-left:     pins 2,4 / 1,3 → VDD/GND face right+down
    (False, True):  180,   # Top-right:    pins 1,2 / 3,4 → VDD/GND face left+down
    (True, False):    0,   # Bottom-left:  pins 4,3 / 2,1 → VDD/GND face right+up
    (False, False):  90,   # Bottom-right: pins 3,1 / 4,2 → VDD/GND face left+up
}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

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


def get_led_row_col(led_idx):
    """
    Calculate the row and column for an LED in simple serpentine pattern.
    Row 0: left to right (0→1→2→...→9)
    Row 1: right to left (19→18→17→...→10)
    Row 2: left to right (20→21→22→...→29)
    Returns (row, col) for the LED's physical position.
    """
    row = led_idx // COLS
    col = led_idx % COLS

    # Serpentine: reverse direction on odd rows
    if row % 2 == 1:
        col = COLS - 1 - col

    return (row, col)


def get_pad_by_number(footprint, pad_number):
    """Get a specific pad from a footprint"""
    for pad in footprint.Pads():
        if pad.GetName() == str(pad_number):
            return pad
    return None


def distance(pos1, pos2):
    """Calculate distance between two positions in mm"""
    dx = pcbnew.ToMM(pos2.x - pos1.x)
    dy = pcbnew.ToMM(pos2.y - pos1.y)
    return math.sqrt(dx * dx + dy * dy)


# ============================================================================
# STEP 1: LED PLACEMENT
# ============================================================================

def place_leds(board, led_footprints):
    """
    Place LEDs in 2-lane serpentine pattern with optimized 2×2 block rotation
    Each LED is rotated so its VDD/GND pins face the center via of its 2×2 block
    """
    print("\n" + "="*60)
    print("STEP 1: Placing LEDs")
    print("="*60)
    print(f"Pattern: Simple full-width serpentine with 2×2 block rotation")
    print(f"Chain: Single continuous chain of {PIXELS_PER_LANE} LEDs")
    print(f"Grid: {COLS} columns × {ROWS} rows")
    print(f"Pitch: {PITCH_X}mm × {PITCH_Y}mm")
    print(f"Rotation: Optimized for via-centered power (VDD/GND face center)")
    print(f"Serpentine: Row 0 (→), Row 1 (←), Row 2 (→), etc.\n")

    for idx, (led_num, fp) in enumerate(led_footprints):
        # Calculate position
        row, col = get_led_row_col(idx)

        x_mm = START_X + (col * PITCH_X)
        y_mm = START_Y + (row * PITCH_Y)
        x_nm = pcbnew.FromMM(x_mm)
        y_nm = pcbnew.FromMM(y_mm)

        # Set position
        fp.SetPosition(pcbnew.VECTOR2I(x_nm, y_nm))

        # Determine position within 2×2 block for optimized rotation
        # This makes VDD/GND pins face the center via
        is_left = (col % 2 == 0)
        is_top = (row % 2 == 0)
        rotation = BLOCK_ROTATIONS[(is_left, is_top)]

        fp.SetOrientationDegrees(rotation)

        if (idx + 1) % 25 == 0:
            print(f"  Placed {idx + 1}/{len(led_footprints)} LEDs...")

    total_width = (COLS - 1) * PITCH_X
    total_height = (ROWS - 1) * PITCH_Y

    print(f"\n✓ Placed {len(led_footprints)} LEDs")
    print(f"  Matrix size: {total_width:.2f}mm × {total_height:.2f}mm")
    print(f"  End position: ({START_X + total_width:.2f}, {START_Y + total_height:.2f})")


# ============================================================================
# STEP 2: POWER VIA PLACEMENT
# ============================================================================

def place_vdd_vias(board):
    """
    Place VDD vias in center of 2×2 LED blocks
    """
    print("\n" + "="*60)
    print("STEP 2A: Placing VDD VIAs")
    print("="*60)

    # Calculate VDD VIA grid
    vdd_cols = COLS // 2
    vdd_rows = ROWS // 2
    total_vdd = vdd_cols * vdd_rows

    print(f"VDD vias: {vdd_cols} × {vdd_rows} = {total_vdd}")
    print(f"Position: Center of each 2×2 LED block")
    print(f"VIA size: {VIA_SIZE}mm / {VIA_DRILL}mm drill\n")

    print("⏸  PAUSE: Review LED placement before adding VDD vias")
    response = input("Continue with VDD VIA placement? (y/n): ")
    if response.lower() != 'y':
        print("Skipping VDD VIA placement")
        return 0

    # Get VDD net
    vdd_net = board.FindNet(VDD_NET_NAME)
    if not vdd_net or vdd_net.GetNetname() != VDD_NET_NAME:
        print(f"Warning: Net '{VDD_NET_NAME}' not found - VDD VIAs created without net")
        vdd_net = None
    else:
        print(f"✓ Found net: {VDD_NET_NAME}")

    print()

    # Place VDD vias (center of 2×2 blocks)
    print(f"Placing {total_vdd} VDD vias...")
    vdd_placed = 0
    via_offset_x = PITCH_X / 2
    via_offset_y = PITCH_Y / 2

    for via_row in range(vdd_rows):
        for via_col in range(vdd_cols):
            # Calculate VIA position (center of 2×2 block)
            via_x = START_X + (via_col * 2 * PITCH_X) + via_offset_x
            via_y = START_Y + (via_row * 2 * PITCH_Y) + via_offset_y

            x_nm = pcbnew.FromMM(via_x)
            y_nm = pcbnew.FromMM(via_y)

            # Create VDD via
            via = pcbnew.PCB_VIA(board)
            via.SetPosition(pcbnew.VECTOR2I(x_nm, y_nm))
            via.SetDrill(pcbnew.FromMM(VIA_DRILL))
            via.SetWidth(pcbnew.FromMM(VIA_SIZE))
            via.SetLayerPair(board.GetLayerID("F.Cu"), board.GetLayerID("B.Cu"))

            if vdd_net:
                via.SetNet(vdd_net)

            board.Add(via)
            vdd_placed += 1

    print(f"✓ Placed {vdd_placed} VDD vias")
    return vdd_placed


def place_gnd_vias(board):
    """
    Place GND vias on expanded grid (LED grid intersections)
    """
    print("\n" + "="*60)
    print("STEP 2B: Placing GND VIAs")
    print("="*60)

    # Calculate GND VIA grid
    vdd_cols = COLS // 2
    vdd_rows = ROWS // 2
    gnd_cols = vdd_cols + 1  # +1 on each axis
    gnd_rows = vdd_rows + 1
    total_gnd = gnd_cols * gnd_rows

    print(f"GND vias: {gnd_cols} × {gnd_rows} = {total_gnd}")
    print(f"Position: LED grid intersections and corners")
    print(f"VIA size: {VIA_SIZE}mm / {VIA_DRILL}mm drill\n")

    print("⏸  PAUSE: Review VDD via placement before adding GND vias")
    print("This is your chance to adjust VDD via positions if needed")
    response = input("Continue with GND VIA placement? (y/n): ")
    if response.lower() != 'y':
        print("Skipping GND VIA placement")
        return 0

    # Get GND net
    gnd_net = board.FindNet(GND_NET_NAME)
    if not gnd_net or gnd_net.GetNetname() != GND_NET_NAME:
        print(f"Warning: Net '{GND_NET_NAME}' not found - GND VIAs created without net")
        gnd_net = None
    else:
        print(f"✓ Found net: {GND_NET_NAME}")

    print()

    # Place GND vias (expanded grid at LED grid intersections)
    print(f"Placing {total_gnd} GND vias...")
    gnd_placed = 0

    for via_row in range(gnd_rows):
        for via_col in range(gnd_cols):
            # Calculate GND via position (at LED grid points and corners)
            via_x = START_X + (via_col * 2 * PITCH_X)
            via_y = START_Y + (via_row * 2 * PITCH_Y)

            x_nm = pcbnew.FromMM(via_x)
            y_nm = pcbnew.FromMM(via_y)

            # Create GND via
            via = pcbnew.PCB_VIA(board)
            via.SetPosition(pcbnew.VECTOR2I(x_nm, y_nm))
            via.SetDrill(pcbnew.FromMM(VIA_DRILL))
            via.SetWidth(pcbnew.FromMM(VIA_SIZE))
            via.SetLayerPair(board.GetLayerID("F.Cu"), board.GetLayerID("B.Cu"))

            if gnd_net:
                via.SetNet(gnd_net)

            board.Add(via)
            gnd_placed += 1

    print(f"✓ Placed {gnd_placed} GND vias")
    return gnd_placed


# ============================================================================
# STEP 3: DATA ROUTING
# ============================================================================

def create_track_with_net(board, start_pos, end_pos, width_mm, layer, net):
    """Create a track segment with net assignment"""
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
    """Create a via with net assignment"""
    via = pcbnew.PCB_VIA(board)
    via.SetPosition(position)
    via.SetDrill(pcbnew.FromMM(drill_mm))
    via.SetWidth(pcbnew.FromMM(size_mm))
    if net:
        via.SetNet(net)
    board.Add(via)
    return via


def route_data_connections(board, led_footprints):
    """
    Route data connections between LEDs with smart via usage
    """
    print("\n" + "="*60)
    print("STEP 3: Routing Data Connections")
    print("="*60)
    print(f"Trace width: {DATA_TRACE_WIDTH}mm")
    print(f"Strategy: Top layer for same row, bottom layer for row transitions")
    print(f"Via size: {DATA_VIA_SIZE}mm / {DATA_VIA_DRILL}mm drill\n")

    print("⏸  PAUSE: Review layout before auto-routing data connections")
    print("This is your chance to manually adjust LED positions or via placements")
    response = input("Continue with data routing? (y/n): ")
    if response.lower() != 'y':
        print("Skipping data routing")
        return 0

    PAD_DIN = 4
    PAD_DOUT = 1

    total_segments = 0

    # Route each connection
    for idx in range(len(led_footprints) - 1):
        led_num, current_fp = led_footprints[idx]
        next_num, next_fp = led_footprints[idx + 1]

        # Get pads
        dout_pad = get_pad_by_number(current_fp, PAD_DOUT)
        din_pad = get_pad_by_number(next_fp, PAD_DIN)

        if not dout_pad or not din_pad:
            print(f"  Warning: Missing pads for {LED_PREFIX}{led_num} -> {LED_PREFIX}{next_num}")
            continue

        start_pos = dout_pad.GetPosition()
        end_pos = din_pad.GetPosition()
        net = dout_pad.GetNet()

        # Calculate positions
        current_row, current_col = get_led_row_col(idx)
        next_row, next_col = get_led_row_col(idx + 1)

        # Check if this is a row transition
        is_row_transition = (current_row != next_row)

        if not is_row_transition:
            # Same row: simple horizontal trace on top layer
            create_track_with_net(board, start_pos, end_pos, DATA_TRACE_WIDTH, LAYER_TOP, net)
            total_segments += 1
        else:
            # Row transition: use bottom layer with vias
            create_via_with_net(board, start_pos, DATA_VIA_DRILL, DATA_VIA_SIZE, net)
            create_track_with_net(board, start_pos, end_pos, DATA_TRACE_WIDTH, LAYER_BOTTOM, net)
            create_via_with_net(board, end_pos, DATA_VIA_DRILL, DATA_VIA_SIZE, net)
            total_segments += 3

        if (idx + 1) % 25 == 0:
            print(f"  Routed {idx + 1}/{len(led_footprints)-1} connections...")

    print(f"\n✓ Created {total_segments} routing segments for data")
    return total_segments


# ============================================================================
# STEP 4: POWER ROUTING
# ============================================================================

def find_nearest_via(board, pad_pos, max_distance_mm):
    """Find the nearest VIA to a pad"""
    nearest_via = None
    nearest_dist = float('inf')

    for track in board.GetTracks():
        if track.Type() == pcbnew.PCB_VIA_T:
            via_pos = track.GetPosition()
            dist = distance(pad_pos, via_pos)

            if dist < max_distance_mm and dist < nearest_dist:
                nearest_via = track
                nearest_dist = dist

    return nearest_via, nearest_dist


def route_power_to_vias(board, led_footprints):
    """
    Route VDD and GND pads to nearest vias
    """
    print("\n" + "="*60)
    print("STEP 4: Routing Power Connections")
    print("="*60)
    print(f"Trace width: {POWER_TRACE_WIDTH}mm")
    print(f"Search radius: 2.5mm\n")

    print("⏸  PAUSE: Review data routing before adding power traces")
    print("This is your chance to manually adjust data traces if needed")
    response = input("Continue with power routing? (y/n): ")
    if response.lower() != 'y':
        print("Skipping power routing")
        return 0, 0

    VIA_SEARCH_RADIUS = 2.5  # mm
    layer_id = board.GetLayerID("F.Cu")

    vdd_routed = 0
    gnd_routed = 0
    failed = 0

    for idx, (led_num, fp) in enumerate(led_footprints):
        # Get VDD (pin 2) and GND (pin 3) pads
        vdd_pad = get_pad_by_number(fp, 2)
        gnd_pad = get_pad_by_number(fp, 3)

        if not vdd_pad or not gnd_pad:
            print(f"  Warning: Pads not found for {LED_PREFIX}{led_num}")
            failed += 1
            continue

        # Find nearest vias
        vdd_via, vdd_dist = find_nearest_via(board, vdd_pad.GetPosition(), VIA_SEARCH_RADIUS)
        gnd_via, gnd_dist = find_nearest_via(board, gnd_pad.GetPosition(), VIA_SEARCH_RADIUS)

        # Route VDD
        if vdd_via:
            pad_net = vdd_pad.GetNet()
            via_net = vdd_via.GetNet()

            # Assign VIA net if empty
            if not via_net or via_net.GetNetname() == "":
                vdd_via.SetNet(pad_net)
                via_net = pad_net

            # Create track if nets match
            if pad_net.GetNetname() == via_net.GetNetname():
                track = pcbnew.PCB_TRACK(board)
                track.SetStart(vdd_pad.GetPosition())
                track.SetEnd(vdd_via.GetPosition())
                track.SetWidth(pcbnew.FromMM(POWER_TRACE_WIDTH))
                track.SetLayer(layer_id)
                track.SetNet(pad_net)
                board.Add(track)
                vdd_routed += 1
            else:
                failed += 1
        else:
            failed += 1

        # Route GND
        if gnd_via:
            pad_net = gnd_pad.GetNet()
            via_net = gnd_via.GetNet()

            if not via_net or via_net.GetNetname() == "":
                gnd_via.SetNet(pad_net)
                via_net = pad_net

            if pad_net.GetNetname() == via_net.GetNetname():
                track = pcbnew.PCB_TRACK(board)
                track.SetStart(gnd_pad.GetPosition())
                track.SetEnd(gnd_via.GetPosition())
                track.SetWidth(pcbnew.FromMM(POWER_TRACE_WIDTH))
                track.SetLayer(layer_id)
                track.SetNet(pad_net)
                board.Add(track)
                gnd_routed += 1
            else:
                failed += 1
        else:
            failed += 1

        if (idx + 1) % 25 == 0:
            print(f"  Processed {idx + 1}/{len(led_footprints)} LEDs...")

    total_routed = vdd_routed + gnd_routed
    print(f"\n✓ Routed {total_routed} power connections")
    print(f"  VDD: {vdd_routed}, GND: {gnd_routed}")
    if failed > 0:
        print(f"  ⚠ {failed} connections failed (via too far or net mismatch)")

    return vdd_routed, gnd_routed


# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    """
    Main function - executes all steps
    """
    print("\n" + "="*60)
    print("10×10 LED Matrix Test Sample Generator")
    print("="*60)
    print(f"Configuration:")
    print(f"  Matrix: {COLS}×{ROWS} = {TOTAL_LEDS} LEDs")
    print(f"  Data chain: Single continuous serpentine ({PIXELS_PER_LANE} LEDs)")
    print(f"  Pitch: {PITCH_X}mm × {PITCH_Y}mm")
    print(f"  Start: ({START_X}, {START_Y})")
    print(f"\nThis will:")
    print(f"  1. Place LEDs in full-width serpentine pattern")
    print(f"  2. Rotate LEDs in 2×2 blocks for optimal via access")
    print(f"  3. Place VDD vias (center of 2×2 blocks)")
    print(f"  4. Place GND vias (expanded grid)")
    print(f"  5. Route data connections")
    print(f"  6. Route power to vias")

    response = input("\nContinue? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled")
        return

    board = pcbnew.GetBoard()

    # Get LED footprints
    led_footprints = get_led_footprints(board)

    if len(led_footprints) != TOTAL_LEDS:
        print(f"\nWarning: Found {len(led_footprints)} LEDs, expected {TOTAL_LEDS}")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return

    # Execute all steps with pauses
    place_leds(board, led_footprints)

    # Refresh after placement
    pcbnew.Refresh()

    # Place VDD vias first
    vdd_vias = place_vdd_vias(board)
    if vdd_vias == 0:
        print("\n✓ Stopped after LED placement")
        return

    # Refresh so user can see VDD vias
    pcbnew.Refresh()

    # Place GND vias second
    gnd_vias = place_gnd_vias(board)
    if gnd_vias == 0:
        print("\n✓ Stopped after VDD via placement")
        return

    # Refresh after all vias
    pcbnew.Refresh()
    print(f"\n✓ Total power vias placed: {vdd_vias + gnd_vias} ({vdd_vias} VDD + {gnd_vias} GND)")

    data_segments = route_data_connections(board, led_footprints)
    if data_segments == 0:
        print("\n✓ Stopped after via placement")
        return

    # Refresh after data routing
    pcbnew.Refresh()

    vdd_routed, gnd_routed = route_power_to_vias(board, led_footprints)
    if vdd_routed == 0 and gnd_routed == 0:
        print("\n✓ Stopped after data routing")
        return

    # Final summary
    print("\n" + "="*60)
    print("✓ COMPLETE!")
    print("="*60)
    print("Next steps:")
    print("  1. Review the layout in PCB editor")
    print("  2. Add power planes (VDD and GND) on inner layers")
    print("  3. Add board edge and mounting holes")
    print("  4. Run DRC to check for issues")
    print("  5. Generate Gerber files for manufacturing")

    # Refresh board
    pcbnew.Refresh()
    print("\nBoard refreshed!")


if __name__ == "__main__":
    main()
