.PHONY: help setup convert build flash upload-fs flash-all monitor clean

help:
	@echo "Bad Apple RGB Edition - Make Commands"
	@echo ""
	@echo "Quick start:"
	@echo "  make all           - Do everything (convert + build + flash + upload)"
	@echo ""
	@echo "Individual steps:"
	@echo "  make setup         - Install dependencies"
	@echo "  make convert       - Convert video to frames"
	@echo "  make build         - Build firmware"
	@echo "  make flash         - Flash firmware to ESP32"
	@echo "  make upload-fs     - Upload filesystem (frame data)"
	@echo "  make monitor       - Open serial monitor"
	@echo "  make clean         - Clean build files"
	@echo ""

setup:
	@echo "Setting up Python virtual environment..."
	@cd .. && python3 -m venv .venv
	@cd .. && .venv/bin/pip install --upgrade pip -q
	@cd .. && .venv/bin/pip install -q opencv-python numpy pillow requests tqdm
	@echo "✓ Virtual environment created at ../.venv"
	@echo "To activate: source ../.venv/bin/activate"

convert:
	@echo "Converting Bad Apple video..."
	@if [ ! -d "../.venv" ]; then \
		echo "Creating venv first..."; \
		make setup; \
	fi
	@cd .. && .venv/bin/python bad_apple_converter.py
	@mkdir -p data
	@cp ../bad_apple_data/bad_apple_frames.bin data/
	@echo "✓ Frame data copied to data/"

build:
	@pio run

flash:
	@pio run --target upload

upload-fs:
	@echo "Uploading filesystem (this may take 30-60 seconds)..."
	@pio run --target uploadfs

flash-all: build flash upload-fs
	@echo ""
	@echo "✓ Complete! Bad Apple should be playing now."
	@echo "Run 'make monitor' to see serial output"

all: setup convert flash-all

monitor:
	@pio device monitor

clean:
	@pio run --target clean
	@rm -rf .pio
	@echo "✓ Build files cleaned"

clean-all: clean
	@rm -rf data/
	@rm -rf ../bad_apple_data/
	@rm -f ../bad_apple.mp4
	@echo "✓ All generated files cleaned"
