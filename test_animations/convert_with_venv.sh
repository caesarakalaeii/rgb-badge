#!/bin/bash

# Standalone converter script with venv
# Use this if you want to just convert the video without flashing

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

echo -e "${YELLOW}Bad Apple Video Converter${NC}\n"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 not found${NC}"
    exit 1
fi

# Create venv if needed
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ Failed to create venv${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Created venv at .venv/${NC}"
fi

# Activate venv
source "$VENV_DIR/bin/activate"

# Install requirements if needed
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies..."
    pip install -q -r requirements.txt
else
    echo "Installing dependencies..."
    pip install -q opencv-python numpy pillow requests tqdm
fi

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Failed to install dependencies${NC}"
    deactivate
    exit 1
fi

# Run converter
echo -e "\n${GREEN}Running converter...${NC}\n"
python bad_apple_converter.py

EXIT_CODE=$?

deactivate

if [ $EXIT_CODE -eq 0 ]; then
    echo -e "\n${GREEN}✓ Conversion complete!${NC}"
    echo "Output: bad_apple_data/bad_apple_frames.bin"
else
    echo -e "\n${RED}✗ Conversion failed${NC}"
    exit 1
fi
