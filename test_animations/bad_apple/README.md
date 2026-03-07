# Bad Apple RGB Edition for 10x10 LED Matrix

A colorful version of the iconic Bad Apple animation running on ESP32 with a 10x10 RGB LED matrix.

## Features

- **6 Color Modes:**
  - Classic Black & White
  - Rainbow Cycle
  - Pulsing Pink/Purple
  - Fire Effect (red-orange-yellow)
  - Matrix Green
  - Ocean Waves (blue-cyan)

- **Auto-looping** with color mode changes
- **20 FPS** smooth playback
- **~6500 frames** of animation
- **LittleFS storage** for efficient data access

## Hardware Setup

- **ESP32 Dev Board**
- **10x10 RGB LED Matrix** (WS2812B)
  - Data line 1: GPIO 13 (first 50 LEDs)
  - Data line 2: GPIO 12 (second 50 LEDs)
- **5V Power Supply** (adequate current for 100 LEDs)

## Quick Start (One Command!)

```bash
./setup_and_flash.sh
```

This will:
1. Install Python dependencies
2. Download and convert Bad Apple video
3. Build firmware
4. Flash to ESP32
5. Upload filesystem data

That's it! The animation will start playing automatically.

## Manual Setup (Step by Step)

### 1. Install Dependencies

**Using virtual environment (recommended):**
```bash
cd ..
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Or system-wide:**
```bash
pip install opencv-python numpy pillow requests tqdm
```

**PlatformIO:**
```bash
pip install platformio
```

### 2. Convert Video to Frame Data

**Easy way:**
```bash
cd ..
./convert_with_venv.sh  # Handles venv automatically
```

**Or manually:**
```bash
cd ..
source .venv/bin/activate  # If using venv
python bad_apple_converter.py
deactivate  # If using venv
```

This will:
- Download Bad Apple video (~16MB)
- Convert to 10x10 resolution
- Generate `bad_apple_data/bad_apple_frames.bin`
- Create preview images

### 3. Copy Data to Project

```bash
cd bad_apple
mkdir -p data
cp ../bad_apple_data/bad_apple_frames.bin data/
```

### 4. Build and Flash

```bash
# Build and flash firmware
pio run --target upload

# Upload filesystem (contains frame data)
pio run --target uploadfs
```

### 5. Watch It Play!

```bash
pio device monitor
```

## Using the Flash Scripts

**Quick flash:**
```bash
./flash.sh
```

**With serial monitor:**
```bash
./flash.sh -m
```

**Upload filesystem only:**
```bash
./flash.sh -f
```

## Color Modes

The animation automatically cycles through different color modes each time it loops:

| Mode | Description | Visual Effect |
|------|-------------|---------------|
| 0 | Classic | Traditional black and white |
| 1 | Rainbow | Full spectrum color cycling |
| 2 | Pulse | Pulsing pink/purple |
| 3 | Fire | Random orange/red flames |
| 4 | Matrix | Classic Matrix green |
| 5 | Ocean | Blue-cyan waves |

## Technical Details

### Frame Format
- **Resolution:** 10x10 pixels (100 pixels total)
- **Encoding:** 1 bit per pixel (monochrome)
- **Storage:** 13 bytes per frame
- **Total size:** ~85KB (6500 frames)
- **Frame rate:** 20 FPS
- **Duration:** ~5.4 minutes

### File Structure
```
bad_apple_frames.bin:
  Header (6 bytes):
    - uint16_t: frame count
    - uint8_t:  FPS
    - uint8_t:  width (10)
    - uint8_t:  height (10)
    - uint8_t:  padding
  Frames (13 bytes each):
    - 100 pixels packed into 13 bytes
    - MSB first, row-major order
```

### Memory Usage
- **Flash:** ~85KB for frame data
- **RAM:** <1KB (single frame buffer)
- **Program:** ~300KB

## Troubleshooting

### "LittleFS initialization failed"
- Make sure you ran: `pio run --target uploadfs`
- Try: `./flash.sh -f` to re-upload filesystem

### "Failed to open data file"
1. Check data folder exists: `ls data/`
2. Verify file: `ls -lh data/bad_apple_frames.bin`
3. Re-run converter: `python3 ../bad_apple_converter.py`
4. Re-upload: `pio run --target uploadfs`

### "Upload failed" or "Permission denied"
```bash
# Add user to dialout group (Linux)
sudo usermod -a -G dialout $USER
# Log out and back in

# Or specify port manually
pio run --target upload --upload-port /dev/ttyUSB0
```

### Video plays too fast/slow
Adjust `BA_FRAME_MS` in `src/main.cpp`:
```cpp
#define BA_FRAME_MS 50  // 50ms = 20 FPS, increase for slower
```

### Wrong colors or brightness
Adjust in `setup()`:
```cpp
FastLED.setBrightness(80);  // 0-255
```

### LEDs not responding
- Check power supply (5V, adequate amperage)
- Verify GPIO connections (13 and 12)
- Test LED strip direction
- Check wiring layout (serpentine pattern expected)

## Customization

### Add More Color Modes

Edit `getColorForMode()` in `src/main.cpp`:

```cpp
case MODE_CUSTOM:
  return CHSV(hue, saturation, brightness);
```

Don't forget to update `MODE_COUNT`.

### Change Layout

If your matrix has different wiring, modify `setPixel()`:

```cpp
// For non-serpentine layout:
int ledIndex = y * MATRIX_WIDTH + x;
```

### Disable Looping

In `setup()`:
```cpp
bool loopVideo = false;
```

### Manual Color Mode Control

Replace `nextColorMode()` call with specific mode:
```cpp
colorMode = MODE_FIRE;  // Lock to fire mode
```

## Credits

- **Bad Apple!!** - Original video from Touhou Project
- **FastLED** - LED control library
- **Archive.org** - Video source

## What is Bad Apple?

Bad Apple is a famous music video from the Touhou Project series featuring distinctive black-and-white silhouette animation. It became an internet phenomenon and a popular benchmark for demonstrating display capabilities on various hardware platforms, from oscilloscopes to graphing calculators.

## License

This project is for educational and personal use. The Bad Apple video content belongs to its original creators.

## Additional Resources

- [Bad Apple on Know Your Meme](https://knowyourmeme.com/memes/bad-apple)
- [FastLED Documentation](https://fastled.io/)
- [PlatformIO Documentation](https://docs.platformio.org/)

## Support

Having issues? Check:
1. Serial monitor output for error messages
2. File sizes match expected values
3. All dependencies installed correctly
4. ESP32 properly powered

Enjoy the show! 🍎✨
