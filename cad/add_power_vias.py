#!/usr/bin/env python3
"""
Add via-in-pad fanouts from each WS2812B LED's VDD and GND pads into the
inner-layer power planes. The pad's existing net assignment is used, so
this works regardless of whether the board labels the LED supply as VDD
or VDD_S.

Assumes a 4-layer board with solid power zones already placed on In1.Cu
and In2.Cu. Through-vias (F.Cu → B.Cu) connect the F.Cu pad to the plane
on the matching inner layer.

Via geometry is read from the 'Default' netclass.
"""
import sys
import pcbnew

LIB_ID = 'LED_SMD:LED_WS2812B-1010_PLCC4_1.0x1.0mm'
POWER_PINS = {'VDD', 'GND'}


def add_via(board, pos, net_info, diameter, drill):
    v = pcbnew.PCB_VIA(board)
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetPosition(pos)
    v.SetWidth(diameter)
    v.SetDrill(drill)
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNet(net_info)
    board.Add(v)


def add_fanouts(path: str) -> None:
    board = pcbnew.LoadBoard(path)
    nc = board.GetAllNetClasses()['Default']
    diameter = nc.GetViaDiameter()
    drill = nc.GetViaDrill()

    added = 0
    for fp in board.GetFootprints():
        if fp.GetFPIDAsString() != LIB_ID:
            continue
        for pad in fp.Pads():
            if pad.GetPinFunction() not in POWER_PINS:
                continue
            add_via(board, pad.GetPosition(), pad.GetNet(), diameter, drill)
            added += 1
    board.Save(path)
    print(f'{path}: added {added} power fanout vias')


if __name__ == '__main__':
    for p in sys.argv[1:]:
        add_fanouts(p)
