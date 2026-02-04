#!/usr/bin/env python3
"""
Remove all tracks and vias from KiCad PCB
Complete routing cleanup script

Usage in KiCad Scripting Console:
    exec(open('scripts/remove_all_routing.py').read())
"""

import pcbnew

def remove_all_routing():
    """Remove all tracks and vias from the board"""
    board = pcbnew.GetBoard()

    print("Scanning for tracks and vias...")

    # Collect all tracks and vias
    tracks_to_remove = []
    vias_to_remove = []

    for item in board.GetTracks():
        if item.Type() == pcbnew.PCB_VIA_T:
            vias_to_remove.append(item)
        elif item.Type() == pcbnew.PCB_TRACE_T:
            tracks_to_remove.append(item)

    print(f"Found {len(tracks_to_remove)} tracks")
    print(f"Found {len(vias_to_remove)} vias")

    total = len(tracks_to_remove) + len(vias_to_remove)

    if total == 0:
        print("No tracks or vias found on board")
        return

    print(f"\nThis will remove ALL routing from the board!")
    response = input(f"Remove all {total} items? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled")
        return

    # Remove all tracks
    if len(tracks_to_remove) > 0:
        print(f"\nRemoving {len(tracks_to_remove)} tracks...")
        removed_count = 0

        for track in tracks_to_remove:
            board.Remove(track)
            removed_count += 1

            if removed_count % 1000 == 0:
                print(f"  Removed {removed_count}/{len(tracks_to_remove)} tracks...")

        print(f"✓ Removed {removed_count} tracks")

    # Remove all vias
    if len(vias_to_remove) > 0:
        print(f"\nRemoving {len(vias_to_remove)} vias...")
        removed_count = 0

        for via in vias_to_remove:
            board.Remove(via)
            removed_count += 1

            if removed_count % 1000 == 0:
                print(f"  Removed {removed_count}/{len(vias_to_remove)} vias...")

        print(f"✓ Removed {removed_count} vias")

    print(f"\n✓ Successfully removed all routing ({total} items total)")

    # Refresh board
    pcbnew.Refresh()
    print("Board refreshed")

if __name__ == "__main__":
    remove_all_routing()
