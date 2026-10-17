#!/usr/bin/env python3
"""
End-to-end checks for led_bage.kicad_pcb: outline, lanyard holes, power entry, DRC.

Run from anywhere (needs pcbnew + kicad-cli, e.g. inside `nix develop`):
    python3 cad/test_board.py
"""
import pathlib
import re
import subprocess
import tempfile

import pcbnew

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


def test_through_hole_pads_have_mask_openings():
    # Every PTH pad must keep F.Mask/B.Mask in the saved file, not just in memory.
    layer_lists = re.findall(r"\(pad \"[^\"]*\" thru_hole[\s\S]*?\(layers ([^)]*)\)", PCB.read_text())
    assert layer_lists and all('"*.Mask"' in l or ('"F.Mask"' in l and '"B.Mask"' in l)
                               for l in layer_lists), set(layer_lists)


def test_drc():
    with tempfile.TemporaryDirectory() as tmp:
        rpt = pathlib.Path(tmp, "drc.rpt")
        subprocess.run(
            ["kicad-cli", "pcb", "drc", "--refill-zones", "--schematic-parity",
             "--severity-all", "-o", str(rpt), str(PCB)],
            check=True, capture_output=True)
        report = rpt.read_text()
    assert "Found 0 unconnected pads" in report, report
    errors = re.findall(r"^(\[\w+\]: .*)\n.*; error$", report, re.M)
    assert not errors, "\n".join(errors)
    conflicts = re.findall(r"\[net_conflict\].*\n.*\n.* of (U1|R3|J2|TVS1|C28) ", report)
    assert not conflicts, f"schematic/PCB net mismatch on {conflicts}"


if __name__ == "__main__":
    board = pcbnew.LoadBoard(str(PCB))
    for test in (test_outline, test_lanyard_holes, test_j2_centered_on_top_edge,
                 test_u1_blocks_reverse_polarity):
        test(board)
        print("ok", test.__name__)
    for test in (test_through_hole_pads_have_mask_openings, test_drc):
        test()
        print("ok", test.__name__)
