#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== ESP32 Development Environment Setup ===${NC}\n"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed!${NC}"
    echo "Please install Python 3 first."
    exit 1
fi

echo -e "${GREEN}✓ Python 3 found${NC}"

# Check if pip is installed
if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
    echo -e "${RED}Error: pip is not installed!${NC}"
    echo "Please install pip first."
    exit 1
fi

echo -e "${GREEN}✓ pip found${NC}"

# Check if PlatformIO is already installed
if command -v pio &> /dev/null; then
    echo -e "${GREEN}✓ PlatformIO is already installed${NC}"
    pio --version
else
    echo -e "\n${YELLOW}Installing PlatformIO...${NC}"

    # Try to install via pip
    if command -v pip3 &> /dev/null; then
        pip3 install --user platformio
    else
        pip install --user platformio
    fi

    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ PlatformIO installation failed via pip${NC}"
        echo -e "${YELLOW}Trying alternative installation method...${NC}"

        # Try the official installer
        curl -fsSL https://raw.githubusercontent.com/platformio/platformio-core/master/scripts/get-platformio.py | python3

        if [ $? -ne 0 ]; then
            echo -e "${RED}✗ Installation failed${NC}"
            exit 1
        fi
    fi

    echo -e "${GREEN}✓ PlatformIO installed${NC}"

    # Add to PATH if needed
    if ! command -v pio &> /dev/null; then
        echo -e "\n${YELLOW}Note: You may need to add PlatformIO to your PATH${NC}"
        echo "Add this to your ~/.bashrc or ~/.zshrc:"
        echo "  export PATH=\$PATH:\$HOME/.local/bin"
        echo ""
        echo "Then run: source ~/.bashrc  (or source ~/.zshrc)"
    fi
fi

# Check for udev rules (Linux only)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo -e "\n${YELLOW}Checking USB permissions...${NC}"

    if groups | grep -q "dialout\|uucp"; then
        echo -e "${GREEN}✓ User is in dialout/uucp group${NC}"
    else
        echo -e "${YELLOW}Warning: User is not in dialout group${NC}"
        echo "To add yourself to the dialout group, run:"
        echo "  sudo usermod -a -G dialout \$USER"
        echo "Then log out and log back in for changes to take effect."
    fi

    # Install udev rules for PlatformIO
    if [ ! -f /etc/udev/rules.d/99-platformio-udev.rules ]; then
        echo -e "\n${YELLOW}Installing udev rules for ESP32 devices...${NC}"
        curl -fsSL https://raw.githubusercontent.com/platformio/platformio-core/master/scripts/99-platformio-udev.rules | sudo tee /etc/udev/rules.d/99-platformio-udev.rules > /dev/null
        sudo udevadm control --reload-rules
        sudo udevadm trigger
        echo -e "${GREEN}✓ udev rules installed${NC}"
    else
        echo -e "${GREEN}✓ udev rules already installed${NC}"
    fi
fi

echo -e "\n${GREEN}=== Setup Complete! ===${NC}"
echo -e "\n${BLUE}Next steps:${NC}"
echo "  1. Connect your ESP32 via USB"
echo "  2. Run: ./flash.sh"
echo ""
echo "For help: ./flash.sh --help"
