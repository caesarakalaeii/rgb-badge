#!/bin/bash

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo -e "${BLUE}=== Bad Apple RGB Edition Flasher ===${NC}\n"

# Check PlatformIO
if ! command -v pio &> /dev/null; then
    echo -e "${RED}Error: PlatformIO not installed${NC}"
    echo "Run: pip install platformio"
    exit 1
fi

# Parse arguments
UPLOAD_FS=false
MONITOR=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--filesystem)
            UPLOAD_FS=true
            shift
            ;;
        -m|--monitor)
            MONITOR=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -f, --filesystem    Upload filesystem (data folder)"
            echo "  -m, --monitor       Open serial monitor after flashing"
            echo "  -h, --help          Show this help"
            echo ""
            echo "Examples:"
            echo "  $0                  Build and flash firmware"
            echo "  $0 -f               Upload filesystem only"
            echo "  $0 -m               Flash and monitor"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Upload filesystem if requested
if [ "$UPLOAD_FS" = true ]; then
    echo -e "${YELLOW}Uploading filesystem...${NC}"
    echo "This will upload files from the 'data' folder"

    if [ ! -d "data" ]; then
        echo -e "${RED}✗ No 'data' folder found${NC}"
        echo "Run: python3 ../bad_apple_converter.py first"
        exit 1
    fi

    pio run --target uploadfs
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ Filesystem upload failed${NC}"
        exit 1
    fi

    echo -e "${GREEN}✓ Filesystem uploaded${NC}"
    exit 0
fi

# Build and flash firmware
echo -e "${YELLOW}Building firmware...${NC}"
pio run
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Build failed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Build successful${NC}"

echo -e "\n${YELLOW}Flashing to ESP32...${NC}"
pio run --target upload
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Flash failed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Flash successful!${NC}"

# Monitor if requested
if [ "$MONITOR" = true ]; then
    echo -e "\n${BLUE}Opening serial monitor...${NC}"
    echo -e "${YELLOW}Press Ctrl+C to exit${NC}\n"
    sleep 2
    pio device monitor
fi

echo -e "\n${GREEN}=== Done! ===${NC}"
