.PHONY: help upload monitor clean all

help:
	@echo "Makefile targets:"
	@echo "  help			- Shows this help :3"
	@echo "	 upload			- Uploads firmware"
	@echo "  monitor		- Monitors serial output"
	@echo "  clean			- Runs pio clean target"
	@echo "  venv			- Sets up a venv"
	@echo "  venva			- Activates the venv"
	@echo "  all			- Uploads and monitors serial output"
	@echo ""

upload:
	@pio run --target upload

monitor:
	@pio run --target monitor

clean:
	@pio run --target clean

venv:
	@python3 -m venv .venv

venva:
	@if [ ! -f .venv/bin/activate ]; then \
		make venv; \
	fi
	@source .venv/bin/activate

all: venva upload monitor
