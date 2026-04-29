#!/usr/bin/env python3
"""
Stitch the inner power planes (In1.Cu = VDD_S, In2.Cu = GND) with a
checkerboard grid of through-vias across the board area. Each via is
F.Cu -> B.Cu and uses pad/drill geometry from the 'Default' netclass.

Vias are skipped when the candidate point is:
  - Outside the edge-cut bounding box
  - Inside any footprint bounding box (with clearance margin)
  - Closer than (via radius + track half-width + clearance) to an existing track
  - Closer than (via radius + via radius + clearance) to an existing via

Run after routing is complete: this avoids existing routes rather than
forcing the router to dodge the stitch grid.

Complements add_power_vias.py: that handles per-LED fanouts; this keeps
the planes coherent between F.Cu and B.Cu globally.
"""
import sys
import pcbnew

DEFAULT_PITCH_MM = 5.0
DEFAULT_CLEARANCE_MM = 0.3
VDD_NET_NAME = 'VDD_S'
GND_NET_NAME = 'GND'


def find_net(board, name):
    nets = board.GetNetsByName()
    if name in nets:
        return nets[name]
    for key, net in nets.items():
        if str(key).lstrip('/') == name:
            return net
    return None


def point_seg_dist_sq(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    if dx == 0 and dy == 0:
        ex, ey = px - x1, py - y1
        return ex * ex + ey * ey
    t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
    if t < 0.0:
        t = 0.0
    elif t > 1.0:
        t = 1.0
    nx, ny = x1 + t * dx, y1 + t * dy
    ex, ey = px - nx, py - ny
    return ex * ex + ey * ey


def stitch(path, pitch_mm=DEFAULT_PITCH_MM, clearance_mm=DEFAULT_CLEARANCE_MM):
    board = pcbnew.LoadBoard(path)
    nc = board.GetAllNetClasses()['Default']
    via_dia = nc.GetViaDiameter()
    via_drill = nc.GetViaDrill()
    via_radius = via_dia // 2

    vdd_net = find_net(board, VDD_NET_NAME)
    gnd_net = find_net(board, GND_NET_NAME)
    if vdd_net is None or gnd_net is None:
        print(f'{path}: ERROR - could not find net {VDD_NET_NAME} or {GND_NET_NAME}')
        return

    bbox = board.GetBoardEdgesBoundingBox()
    pitch = pcbnew.FromMM(pitch_mm)
    clearance = pcbnew.FromMM(clearance_mm)

    fp_boxes = []
    for fp in board.GetFootprints():
        bb = fp.GetBoundingBox()
        fp_boxes.append((
            bb.GetLeft() - clearance,
            bb.GetTop() - clearance,
            bb.GetRight() + clearance,
            bb.GetBottom() + clearance,
        ))

    # Existing vias use the same Default netclass geometry as this script,
    # so approximate their radius with via_radius rather than calling the
    # KiCad 10 layer-aware GetWidth(layer) API on each via.
    tracks = []
    existing_vias = []
    for t in board.GetTracks():
        if t.GetClass() == 'PCB_VIA':
            p = t.GetPosition()
            existing_vias.append((p.x, p.y, via_radius))
        else:
            s, e = t.GetStart(), t.GetEnd()
            tracks.append((s.x, s.y, e.x, e.y, t.GetWidth() // 2))

    def is_free(x, y):
        if not (bbox.GetLeft() <= x <= bbox.GetRight() and
                bbox.GetTop() <= y <= bbox.GetBottom()):
            return False
        for x1, y1, x2, y2 in fp_boxes:
            if x1 <= x <= x2 and y1 <= y <= y2:
                return False
        for x1, y1, x2, y2, half_w in tracks:
            min_d = via_radius + half_w + clearance
            if point_seg_dist_sq(x, y, x1, y1, x2, y2) < min_d * min_d:
                return False
        for vx, vy, vr in existing_vias:
            min_d = via_radius + vr + clearance
            ex, ey = x - vx, y - vy
            if ex * ex + ey * ey < min_d * min_d:
                return False
        return True

    added_vdd = 0
    added_gnd = 0
    iy = 0
    y = bbox.GetTop()
    while y <= bbox.GetBottom():
        ix = 0
        x = bbox.GetLeft()
        while x <= bbox.GetRight():
            if is_free(x, y):
                use_vdd = (ix + iy) % 2 == 0
                net = vdd_net if use_vdd else gnd_net
                v = pcbnew.PCB_VIA(board)
                v.SetViaType(pcbnew.VIATYPE_THROUGH)
                v.SetPosition(pcbnew.VECTOR2I(x, y))
                v.SetWidth(via_dia)
                v.SetDrill(via_drill)
                v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                v.SetNet(net)
                board.Add(v)
                if use_vdd:
                    added_vdd += 1
                else:
                    added_gnd += 1
            x += pitch
            ix += 1
        y += pitch
        iy += 1

    board.Save(path)
    print(f'{path}: added {added_vdd} {VDD_NET_NAME} + {added_gnd} {GND_NET_NAME} stitch vias')


if __name__ == '__main__':
    for p in sys.argv[1:]:
        stitch(p)
