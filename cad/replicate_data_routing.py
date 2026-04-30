#!/usr/bin/env python3
"""
Replicate the data-line routing pattern across all in-row LED-pair
segments in the chain.

Templates: pick one already-routed L-to-R segment and one R-to-L segment
(by their source-LED reference). The script reads every track on those
nets, then for each remaining same-row LED-pair (D[n], D[n+1]) it
translates the template tracks by (dst_anchor - src_anchor) and assigns
them to Net-(D[n]-DOUT).

Skips:
- Pairs whose nets already have tracks (idempotent: re-running won't
  duplicate)
- Pairs that span rows (chain row-transitions and inter-chain breaks)

Chain row-transitions stay unrouted -- they have a different shape and
should be done by hand or with a separate template.
"""
import sys
import pcbnew

LED_LIB = 'LED_SMD:LED_WS2812B-1010_PLCC4_1.0x1.0mm'
LR_TEMPLATE_SRC = 1   # D1 -> D2 is the L-to-R template
RL_TEMPLATE_SRC = 79  # D79 -> D80 is the R-to-L template
SAME_ROW_TOL_NM = 100_000  # 0.1 mm


def collect_template(board, src_led_n):
    net_name = f'Net-(D{src_led_n}-DOUT)'
    tracks = []
    for t in board.GetTracks():
        if t.GetClass() == 'PCB_TRACK' and t.GetNet().GetNetname() == net_name:
            tracks.append(t)
    return net_name, tracks


def replicate(path):
    board = pcbnew.LoadBoard(path)

    leds = {}
    for fp in board.GetFootprints():
        if fp.GetFPIDAsString() != LED_LIB:
            continue
        ref = fp.GetReference()
        if ref.startswith('D') and ref[1:].isdigit():
            leds[int(ref[1:])] = fp

    lr_net, lr_tracks = collect_template(board, LR_TEMPLATE_SRC)
    rl_net, rl_tracks = collect_template(board, RL_TEMPLATE_SRC)
    if not lr_tracks:
        print(f'{path}: ERROR - no tracks on {lr_net} (L-to-R template missing)')
        return
    if not rl_tracks:
        print(f'{path}: ERROR - no tracks on {rl_net} (R-to-L template missing)')
        return

    lr_anchor = leds[LR_TEMPLATE_SRC].GetPosition()
    rl_anchor = leds[RL_TEMPLATE_SRC].GetPosition()

    # Pre-compute set of nets that already have tracks (skip these)
    already_routed = set()
    for t in board.GetTracks():
        if t.GetClass() == 'PCB_TRACK':
            already_routed.add(t.GetNet().GetNetname())

    nets_by_name = board.GetNetsByName()

    n_lr = n_rl = n_skip = n_cross_row = n_missing_net = 0
    for n in sorted(leds):
        src = leds.get(n)
        dst = leds.get(n + 1)
        if src is None or dst is None:
            continue
        src_pos = src.GetPosition()
        dst_pos = dst.GetPosition()

        if abs(src_pos.y - dst_pos.y) > SAME_ROW_TOL_NM:
            n_cross_row += 1
            continue

        # KiCad picks one of two naming conventions for the LED-pair net,
        # depending on schematic ordering: Net-(D[n]-DOUT) or Net-(D[n+1]-DIN).
        # Try both before giving up.
        candidate_names = [f'Net-(D{n}-DOUT)', f'Net-(D{n+1}-DIN)']
        target_net_name = next((c for c in candidate_names if c in nets_by_name), None)
        if target_net_name is None:
            n_missing_net += 1
            continue
        if target_net_name in already_routed:
            n_skip += 1
            continue
        target_net = nets_by_name[target_net_name]

        if dst_pos.x > src_pos.x:
            template, anchor = lr_tracks, lr_anchor
            n_lr += 1
        else:
            template, anchor = rl_tracks, rl_anchor
            n_rl += 1

        dx = src_pos.x - anchor.x
        dy = src_pos.y - anchor.y
        for t in template:
            new = pcbnew.PCB_TRACK(board)
            s, e = t.GetStart(), t.GetEnd()
            new.SetStart(pcbnew.VECTOR2I(s.x + dx, s.y + dy))
            new.SetEnd(pcbnew.VECTOR2I(e.x + dx, e.y + dy))
            new.SetWidth(t.GetWidth())
            new.SetLayer(t.GetLayer())
            new.SetNet(target_net)
            board.Add(new)

    pcbnew.SaveBoard(path, board)
    print(f'{path}: replicated {n_lr} L->R + {n_rl} R->L segments '
          f'(skipped {n_skip} already-routed, {n_cross_row} cross-row, '
          f'{n_missing_net} no-net)')


if __name__ == '__main__':
    for p in sys.argv[1:]:
        replicate(p)
