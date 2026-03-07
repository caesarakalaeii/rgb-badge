# Bad Apple RGB - Quick Start

## One-Line Setup

```bash
./setup_and_flash.sh
```

Done! The animation will start automatically.

---

## Alternative: Using Make

```bash
make all          # Does everything
make monitor      # Watch serial output
```

---

## Manual Steps (if you prefer)

### 1. Convert Video (with venv)
```bash
cd ..
./convert_with_venv.sh
cd bad_apple
```

Or manually:
```bash
cd ..
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python bad_apple_converter.py
deactivate
cd bad_apple
```

### 3. Copy Data
```bash
mkdir -p data
cp ../bad_apple_data/bad_apple_frames.bin data/
```

### 4. Flash Everything
```bash
pio run --target upload      # Firmware
pio run --target uploadfs    # Data
```

---

## Troubleshooting

**"LittleFS init failed"**
```bash
pio run --target uploadfs
```

**"Permission denied"**
```bash
sudo usermod -a -G dialout $USER
# Then log out and back in
```

**"Port not found"**
```bash
pio device list
pio run --target upload --upload-port /dev/ttyUSB0
```

---

## What You'll See

- **Duration:** ~5.4 minutes
- **Frame rate:** 20 FPS
- **Resolution:** 10×10 pixels
- **Color modes:** Cycles through 6 different color schemes
  - Classic B&W
  - Rainbow
  - Pulsing Pink
  - Fire Effect
  - Matrix Green
  - Ocean Blue

The animation loops forever with different colors each time!

---

## Quick Commands

```bash
# See what's happening
pio device monitor

# Re-flash firmware only
./flash.sh

# Re-upload data only
./flash.sh -f

# Flash and monitor
./flash.sh -m
```

That's it! 🍎✨
