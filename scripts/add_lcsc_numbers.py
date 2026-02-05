#!/usr/bin/env python3
"""
LCSC Part Number Assignment Script
Adds LCSC part numbers to footprints in KiCad PCB

Usage in KiCad Scripting Console:
    exec(open('scripts/add_lcsc_numbers.py').read())
"""

import pcbnew

# LCSC Part Number Mapping
# Add your LCSC part numbers here
LCSC_MAPPING = {
    # LED
    "XL-1010RGBC-WS2812B": "C5349953",  # Your LED from datasheet link

    # Connectors (examples - update with your actual parts)
    # "CONNECTOR_NAME": "CXXXXXXX",

    # Resistors (examples - update with your actual parts)
    # "220": "C17960",   # 0805 220Ω resistor
    # "470": "C17710",   # 0805 470Ω resistor

    # Capacitors (examples - update with your actual parts)
    # "100nF": "C49678",  # 0805 100nF capacitor
    # "10uF": "C15850",   # 0805 10µF capacitor
}

# Alternative: Map by reference pattern
# Useful when all components of same type use same LCSC number
LCSC_BY_REFERENCE = {
    # "D": "C5349953",  # All D* references (LEDs)
    # "R": "C17960",    # All R* references (resistors)
    # "C": "C49678",    # All C* references (capacitors)
}


def add_lcsc_field(footprint, lcsc_number):
    """Add or update LCSC field in footprint"""
    # Check if LCSC field already exists
    field_found = False
    for field in footprint.GetFields():
        if field.GetName().upper() in ["LCSC", "LCSC PART", "LCSC_PART"]:
            field.SetText(lcsc_number)
            field_found = True
            break

    # If field doesn't exist, create it
    if not field_found:
        # Note: In KiCad 9, field creation might work differently
        # This is a simplified version
        print(f"  Note: Add LCSC field manually for {footprint.GetReference()}: {lcsc_number}")


def assign_lcsc_numbers():
    """Main function to assign LCSC numbers"""
    board = pcbnew.GetBoard()

    print("\n" + "="*70)
    print("LCSC PART NUMBER ASSIGNMENT")
    print("="*70)

    assigned = 0
    not_found = 0
    not_found_list = []

    for fp in board.GetFootprints():
        ref = fp.GetReference()
        value = fp.GetValue()
        footprint_name = fp.GetFPID().GetLibItemName().GetUniString()

        # Skip special components
        skip_prefixes = ["TP", "H", "MH", "FID", "LOGO", ""]
        if any(ref.startswith(prefix) for prefix in skip_prefixes):
            continue

        lcsc_number = None

        # Try to find LCSC by value
        if value in LCSC_MAPPING:
            lcsc_number = LCSC_MAPPING[value]
        # Try to find by footprint name
        elif footprint_name in LCSC_MAPPING:
            lcsc_number = LCSC_MAPPING[footprint_name]
        # Try to find by reference prefix
        else:
            ref_prefix = ''.join(c for c in ref if c.isalpha())
            if ref_prefix in LCSC_BY_REFERENCE:
                lcsc_number = LCSC_BY_REFERENCE[ref_prefix]

        if lcsc_number:
            add_lcsc_field(fp, lcsc_number)
            assigned += 1
            if assigned <= 5:  # Show first few
                print(f"✓ {ref} ({value}): {lcsc_number}")
        else:
            not_found += 1
            not_found_list.append((ref, value, footprint_name))

    print(f"\n{'='*70}")
    print(f"Assigned: {assigned} components")
    print(f"Not found: {not_found} components")

    if not_found > 0:
        print(f"\n⚠ Components without LCSC numbers:")
        for ref, value, footprint in not_found_list[:20]:  # Show first 20
            print(f"  - {ref}: {value} ({footprint})")
        if not_found > 20:
            print(f"  ... and {not_found - 20} more")

        print(f"\nTo assign LCSC numbers:")
        print(f"  1. Search for parts on https://jlcpcb.com/parts")
        print(f"  2. Add part numbers to LCSC_MAPPING in this script")
        print(f"  3. Run this script again")

    print("\n")


if __name__ == "__main__":
    assign_lcsc_numbers()
