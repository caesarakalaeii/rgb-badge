# ADR 0003: Design rules for fabrication at PCBWay

- Status: Accepted
- Date: 2026-10-30

## Context

The matrix PCB is ordered from PCBWay with turnkey assembly. Their standard
capability is 4/4 mil (0.1 mm) track and space, with a 0.15 mm via annular ring.

DRC passed, but only because the rules were looser than any fab: the project
minimum clearance was 0.05 mm, the Default netclass (which held every data net)
used 0.05 mm, and each LED pad carries a 0.05 mm local clearance override. With
the floor raised, the real copper gaps were 0.05 mm in 8 places (the lane input
bus down the left margin) and 0.07–0.1 mm in several hundred more. DRC reports
stop at 499 per type, so the full count was never visible. Every gap involved a
0.15 mm data track.

The 0.5/0.3 mm fanout vias have a 0.1 mm annular ring, fine for JLC but under
PCBWay's 0.15 mm. Trying 0.55/0.25 mm vias added gaps under 0.1 mm instead.

## Decision

- Board-level floors: minimum clearance 0.1 mm, minimum track width 0.1 mm.
  DRC applies the floor over the LED pads' local override, so it measures real
  gaps. `cad/test_board.py` checks the floor.
- The `Data` netclass (0.1 mm track, 0.1 mm clearance; patterns
  `Net-(D*-DOUT)`, `Net-(D*-DIN)`, `DATA*`) is applied, and existing data tracks
  are narrowed to 0.1 mm. Centerlines stay put, so every gap grows by 0.025 mm
  per narrowed side.
- The 60 row-wraparound jogs at the grid's left and right edges sat 0.075 mm
  from an LED pad. They move 0.025 mm away, and their 45° neighbours slide along
  so the angles are kept.
- Vias stay 0.5/0.3 mm. The order asks PCBWay to accept a 0.1 mm via annular
  ring.

All of this is done by `cad/add_data_netclass.py` (re-runnable).
`cad/export_fab.py` writes Gerbers, drill, BOM and centroid to `cad/fab/`.

## Consequences

- Data tracks at 0.1 mm are PCBWay's standard minimum, not an advanced option.
  At ~1 mA and 800 kHz, the width makes no difference to the signal.
- New data routing must keep 0.1 mm to everything. The 0.05 mm pad overrides
  still exist in the footprints, so the interactive router may offer tighter
  gaps; DRC will reject them.
- If PCBWay rejects the 0.1 mm via annular ring, the fanout vias need a new
  size, and the LED pitch leaves little room for one.
