# Quick Start Guide

## 1. Setup (First Time Only)
```bash
cd test_animations
./setup.sh
```

## 2. Flash to ESP32
```bash
# Connect ESP32 via USB, then:
./flash.sh
```

## 3. Watch It Run
```bash
# To see serial output:
./flash.sh -m
```

## Alternative: Using Make
```bash
make setup        # First time only
make flash        # Build and upload
make monitor      # View serial output
```

## Troubleshooting

**"Permission denied" error:**
```bash
sudo usermod -a -G dialout $USER
# Then log out and back in
```

**"Device not found" error:**
```bash
# List available ports:
pio device list

# Flash to specific port:
./flash.sh -p /dev/ttyUSB0
```

**Need to rebuild from scratch:**
```bash
./flash.sh -c    # Clean and rebuild
```

That's it! The snake should start playing automatically.
