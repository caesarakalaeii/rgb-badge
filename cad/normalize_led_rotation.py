#!/usr/bin/env python3
"""
Set every WS2812B-1010 LED footprint's orientation to 0 degrees using the
KiCad pcbnew API. Footprint positions are preserved (pitch/dimensions unchanged);
only the rotation is normalized so the LED packages face the same direction.
"""
import sys
import pcbnew

LIB_ID = 'LED_SMD:LED_WS2812B-1010_PLCC4_1.0x1.0mm'


def normalize(path: str) -> None:
    board = pcbnew.LoadBoard(path)
    n = 0
    for fp in board.GetFootprints():
        if fp.GetFPIDAsString() != LIB_ID:
            continue
        if fp.GetOrientationDegrees() != 0.0:
            fp.SetOrientationDegrees(0.0)
            n += 1
    board.Save(path)
    print(f'{path}: rotated {n} LED footprints to 0 deg')


if __name__ == '__main__':
    for p in sys.argv[1:]:
        normalize(p)
