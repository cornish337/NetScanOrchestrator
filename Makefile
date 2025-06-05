# Makefile for nmap-parallel-scanner

.PHONY: help install build-docker run-docker-scan run-cli-scan start-webui lint test clean

# Default target when 'make' is run without arguments
help:
	@echo "Nmap Parallel Scanner Makefile"
	@echo "--------------------------------"
	@echo "Available targets:"
	@echo "  install          - Install Python dependencies for local development."
	@echo "  build-docker     - Build the Docker image."
	@echo "  run-docker-scan  - Run a sample Nmap scan using Docker. (Edit params in Makefile first)"
	@echo "  run-cli-scan     - Run a sample Nmap scan using the local Python script. (Edit params in Makefile first)"
	@echo "  start-webui      - Start the local Flask web UI."
	@echo "  lint             - Run linters (placeholder)."
	@echo "  test             - Run tests (placeholder)."
	@echo "  clean            - Remove Python cache files and other temporary files."
	@echo ""
	@echo "Before running 'run-docker-scan' or 'run-cli-scan', you might want to "
	@echo "customize the INPUT_FILE and OUTPUT_PREFIX variables in this Makefile."

# Configuration for scan commands (customize as needed)
INPUT_FILE ?= data/sample_inputs/example_ips.txt
OUTPUT_PREFIX ?= data/cli_outputs/make_scan_results
NMAP_OPTIONS ?= "-T4 -F"
FORMATS ?= json,csv,md

# Check if virtual environment is activated, otherwise use system python/pip
VENV_PYTHON = $(shell command -v python || echo "python")
VENV_PIP = $(shell command -v pip || echo "pip")

install:
	@echo "Installing Python dependencies from requirements.txt..."
	$(VENV_PIP) install -r requirements.txt
	@echo "Dependencies installed."

build-docker:
	@echo "Building Docker image 'nmap_parallel_scanner'..."
	docker build -t nmap_parallel_scanner .
	@echo "Docker image built."

run-docker-scan:
	@echo "Running Nmap scan via Docker..."
	@echo "Ensure Docker is running."
	@echo "Using input: $(INPUT_FILE), output prefix: $(OUTPUT_PREFIX)"
	@echo "Nmap options: $(NMAP_OPTIONS), Formats: $(FORMATS)"
	mkdir -p $$(dirname $(OUTPUT_PREFIX)) # Ensure host output directory exists
	docker run --rm 		-v "$$(pwd)/$(INPUT_FILE):/inputs/$(shell basename $(INPUT_FILE))" 		-v "$$(pwd)/$$(dirname $(OUTPUT_PREFIX)):/outputs" 		nmap_parallel_scanner 		-i /inputs/$(shell basename $(INPUT_FILE)) 		-o /outputs/$(shell basename $(OUTPUT_PREFIX)) 		--nmap-options "$(NMAP_OPTIONS)" 		--formats "$(FORMATS)"
	@echo "Docker scan finished. Results should be in $(OUTPUT_PREFIX).*"

run-cli-scan:
	@echo "Running Nmap scan via local Python script..."
	@echo "Ensure Nmap is installed and in your PATH, and you are in an active virtual environment if desired."
	@echo "Using input: $(INPUT_FILE), output prefix: $(OUTPUT_PREFIX)"
	@echo "Nmap options: $(NMAP_OPTIONS), Formats: $(FORMATS)"
	mkdir -p $$(dirname $(OUTPUT_PREFIX))
	$(VENV_PYTHON) nmap_parallel_scanner.py 		-i $(INPUT_FILE) 		-o $(OUTPUT_PREFIX) 		--nmap-options "$(NMAP_OPTIONS)" 		--formats "$(FORMATS)"
	@echo "CLI scan finished. Results should be in $(OUTPUT_PREFIX).*"

start-webui:
	@echo "Starting Flask web UI..."
	@echo "Make sure you have generated some JSON scan results in data/cli_outputs/ or configure app.py."
	@echo "Access at http://127.0.0.1:5000 (or as indicated by Flask)"
	$(VENV_PYTHON) web_ui/app.py

lint:
	@echo "Running linters (placeholder)..."
	@echo "To implement, add your linting commands here (e.g., flake8 src/ tests/ nmap_parallel_scanner.py)."

test:
	@echo "Running tests (placeholder)..."
	@echo "To implement, add your test commands here (e.g., python -m unittest discover -s tests)."

clean:
	@echo "Cleaning up..."
	find . -type f -name '*.py[co]' -delete
	find . -type d -name '__pycache__' -delete -print
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -f .coverage
	@echo "Clean up complete."
