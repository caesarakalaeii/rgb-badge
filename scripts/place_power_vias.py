#!/usr/bin/env python3
"""
Shared VIA Placement Script for VIA-Optimized LED Matrix
Places VIAs in the center of each 2×2 LED block for shared VDD/GND connections

This script should be run AFTER place_led_matrix_via_optimized.py

Layout: 40 columns × 64 rows of LEDs in 2×2 blocks
        = 20 × 32 = 640 shared VIAs

Usage in KiCad Scripting Console:
    exec(open('scripts/place_power_vias.py').read())
"""

import pcbnew

# Matrix configuration (must match place_led_matrix_via_optimized.py)
LED_COLS = 40
LED_ROWS = 64
PITCH_X = 1.5625  # mm
PITCH_Y = 1.625   # mm

# Starting position (must match place_led_matrix_via_optimized.py)
START_X = 10.0  # mm
START_Y = 10.0  # mm

# VIA configuration
VIA_SIZE = 0.4    # mm (drill diameter)
VIA_DRILL = 0.2   # mm (finished hole)

# VIA placement offset from LED grid origin
# VIAs go in the CENTER of each 2×2 LED block
VIA_OFFSET_X = PITCH_X / 2  # Half pitch to center between LEDs
VIA_OFFSET_Y = PITCH_Y / 2  # Half pitch to center between LEDs

# Nets for VDD and GND
# All VIAs will be assigned to GND by default
# You can manually change some to VDD in KiCad after placement
VDD_NET_NAME = "VDD"
GND_NET_NAME = "GND"


def create_via(board, x_mm, y_mm, net_name=None):
    """Create a via at the specified position"""
    x_nm = pcbnew.FromMM(x_mm)
    y_nm = pcbnew.FromMM(y_mm)

    via = pcbnew.PCB_VIA(board)
    via.SetPosition(pcbnew.VECTOR2I(x_nm, y_nm))
    via.SetDrill(pcbnew.FromMM(VIA_DRILL))
    via.SetWidth(pcbnew.FromMM(VIA_SIZE))

    # Set layers (through-hole via)
    via.SetLayerPair(board.GetLayerID("F.Cu"), board.GetLayerID("B.Cu"))

    # Assign net if specified
    if net_name:
        netinfo = board.FindNet(net_name)
        if netinfo and netinfo.GetNetname() == net_name:
            via.SetNet(netinfo)
        else:
            print(f"  Warning: Net '{net_name}' not found, VIA created without net assignment")

    board.Add(via)
    return via


def place_power_vias():
    """Place VIAs in the center of each 2×2 LED block"""
    board = pcbnew.GetBoard()

    # Calculate number of VIA positions
    via_cols = LED_COLS // 2  # One VIA per 2 LED columns
    via_rows = LED_ROWS // 2  # One VIA per 2 LED rows
    total_vias = via_cols * via_rows

    print(f"\nPlacing {total_vias} shared power VIAs")
    print(f"VIA grid: {via_cols} columns × {via_rows} rows")
    print(f"VIA size: {VIA_SIZE}mm (drill: {VIA_DRILL}mm)")
    print(f"Each VIA serves 4 LEDs (2×2 block)")

    # Check if nets exist
    gnd_net = board.FindNet(GND_NET_NAME)
    vdd_net = board.FindNet(VDD_NET_NAME)

    if gnd_net and gnd_net.GetNetname() == GND_NET_NAME:
        print(f"✓ Found net: {GND_NET_NAME}")
    else:
        print(f"⚠ Warning: Net '{GND_NET_NAME}' not found - VIAs will be created without net assignment")

    if vdd_net and vdd_net.GetNetname() == VDD_NET_NAME:
        print(f"✓ Found net: {VDD_NET_NAME}")

    print()

    vias_placed = 0

    # Place VIAs in grid
    for via_row in range(via_rows):
        for via_col in range(via_cols):
            # Calculate VIA position (center of 2×2 LED block)
            # VIA goes between LEDs at positions (2*col, 2*col+1) and (2*row, 2*row+1)
            via_x = START_X + (via_col * 2 * PITCH_X) + VIA_OFFSET_X
            via_y = START_Y + (via_row * 2 * PITCH_Y) + VIA_OFFSET_Y

            # Assign all VIAs to GND by default
            # You can manually change some to VDD in KiCad after placement
            create_via(board, via_x, via_y, net_name=GND_NET_NAME if gnd_net else None)
            vias_placed += 1

            if vias_placed % 100 == 0:
                print(f"  Placed {vias_placed}/{total_vias} VIAs...")

    # Report results
    via_area_width = (via_cols - 1) * 2 * PITCH_X
    via_area_height = (via_rows - 1) * 2 * PITCH_Y

    print(f"\n✓ Successfully placed {vias_placed} VIAs")
    print(f"\nVIA grid dimensions:")
    print(f"  Width: {via_area_width:.3f} mm ({via_cols} VIA columns)")
    print(f"  Height: {via_area_height:.3f} mm ({via_rows} VIA rows)")
    print(f"  VIA spacing: {2 * PITCH_X:.3f}mm × {2 * PITCH_Y:.3f}mm")

    print(f"\nNext steps:")
    print(f"  1. Review VIA placements in PCB editor")
    print(f"  2. Assign VIAs to VDD or GND nets as needed")
    print(f"  3. Add power planes or traces connecting VIAs")
    print(f"  4. Route data connections between LEDs")

    # Refresh board
    pcbnew.Refresh()
    print("\nDone! Board refreshed.")


if __name__ == "__main__":
    place_power_vias()
