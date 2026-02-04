#!/usr/bin/env python3
"""
LED Matrix Router - ALL routing on bottom layer
Routes all data connections via bottom layer to avoid any top-layer conflicts

Usage in KiCad Scripting Console:
    exec(open('scripts/route_led_matrix_bottom_layer.py').read())
"""

import pcbnew

# Matrix configuration
COLS = 64
ROWS = 40
LED_PREFIX = "D"

# Routing configuration
TRACE_WIDTH = 0.08   # mm (narrower for tighter clearance)
VIA_DRILL = 0.3     # mm
VIA_SIZE = 0.6      # mm

# Layers
LAYER_TOP = pcbnew.F_Cu
LAYER_BOTTOM = pcbnew.B_Cu


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


def route_all_bottom_layer(board, led_footprints):
    """
    Route ALL connections on bottom layer.
    The pads themselves provide the layer transition (through-hole plating).
    We just need traces on bottom layer between pads.
    """
    print("Routing ALL connections on bottom layer...")

    PAD_DIN = 4
    PAD_DOUT = 1

    total_traces = 0
    errors = 0

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

        dout_pos = dout_pad.GetPosition()
        din_pos = din_pad.GetPosition()
        net = dout_pad.GetNet()

        # Simple: Just trace on bottom layer between pads
        # The pads themselves connect top and bottom layers
        create_track_with_net(board, dout_pos, din_pos, TRACE_WIDTH, LAYER_BOTTOM, net)
        total_traces += 1

        # Progress indicator
        if (idx + 1) % 100 == 0:
            print(f"  Routed {idx + 1}/{len(led_footprints)-1} connections...")

    print(f"\n✓ Created {total_traces} bottom-layer traces")
    print(f"  - No vias needed (pads provide layer connection)")

    if errors > 0:
        print(f"⚠ {errors} connections had errors")

    return total_traces


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
    print(f"\nRouting strategy:")
    print(f"  - ALL connections routed on bottom layer (B.Cu)")
    print(f"  - Top layer stays clean (LEDs only)")
    print(f"  - Pads provide top↔bottom layer connection (no vias needed)")
    print(f"  - Expected: {len(led_footprints)-1} traces on bottom layer\n")

    response = input("Start routing? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled")
        return

    # Route everything on bottom
    route_all_bottom_layer(board, led_footprints)

    # Refresh board
    pcbnew.Refresh()
    print("\n✓ Done! Board refreshed.")
    print("\nNext steps:")
    print("  1. Add GND plane on In1.Cu")
    print("  2. Add VDD plane on In2.Cu")
    print("  3. Fill zones and run DRC")


if __name__ == "__main__":
    main()
