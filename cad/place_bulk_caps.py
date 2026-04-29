#!/usr/bin/env python3
"""
Distribute bulk caps across the LED bbox by cloning a template footprint.

Workflow:
  1. Place ONE cap manually with the correct footprint, layer, rotation,
     and net assignments (default ref: C901).
  2. Run this script. It clones that template N times at evenly-spaced
     grid positions across the LED area, with auto-assigned references
     starting one above the highest existing C-number.

Caveats:
  - Output positions are a first pass on a sqrt(N) x sqrt(N) grid in the
    LED bbox. Expect to nudge them in pcbnew based on actual layout
    (DATA traces, MCU, connector, etc.).
  - Calculated positions land on the LED grid, so you will likely need
    to delete or shift a few LEDs underneath each cap to make room. The
    script does not modify LEDs.
  - Net assignments and footprint identity come from the template, so
    set those up correctly on the template before running.
"""
import math
import sys
import pcbnew

LED_LIB = 'LED_SMD:LED_WS2812B-1010_PLCC4_1.0x1.0mm'
TEMPLATE_REF = 'C901'
COUNT = 8


def highest_cap_number(board):
    high = 0
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref.startswith('C'):
            try:
                n = int(ref[1:])
                if n > high:
                    high = n
            except ValueError:
                pass
    return high


def grid_dims(n):
    cols = int(round(math.sqrt(n)))
    if cols < 1:
        cols = 1
    rows = (n + cols - 1) // cols
    return cols, rows


def grid_centers(x_min, x_max, y_min, y_max, n):
    cols, rows = grid_dims(n)
    cell_w = (x_max - x_min) // cols
    cell_h = (y_max - y_min) // rows
    out = []
    for r in range(rows):
        for c in range(cols):
            if len(out) >= n:
                break
            cx = x_min + cell_w * c + cell_w // 2
            cy = y_min + cell_h * r + cell_h // 2
            out.append((cx, cy))
    return out


def place_bulk_caps(path, template_ref=TEMPLATE_REF, count=COUNT):
    board = pcbnew.LoadBoard(path)

    template = board.FindFootprintByReference(template_ref)
    if template is None:
        print(f'{path}: ERROR - template {template_ref} not found, place it first')
        return

    leds = [fp for fp in board.GetFootprints() if fp.GetFPIDAsString() == LED_LIB]
    if not leds:
        print(f'{path}: ERROR - no LEDs found')
        return

    xs = [fp.GetPosition().x for fp in leds]
    ys = [fp.GetPosition().y for fp in leds]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)

    positions = grid_centers(x_min, x_max, y_min, y_max, count)
    next_n = highest_cap_number(board) + 1

    placed = 0
    for cx, cy in positions:
        clone = template.Duplicate()
        clone.SetReference(f'C{next_n}')
        clone.SetPosition(pcbnew.VECTOR2I(int(cx), int(cy)))
        board.Add(clone)
        next_n += 1
        placed += 1

    cols, rows = grid_dims(count)
    board.Save(path)
    print(f'{path}: placed {placed} bulk caps cloned from {template_ref} '
          f'on a {cols}x{rows} grid in the LED bbox')


if __name__ == '__main__':
    for p in sys.argv[1:]:
        place_bulk_caps(p)
