#!/usr/bin/env python3
"""
Place WS2812B-1010 LEDs in a serpentine grid for the main board.

Layout: 40 cols x 64 rows = 2560 LEDs, in 8 data chains of 320 LEDs each
(8 rows per chain). Pattern: row 1 (top) goes left to right, row 2 right
to left, alternating. Chain transitions continue the snake across row
boundaries (matches the led_bage_sample chain split between D50/D51).

LED reference order:
  D1     -> top-left (row 1, col 1)
  D40    -> top-right (row 1, col 40)
  D41    -> row 2, col 40 (right side, R-to-L starts)
  D80    -> row 2, col 1
  D81    -> row 3, col 1 (back to L-to-R)
  ...
  D320   -> end of chain 1 (row 8)
  D321   -> start of chain 2 (row 9)
  ...
  D2560  -> end of chain 8 (row 64)

Origin defaults to D1's existing position so the grid stays roughly where
the LEDs already are. Override ORIGIN_X_MM / ORIGIN_Y_MM constants below
to pin to specific coordinates.

LEDs missing from the board are reported but do not abort the run.
"""
import sys
import pcbnew

LED_LIB = 'LED_SMD:LED_WS2812B-1010_PLCC4_1.0x1.0mm'
COLS = 40
ROWS = 64
PITCH_X_MM = 1.5625
PITCH_Y_MM = 1.625
ORIGIN_X_MM = None  # None = use existing D1 X position
ORIGIN_Y_MM = None  # None = use existing D1 Y position
TOTAL = COLS * ROWS


def grid_position(led_index_one_based):
    idx = led_index_one_based - 1
    row = idx // COLS
    col_in_row = idx % COLS
    col = col_in_row if row % 2 == 0 else COLS - 1 - col_in_row
    return row, col


def place(path, origin_x_mm=ORIGIN_X_MM, origin_y_mm=ORIGIN_Y_MM):
    board = pcbnew.LoadBoard(path)

    leds_by_ref = {}
    for fp in board.GetFootprints():
        if fp.GetFPIDAsString() != LED_LIB:
            continue
        ref = fp.GetReference()
        if ref.startswith('D') and ref[1:].isdigit():
            n = int(ref[1:])
            if 1 <= n <= TOTAL:
                leds_by_ref[n] = fp

    if len(leds_by_ref) != TOTAL:
        present = set(leds_by_ref.keys())
        missing = sorted(set(range(1, TOTAL + 1)) - present)[:10]
        extra = sorted(n for n in present if n > TOTAL)[:10]
        print(f'{path}: WARNING - found {len(leds_by_ref)}/{TOTAL} expected LEDs')
        if missing:
            print(f'  first missing: {missing}')
        if extra:
            print(f'  out-of-range refs: {extra}')

    if origin_x_mm is None or origin_y_mm is None:
        if 1 not in leds_by_ref:
            print(f'{path}: ERROR - need D1 placed (or set ORIGIN_*_MM constants)')
            return
        d1 = leds_by_ref[1].GetPosition()
        if origin_x_mm is None:
            origin_x_mm = d1.x / 1e6
        if origin_y_mm is None:
            origin_y_mm = d1.y / 1e6

    pitch_x = pcbnew.FromMM(PITCH_X_MM)
    pitch_y = pcbnew.FromMM(PITCH_Y_MM)
    origin_x = pcbnew.FromMM(origin_x_mm)
    origin_y = pcbnew.FromMM(origin_y_mm)

    placed = 0
    for n in sorted(leds_by_ref):
        if n > TOTAL:
            continue
        row, col = grid_position(n)
        x = origin_x + col * pitch_x
        y = origin_y + row * pitch_y
        fp = leds_by_ref[n]
        fp.SetPosition(pcbnew.VECTOR2I(x, y))
        fp.SetOrientationDegrees(0.0)
        placed += 1

    board.Save(path)
    grid_w = (COLS - 1) * PITCH_X_MM
    grid_h = (ROWS - 1) * PITCH_Y_MM
    print(f'{path}: placed {placed} LEDs in {COLS}x{ROWS} serpentine grid '
          f'origin=({origin_x_mm:.3f}, {origin_y_mm:.3f}) mm '
          f'span={grid_w:.2f}x{grid_h:.2f} mm')


if __name__ == '__main__':
    for p in sys.argv[1:]:
        place(p)
