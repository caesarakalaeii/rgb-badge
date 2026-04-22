#!/usr/bin/env python3
"""
Snap 0603 decoupling caps to the centers of 2x2 LED blocks on B.Cu,
rotated 45°. The interior VDD and GND LED fanout vias of each block fall
inside the cap's pad area (~0.25 mm off pad center, well within the 0.9 mm
pad), so no dedicated drop vias are needed — the cap pads pick up the
power planes through the existing LED fanout vias. Also strips any stray
vias that sit directly under a cap pad (leftovers from earlier passes that
added redundant drop vias).

Caps outside the LED grid bbox (MCU / connector decoupling) are left alone.
"""
import math
import sys
import pcbnew

LED_LIB = 'LED_SMD:LED_WS2812B-1010_PLCC4_1.0x1.0mm'
CAP_LIB_SUBSTR = 'C_0603'
MARGIN_NM = 3_000_000
STRAY_VIA_TOL_NM = 100_000  # 0.1 mm — only a via dropped exactly on a pad qualifies


def rectify(path: str) -> None:
    board = pcbnew.LoadBoard(path)

    leds = [fp for fp in board.GetFootprints() if fp.GetFPIDAsString() == LED_LIB]
    if not leds:
        print(f'{path}: no LEDs found')
        return
    xs = sorted({fp.GetPosition().x for fp in leds})
    ys = sorted({fp.GetPosition().y for fp in leds})
    if len(xs) % 2 or len(ys) % 2:
        print(f'{path}: LED grid {len(xs)}×{len(ys)} has odd dimension — 2x2 blocks impossible')
        return

    blocks = []
    for iy in range(0, len(ys), 2):
        cy = (ys[iy] + ys[iy + 1]) // 2
        for ix in range(0, len(xs), 2):
            cx = (xs[ix] + xs[ix + 1]) // 2
            blocks.append((cx, cy))
    blocks.sort(key=lambda c: (c[1], c[0]))

    x_min, x_max = xs[0] - MARGIN_NM, xs[-1] + MARGIN_NM
    y_min, y_max = ys[0] - MARGIN_NM, ys[-1] + MARGIN_NM
    caps_in_area = []
    for fp in board.GetFootprints():
        if CAP_LIB_SUBSTR not in fp.GetFPIDAsString():
            continue
        p = fp.GetPosition()
        if x_min <= p.x <= x_max and y_min <= p.y <= y_max:
            caps_in_area.append(fp)

    if len(caps_in_area) != len(blocks):
        print(f'{path}: WARNING — {len(caps_in_area)} caps in LED area vs {len(blocks)} blocks')
    caps_in_area.sort(key=lambda fp: (fp.GetPosition().y, fp.GetPosition().x))

    moved = 0
    for cap, (cx, cy) in zip(caps_in_area, blocks):
        cap.SetPosition(pcbnew.VECTOR2I(cx, cy))
        if cap.GetLayer() != pcbnew.B_Cu:
            cap.Flip(cap.GetPosition(), False)
        cap.SetOrientationDegrees(45.0)
        moved += 1

    cap_pad_positions = []
    for cap in caps_in_area[:len(blocks)]:
        for pad in cap.Pads():
            cap_pad_positions.append(pad.GetPosition())

    stray_removed = 0
    for t in list(board.GetTracks()):
        if t.GetClass() != 'PCB_VIA':
            continue
        vp = t.GetPosition()
        for pp in cap_pad_positions:
            if math.hypot(vp.x - pp.x, vp.y - pp.y) <= STRAY_VIA_TOL_NM:
                board.Remove(t)
                stray_removed += 1
                break

    board.Save(path)
    print(f'{path}: snapped {moved} caps to block centers, removed {stray_removed} stray drop vias')


if __name__ == '__main__':
    for p in sys.argv[1:]:
        rectify(p)
