# Snake Animation for ESP32 with 10x10 LED Matrix

## Hardware Setup
- **LED Matrix:** 10x10 (100 LEDs total)
- **Data Pins:**
  - D13 (GPIO 13) - First 50 LEDs
  - D12 (GPIO 12) - Second 50 LEDs
- **LED Type:** WS2812B (addressable RGB)
- **Board:** ESP32

## Features
- **Snake Game Animation:** Automatically navigating snake
- **Color-Changing Snake:** Snake changes color to match the food it eats
- **Cycling Food Colors:** Food continuously cycles through the full color spectrum
- **Auto-Wrap:** Snake wraps around screen edges
- **Game Over:** Restarts automatically when snake hits itself

## Installation

### Method 1: PlatformIO (Recommended)

**Quick Start:**
```bash
# Install PlatformIO and setup environment
./setup.sh

# Build and flash to ESP32
./flash.sh

# Build, flash, and open serial monitor
./flash.sh -m
```

**Available Options:**
```bash
./flash.sh              # Build and flash
./flash.sh -m           # Build, flash, and monitor
./flash.sh -c           # Clean build first
./flash.sh -p /dev/ttyUSB0  # Specify port
./flash.sh --help       # Show all options
```

**Manual PlatformIO Installation:**
```bash
# Install PlatformIO
pip install platformio

# Build project
pio run

# Upload to ESP32
pio run --target upload

# Open serial monitor
pio device monitor
```

### Method 2: Arduino IDE

1. Install the FastLED library:
   - Go to **Sketch → Include Library → Manage Libraries**
   - Search for "FastLED"
   - Install "FastLED by Daniel Garcia"
2. Open `src/main.cpp` (or rename to `.ino`)
3. Select ESP32 board from **Tools → Board**
4. Select COM port from **Tools → Port**
5. Click Upload

## Configuration

### Adjustable Parameters
```cpp
#define SNAKE_SPEED 200        // Speed in milliseconds (lower = faster)
#define INITIAL_SNAKE_LENGTH 3 // Starting snake length
FastLED.setBrightness(50);     // LED brightness (0-255)
```

### LED Layout
The code assumes a serpentine/zigzag layout:
```
→ → → → → → → → → →
                    ↓
← ← ← ← ← ← ← ← ← ←
↓
→ → → → → → → → → →
```

If your matrix has a different layout, you may need to adjust the `setPixel()` function.

## How It Works
1. Snake starts at position (5,5) moving right
2. Food appears at random positions with cycling colors
3. Snake automatically navigates toward food
4. When snake eats food, it grows and changes to food's color
5. Game ends if snake collides with itself, then auto-restarts

## Troubleshooting

### LEDs not lighting up
- Check power supply (WS2812B needs 5V, adequate current)
- Verify GPIO pin connections (D13 = GPIO13, D12 = GPIO12)
- Check LED strip data direction

### Wrong colors or patterns
- Verify `LED_TYPE` and `COLOR_ORDER` in code
- Some strips use RGB instead of GRB order
- Adjust serpentine pattern in `setPixel()` if needed

### Compilation errors
- Ensure FastLED library is installed
- Select ESP32 board (not Arduino boards)
- Update Arduino ESP32 board package if needed

## Serial Monitor
Open Serial Monitor (115200 baud) to see game status:
- Food eaten events
- Snake length updates
- Game over notifications

## Alternative: Using with WLED
This is a standalone sketch. If you want to use WLED firmware instead:
- Flash WLED to ESP32
- Use WLED's built-in effects via web interface
- Note: WLED doesn't have a snake game effect built-in
- You would need to create a custom WLED usermod for this animation
