#!/usr/bin/env python3
"""
Drop a grid of through-vias under the exposed thermal pad of one or more
footprints (default: Q2, the Si7145DP reverse-polarity FET).

The largest F.Cu pad on each target footprint is treated as the thermal
pad. Vias are tiled across that pad in a regular grid using the 'Default'
netclass via geometry, on the pad's own net (so the inner plane on the
matching net pulls heat away from the FET die).

Idempotent: skips grid points that already have a via on the same net
within one via-diameter, so re-running after small moves doesn't pile up
duplicate vias.
"""
import math
import sys
import pcbnew

DEFAULT_REFS = ['Q2']
DEFAULT_PITCH_MM = 1.2
DEFAULT_EDGE_CLEARANCE_MM = 0.3


def find_thermal_pad(fp):
    largest = None
    largest_area = 0
    for pad in fp.Pads():
        if not pad.IsOnLayer(pcbnew.F_Cu):
            continue
        sz = pad.GetSize()
        area = sz.x * sz.y
        if area > largest_area:
            largest = pad
            largest_area = area
    return largest


def existing_via_index(board):
    vias = []
    for t in board.GetTracks():
        if t.GetClass() == 'PCB_VIA':
            p = t.GetPosition()
            vias.append((p.x, p.y, t.GetNetCode()))
    return vias


def grid_points(half_x, half_y, pitch):
    nx = max(1, 1 + (2 * half_x) // pitch)
    ny = max(1, 1 + (2 * half_y) // pitch)
    xs = [-half_x + (2 * half_x * i) // (nx - 1) if nx > 1 else 0 for i in range(nx)]
    ys = [-half_y + (2 * half_y * j) // (ny - 1) if ny > 1 else 0 for j in range(ny)]
    return [(x, y) for y in ys for x in xs]


def add_for_ref(board, ref, pitch, edge_clear, via_dia, via_drill, existing):
    fp = board.FindFootprintByReference(ref)
    if fp is None:
        print(f'  {ref}: footprint not found')
        return 0

    pad = find_thermal_pad(fp)
    if pad is None:
        print(f'  {ref}: no F.Cu pad found')
        return 0

    sz = pad.GetSize()
    via_radius = via_dia // 2
    margin = via_radius + edge_clear
    half_x = sz.x // 2 - margin
    half_y = sz.y // 2 - margin
    if half_x < 0 or half_y < 0:
        print(f'  {ref}: thermal pad ({sz.x/1e6:.2f} x {sz.y/1e6:.2f} mm) too small for via grid')
        return 0

    pad_pos = pad.GetPosition()
    angle_rad = pad.GetOrientation().AsRadians()
    cos_a, sin_a = math.cos(angle_rad), math.sin(angle_rad)
    net = pad.GetNet()
    netcode = net.GetNetCode()

    dup_radius = via_dia
    dup_radius_sq = dup_radius * dup_radius

    added = 0
    for lx, ly in grid_points(half_x, half_y, pitch):
        wx = int(pad_pos.x + cos_a * lx - sin_a * ly)
        wy = int(pad_pos.y + sin_a * lx + cos_a * ly)

        skip = False
        for vx, vy, vn in existing:
            if vn != netcode:
                continue
            ex, ey = wx - vx, wy - vy
            if ex * ex + ey * ey < dup_radius_sq:
                skip = True
                break
        if skip:
            continue

        v = pcbnew.PCB_VIA(board)
        v.SetViaType(pcbnew.VIATYPE_THROUGH)
        v.SetPosition(pcbnew.VECTOR2I(wx, wy))
        v.SetWidth(via_dia)
        v.SetDrill(via_drill)
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetNet(net)
        board.Add(v)
        existing.append((wx, wy, netcode))
        added += 1

    print(f'  {ref}: added {added} vias on net "{net.GetNetname()}" '
          f'(pad {sz.x/1e6:.2f} x {sz.y/1e6:.2f} mm)')
    return added


def add_thermal_vias(path, refs=None, pitch_mm=DEFAULT_PITCH_MM, edge_clearance_mm=DEFAULT_EDGE_CLEARANCE_MM):
    refs = refs if refs is not None else DEFAULT_REFS
    board = pcbnew.LoadBoard(path)
    nc = board.GetAllNetClasses()['Default']
    via_dia = nc.GetViaDiameter()
    via_drill = nc.GetViaDrill()

    pitch = pcbnew.FromMM(pitch_mm)
    edge_clear = pcbnew.FromMM(edge_clearance_mm)

    existing = existing_via_index(board)
    print(f'{path}:')
    total = 0
    for ref in refs:
        total += add_for_ref(board, ref, pitch, edge_clear, via_dia, via_drill, existing)
    board.Save(path)
    print(f'  total: {total} thermal vias')


if __name__ == '__main__':
    for p in sys.argv[1:]:
        add_thermal_vias(p)
