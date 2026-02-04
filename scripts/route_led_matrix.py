#!/usr/bin/env python3
"""
LED Matrix Auto-Router for KiCad PCB
Routes data traces for 8-lane serpentine LED matrix

Usage in KiCad Scripting Console:
    exec(open('scripts/route_led_matrix.py').read())
"""

import pcbnew

# Matrix configuration (must match placement script)
COLS = 64
ROWS = 40
PITCH_X = 1.5625  # mm
PITCH_Y = 1.625   # mm
START_X = 10.0
START_Y = 10.0

# Routing configuration
TRACE_WIDTH = 0.15  # mm (adjust based on fab capabilities)
VIA_DRILL = 0.3     # mm
VIA_SIZE = 0.6      # mm

# Layer definitions
LAYER_TOP = pcbnew.F_Cu
LAYER_BOTTOM = pcbnew.B_Cu

# LED prefix
LED_PREFIX = "D"

# 8-lane configuration
LANES = 8
COLS_PER_LANE = COLS // LANES  # 8 columns per lane
PIXELS_PER_LANE = COLS_PER_LANE * ROWS  # 320 pixels per lane


def get_pad_position(footprint, pad_name):
    """Get the absolute position of a specific pad on a footprint"""
    for pad in footprint.Pads():
        if pad.GetName() == pad_name:
            return pad.GetPosition()
    return None


def create_track(board, start_pos, end_pos, width_mm, layer):
    """Create a track between two points"""
    track = pcbnew.PCB_TRACK(board)
    track.SetStart(start_pos)
    track.SetEnd(end_pos)
    track.SetWidth(pcbnew.FromMM(width_mm))
    track.SetLayer(layer)
    board.Add(track)
    return track


def create_via(board, position, drill_mm, size_mm):
    """Create a via at the specified position"""
    via = pcbnew.PCB_VIA(board)
    via.SetPosition(position)
    via.SetDrill(pcbnew.FromMM(drill_mm))
    via.SetWidth(pcbnew.FromMM(size_mm))
    board.Add(via)
    return via


def get_footprint_by_ref(board, reference):
    """Get footprint by reference designator"""
    for fp in board.GetFootprints():
        if fp.GetReference() == reference:
            return fp
    return None


def route_data_lanes(board, led_footprints):
    """
    Route data traces for 8-lane serpentine pattern
    Connects DOUT of each LED to DIN of next LED in chain
    """
    print("Routing data traces for 8-lane serpentine pattern...")

    # Pad configuration for XL-1010RGBC-2812B:
    # Pad 1: DOUT
    # Pad 2: VDD
    # Pad 3: GND
    # Pad 4: DIN
    PAD_DIN = "4"
    PAD_DOUT = "1"

    tracks_created = 0

    for lane in range(LANES):
        print(f"  Routing lane {lane + 1}/{LANES}...")

        # Route each lane's chain
        for pixel_in_lane in range(PIXELS_PER_LANE - 1):
            # Calculate LED index in the overall array
            led_idx = lane * PIXELS_PER_LANE + pixel_in_lane

            if led_idx >= len(led_footprints):
                break

            # Current LED (DOUT) -> Next LED (DIN)
            current_led_num, current_fp = led_footprints[led_idx]
            next_led_num, next_fp = led_footprints[led_idx + 1]

            # Get pad positions
            dout_pos = get_pad_position(current_fp, PAD_DOUT)
            din_pos = get_pad_position(next_fp, PAD_DIN)

            if dout_pos and din_pos:
                # Create direct track (for now - may need vias/dogleg for complex routing)
                create_track(board, dout_pos, din_pos, TRACE_WIDTH, LAYER_TOP)
                tracks_created += 1
            else:
                print(f"    Warning: Could not find pads for {LED_PREFIX}{current_led_num} -> {LED_PREFIX}{next_led_num}")

        if (lane + 1) % 2 == 0:
            print(f"    Created {tracks_created} tracks so far...")

    print(f"\n✓ Created {tracks_created} data traces")
    return tracks_created


def route_power_vias(board, led_footprints, add_vias=False):
    """
    Add vias from power pads to internal planes
    Set add_vias=True to actually create the vias
    """
    PAD_VDD = "2"
    PAD_GND = "3"

    if not add_vias:
        print("\nPower via placement (currently disabled):")
        print("  Set add_vias=True in route_power_vias() to enable")
        print("  This will add 5120 vias (2 per LED) for power distribution")
        return 0

    print("\nAdding power vias to planes...")
    vias_created = 0

    for idx, (led_num, fp) in enumerate(led_footprints):
        # Get VDD and GND pad positions
        vdd_pos = get_pad_position(fp, PAD_VDD)
        gnd_pos = get_pad_position(fp, PAD_GND)

        # Add via at VDD pad (connects to Layer 3 power plane)
        if vdd_pos:
            create_via(board, vdd_pos, VIA_DRILL, VIA_SIZE)
            vias_created += 1

        # Add via at GND pad (connects to Layer 2 ground plane)
        if gnd_pos:
            create_via(board, gnd_pos, VIA_DRILL, VIA_SIZE)
            vias_created += 1

        if (idx + 1) % 500 == 0:
            print(f"  Added {vias_created} vias so far...")

    print(f"\n✓ Created {vias_created} power vias")
    return vias_created


def print_power_routing_instructions():
    """Print instructions for manual power plane setup"""
    print("\nPower plane setup (manual steps in KiCad):")
    print("  1. Draw zones on Layer 2 (GND) and Layer 3 (VDD)")
    print("  2. Set zone priority and clearances")
    print("  3. Configure thermal reliefs for LED power pads")
    print("  4. Fill zones (B key)")
    print("  5. Optionally add via stitching for lower impedance")


def verify_footprint_pads(board):
    """Verify LED footprint pad configuration"""
    print("\nVerifying LED footprint pad configuration...")

    # Get first LED to check pad names
    first_led = get_footprint_by_ref(board, f"{LED_PREFIX}1")
    if not first_led:
        print(f"  Error: Could not find {LED_PREFIX}1")
        return False

    print(f"  Found {LED_PREFIX}1, checking pads:")
    for pad in first_led.Pads():
        pad_name = pad.GetName()
        pad_pos = pad.GetPosition()
        print(f"    Pad {pad_name}: ({pcbnew.ToMM(pad_pos.x):.3f}, {pcbnew.ToMM(pad_pos.y):.3f})")

    print("\n  ⚠ IMPORTANT: Verify pad numbering matches your footprint!")
    print("  Update PAD_DIN and PAD_DOUT in the script if needed.")
    return True


def main():
    """Main routing function"""
    board = pcbnew.GetBoard()

    # Verify footprint configuration
    if not verify_footprint_pads(board):
        return

    response = input("\nDo the pad numbers look correct? Continue with routing? (y/n): ")
    if response.lower() != 'y':
        print("Aborted. Please update PAD_DIN and PAD_DOUT in the script.")
        return

    # Get LED footprints (same as placement script)
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

    # Route data lanes
    route_data_lanes(board, led_footprints)

    # Power vias (DISABLED - not needed with copper pours!)
    # DO NOT ENABLE - use copper zones on In1.Cu and In2.Cu instead
    route_power_vias(board, led_footprints, add_vias=False)

    # Power routing instructions
    print_power_routing_instructions()

    # Refresh board
    pcbnew.Refresh()
    print("\n✓ Done! Board refreshed.")
    print("\nNext steps:")
    print("  1. Review data traces")
    print("  2. Add copper pours for GND (Layer 2) and VDD (Layer 3)")
    print("  3. Configure thermal reliefs on power pads")
    print("  4. Add decoupling capacitors on bottom layer")
    print("  5. Fill zones and run DRC")


if __name__ == "__main__":
    main()
