#!/usr/bin/env python3
"""
BOM Generator for JLCPCB
Exports Bill of Materials from KiCad PCB in JLCPCB-compatible CSV format

Usage in KiCad Scripting Console:
    exec(open('scripts/generate_bom.py').read())

Or run from command line:
    python3 scripts/generate_bom.py
"""

import pcbnew
import csv
from collections import defaultdict
import os

# Output file configuration
OUTPUT_DIR = "bom"
OUTPUT_FILENAME = "bom_jlcpcb.csv"

# JLCPCB BOM columns
BOM_COLUMNS = [
    "Comment",           # Component value/description
    "Designator",        # Reference designators (comma-separated)
    "Footprint",         # KiCad footprint name
    "LCSC Part #",       # LCSC part number (if available)
]


def get_all_footprints(board):
    """Get all footprints from the board"""
    footprints = []
    for fp in board.GetFootprints():
        footprints.append(fp)
    return footprints


def extract_lcsc_part_number(footprint):
    """Extract LCSC part number from footprint properties"""
    # Check custom fields for LCSC part number
    for field in footprint.GetFields():
        field_name = field.GetName().upper()
        if field_name in ["LCSC", "LCSC PART", "LCSC_PART", "LCSC PART #", "JLCPCB"]:
            return field.GetText()

    # Check description or other properties
    return ""


def group_components(footprints):
    """Group components by value and footprint"""
    groups = defaultdict(list)

    for fp in footprints:
        # Skip if component is on back side and marked as "Do Not Place"
        # or if it's a test point, mounting hole, etc.
        ref = fp.GetReference()
        value = fp.GetValue()
        footprint_name = fp.GetFPID().GetLibItemName().GetUniString()

        # Skip certain reference prefixes that typically aren't placed
        skip_prefixes = ["TP", "H", "MH", "FID", "LOGO", ""]
        if any(ref.startswith(prefix) for prefix in skip_prefixes):
            continue

        # Create grouping key
        lcsc = extract_lcsc_part_number(fp)
        key = (value, footprint_name, lcsc)
        groups[key].append(ref)

    return groups


def sort_references(refs):
    """Sort reference designators naturally (D1, D2, D10 instead of D1, D10, D2)"""
    def natural_key(ref):
        import re
        # Split into prefix and number
        match = re.match(r'([A-Z]+)(\d+)', ref)
        if match:
            prefix, number = match.groups()
            return (prefix, int(number))
        return (ref, 0)

    return sorted(refs, key=natural_key)


def generate_bom(board, output_path):
    """Generate BOM and save to CSV"""
    footprints = get_all_footprints(board)
    groups = group_components(footprints)

    # Prepare BOM data
    bom_data = []
    total_components = 0

    for (value, footprint, lcsc), refs in groups.items():
        sorted_refs = sort_references(refs)
        designators = ",".join(sorted_refs)

        bom_data.append({
            "Comment": value,
            "Designator": designators,
            "Footprint": footprint,
            "LCSC Part #": lcsc,
        })

        total_components += len(refs)

    # Sort BOM by reference designator prefix and value
    bom_data.sort(key=lambda x: (x["Designator"].split(',')[0][0], x["Comment"]))

    # Write to CSV
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=BOM_COLUMNS)
        writer.writeheader()
        writer.writerows(bom_data)

    return bom_data, total_components


def print_bom_summary(bom_data, total_components):
    """Print BOM summary to console"""
    print("\n" + "="*70)
    print("BOM SUMMARY")
    print("="*70)
    print(f"Total unique parts: {len(bom_data)}")
    print(f"Total components: {total_components}")
    print("\n" + "-"*70)
    print(f"{'Qty':<6} {'Value':<20} {'Designators':<30} {'LCSC':<15}")
    print("-"*70)

    for item in bom_data:
        refs = item["Designator"].split(',')
        qty = len(refs)

        # Truncate long designator lists
        if len(refs) > 5:
            designators_display = f"{refs[0]}...{refs[-1]} ({qty} total)"
        else:
            designators_display = item["Designator"]

        print(f"{qty:<6} {item['Comment']:<20} {designators_display:<30} {item['LCSC Part #']:<15}")

    print("="*70)


def main():
    """Main BOM generation function"""
    board = pcbnew.GetBoard()

    # Create output directory if it doesn't exist
    project_path = board.GetFileName()
    project_dir = os.path.dirname(project_path)
    output_dir_path = os.path.join(project_dir, OUTPUT_DIR)

    if not os.path.exists(output_dir_path):
        os.makedirs(output_dir_path)

    output_file = os.path.join(output_dir_path, OUTPUT_FILENAME)

    print("\n" + "="*70)
    print("JLCPCB BOM GENERATOR")
    print("="*70)
    print(f"Project: {os.path.basename(project_path)}")
    print(f"Output: {output_file}")

    # Generate BOM
    bom_data, total_components = generate_bom(board, output_file)

    # Print summary
    print_bom_summary(bom_data, total_components)

    print(f"\n✓ BOM saved to: {output_file}")
    print("\nNext steps:")
    print("  1. Open the BOM CSV file")
    print("  2. Add LCSC part numbers for components without them")
    print("  3. Upload to JLCPCB along with Gerber files")
    print("  4. JLCPCB will match components for assembly service")

    # Check for missing LCSC numbers
    missing_lcsc = [item for item in bom_data if not item["LCSC Part #"]]
    if missing_lcsc:
        print(f"\n⚠ Warning: {len(missing_lcsc)} parts missing LCSC numbers:")
        for item in missing_lcsc[:10]:  # Show first 10
            refs = item["Designator"].split(',')
            print(f"  - {item['Comment']} ({len(refs)} pcs): {refs[0]}...")
        if len(missing_lcsc) > 10:
            print(f"  ... and {len(missing_lcsc) - 10} more")

    print("\n")


if __name__ == "__main__":
    main()
