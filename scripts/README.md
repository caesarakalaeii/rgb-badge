# KiCad LED Matrix Placement Scripts

Python scripts for automated placement of the 40×64 LED matrix in KiCad PCB Editor with VIA-optimized power distribution.

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

### 3. VIA-Optimized Placement Script (Recommended)

**File:** `place_led_matrix_via_optimized.py`

Optimized LED placement for shared power VIAs with 2×2 LED block pattern.

**Features:**
- 40 columns × 64 rows = 2560 LEDs
- 8 data lanes, each handling 8 rows × 40 columns (320 LEDs per lane)
- Serpentine routing within each lane for optimal data flow
- LEDs rotated in 2×2 blocks so VDD/GND pins face center
- Enables one shared VIA per 4 LEDs (640 VIAs total vs 2560)

**Target Pin Arrangement (2×2 block with center VIA):**
```
2 4 | 1 2
1 3 | 3 4
----V----
4 3 | 3 1
2 1 | 4 2
```
Where: 1=DOUT, 2=VDD, 3=GND, 4=DIN, V=shared VIA

**Usage:**
1. Adjust starting position and verify rotation angles:
   ```python
   START_X = 10.0
   START_Y = 10.0

   # Verify these match your footprint orientation
   BLOCK_ROTATIONS = {
       (True, True):   -90,   # Top-left
       (False, True):    0,   # Top-right
       (True, False):  180,   # Bottom-left
       (False, False):  90,   # Bottom-right
   }
   ```
2. Run in KiCad Scripting Console:
   ```python
   exec(open('scripts/place_led_matrix_via_optimized.py').read())
   ```
3. Verify LED orientations visually
4. Adjust BLOCK_ROTATIONS if pins don't align correctly

### 4. Shared VIA Placement Script

**File:** `place_power_vias.py`

Automatically places power VIAs in the center of each 2×2 LED block.

**Usage:**
1. **Run AFTER** running `place_led_matrix_via_optimized.py`
2. Verify configuration matches LED placement:
   ```python
   LED_COLS = 40
   LED_ROWS = 64
   VIA_SIZE = 0.4    # mm diameter
   VIA_DRILL = 0.2   # mm drill
   ```
3. Run in KiCad Scripting Console:
   ```python
   exec(open('scripts/place_power_vias.py').read())
   ```
4. Manually assign VIAs to VDD or GND nets as needed
5. Add power planes or heavy traces between VIAs

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

### For VIA-Optimized Scripts (Recommended)

Edit these variables in `place_led_matrix_via_optimized.py`:

```python
# Matrix size (VIA-optimized layout)
COLS = 40   # 40 columns
ROWS = 64   # 64 rows (8 data lanes × 8 rows each)
PITCH_X = 1.5625  # mm
PITCH_Y = 1.625   # mm

# Starting position (adjust for your board)
START_X = 10.0  # mm
START_Y = 10.0  # mm

# LED reference prefix (e.g., "D" for D1, D2, ...)
LED_PREFIX = "D"

# Block rotations for VIA optimization
BLOCK_ROTATIONS = {
    (True, True):   -90,   # Top-left LED in each 2×2 block
    (False, True):    0,   # Top-right LED
    (True, False):  180,   # Bottom-left LED
    (False, False):  90,   # Bottom-right LED
}
```

### For Legacy Scripts

Edit these variables in `place_led_matrix.py` or `place_led_matrix_advanced.py`:

```python
# Matrix size (legacy layout)
COLS = 64
ROWS = 40
PITCH_X = 1.5625  # mm
PITCH_Y = 1.625   # mm

# Starting position (adjust for your board)
START_X = 10.0  # mm
START_Y = 10.0  # mm

# LED reference prefix (e.g., "D" for D1, D2, ...)
LED_PREFIX = "D"

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

### Method 1: VIA-Optimized Workflow (Recommended)

1. **Design schematic** with 2560 LED symbols
   - Use hierarchical sheets or array annotations if needed
   - Assign XL-1010RGBC-2812B footprint to all
   - Add connectors: J1 (data lines) and J2 (VDD/GND)

2. **Update PCB from schematic**
   - All LEDs import as a stack at origin

3. **Run LED placement script**
   - `exec(open('scripts/place_led_matrix_via_optimized.py').read())`
   - Verify LED orientations match intended 2×2 block pattern

4. **Run VIA placement script**
   - `exec(open('scripts/place_power_vias.py').read())`
   - Places 640 shared VIAs in 2×2 block centers

5. **Power distribution**
   - Assign VIAs to VDD/GND nets
   - Add power planes on inner layers
   - Connect J2 (power connector) to power distribution

6. **Data routing**
   - Route 8 data lanes from J1 (data connector)
   - Each lane: 8 rows × 40 LEDs in serpentine pattern
   - Add series resistors on data lines if needed

### Method 2: Legacy Import then Auto-Place

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

### VIA-Optimized Script

```
Placing 2560 LEDs in VIA-optimized pattern
Matrix: 40 columns × 64 rows
Pitch: 1.5625mm × 1.625mm
Pattern: 8-lane serpentine with 2×2 block VIA optimization
Starting position: (10.0, 10.0)

  Using VIA-optimized 8-lane serpentine pattern
  Layout: 40 columns × 64 rows = 2560 LEDs
  Data lanes: 8 lanes × 320 pixels
  Each lane: 8 rows × 40 columns
  2×2 block rotations for shared center VIAs

  Placed 100/2560 LEDs...
  Placed 200/2560 LEDs...
  ...
  Placed 2560/2560 LEDs...

✓ Successfully placed 2560 LEDs

Matrix dimensions:
  Width: 60.938 mm (40 columns)
  Height: 102.375 mm (64 rows)
  Total area: 60.9 × 102.4 mm
  End position: (70.938, 112.375)

  VIA optimization: LEDs grouped in 2×2 blocks
  - 640 shared VIAs possible
  - Each VIA serves 4 LEDs (VDD + GND)

Done! Board refreshed.
```

### Legacy Script

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

### VIA-Optimized Layout (40×64)

After placement, verify:
- Total matrix width: ~60.94 mm (40 columns)
- Total matrix height: ~102.38 mm (64 rows)
- Body-to-body clearance: 0.56–0.63 mm (as specified in README)
- VIA positions: centered between each 2×2 LED block
- VDD/GND pins oriented toward center VIAs in each 2×2 block

### Legacy Layout (64×40)

After placement, verify:
- Total matrix width: ~98.44 mm (64 columns, matches README: 100mm including margins)
- Total matrix height: ~63.38 mm (40 rows, matches README: 65mm including margins)
- Body-to-body clearance: 0.56–0.63 mm (as specified in README)

## Next Steps

### After VIA-Optimized Placement

1. **Place and route power VIAs** (use `place_power_vias.py`)
2. **Add power distribution network**
   - Connect J2 connector (VDD/GND) to power planes
   - Use inner layers for power planes
   - Heavy traces or copper pours between VIAs
3. **Add decoupling capacitors** (per 2×2 block or per LED row)
4. **Route 8 data lanes**
   - Connect J1 connector (8 data inputs) to start of each lane
   - Follow serpentine pattern within each lane
   - Add series resistors (220-470Ω) on each data line
5. **Verify LED orientations**
   - Check that VDD/GND pins face center VIAs in each 2×2 block
   - Adjust BLOCK_ROTATIONS if needed
6. **Add soldermask and silkscreen**
7. **DRC check** focusing on soldermask webbing between pads
8. **Generate Gerbers**

### After Legacy Placement

1. Add power distribution network
2. Add decoupling capacitors (per LED or per cluster)
3. Route data lanes from connector to lane entry points
4. Add soldermask and silkscreen
5. DRC check focusing on soldermask webbing between pads
6. Generate Gerbers

## License

Part of the Ultra-High-Density RGB Matrix Badge project (AGPL-3.0)
