#!/bin/bash

# Complete setup and flash script for Bad Apple RGB Edition
# This automates the entire process

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}"
echo "================================================================"
echo "  Bad Apple RGB Edition - Complete Setup & Flash"
echo "================================================================"
echo -e "${NC}\n"

# Step 1: Setup Python virtual environment
echo -e "${YELLOW}[1/5] Setting up Python environment...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 not found${NC}"
    exit 1
fi

VENV_DIR="$PROJECT_DIR/../.venv"

# Create venv if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ Failed to create virtual environment${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo "Using existing virtual environment"
fi

# Activate venv
source "$VENV_DIR/bin/activate"

# Install/upgrade pip
python -m pip install --upgrade pip -q

# Install dependencies
echo "Installing Python packages in venv..."
pip install -q opencv-python numpy pillow requests tqdm
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Failed to install Python dependencies${NC}"
    deactivate
    exit 1
fi

echo -e "${GREEN}✓ Python environment ready${NC}"

# Step 2: Convert video
echo -e "\n${YELLOW}[2/5] Converting Bad Apple video to frames...${NC}"
echo "This will download and process the video (~16MB download)"

cd "$PROJECT_DIR/.."

if [ ! -f "bad_apple_converter.py" ]; then
    echo -e "${RED}✗ Converter script not found${NC}"
    deactivate
    exit 1
fi

# Run converter with venv Python
python bad_apple_converter.py
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Conversion failed${NC}"
    deactivate
    exit 1
fi

echo -e "${GREEN}✓ Conversion complete${NC}"

# Step 3: Copy data to project
echo -e "\n${YELLOW}[3/5] Copying frame data to project...${NC}"

cd "$PROJECT_DIR"
mkdir -p data

if [ -f "../bad_apple_data/bad_apple_frames.bin" ]; then
    cp ../bad_apple_data/bad_apple_frames.bin data/
    FILE_SIZE=$(stat -f%z data/bad_apple_frames.bin 2>/dev/null || stat -c%s data/bad_apple_frames.bin 2>/dev/null)
    echo -e "${GREEN}✓ Copied frame data (${FILE_SIZE} bytes)${NC}"
else
    echo -e "${RED}✗ Frame data not found${NC}"
    deactivate
    exit 1
fi

# Deactivate venv before PlatformIO operations
deactivate

# Step 4: Build and flash firmware
echo -e "\n${YELLOW}[4/5] Building and flashing firmware...${NC}"

if ! command -v pio &> /dev/null; then
    echo -e "${RED}✗ PlatformIO not installed${NC}"
    echo "Install with: pip install platformio"
    echo "Or in venv: source ../.venv/bin/activate && pip install platformio"
    exit 1
fi

pio run --target upload
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Firmware flash failed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Firmware flashed${NC}"

# Step 5: Upload filesystem
echo -e "\n${YELLOW}[5/5] Uploading filesystem data...${NC}"
echo "This may take 30-60 seconds..."

pio run --target uploadfs
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Filesystem upload failed${NC}"
    echo -e "${YELLOW}You may need to hold the BOOT button on ESP32${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Filesystem uploaded${NC}"

# Done!
echo -e "\n${GREEN}"
echo "================================================================"
echo "  ✓ Setup Complete!"
echo "================================================================"
echo -e "${NC}"
echo "Bad Apple should now be playing on your LED matrix!"
echo ""
echo "To monitor serial output:"
echo "  pio device monitor"
echo ""
echo "Or run: ./flash.sh -m"
echo ""

# Ask if user wants to see serial monitor
read -p "Open serial monitor now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "\n${BLUE}Opening serial monitor (Ctrl+C to exit)...${NC}\n"
    sleep 2
    pio device monitor
fi
