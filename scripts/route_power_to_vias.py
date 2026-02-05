#!/usr/bin/env python3
"""
Automatic Power Routing Script for VIA-Optimized LED Matrix
Routes VDD and GND pins from each LED to the shared center VIA in their 2×2 block

This script should be run AFTER:
1. place_led_matrix_via_optimized.py
2. place_power_vias.py

Usage in KiCad Scripting Console:
    exec(open('scripts/route_power_to_vias.py').read())
"""

import pcbnew

# Matrix configuration (must match placement scripts)
LED_COLS = 40
LED_ROWS = 64
PITCH_X = 1.5625  # mm
PITCH_Y = 1.625   # mm
START_X = 10.0    # mm
START_Y = 10.0    # mm

# LED configuration
LED_PREFIX = "D"
NUM_LANES = 8
ROWS_PER_LANE = LED_ROWS // NUM_LANES

# Routing configuration
TRACK_WIDTH = 0.2        # mm (trace width for power connections)
VIA_OFFSET_X = PITCH_X / 2
VIA_OFFSET_Y = PITCH_Y / 2

# Layer for routing (usually top layer)
ROUTING_LAYER = "F.Cu"


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
                pass

    led_footprints.sort(key=lambda x: x[0])
    return led_footprints


def get_via_at_position(board, x_mm, y_mm, tolerance_mm=0.1):
    """Find a VIA near the specified position"""
    x_nm = pcbnew.FromMM(x_mm)
    y_nm = pcbnew.FromMM(y_mm)
    tolerance_nm = pcbnew.FromMM(tolerance_mm)

    for track in board.GetTracks():
        if track.Type() == pcbnew.PCB_VIA_T:
            via_pos = track.GetPosition()
            dx = abs(via_pos.x - x_nm)
            dy = abs(via_pos.y - y_nm)
            if dx < tolerance_nm and dy < tolerance_nm:
                return track

    return None


def get_pad_by_number(footprint, pad_number):
    """Get a specific pad from a footprint by its number"""
    for pad in footprint.Pads():
        if pad.GetNumber() == str(pad_number):
            return pad
    return None


def create_track(board, start_pos, end_pos, width_mm, layer_name, net):
    """Create a track segment"""
    track = pcbnew.PCB_TRACK(board)
    track.SetStart(start_pos)
    track.SetEnd(end_pos)
    track.SetWidth(pcbnew.FromMM(width_mm))

    layer_id = board.GetLayerID(layer_name)
    track.SetLayer(layer_id)

    if net:
        track.SetNet(net)

    board.Add(track)
    return track


def route_power_to_vias():
    """Main routing function"""
    board = pcbnew.GetBoard()

    led_footprints = get_led_footprints(board)
    pixels_per_lane = ROWS_PER_LANE * LED_COLS

    print(f"\nRouting power connections for {len(led_footprints)} LEDs")
    print(f"Track width: {TRACK_WIDTH}mm")
    print(f"Layer: {ROUTING_LAYER}\n")

    tracks_created = 0
    vias_not_found = 0
    pads_not_found = 0

    for idx, (led_num, fp) in enumerate(led_footprints):
        # Calculate LED position in grid (same logic as placement script)
        lane = idx // pixels_per_lane
        pixel_in_lane = idx % pixels_per_lane
        row_in_lane = pixel_in_lane // LED_COLS
        col = pixel_in_lane % LED_COLS

        # Serpentine: reverse direction on odd rows
        if row_in_lane % 2 == 1:
            col = LED_COLS - 1 - col

        row = lane * ROWS_PER_LANE + row_in_lane

        # Calculate which 2×2 block this LED belongs to
        block_col = col // 2
        block_row = row // 2

        # Calculate center VIA position for this block
        via_x = START_X + (block_col * 2 * PITCH_X) + VIA_OFFSET_X
        via_y = START_Y + (block_row * 2 * PITCH_Y) + VIA_OFFSET_Y

        # Find the VIA
        via = get_via_at_position(board, via_x, via_y)
        if not via:
            vias_not_found += 1
            if vias_not_found <= 5:  # Only print first few warnings
                print(f"  Warning: VIA not found for {LED_PREFIX}{led_num} at ({via_x:.3f}, {via_y:.3f})")
            continue

        via_pos = via.GetPosition()
        via_net = via.GetNet()

        # Get VDD (pin 2) and GND (pin 3) pads
        vdd_pad = get_pad_by_number(fp, 2)
        gnd_pad = get_pad_by_number(fp, 3)

        if not vdd_pad or not gnd_pad:
            pads_not_found += 1
            if pads_not_found <= 5:
                print(f"  Warning: VDD or GND pad not found for {LED_PREFIX}{led_num}")
            continue

        # Create tracks from pads to VIA
        # VDD pad to VIA (if VIA is on VDD net)
        vdd_pos = vdd_pad.GetPosition()
        vdd_net = vdd_pad.GetNet()

        # Only route if pad and via are on same net, or via has no net yet
        if via_net.GetNetname() == "GND":
            # Route GND pad to VIA
            gnd_pos = gnd_pad.GetPosition()
            create_track(board, gnd_pos, via_pos, TRACK_WIDTH, ROUTING_LAYER, via_net)
            tracks_created += 1
        elif via_net.GetNetname() == "VDD":
            # Route VDD pad to VIA
            create_track(board, vdd_pos, via_pos, TRACK_WIDTH, ROUTING_LAYER, via_net)
            tracks_created += 1
        else:
            # VIA has no net or unknown net, skip
            pass

        if (idx + 1) % 100 == 0:
            print(f"  Processed {idx + 1}/{len(led_footprints)} LEDs...")

    print(f"\n✓ Routing complete")
    print(f"  Tracks created: {tracks_created}")
    if vias_not_found > 0:
        print(f"  ⚠ VIAs not found: {vias_not_found}")
    if pads_not_found > 0:
        print(f"  ⚠ Pads not found: {pads_not_found}")

    print(f"\nNext steps:")
    print(f"  1. Review power routing in PCB editor")
    print(f"  2. Some VIAs should be manually changed to VDD net")
    print(f"  3. Re-run this script to route VDD connections")
    print(f"  4. Add power planes on inner layers")
    print(f"  5. Run DRC to check for issues")

    # Refresh board
    pcbnew.Refresh()
    print("\nDone! Board refreshed.")


if __name__ == "__main__":
    route_power_to_vias()
