#!/usr/bin/env python3
"""
End-to-end checks for led_bage.kicad_pcb: outline, lanyard holes, power entry,
silkscreen art, fab minimums, fab outputs (gerbers, BOM, centroid, JLCPCB
assembly files), DRC.

Run from anywhere (needs pcbnew + kicad-cli, e.g. inside `nix develop`):
    python3 cad/test_board.py
"""
import csv
import functools
import json
import pathlib
import re
import subprocess
import tempfile

import pcbnew
from export_fab import export
from PIL import Image

PCB = pathlib.Path(__file__).resolve().with_name("led_bage.kicad_pcb")
mm = pcbnew.ToMM

# Rounded-rectangle outline (see ADR 0001)
LEFT, TOP, RIGHT, BOTTOM, CORNER_R = 1.3, -19.7, 72.36, 130.4, 5.0
CENTER_X = (LEFT + RIGHT) / 2


def close(a, b, tol=0.05):
    return abs(a - b) <= tol


def test_outline(board):
    bb = board.GetBoardEdgesBoundingBox()
    got = [mm(v) for v in (bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom())]
    # bbox includes half the 0.1 mm edge line width
    assert all(close(g, w, 0.1) for g, w in zip(got, (LEFT, TOP, RIGHT, BOTTOM))), got
    drawings = board.Drawings()  # GetDrawings() iteration is broken under Python 3.14
    arcs = [s for s in (drawings[i].Cast() for i in range(len(drawings)))
            if s.GetLayer() == pcbnew.Edge_Cuts and s.GetShape() == pcbnew.SHAPE_T_ARC]
    assert len(arcs) == 4, f"{len(arcs)} corner arcs"
    assert all(close(mm(a.GetRadius()), CORNER_R) for a in arcs)


def test_lanyard_holes(board):
    for ref, x in (("H1", LEFT + 6.5), ("H2", RIGHT - 6.5)):
        fp = board.FindFootprintByReference(ref)
        assert fp, f"{ref} missing"
        assert fp.IsBoardOnly(), f"{ref} must be board-only (no schematic symbol)"
        holes = [p for p in fp.Pads() if close(mm(p.GetDrillSize().x), 5.0)]
        assert len(holes) == 1, f"{ref}: expected one 5 mm hole"
        pos = holes[0].GetPosition()
        assert close(mm(pos.x), x) and close(mm(pos.y), TOP + 6.5), (ref, mm(pos.x), mm(pos.y))
        assert all(p.GetNetname() == "GND" for p in fp.Pads())


def test_j2_centered_on_top_edge(board):
    j2 = board.FindFootprintByReference("J2")
    cy = j2.GetCourtyard(pcbnew.B_CrtYd).BBox()
    assert close((mm(cy.GetLeft()) + mm(cy.GetRight())) / 2, CENTER_X, 0.1)
    assert close(mm(cy.GetTop()), TOP, 0.1), "J2 mating face must sit on the top edge"


def test_u1_blocks_reverse_polarity(board):
    # P-FET: drain to the input (VDD), source to the protected rail (VDD_S),
    # otherwise the body diode conducts when the plug is reversed.
    for pad in board.FindFootprintByReference("U1").Pads():
        fn = pad.GetPinFunction().split("_")[0]
        want = {"S": "VDD_S", "D": "VDD", "G": "Net-(U1-G)"}[fn]
        assert pad.GetNetname() == want, (pad.GetNumber(), fn, pad.GetNetname())
    r3 = {p.GetNetname() for p in board.FindFootprintByReference("R3").Pads()}
    assert r3 == {"VDD_S", "Net-(U1-G)"}, f"R3 must bridge gate and source: {r3}"


def test_silkscreen_art(board):
    # cad/art/<side>.png (canvas = board outline) lands as filled polygons on that side's silk.
    drawings = board.Drawings()
    art = {}
    for s in (drawings[i].Cast() for i in range(len(drawings))):
        if (g := s.GetParentGroup()) and g.GetName().startswith("art-"):
            art.setdefault(g.GetName(), []).append(s)
    for side, layer in (("front", pcbnew.F_SilkS), ("back", pcbnew.B_SilkS)):
        shapes = art.get(f"art-{side}")
        assert shapes, f"art-{side} group missing"
        assert all(s.GetLayer() == layer and s.IsSolidFill() for s in shapes), side
        ink = Image.open(PCB.with_name("art") / f"{side}.png").convert("1")
        px = (RIGHT - LEFT) / ink.width
        bb = shapes[0].GetBoundingBox()
        for s in shapes[1:]:
            bb.Merge(s.GetBoundingBox())
        got = [mm(v) for v in (bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom())]
        x0, y0, x1, y1 = ink.getbbox()
        want = [LEFT + x0 * px, TOP + y0 * px, LEFT + x1 * px, TOP + y1 * px]
        assert all(close(g, w, 2 * px) for g, w in zip(got, want)), (side, got, want)
        area = sum(s.GetPolyShape().Area() for s in shapes) / 1e12  # nm^2 -> mm^2
        want_area = ink.histogram()[255] * px * px
        assert abs(area - want_area) < 0.03 * want_area, (side, area, want_area)


def test_through_hole_pads_have_mask_openings():
    # Every PTH pad must keep F.Mask/B.Mask in the saved file, not just in memory.
    layer_lists = re.findall(r"\(pad \"[^\"]*\" thru_hole[\s\S]*?\(layers ([^)]*)\)", PCB.read_text())
    assert layer_lists and all('"*.Mask"' in l or ('"F.Mask"' in l and '"B.Mask"' in l)
                               for l in layer_lists), set(layer_lists)


def test_fab_minimums():
    # Board-level floors make DRC measure real copper gaps: the LED pads carry a
    # 0.05 mm local clearance override that would otherwise hide them.
    # PCBWay standard capability: 4/4 mil (0.1 mm) track/space.
    rules = json.loads(PCB.with_suffix(".kicad_pro").read_text())["board"]["design_settings"]["rules"]
    assert rules["min_clearance"] >= 0.1, rules["min_clearance"]
    assert rules["min_track_width"] >= 0.1, rules["min_track_width"]


FAB = tempfile.TemporaryDirectory()


@functools.cache
def fab_outputs():
    """Export once per run; returns {file name: rows} for the CSVs and the set of all file names."""
    out = pathlib.Path(FAB.name)
    export(out)
    csvs = {p.name: list(csv.DictReader(p.read_text().splitlines())) for p in out.glob("*.csv")}
    return csvs, {p.name for p in out.rglob("*") if p.is_file()}


def test_fab_outputs():
    # Gerbers for every layer, and a BOM and centroid file that agree part for part.
    csvs, files = fab_outputs()
    for layer in ("F_Cu", "In1_Cu", "In2_Cu", "In3_Cu", "In4_Cu", "B_Cu", "F_Mask", "B_Mask",
                  "F_Paste", "B_Paste", "F_Silkscreen", "B_Silkscreen", "Edge_Cuts"):
        assert any(f"-{layer}." in f for f in files), f"no gerber for {layer}"
    assert {"led_bage-PTH.drl", "led_bage-gerbers.zip"} <= files, files
    bom, pos = csvs["led_bage-bom.csv"], {row["Ref"] for row in csvs["led_bage-pos.csv"]}
    assert all(row["Manufacturer"] and row["Manufacturer Part Number"] for row in bom), bom
    placed = {ref for row in bom for ref in row["Designator"].split(",")}
    assert sum(int(row["Qty"]) for row in bom) == len(placed)
    assert pos == placed, (pos ^ placed)


def test_jlc_outputs(board):
    # JLCPCB BOM/CPL: every placed part has an LCSC number, designator cells stay under
    # what JLC accepts (2000 characters), and placements match what its preview shows as correct.
    csvs, _ = fab_outputs()
    bom, cpl = csvs["led_bage-bom-jlc.csv"], {r["Designator"]: r for r in csvs["led_bage-cpl-jlc.csv"]}
    placed = {row["Ref"] for row in csvs["led_bage-pos.csv"]}
    assert all(row["LCSC Part #"].startswith("C") for row in bom), bom
    assert max(len(row["Designator"]) for row in bom) <= 2000
    assert {ref for row in bom for ref in row["Designator"].split(",")} == placed == set(cpl)
    lcsc = {ref: row["LCSC Part #"] for row in bom for ref in row["Designator"].split(",")}
    assert lcsc["R3"] == "C25741", "C173682 has no placement model at JLC"

    def at(ref):
        r = cpl[ref]
        return float(r["Mid X"].removesuffix("mm")), float(r["Mid Y"].removesuffix("mm")), float(r["Rotation"])
    # Bottom angles are read from below; SOT-23-5 and the PowerPAK model sit 90 deg off KiCad's.
    for ref, rot in (("C1", 135), ("C655", 90), ("U2", 90), ("U1", 0), ("C650", 90), ("DA1", 0),
                     ("J2", 180), ("J1", 180)):
        assert close(at(ref)[2], rot), (ref, at(ref))
    # JLC anchors its connector models mid-pads; KiCad's J2 origin is pin 1, J1's is 0.175 mm off.
    for ref in ("J1", "J2"):
        pads = [p.GetPosition() for p in board.FindFootprintByReference(ref).Pads()]
        x = (min(p.x for p in pads) + max(p.x for p in pads)) / 2
        y = (min(p.y for p in pads) + max(p.y for p in pads)) / 2
        assert close(at(ref)[0], mm(x), 0.01) and close(at(ref)[1], -mm(y), 0.01), (ref, at(ref), mm(x), mm(y))


def test_drc():
    with tempfile.TemporaryDirectory() as tmp:
        rpt = pathlib.Path(tmp, "drc.rpt")
        subprocess.run(
            ["kicad-cli", "pcb", "drc", "--refill-zones", "--schematic-parity",
             "--severity-all", "-o", str(rpt), str(PCB)],
            check=True, capture_output=True)
        report = rpt.read_text()
    assert "Found 0 unconnected pads" in report, report
    errors = re.findall(r"^(\[\w+\]: .*)\n.*; error$", report, re.MULTILINE)
    assert not errors, "\n".join(errors)
    conflicts = re.findall(r"\[net_conflict\].*\n.*\n.* of (U1|R3|J2|TVS1|C28) ", report)
    assert not conflicts, f"schematic/PCB net mismatch on {conflicts}"


if __name__ == "__main__":
    board = pcbnew.LoadBoard(str(PCB))
    for test in (test_outline, test_lanyard_holes, test_j2_centered_on_top_edge,
                 test_u1_blocks_reverse_polarity, test_silkscreen_art, test_jlc_outputs):
        test(board)
        print("ok", test.__name__)
    for test in (test_through_hole_pads_have_mask_openings, test_fab_minimums,
                 test_fab_outputs, test_drc):
        test()
        print("ok", test.__name__)
