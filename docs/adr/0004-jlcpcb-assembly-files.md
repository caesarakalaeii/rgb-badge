# ADR 0004: JLCPCB assembly files

- Status: Accepted
- Date: 2026-10-30

## Context

JLCPCB was quoted as a second source for the 5-board turnkey order. Its
assembly flow differs from PCBWay's in three ways:

- The BOM is matched by LCSC part number. Several designed parts can't be
  placed there:
  - The C&C polymer caps are not stocked.
  - RCT02100KFLF (C173682) has no placement model.
  - J1 (C587927) is placeable, but JLC unticks it on every upload because it
    carries a hard-to-place fee.
- JLC places its own model of each part at the CPL position and angle.
  KiCad's centroid uses footprint origins and angles that don't always match
  those models. JLC's preview showed:
  - U1 and U2–U9 turned 90°.
  - J2 four pins off its pads, because KiCad's origin is pin 1.
- JLC reads bottom-side angles as seen from below. The 45° back-side 0603 caps
  showed up 90° off.

## Decision

`cad/export_fab.py` writes `led_bage-bom-jlc.csv` and `led_bage-cpl-jlc.csv`
next to the vendor-neutral BOM and centroid.

**BOM.** The BOM maps each MPN to an LCSC part. Where JLC can't place the
designed part, a stocked equivalent stands in:

| Designed part | JLC part |
|---|---|
| CSH0605-101M1CT | JBLM2101M016C058RTM (C19270701): 100 µF 16 V polymer, 6.3 × 5.8 mm |
| RCT02330RFLF | basic part C25104 |
| RCT02100KFLF | basic part C25741 |
| RCT0210KFLF | basic part C25744 |

The schematic keeps the designed MPNs, so the PCBWay BOM is unchanged.

Designator cells are split at 2000 characters. JLC states a 2048-character
cap, but it rejected a file with 2045–2048-character cells.

**CPL.**
- Bottom-side angle = 180° − KiCad angle.
- Per-footprint corrections:
  - SOT-23-5: −90°.
  - PowerPAK SO-8 (U1): −90°.
  - JST VH (J2): origin moved from pin 1 to the middle of the pin row.
  - Molex CLIK-Mate (J1): +180°, and the origin moved 0.175 mm to the middle
    of the pads.

All corrections were read off JLC's placement preview. `cad/test_board.py`
pins the resulting placement of one part of each kind.

## Consequences

- A new footprint, or a part moved to the other side, needs a look in JLC's
  preview. If its model is off, it needs a `JLC_FIX` entry.
- After each BOM/CPL upload, J1 and the LED rows (flagged "multiple types")
  must be ticked again by hand.
- The polymer cap substitute is 0.4 mm taller than the designed part.
