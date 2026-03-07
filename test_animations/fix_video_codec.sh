#!/bin/bash

# Convert video to H.264 format (compatible with OpenCV)

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

INPUT="bad_apple.mp4"
OUTPUT="bad_apple_h264.mp4"

echo -e "${YELLOW}Video Codec Converter${NC}\n"

# Check if ffmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${RED}✗ ffmpeg not found${NC}"
    echo "Install with:"
    echo "  sudo apt install ffmpeg      # Debian/Ubuntu"
    echo "  sudo pacman -S ffmpeg        # Arch"
    echo "  brew install ffmpeg          # macOS"
    exit 1
fi

# Check if input exists
if [ ! -f "$INPUT" ]; then
    echo -e "${RED}✗ $INPUT not found${NC}"
    exit 1
fi

echo "Converting $INPUT to H.264 format..."
echo "This will take a few minutes..."
echo ""

# Convert to H.264 with compatible settings
ffmpeg -i "$INPUT" \
    -c:v libx264 \
    -preset fast \
    -crf 23 \
    -c:a aac \
    -b:a 128k \
    -y \
    "$OUTPUT"

if [ $? -eq 0 ] && [ -f "$OUTPUT" ]; then
    echo -e "\n${GREEN}✓ Conversion complete!${NC}"

    # Replace original file
    mv "$INPUT" "${INPUT}.av1.bak"
    mv "$OUTPUT" "$INPUT"

    echo -e "${GREEN}✓ Replaced $INPUT with H.264 version${NC}"
    echo "Original AV1 version backed up as: ${INPUT}.av1.bak"
    echo ""
    echo "Now run: ./convert_with_venv.sh"
else
    echo -e "\n${RED}✗ Conversion failed${NC}"
    exit 1
fi
