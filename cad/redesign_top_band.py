#!/usr/bin/env python3
"""
Rounded-rectangle outline with a top band for the lanyard holes and J2 (ADR 0001),
plus the corrected reverse-polarity power entry (ADR 0002).

  - Edge.Cuts: 71.06 x 150.1 mm rectangle, 5 mm corner radius. The old top strip
    edge (y=-3.7) moves up 16 mm to y=-19.7.
  - H1/H2: 5 mm plated lanyard holes with an 11 mm GND ring on every copper layer
    and 12 GND stitch pads, 6.5 mm in from the top and side edges. Board-only
    footprints, so they need no schematic symbol.
  - J2 (horizontal JST VH, cable exits through the top edge) moves into the band,
    centered between the holes. J1 and the lane buffers stay put.
  - Power entry: J2 -> F/B VDD pours -> U1 drain/EP -> U1 source pins -> F.Cu
    VDD_S pour -> via field into the In2/In3 VDD_S planes. Replaces the 0.5-2 mm
    traces that could not carry the ~30 A peak.
  - Inner GND/VDD_S planes grow to the new outline.

Idempotent: re-running rebuilds the outline, eyelets and named pours from scratch.
Run: python3 cad/redesign_top_band.py [board.kicad_pcb], then python3 cad/test_board.py
"""
import math
import sys

import pcbnew

# Outline
LEFT, TOP, RIGHT, BOTTOM = 1.3, -19.7, 72.36, 130.4
CORNER_R = 5.0
EDGE_LINE_WIDTH = 0.1
CENTER_X = (LEFT + RIGHT) / 2

# Lanyard eyelets
HOLE_INSET = 6.5          # hole center from top and side edges
HOLE_DIA = 5.0
EYELET_OD = 11.0
STITCH_RING_R = 4.25
STITCH_PAD_DIA = 0.5
STITCH_DRILL = 0.3
STITCH_COUNT = 12

# J2: footprint origin is pin 1. Courtyard spans pin1 -2.5..+38.15 in x and
# -15.45..+1.9 in y (rotated so the mating face points up).
J2_PIN1 = (CENTER_X - (38.15 - 2.5) / 2, TOP - 0.05 + 15.45)
J1_REF_POS = (5.2, 2.5)   # free B.Silkscreen corner; J2's silk now runs above J1

# Old J2 pin positions now dangling on the GND traces from R4/C28 and TVS1
GND_VIAS = [(42.16, 11.7), (49.55, 11.7), (50.6, 11.7)]
# R3 pad 1 is boxed in by R4's GND trace, so the VDD_S pour can't reach it.
R3_SOURCE_STUB = ((39.51, 9.1), (39.51, 10.6), 0.3)

# Pours: (name, net, layer, priority, polygon)
POURS = [
    ("VDD_IN_F", "VDD", pcbnew.F_Cu, 1,
     [(15, -19.2), (58, -19.2), (58, 11.6), (44.5, 11.6), (44.5, 7.0), (15, 7.0)]),
    ("VDD_IN_B", "VDD", pcbnew.B_Cu, 1,
     [(15, -19.2), (58, -19.2), (58, 7.0), (32.2, 7.0), (32.2, -2.6), (15, -2.6)]),
    ("VDD_S_OUT_F", "VDD_S", pcbnew.F_Cu, 0,
     [(32.0, 7.3), (44.2, 7.3), (44.2, 13.3), (32.0, 13.3)]),
]
POUR_CLEARANCE = 0.3
POUR_MIN_WIDTH = 0.25
POUR_SPOKE_WIDTH = 1.0

# VDD_S via field below U1 into the inner planes (~1.25 A per via at 30 A)
VDD_S_VIAS = [(32.8 + 0.85 * i, y) for y in (10.2, 11.05, 11.9) for i in range(8)]
VIA_DIA, VIA_DRILL = 0.5, 0.3

INNER_ZONE_RECT = (-1.0, -21.0, 74.5, 132.0)


def mm(v):
    return pcbnew.FromMM(v)


def vec(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))


def remove(board, item):
    board.Remove(item)
    # Garbage-collecting a removed item's wrapper corrupts SWIG's type table
    # (KiCad 10 + Python 3.14), so leak it instead.
    item.thisown = False


def edge_shape(board, shape):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(shape)
    s.SetLayer(pcbnew.Edge_Cuts)
    s.SetWidth(mm(EDGE_LINE_WIDTH))
    board.Add(s)
    return s


def build_outline(board):
    drawings = board.Drawings()  # GetDrawings() iteration is broken under Python 3.14
    for d in [drawings[i] for i in range(len(drawings)) if drawings[i].GetLayer() == pcbnew.Edge_Cuts]:
        remove(board, d)
    r = CORNER_R
    for x1, y1, x2, y2 in ((LEFT + r, TOP, RIGHT - r, TOP), (RIGHT, TOP + r, RIGHT, BOTTOM - r),
                           (RIGHT - r, BOTTOM, LEFT + r, BOTTOM), (LEFT, BOTTOM - r, LEFT, TOP + r)):
        seg = edge_shape(board, pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(vec(x1, y1))
        seg.SetEnd(vec(x2, y2))
    d = r * (1 - math.sqrt(0.5))  # corner-to-arc-midpoint offset per axis
    for cx, cy, sx, sy, ex, ey, mx, my in (
            (LEFT + r, TOP + r, LEFT, TOP + r, LEFT + r, TOP, LEFT + d, TOP + d),
            (RIGHT - r, TOP + r, RIGHT - r, TOP, RIGHT, TOP + r, RIGHT - d, TOP + d),
            (RIGHT - r, BOTTOM - r, RIGHT, BOTTOM - r, RIGHT - r, BOTTOM, RIGHT - d, BOTTOM - d),
            (LEFT + r, BOTTOM - r, LEFT + r, BOTTOM, LEFT, BOTTOM - r, LEFT + d, BOTTOM - d)):
        edge_shape(board, pcbnew.SHAPE_T_ARC).SetArcGeometry(vec(sx, sy), vec(mx, my), vec(ex, ey))


def pth_pad(fp, x, y, size, drill, net):
    pad = pcbnew.PAD(fp)
    pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
    pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
    pad.SetSize(vec(size, size))
    pad.SetDrillSize(vec(drill, drill))
    pad.SetPosition(vec(x, y))
    pad.SetNumber("1")
    # Copy: AllCuMask() is KiCad's shared static, and mutating it makes every
    # through-hole pad save without "*.Mask" (no solder-mask opening).
    layers = pcbnew.LSET(pcbnew.LSET.AllCuMask())
    layers.AddLayer(pcbnew.F_Mask)
    layers.AddLayer(pcbnew.B_Mask)
    pad.SetLayerSet(layers)
    pad.SetNet(net)
    fp.Add(pad)


def add_eyelet(board, ref, cx, cy):
    gnd = board.FindNet("GND")
    fp = pcbnew.FOOTPRINT(board)
    board.Add(fp)
    fp.SetPosition(vec(cx, cy))
    fp.SetReference(ref)
    fp.Reference().SetVisible(False)
    fp.SetValue(f"Lanyard_Eyelet_{HOLE_DIA:g}mm")
    fp.Value().SetVisible(False)
    fp.SetAttributes(pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES)
    fp.SetBoardOnly(True)
    pth_pad(fp, cx, cy, EYELET_OD, HOLE_DIA, gnd)
    for i in range(STITCH_COUNT):
        a = 2 * math.pi * i / STITCH_COUNT
        pth_pad(fp, cx + STITCH_RING_R * math.cos(a), cy + STITCH_RING_R * math.sin(a),
                STITCH_PAD_DIA, STITCH_DRILL, gnd)


def add_via(board, x, y, net):
    if any(v.GetPosition() == vec(x, y) for v in board.TracksInNet(net.GetNetCode())
           if v.Type() == pcbnew.PCB_VIA_T):
        return
    via = pcbnew.PCB_VIA(board)
    via.SetPosition(vec(x, y))
    via.SetWidth(pcbnew.F_Cu, mm(VIA_DIA))
    via.SetDrill(mm(VIA_DRILL))
    via.SetNet(net)
    board.Add(via)


def add_pour(board, name, net, layer, priority, pts):
    zone = pcbnew.ZONE(board)
    zone.SetZoneName(name)
    zone.SetLayer(layer)
    zone.SetNet(board.FindNet(net))
    zone.SetAssignedPriority(priority)
    zone.SetLocalClearance(mm(POUR_CLEARANCE))
    zone.SetMinThickness(mm(POUR_MIN_WIDTH))
    zone.SetPadConnection(pcbnew.ZONE_CONNECTION_THT_THERMAL)
    zone.SetThermalReliefSpokeWidth(mm(POUR_SPOKE_WIDTH))
    zone.SetThermalReliefGap(mm(0.5))
    zone.Outline().NewOutline()
    for x, y in pts:
        zone.Outline().Append(mm(x), mm(y))
    board.Add(zone)


def rebuild_power_entry(board):
    vdd, vdd_s, gnd = (board.FindNet(n) for n in ("VDD", "VDD_S", "GND"))

    # Old J2-to-U1 traces; the pours replace them.
    for t in board.TracksInNet(vdd.GetNetCode()):
        if t.Type() != pcbnew.PCB_VIA_T:
            remove(board, t)

    # ADR 0002: drain on the input, source on the protected rail.
    drains = []
    for pad in board.FindFootprintByReference("U1").Pads():
        fn = pad.GetPinFunction().split("_")[0]
        if fn == "S":
            pad.SetNet(vdd_s)
        elif fn == "D":
            pad.SetNet(vdd)
            drains.append(pad)
    for pad in board.FindFootprintByReference("R3").Pads():
        if pad.GetNumber() == "1":
            pad.SetNet(vdd_s)
    # Vias in the drain pads/EP now tie the drain to the B.Cu VDD pour.
    for v in board.TracksInNet(vdd_s.GetNetCode()):
        if v.Type() == pcbnew.PCB_VIA_T and any(p.HitTest(v.GetPosition()) for p in drains):
            v.SetNet(vdd)

    for x, y in GND_VIAS:
        add_via(board, x, y, gnd)
    for x, y in VDD_S_VIAS:
        add_via(board, x, y, vdd_s)

    (x1, y1), (x2, y2), width = R3_SOURCE_STUB
    if not any(t.GetStart() == vec(x1, y1) and t.GetEnd() == vec(x2, y2)
               for t in board.TracksInNet(vdd_s.GetNetCode())):
        stub = pcbnew.PCB_TRACK(board)
        stub.SetStart(vec(x1, y1))
        stub.SetEnd(vec(x2, y2))
        stub.SetWidth(mm(width))
        stub.SetLayer(pcbnew.F_Cu)
        stub.SetNet(vdd_s)
        board.Add(stub)

    names = {p[0] for p in POURS}
    for z in [z for z in board.Zones() if z.GetZoneName() in names]:
        remove(board, z)
    for pour in POURS:
        add_pour(board, *pour)


def redesign(path):
    board = pcbnew.LoadBoard(path)

    build_outline(board)

    for ref in ("H1", "H2"):
        if fp := board.FindFootprintByReference(ref):
            remove(board, fp)
    add_eyelet(board, "H1", LEFT + HOLE_INSET, TOP + HOLE_INSET)
    add_eyelet(board, "H2", RIGHT - HOLE_INSET, TOP + HOLE_INSET)

    j2 = board.FindFootprintByReference("J2")
    j2.SetPosition(vec(*J2_PIN1))
    board.FindFootprintByReference("J1").Reference().SetPosition(vec(*J1_REF_POS))

    rebuild_power_entry(board)

    x0, y0, x1, y1 = INNER_ZONE_RECT
    for z in board.Zones():
        if z.GetFirstLayer() in (pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.In3_Cu, pcbnew.In4_Cu):
            z.Outline().RemoveAllContours()
            z.Outline().NewOutline()
            for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
                z.Outline().Append(mm(x), mm(y))

    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.Save(path)
    print(f"{path}: top band, lanyard holes and power entry rebuilt")


if __name__ == "__main__":
    for p in sys.argv[1:] or ["led_bage.kicad_pcb"]:
        redesign(p)
