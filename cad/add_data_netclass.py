#!/usr/bin/env python3
"""
Add a 'Data' netclass to the project and assign all LED-chain DOUT/DIN
nets to it. The class uses a 0.1 mm track and 0.1 mm clearance (0.3 mm
total) so a trace fits through the 0.4 mm gap between adjacent LED pads.
Vias shrink to 0.4 mm Ø / 0.2 mm drill for the same reason.

Target: <project>.kicad_pro files. Idempotent — reruns overwrite the
existing 'Data' class entry in place.
"""
import copy
import json
import sys
from pathlib import Path

DATA_CLASS = {
    "bus_width": 12,
    "clearance": 0.1,
    "diff_pair_gap": 0.15,
    "diff_pair_via_gap": 0.15,
    "diff_pair_width": 0.1,
    "line_style": 0,
    "microvia_diameter": 0.3,
    "microvia_drill": 0.1,
    "name": "Data",
    "pcb_color": "rgba(0, 0, 0, 0.000)",
    "priority": 0,
    "schematic_color": "rgba(0, 0, 0, 0.000)",
    "track_width": 0.1,
    "tuning_profile": "",
    "via_diameter": 0.4,
    "via_drill": 0.2,
    "wire_width": 6,
}

PATTERNS = [
    {"netclass": "Data", "pattern": "Net-(D*-DOUT)"},
    {"netclass": "Data", "pattern": "Net-(D*-DIN)"},
    {"netclass": "Data", "pattern": "DATA*"},
]


def patch(path: Path) -> None:
    data = json.loads(path.read_text())
    ns = data.setdefault("net_settings", {})
    classes = ns.setdefault("classes", [])
    classes[:] = [c for c in classes if c.get("name") != "Data"]
    classes.append(copy.deepcopy(DATA_CLASS))

    existing_patterns = ns.get("netclass_patterns") or []
    # drop any prior Data-class patterns so we can re-add cleanly
    kept = [p for p in existing_patterns if p.get("netclass") != "Data"]
    ns["netclass_patterns"] = kept + [copy.deepcopy(p) for p in PATTERNS]

    # pretty-print to match KiCad's 2-space indent
    path.write_text(json.dumps(data, indent=2) + "\n")
    print(f"{path}: Data netclass + {len(PATTERNS)} patterns written")


if __name__ == "__main__":
    for p in sys.argv[1:]:
        patch(Path(p))
