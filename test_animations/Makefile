.PHONY: help setup build flash monitor clean list-ports

help:
	@echo "ESP32 Snake Animation - Make Commands"
	@echo ""
	@echo "Usage:"
	@echo "  make setup        - Install PlatformIO and dependencies"
	@echo "  make build        - Build the project"
	@echo "  make flash        - Build and flash to ESP32"
	@echo "  make monitor      - Open serial monitor"
	@echo "  make flash-monitor - Flash and open monitor"
	@echo "  make clean        - Clean build files"
	@echo "  make list-ports   - List available serial ports"
	@echo ""

setup:
	@./setup.sh

build:
	@pio run

flash:
	@pio run --target upload

monitor:
	@pio device monitor

flash-monitor: flash
	@sleep 2
	@pio device monitor

clean:
	@pio run --target clean

list-ports:
	@pio device list
