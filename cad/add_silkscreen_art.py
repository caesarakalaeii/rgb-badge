#!/usr/bin/env python3
"""
Silkscreen artwork: cad/art/front.png -> F.SilkS, cad/art/back.png -> B.SilkS.

The PNGs are 1-bit exports of the artist's layers in p2610.psd ("Layer 2" is the
front, "Layer 4" the back). They were drawn on a canvas laid over KiCad
screenshots of the board, so pixel (0, 0) is the outline's top-left corner and
the canvas width is the board width. Both screenshots are KiCad's normal
top-down view, so the back art goes on B.SilkS unmirrored, where the artist put
it clear of J1, J2 and the caps.

Each ink island becomes one filled silkscreen polygon (holes fractured in),
grouped as art-front / art-back. Idempotent: re-running replaces both groups.
Run inside `nix develop` (needs cv2):
    python3 cad/add_silkscreen_art.py [board.kicad_pcb], then python3 cad/test_board.py
"""
import pathlib
import sys

import cv2
import pcbnew
from redesign_top_band import LEFT, RIGHT, TOP, mm, remove

ART = pathlib.Path(__file__).resolve().with_name("art")
SIDES = {"front": pcbnew.F_SilkS, "back": pcbnew.B_SilkS}
SIMPLIFY_PX = 0.5  # max outline deviation from the pixel staircase (~19 um)


def ink_polygons(png):
    """Return (px size in mm, SHAPE_POLY_SET of the ink traced through pixel centers)."""
    img = cv2.imread(str(png), cv2.IMREAD_GRAYSCALE)
    px = (RIGHT - LEFT) / img.shape[1]
    contours, hierarchy = cv2.findContours((img > 127).astype("uint8"), cv2.RETR_CCOMP,
                                           cv2.CHAIN_APPROX_NONE)
    poly = pcbnew.SHAPE_POLY_SET()

    def append(contour, outline, hole=-1):
        for x, y in contour[:, 0].tolist():
            poly.Append(mm(LEFT + (x + 0.5) * px), mm(TOP + (y + 0.5) * px), outline, hole)

    # RETR_CCOMP: top-level contours are ink outlines, their children are holes.
    for i, (_, _, child, parent) in enumerate(hierarchy[0]):
        outer = cv2.approxPolyDP(contours[i], SIMPLIFY_PX, True)
        if parent >= 0 or len(outer) < 3:
            continue
        outline = poly.NewOutline()
        append(outer, outline)
        while child >= 0:
            hole = cv2.approxPolyDP(contours[child], SIMPLIFY_PX, True)
            if len(hole) >= 3:
                append(hole, outline, poly.NewHole(outline))
            child = hierarchy[0][child][0]
    return px, poly


def add_art(path):
    board = pcbnew.LoadBoard(path)

    drawings = board.Drawings()  # GetDrawings() iteration is broken under Python 3.14
    for s in [drawings[i].Cast() for i in range(len(drawings))]:
        if (g := s.GetParentGroup()) and g.GetName().startswith("art-"):
            g.RemoveItem(s)
            remove(board, s)
    for g in board.Groups():
        if g.GetName().startswith("art-"):
            remove(board, g)

    max_error = board.GetDesignSettings().m_MaxError
    for side, layer in SIDES.items():
        px, poly = ink_polygons(ART / f"{side}.png")
        # Contours run through boundary pixel centers; grow half a pixel back to the ink edge.
        poly.Inflate(mm(px / 2), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, max_error, True)
        poly.Fracture()

        group = pcbnew.PCB_GROUP(board)
        group.SetName(f"art-{side}")
        board.Add(group)
        for i in range(poly.OutlineCount()):
            s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_POLY)
            s.SetPolyShape(pcbnew.SHAPE_POLY_SET(poly.Outline(i)))
            s.SetFilled(True)
            s.SetWidth(0)
            s.SetLayer(layer)
            board.Add(s)
            group.AddItem(s)

    board.Save(path)
    print(f"{path}: silkscreen art from {ART} placed")


if __name__ == "__main__":
    for p in sys.argv[1:] or ["led_bage.kicad_pcb"]:
        add_art(p)
