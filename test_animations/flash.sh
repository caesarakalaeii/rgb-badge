#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}=== ESP32 Snake Animation Flasher ===${NC}\n"

# Check if PlatformIO is installed
if ! command -v pio &> /dev/null; then
    echo -e "${RED}Error: PlatformIO is not installed!${NC}"
    echo -e "${YELLOW}Install it with:${NC}"
    echo "  pip install platformio"
    echo "  or"
    echo "  curl -fsSL https://raw.githubusercontent.com/platformio/platformio-core/master/scripts/get-platformio.py | python3"
    exit 1
fi

echo -e "${GREEN}✓ PlatformIO found${NC}"

# Change to project directory
cd "$PROJECT_DIR"

# Parse command line arguments
BUILD_ONLY=false
MONITOR_ONLY=false
CLEAN=false
PORT=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -b|--build-only)
            BUILD_ONLY=true
            shift
            ;;
        -m|--monitor)
            MONITOR_ONLY=true
            shift
            ;;
        -c|--clean)
            CLEAN=true
            shift
            ;;
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -b, --build-only    Build only, don't flash"
            echo "  -m, --monitor       Open serial monitor after flashing"
            echo "  -c, --clean         Clean build files before building"
            echo "  -p, --port PORT     Specify upload port (e.g., /dev/ttyUSB0)"
            echo "  -h, --help          Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                  Build and flash"
            echo "  $0 -m               Build, flash, and open monitor"
            echo "  $0 -c -p /dev/ttyUSB0  Clean, build, and flash to specific port"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Clean if requested
if [ "$CLEAN" = true ]; then
    echo -e "\n${YELLOW}Cleaning build files...${NC}"
    pio run --target clean
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ Clean failed${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Clean completed${NC}"
fi

# Build the project
echo -e "\n${YELLOW}Building project...${NC}"
pio run
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Build failed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Build successful${NC}"

# Exit if build-only
if [ "$BUILD_ONLY" = true ]; then
    echo -e "\n${GREEN}Build completed. Skipping flash.${NC}"
    exit 0
fi

# Flash if monitor-only is not set
if [ "$MONITOR_ONLY" = false ]; then
    echo -e "\n${YELLOW}Flashing to ESP32...${NC}"

    if [ -n "$PORT" ]; then
        echo -e "${BLUE}Using port: $PORT${NC}"
        pio run --target upload --upload-port "$PORT"
    else
        pio run --target upload
    fi

    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ Flash failed${NC}"
        echo -e "${YELLOW}Troubleshooting:${NC}"
        echo "  - Check if ESP32 is connected via USB"
        echo "  - Try specifying port with: $0 -p /dev/ttyUSB0"
        echo "  - Check permissions: sudo usermod -a -G dialout \$USER"
        echo "  - List ports: pio device list"
        exit 1
    fi

    echo -e "${GREEN}✓ Flash successful!${NC}"

    # Wait a moment for the device to reset
    sleep 2
fi

# Open monitor if requested or if monitor-only
if [ "$MONITOR_ONLY" = true ] || [ "$1" = "-m" ]; then
    echo -e "\n${BLUE}Opening serial monitor (115200 baud)...${NC}"
    echo -e "${YELLOW}Press Ctrl+C to exit monitor${NC}\n"

    if [ -n "$PORT" ]; then
        pio device monitor --port "$PORT" --baud 115200
    else
        pio device monitor --baud 115200
    fi
fi

echo -e "\n${GREEN}=== Done! ===${NC}"
