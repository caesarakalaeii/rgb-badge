#!/usr/bin/env python3
"""
Replicate the user's hand-routed D1→D2 chain trace to every L→R pair in
the chain. The LED grid is serpentine:
  rows 0,2,4,6,8 go left→right; rows 1,3,5,7,9 go right→left.
Only same-row-same-direction-as-D1→D2 (L→R) pairs can be copied verbatim
from the source pattern; R→L and end-of-row transitions need their own
reference traces and are reported as skipped.

Source pattern comes from all PCB_TRACK / PCB_VIA / PCB_ARC segments on
`Net-(D1-DOUT)`. Each segment is translated so its start/end lands at the
target pair's DOUT/DIN positions, and reassigned to `Net-(Dn-DOUT)`.
"""
import sys
import pcbnew

LED_LIB = 'LED_SMD:LED_WS2812B-1010_PLCC4_1.0x1.0mm'
SOURCE_NET = 'Net-(D1-DOUT)'
SOURCE_REF = 'D1'  # the pair is (D1, D2) — source LED


def get_pad(fp, pinfunc):
    for pad in fp.Pads():
        if pad.GetPinFunction() == pinfunc:
            return pad
    return None


def ledref_num(ref: str) -> int:
    return int(ref.lstrip('D'))


def replicate(path: str) -> None:
    board = pcbnew.LoadBoard(path)
    leds = {fp.GetReference(): fp for fp in board.GetFootprints() if fp.GetFPIDAsString() == LED_LIB}
    if SOURCE_REF not in leds:
        print(f'{path}: {SOURCE_REF} not found — aborting')
        return

    src_origin = get_pad(leds[SOURCE_REF], 'DOUT').GetPosition()

    src_segments = [t for t in board.GetTracks() if t.GetNetname() == SOURCE_NET]
    if not src_segments:
        print(f'{path}: no tracks on {SOURCE_NET} — aborting')
        return

    netmap = {str(k): v for k, v in board.GetNetsByName().items()}

    # build pairs (Dn, Dn+1) from chain topology (DOUT→DIN net sharing)
    pad_by_led = {ref: {pad.GetPinFunction(): pad for pad in fp.Pads() if pad.GetPinFunction() in ('DIN', 'DOUT')}
                  for ref, fp in leds.items()}
    dout_net_to_ref = {pad_by_led[r]['DOUT'].GetNetname(): r for r in pad_by_led if pad_by_led[r]['DOUT'].GetNetname() and pad_by_led[r]['DOUT'].GetNetname() != ''}

    pairs = []  # (src_ref, next_ref, transition_type)
    for ref, pads in pad_by_led.items():
        dout_net = pads['DOUT'].GetNetname()
        if not dout_net.startswith('Net-'):
            continue  # tail of chain (unconnected) or no successor
        # find LED whose DIN net matches this DOUT net
        nxt = None
        for ref2, pads2 in pad_by_led.items():
            if ref2 == ref:
                continue
            if pads2['DIN'].GetNetname() == dout_net:
                nxt = ref2
                break
        if nxt is None:
            continue
        src_pos = pads['DOUT'].GetPosition()
        nxt_pos = pad_by_led[nxt]['DIN'].GetPosition()
        dx = nxt_pos.x - src_pos.x
        dy = nxt_pos.y - src_pos.y
        # classify: L→R has Δx≈+2.4125mm Δy≈+0.85mm; R→L has Δx≈-0.7125 Δy≈+0.85; row-jump has large Δy
        if abs(dy) > 1_500_000:
            ttype = 'row_jump'
        elif dx > 1_500_000:
            ttype = 'lr'
        elif dx < -500_000:
            ttype = 'rl'
        else:
            ttype = 'unknown'
        pairs.append((ref, nxt, ttype, src_pos))

    # Replicate L→R pairs (skip source D1→D2 itself — it already has the trace)
    added = skipped = 0
    skipped_types = {}
    for ref, nxt, ttype, pos in pairs:
        if ref == SOURCE_REF:
            continue
        if ttype != 'lr':
            skipped += 1
            skipped_types[ttype] = skipped_types.get(ttype, 0) + 1
            continue
        target_net_name = pad_by_led[ref]['DOUT'].GetNetname()
        target_net = netmap.get(target_net_name)
        if not target_net:
            continue
        tx = pos.x - src_origin.x
        ty = pos.y - src_origin.y
        for t in src_segments:
            cls = t.GetClass()
            if cls == 'PCB_TRACK':
                new = pcbnew.PCB_TRACK(board)
                new.SetStart(pcbnew.VECTOR2I(t.GetStart().x + tx, t.GetStart().y + ty))
                new.SetEnd(pcbnew.VECTOR2I(t.GetEnd().x + tx, t.GetEnd().y + ty))
                new.SetWidth(t.GetWidth())
                new.SetLayer(t.GetLayer())
                new.SetNet(target_net)
                board.Add(new)
                added += 1
            elif cls == 'PCB_ARC':
                new = pcbnew.PCB_ARC(board)
                new.SetStart(pcbnew.VECTOR2I(t.GetStart().x + tx, t.GetStart().y + ty))
                new.SetMid(pcbnew.VECTOR2I(t.GetMid().x + tx, t.GetMid().y + ty))
                new.SetEnd(pcbnew.VECTOR2I(t.GetEnd().x + tx, t.GetEnd().y + ty))
                new.SetWidth(t.GetWidth())
                new.SetLayer(t.GetLayer())
                new.SetNet(target_net)
                board.Add(new)
                added += 1
            elif cls == 'PCB_VIA':
                new = pcbnew.PCB_VIA(board)
                new.SetViaType(t.GetViaType())
                new.SetPosition(pcbnew.VECTOR2I(t.GetPosition().x + tx, t.GetPosition().y + ty))
                new.SetWidth(t.GetWidth())
                new.SetDrill(t.GetDrill())
                new.SetLayerPair(t.TopLayer(), t.BottomLayer())
                new.SetNet(target_net)
                board.Add(new)
                added += 1

    board.Save(path)
    print(f'{path}: added {added} primitives across L→R pairs')
    print(f'  skipped {skipped} non-L→R transitions:')
    for k, v in skipped_types.items():
        print(f'    {k}: {v}')


if __name__ == '__main__':
    for p in sys.argv[1:]:
        replicate(p)
