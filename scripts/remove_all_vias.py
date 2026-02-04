#!/usr/bin/env python3
"""
Remove all vias from KiCad PCB
Emergency cleanup script

Usage in KiCad Scripting Console:
    exec(open('scripts/remove_all_vias.py').read())
"""

import pcbnew

def remove_all_vias():
    """Remove all vias from the board"""
    board = pcbnew.GetBoard()

    print("Scanning for vias...")

    # Collect all vias first (don't modify while iterating)
    vias_to_remove = []

    for item in board.GetTracks():
        if item.Type() == pcbnew.PCB_VIA_T:
            vias_to_remove.append(item)

    print(f"Found {len(vias_to_remove)} vias to remove")

    if len(vias_to_remove) == 0:
        print("No vias found on board")
        return

    response = input(f"Remove all {len(vias_to_remove)} vias? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled")
        return

    # Remove all vias
    print("Removing vias...")
    removed_count = 0

    for via in vias_to_remove:
        board.Remove(via)
        removed_count += 1

        if removed_count % 1000 == 0:
            print(f"  Removed {removed_count}/{len(vias_to_remove)} vias...")

    print(f"\n✓ Successfully removed {removed_count} vias")

    # Refresh board
    pcbnew.Refresh()
    print("Board refreshed")

if __name__ == "__main__":
    remove_all_vias()
