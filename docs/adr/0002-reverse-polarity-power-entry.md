# ADR 0002: Reverse-polarity power entry

- Status: Accepted
- Date: 2026-10-17

## Context

U1 (Si7145DP, P-channel MOSFET) protects the matrix PCB against a reversed
power plug. It was wired with its source on the input (VDD) and its drain on the
protected rail (VDD_S). A P-FET's body diode conducts from drain to source. With
a reversed plug, current flows from board GND (+5 V) through the LEDs' internal
GND-to-VDD diodes into VDD_S, then through U1's body diode to the VDD pin. The
FET is off but the diode bypasses it, so nothing is blocked. The fabricated
100-LED sample (AO4407A) has the same wiring.

The J2-to-U1 path was also 0.5–2 mm traces, which cannot carry the ~30 A peak
the board is designed for.

## Decision

- U1 drain (pins 5–8 + exposed pad) on VDD (input), source (pins 1–3) on VDD_S.
- R3 (100 kΩ) between gate and source (VDD_S); R4 (10 kΩ) gate to GND,
  unchanged. Normal polarity: the body diode conducts first, then V_GS ≈ -4.5 V
  turns the channel on. Reversed: the body diode is reverse-biased and
  V_GS > 0, so the FET blocks.
- Copper pours replace the traces: VDD on F.Cu and B.Cu from J2 to the drain/EP
  (13 vias in the drain pads tie both sides together), VDD_S on F.Cu from the
  source pins to a 24-via field into the In2/In3 VDD_S planes.
- TVS1 (SMBJ6.0CA, bidirectional) and C28 stay on the input side.

## Consequences

- The sample board is not reverse-polarity protected; never plug it in reversed.
- The schematic and the PCB were changed together; `cad/test_board.py` asserts
  the pin-to-net mapping and runs DRC with schematic parity.
