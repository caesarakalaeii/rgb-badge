# KiCad LED Matrix Placement Scripts

Python scripts for automated placement of the 64×40 LED matrix in KiCad PCB Editor.

## Quick Start

### 1. Basic Placement Script

**File:** `place_led_matrix.py`

Simple row-major placement (left-to-right, top-to-bottom).

**Usage:**
1. Open your PCB in KiCad PCB Editor
2. Open scripting console: Tools → Scripting Console
3. Run:
   ```python
   exec(open('scripts/place_led_matrix.py').read())
   ```

### 2. Advanced Placement Script

**File:** `place_led_matrix_advanced.py`

Supports multiple placement patterns including the 8-lane serpentine pattern recommended in the README.

**Usage:**
1. Edit the script to choose your pattern:
   ```python
   PLACEMENT_PATTERN = "8lane_serpentine"  # or "row_major" or "serpentine"
   ```
2. Adjust starting position if needed:
   ```python
   START_X = 10.0  # mm from board origin
   START_Y = 10.0  # mm from board origin
   ```
3. Run in KiCad Scripting Console:
   ```python
   exec(open('scripts/place_led_matrix_advanced.py').read())
   ```

## Placement Patterns

### Row Major
- Simple left-to-right, top-to-bottom
- LED1 at top-left, LED2560 at bottom-right
- Longest data paths

### Serpentine
- Alternates direction each row
- Reduces trace length between rows
- Better for single-lane designs

### 8-Lane Serpentine (Recommended)
- Matches the README's 8 parallel data lanes architecture
- Each lane handles 8 columns × 40 rows (320 pixels)
- Serpentine routing within each lane
- Optimal for the parallel data distribution design

## Configuration

Edit these variables at the top of the script:

```python
# Matrix size (from README)
COLS = 64
ROWS = 40
PITCH_X = 1.5625  # mm
PITCH_Y = 1.625   # mm

# Starting position (adjust for your board)
START_X = 10.0  # mm
START_Y = 10.0  # mm

# LED reference prefix (e.g., "LED" for LED1, LED2, ...)
LED_PREFIX = "LED"

# Rotation (degrees)
LED_ROTATION = 0.0
```

## Prerequisites

### Footprint Naming
LEDs must be named sequentially:
- LED1, LED2, LED3, ..., LED2560

### Component Import
Before running placement:
1. Create schematic with 2560 LED symbols
2. Assign footprints to all LEDs
3. Update PCB from schematic (Tools → Update PCB from Schematic)
4. All 2560 LEDs should now be on the PCB (likely in a pile)

## Workflow

### Method 1: Import then Auto-Place (Recommended)

1. **Design schematic** with 2560 LED symbols
   - Use hierarchical sheets or array annotations if needed
   - Assign XL-1010RGBC-2812B footprint to all

2. **Update PCB from schematic**
   - All LEDs import as a stack at origin

3. **Run placement script**
   - Opens them into perfect matrix

4. **Route**
   - Add data traces, power planes, decoupling caps

### Method 2: Place-as-you-go

1. Place first LED manually at desired start position
2. Note its exact position
3. Update script `START_X` and `START_Y` to match
4. Import remaining LEDs
5. Run script to arrange all

## Expected Output

```
Placing 2560 LEDs in 64×40 matrix
Pitch: 1.5625mm × 1.625mm
Pattern: 8lane_serpentine
Starting position: (10.0, 10.0)

  Using 8-lane serpentine: 8 lanes × 320 pixels
  Each lane: 8 columns × 40 rows
  Placed 100/2560 LEDs...
  Placed 200/2560 LEDs...
  ...
  Placed 2560/2560 LEDs...

✓ Successfully placed 2560 LEDs

Matrix dimensions:
  Width: 98.438 mm (64 columns)
  Height: 63.375 mm (40 rows)
  Total area: 98.4 × 63.4 mm
  End position: (108.438, 73.375)

Done! Board refreshed.
```

## Troubleshooting

### "Found X LEDs, expected 2560"
- Check that all LEDs are named with correct prefix
- Verify LED_PREFIX variable matches your naming
- Run anyway if you're testing with fewer LEDs

### LEDs appear off-board
- Adjust START_X and START_Y values
- Check board origin (some boards use center, others use corner)

### Script doesn't run
- Verify file path is correct (relative to KiCad project)
- Use absolute path if needed:
  ```python
  exec(open('/home/caesar/git/rgb-badge/scripts/place_led_matrix.py').read())
  ```

### Position conflicts/overlaps
- Verify PITCH_X and PITCH_Y are correct
- Check that footprint courtyard isn't causing false conflicts
- May need to disable courtyard visibility: View → Appearance → Graphic Items → Footprint Courtyard

## Physical Verification

After placement, verify:
- Total matrix width: ~98.44 mm (matches README: 100mm including margins)
- Total matrix height: ~63.38 mm (matches README: 65mm including margins)
- Body-to-body clearance: 0.56–0.63 mm (as specified in README)

## Next Steps

After successful placement:
1. Add power distribution network
2. Add decoupling capacitors (per LED or per cluster)
3. Route data lanes from connector to lane entry points
4. Add soldermask and silkscreen
5. DRC check focusing on soldermask webbing between pads
6. Generate Gerbers

## License

Part of the Ultra-High-Density RGB Matrix Badge project (AGPL-3.0)
