#!/usr/bin/env python3
"""
Smart Power Routing Script for VIA-Optimized LED Matrix
Routes VDD and GND pins from LEDs to nearby VIAs with intelligent net handling

Strategy:
- Routes each pad to the closest VIA
- If VIA has no net, assigns it based on which pad type is closer
- Creates short, direct traces from pads to VIAs

This script should be run AFTER:
1. place_led_matrix_via_optimized.py
2. place_power_vias.py

Usage in KiCad Scripting Console:
    exec(open('scripts/route_power_to_vias_smart.py').read())
"""

import pcbnew
import math

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
TRACK_WIDTH = 0.25        # mm (trace width for power connections)
VIA_SEARCH_RADIUS = 2.5   # mm (how far to search for VIAs)

# Layer for routing
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


def distance(pos1, pos2):
    """Calculate distance between two positions"""
    dx = pcbnew.ToMM(pos2.x - pos1.x)
    dy = pcbnew.ToMM(pos2.y - pos1.y)
    return math.sqrt(dx * dx + dy * dy)


def find_nearest_via(board, pad_pos, max_distance_mm):
    """Find the nearest VIA to a pad within max_distance"""
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


def route_pad_to_via(board, pad, via, pad_name):
    """Route a pad to a via, handling net assignment"""
    pad_pos = pad.GetPosition()
    via_pos = via.GetPosition()
    pad_net = pad.GetNet()
    via_net = via.GetNet()

    # If VIA has no net, assign it the pad's net
    if not via_net or via_net.GetNetname() == "":
        via.SetNet(pad_net)
        via_net = pad_net

    # Only route if nets match
    if pad_net.GetNetname() == via_net.GetNetname():
        create_track(board, pad_pos, via_pos, TRACK_WIDTH, ROUTING_LAYER, pad_net)
        return True
    else:
        return False


def route_power_connections():
    """Main routing function"""
    board = pcbnew.GetBoard()

    led_footprints = get_led_footprints(board)

    print(f"\nSmart power routing for {len(led_footprints)} LEDs")
    print(f"Track width: {TRACK_WIDTH}mm")
    print(f"VIA search radius: {VIA_SEARCH_RADIUS}mm")
    print(f"Layer: {ROUTING_LAYER}\n")

    vdd_routed = 0
    gnd_routed = 0
    vdd_failed = 0
    gnd_failed = 0

    for idx, (led_num, fp) in enumerate(led_footprints):
        # Get VDD (pin 2) and GND (pin 3) pads
        vdd_pad = get_pad_by_number(fp, 2)
        gnd_pad = get_pad_by_number(fp, 3)

        if not vdd_pad or not gnd_pad:
            print(f"  Warning: Pads not found for {LED_PREFIX}{led_num}")
            continue

        # Find nearest VIA for each pad
        vdd_pos = vdd_pad.GetPosition()
        gnd_pos = gnd_pad.GetPosition()

        vdd_via, vdd_dist = find_nearest_via(board, vdd_pos, VIA_SEARCH_RADIUS)
        gnd_via, gnd_dist = find_nearest_via(board, gnd_pos, VIA_SEARCH_RADIUS)

        # Route VDD
        if vdd_via:
            if route_pad_to_via(board, vdd_pad, vdd_via, "VDD"):
                vdd_routed += 1
            else:
                vdd_failed += 1
        else:
            vdd_failed += 1

        # Route GND
        if gnd_via:
            if route_pad_to_via(board, gnd_pad, gnd_via, "GND"):
                gnd_routed += 1
            else:
                gnd_failed += 1
        else:
            gnd_failed += 1

        if (idx + 1) % 100 == 0:
            print(f"  Processed {idx + 1}/{len(led_footprints)} LEDs...")

    print(f"\n✓ Routing complete")
    print(f"  VDD connections: {vdd_routed} routed, {vdd_failed} failed")
    print(f"  GND connections: {gnd_routed} routed, {gnd_failed} failed")
    print(f"  Total tracks created: {vdd_routed + gnd_routed}")

    if vdd_failed > 0 or gnd_failed > 0:
        print(f"\n⚠ Some connections failed:")
        print(f"  - VIA might be too far (>{VIA_SEARCH_RADIUS}mm)")
        print(f"  - VIA might be assigned to wrong net")
        print(f"  - Check VIA placement and LED rotations")

    print(f"\nNext steps:")
    print(f"  1. Review power routing in PCB editor")
    print(f"  2. Add power planes on inner layers (VDD and GND)")
    print(f"  3. Connect VIAs to power planes with stitching vias")
    print(f"  4. Run DRC to check for issues")

    # Refresh board
    pcbnew.Refresh()
    print("\nDone! Board refreshed.")


if __name__ == "__main__":
    route_power_connections()
