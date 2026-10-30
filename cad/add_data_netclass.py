#!/usr/bin/env python3
"""
Add a 'Data' netclass to the project and assign all LED-chain DOUT/DIN
nets to it. The class uses a 0.1 mm track and 0.1 mm clearance (0.3 mm
total) so a trace fits through the 0.4 mm gap between adjacent LED pads.
Vias shrink to 0.4 mm Ø / 0.2 mm drill for the same reason.

The 0.1 mm values are also PCBWay's standard 4/4 mil floor, so the project's
board-level min clearance / track width are raised to them too. The LED pads
carry a 0.05 mm local clearance override; the board floor is what makes DRC
measure their real gaps.

Targets:
  <project>.kicad_pro  add the class, its patterns and the board floor
  <board>.kicad_pcb    narrow existing data tracks to the class width, then push
                       straight jogs that sit closer than the class clearance to
                       a pad away from it (the row wraparounds at both grid edges)

Idempotent — reruns overwrite the 'Data' class entry and leave compliant
tracks alone.
Run: python3 cad/add_data_netclass.py cad/led_bage.kicad_pro cad/led_bage.kicad_pcb
"""
import copy
import fnmatch
import json
import math
import sys
from collections import defaultdict
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

    rules = data["board"]["design_settings"]["rules"]
    rules["min_clearance"] = max(rules.get("min_clearance", 0), DATA_CLASS["clearance"])
    rules["min_track_width"] = DATA_CLASS["track_width"]

    # pretty-print to match KiCad's 2-space indent
    path.write_text(json.dumps(data, indent=2) + "\n")
    print(f"{path}: Data netclass + {len(PATTERNS)} patterns written")


def is_data(net: str) -> bool:
    return any(fnmatch.fnmatchcase(net, p["pattern"]) for p in PATTERNS)


def gap_to_pad(start, end, half_width, pad):
    """(dx, dy, gap) in nm between a horizontal track and a pad's bounding box."""
    bb = pad.GetBoundingBox()
    dx = max(0, bb.GetLeft() - max(start.x, end.x), min(start.x, end.x) - bb.GetRight())
    dy = max(0, bb.GetTop() - start.y, start.y - bb.GetBottom())
    return dx, dy, math.hypot(dx, dy) - half_width


def apply(path: Path) -> None:
    import pcbnew  # only the board target needs KiCad

    board = pcbnew.LoadBoard(str(path))
    width = pcbnew.FromMM(DATA_CLASS["track_width"])
    clearance = pcbnew.FromMM(DATA_CLASS["clearance"])
    cell = pcbnew.FromMM(1)

    tracks = board.Tracks()  # GetTracks() iteration is broken under Python 3.14
    items = [tracks[i].Cast() for i in range(len(tracks))]
    data = [t for t in items if t.Type() == pcbnew.PCB_TRACE_T and is_data(t.GetNetname())]
    for t in data:
        t.SetWidth(width)

    pads = defaultdict(list)  # 1 mm spatial hash
    fixed = {(v.GetPosition().x, v.GetPosition().y) for v in items if v.Type() == pcbnew.PCB_VIA_T}
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            pos = pad.GetPosition()
            pads[pos.x // cell, pos.y // cell].append(pad)
            fixed.add((pos.x, pos.y))
    ends = defaultdict(list)
    for t in data:
        for p in (t.GetStart(), t.GetEnd()):
            ends[t.GetNetCode(), p.x, p.y].append(t)

    def follow(seg, p, dy):
        """New position for endpoint p of seg moved by dy, sliding along its neighbour."""
        if (p.x, p.y) in fixed:
            return None
        others = [n for n in ends[seg.GetNetCode(), p.x, p.y] if n is not seg]
        if len(others) != 1:
            return None
        n = others[0]
        q = n.GetEnd() if n.GetStart() == p else n.GetStart()
        if q.y == p.y or abs(dy) >= abs(q.y - p.y):
            return None  # horizontal neighbour, or it would collapse
        return n, pcbnew.VECTOR2I(p.x + round(dy * (q.x - p.x) / (q.y - p.y)), p.y + dy)

    moved, stuck = 0, []
    for t in data:
        s, e = pcbnew.VECTOR2I(t.GetStart()), pcbnew.VECTOR2I(t.GetEnd())  # copies, not views
        if s.y != e.y:
            continue
        near = [pad for gx in range(min(s.x, e.x) // cell - 1, max(s.x, e.x) // cell + 2)
                for gy in (s.y // cell - 1, s.y // cell, s.y // cell + 1) for pad in pads[gx, gy]
                if pad.GetNetCode() != t.GetNetCode() and pad.IsOnLayer(t.GetLayer())]
        for pad in near:
            dx, _, gap = gap_to_pad(s, e, width / 2, pad)
            if gap >= clearance:
                continue
            # straight above/below the pad: slide the jog away, 5 um grid
            away = -1 if pad.GetPosition().y > s.y else 1
            dy = away * math.ceil((clearance - gap) / 5000) * 5000
            moves = [follow(t, s, dy), follow(t, e, dy)]
            if dx or None in moves:
                stuck.append(f"{t.GetNetname()} @ ({pcbnew.ToMM(s.x):.3f}, {pcbnew.ToMM(s.y):.3f})")
                break
            for (n, new), old in zip(moves, (s, e)):
                n.SetStart(new) if n.GetStart() == old else n.SetEnd(new)
                ends[t.GetNetCode(), new.x, new.y].append(n)
            t.SetStart(moves[0][1])
            t.SetEnd(moves[1][1])
            for p in (moves[0][1], moves[1][1]):
                ends[t.GetNetCode(), p.x, p.y].append(t)
            moved += 1
            break

    board.Save(str(path))
    print(f"{path}: {len(data)} data tracks at {DATA_CLASS['track_width']} mm, {moved} jogs moved off pads")
    for s in stuck:
        print("  needs a manual fix:", s)


if __name__ == "__main__":
    for p in map(Path, sys.argv[1:]):
        apply(p) if p.suffix == ".kicad_pcb" else patch(p)
