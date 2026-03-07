#!/bin/bash

# Helper script to download Bad Apple video
# Tries multiple methods

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

VIDEO_FILE="bad_apple.mp4"

echo -e "${YELLOW}Bad Apple Video Downloader${NC}\n"

# Check if file already exists
if [ -f "$VIDEO_FILE" ]; then
    FILE_SIZE=$(stat -f%z "$VIDEO_FILE" 2>/dev/null || stat -c%s "$VIDEO_FILE" 2>/dev/null)
    echo -e "${GREEN}✓ Video already exists: $VIDEO_FILE (${FILE_SIZE} bytes)${NC}"
    exit 0
fi

# Method 1: Try yt-dlp
if command -v yt-dlp &> /dev/null; then
    echo "Method 1: Downloading from YouTube using yt-dlp..."
    yt-dlp -f 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best' \
           -o "$VIDEO_FILE" \
           'https://www.youtube.com/watch?v=FtutLA63Cp8'

    if [ -f "$VIDEO_FILE" ]; then
        echo -e "\n${GREEN}✓ Download complete!${NC}"
        exit 0
    fi
fi

# Method 2: Try youtube-dl (older alternative)
if command -v youtube-dl &> /dev/null; then
    echo "Method 2: Downloading from YouTube using youtube-dl..."
    youtube-dl -f 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best' \
               -o "$VIDEO_FILE" \
               'https://www.youtube.com/watch?v=FtutLA63Cp8'

    if [ -f "$VIDEO_FILE" ]; then
        echo -e "\n${GREEN}✓ Download complete!${NC}"
        exit 0
    fi
fi

# Method 3: Try wget from archive.org
if command -v wget &> /dev/null; then
    echo "Method 3: Downloading from archive.org using wget..."
    wget -O "$VIDEO_FILE" "https://archive.org/download/bad-apple-video/bad_apple.mp4"

    if [ -f "$VIDEO_FILE" ] && [ -s "$VIDEO_FILE" ]; then
        echo -e "\n${GREEN}✓ Download complete!${NC}"
        exit 0
    else
        rm -f "$VIDEO_FILE"
    fi
fi

# Method 4: Try curl from archive.org
if command -v curl &> /dev/null; then
    echo "Method 4: Downloading from archive.org using curl..."
    curl -L -o "$VIDEO_FILE" "https://archive.org/download/bad-apple-video/bad_apple.mp4"

    if [ -f "$VIDEO_FILE" ] && [ -s "$VIDEO_FILE" ]; then
        echo -e "\n${GREEN}✓ Download complete!${NC}"
        exit 0
    else
        rm -f "$VIDEO_FILE"
    fi
fi

# All methods failed
echo -e "\n${RED}✗ All download methods failed${NC}"
echo -e "\n${YELLOW}Please download manually:${NC}"
echo ""
echo "Option 1: Install yt-dlp and retry"
echo "  pip install yt-dlp"
echo "  ./download_bad_apple.sh"
echo ""
echo "Option 2: YouTube (search and download)"
echo "  Search: 'Bad Apple Touhou original'"
echo "  Download and save as: bad_apple.mp4"
echo ""
echo "Option 3: Archive.org (may be down)"
echo "  https://archive.org/details/bad-apple-video"
echo "  Download and save as: bad_apple.mp4"
echo ""

exit 1
