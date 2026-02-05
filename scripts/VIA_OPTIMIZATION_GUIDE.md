# VIA-Optimized LED Matrix Layout Guide

## Overview

This document explains the VIA-optimized LED placement pattern that reduces the number of power VIAs from 2560 to 640 by sharing VIAs between groups of 4 LEDs.

## Layout Dimensions

- **Total LEDs:** 2560 (same as before)
- **Matrix size:** 40 columns × 64 rows
- **Data lanes:** 8 lanes, each handling 8 rows × 40 columns = 320 LEDs
- **VIA blocks:** 20 × 32 = 640 shared VIAs

## Data Flow Pattern

```
Lane 1 (Rows 0-7):
  Row 0: D1 →→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→ D40
  Row 1: D80 ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←← D41
  Row 2: D81 →→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→ D120
  Row 3: D160 ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←← D121
  ...
  Row 7: D280 ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←← D241

Lane 2 (Rows 8-15):
  Row 8: D281 →→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→ D320
  Row 9: D360 ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←← D321
  ...

... (Lanes 3-7) ...

Lane 8 (Rows 56-63):
  Row 56: D2241 →→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→ D2280
  Row 57: D2320 ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←← D2281
  ...
  Row 63: D2560 ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←← D2521
```

## 2×2 LED Block with Shared VIA

### Pin Numbering
- Pin 1: DOUT (data output)
- Pin 2: VDD (power)
- Pin 3: GND (ground)
- Pin 4: DIN (data input)

### Target Pin Arrangement

Each 2×2 block of LEDs is rotated so that VDD (pin 2) and GND (pin 3) face toward the center VIA:

```
╔════════════════╦════════════════╗
║  LED (col 0,   ║  LED (col 1,   ║
║     row 0)     ║     row 0)     ║
║                ║                ║
║   2----4       ║   1----2       ║
║   |    |       ║   |    |       ║
║   1----3       ║   3----4       ║
║           ●━━━━╋━━━●            ║
║           ┃    ║    ┃           ║
╠═══════════╬════╬════╬═══════════╣
║           ┃    ║    ┃           ║
║           ●━━━━╋━━━●            ║
║   4----3       ║   3----1       ║
║   |    |       ║   |    |       ║
║   2----1       ║   4----2       ║
║                ║                ║
║  LED (col 0,   ║  LED (col 1,   ║
║     row 1)     ║     row 1)     ║
╚════════════════╩════════════════╝

         ■ = Shared VIA (center)
         ● = VDD/GND pins facing VIA
```

### Pin Positions in Each Block Position

**Top-Left LED (col even, row even):**
```
2  4    ← Rotation: -90°
1  3
```
- Pins 2,3 (VDD/GND) face RIGHT and DOWN toward center

**Top-Right LED (col odd, row even):**
```
1  2    ← Rotation: 0°
3  4
```
- Pins 2,3 (VDD/GND) face LEFT and DOWN toward center

**Bottom-Left LED (col even, row odd):**
```
4  3    ← Rotation: 180°
2  1
```
- Pins 2,3 (VDD/GND) face RIGHT and UP toward center

**Bottom-Right LED (col odd, row odd):**
```
3  1    ← Rotation: 90°
4  2
```
- Pins 2,3 (VDD/GND) face LEFT and UP toward center

## VIA Placement

VIAs are placed at the CENTER of each 2×2 LED block:

- VIA X position: `LED_START_X + (via_col × 2 × PITCH_X) + (PITCH_X / 2)`
- VIA Y position: `LED_START_Y + (via_row × 2 × PITCH_Y) + (PITCH_Y / 2)`

Where:
- `via_col` = 0 to 19 (20 VIA columns)
- `via_row` = 0 to 31 (32 VIA rows)
- `PITCH_X` = 1.5625 mm
- `PITCH_Y` = 1.625 mm

## Connector Pinout

### J1 - Data Connector (8 pins)
```
Pin 1: Data Lane 1 (Rows 0-7)
Pin 2: Data Lane 2 (Rows 8-15)
Pin 3: Data Lane 3 (Rows 16-23)
Pin 4: Data Lane 4 (Rows 24-31)
Pin 5: Data Lane 5 (Rows 32-39)
Pin 6: Data Lane 6 (Rows 40-47)
Pin 7: Data Lane 7 (Rows 48-55)
Pin 8: Data Lane 8 (Rows 56-63)
```

### J2 - Power Connector (2 pins)
```
Pin 1: VDD (+5V)
Pin 2: GND
```

## Advantages of This Layout

1. **Reduced VIA count:** 640 VIAs instead of 2560 (75% reduction)
2. **Simpler power routing:** Fewer VIAs to connect to power planes
3. **Better power distribution:** Shared VIAs provide natural star topology
4. **Maintains data integrity:** Serpentine pattern keeps data paths short
5. **Easier assembly:** Fewer drill holes, faster manufacturing

## Power Distribution Strategy

1. **Inner layer 1:** VDD power plane
2. **Inner layer 2:** GND power plane
3. **VIAs connect through all layers**
4. **Top/bottom layers:** Data traces and local power connections

### Recommended Routing

- Use 0.4mm VIA diameter, 0.2mm drill
- Connect J2 to power planes with heavy traces (1-2mm width)
- Add decoupling capacitors:
  - Option 1: One 100nF cap per 2×2 LED block (640 caps)
  - Option 2: One 100nF cap per row (64 caps)
  - Option 3: One 470nF cap per data lane (8 caps)

## Verification Checklist

- [ ] All LEDs placed in correct serpentine order
- [ ] LED rotations match 2×2 block pattern
- [ ] VDD/GND pins oriented toward center VIAs
- [ ] 640 VIAs placed at block centers
- [ ] VIAs assigned to correct nets (VDD or GND)
- [ ] Data lanes routed in serpentine pattern
- [ ] Series resistors added to data lines (220-470Ω)
- [ ] Decoupling capacitors placed near power VIAs
- [ ] Power planes on inner layers
- [ ] J1 and J2 connectors placed and routed

## Troubleshooting

### LEDs not oriented correctly
- Adjust `BLOCK_ROTATIONS` dict in `place_led_matrix_via_optimized.py`
- Values depend on your specific footprint orientation
- Test with a small section first (4×4 LEDs)

### VIAs not aligning with LED pins
- Check `PITCH_X` and `PITCH_Y` values match LED spacing
- Verify `START_X` and `START_Y` match between LED and VIA scripts
- VIA offset should be exactly half-pitch in both directions

### Data flow incorrect
- Verify serpentine pattern: even rows L→R, odd rows R→L
- Check lane boundaries: each lane is exactly 8 rows
- Confirm LED numbering matches schematic

## References

- `place_led_matrix_via_optimized.py` - LED placement script
- `place_power_vias.py` - VIA placement script
- `README.md` - General documentation and workflow
- XL-1010RGBC-WS2812B datasheet: https://datasheet.lcsc.com/lcsc/2301111010_XINGLIGHT-XL-1010RGBC-WS2812B_C5349953.pdf
