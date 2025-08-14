# Installation and Running Guide

Follow these steps to set up the NetScan Orchestrator and run basic scans.

## Prerequisites
- Python 3.8 or newer
- Nmap (optional for real network scans but required for full functionality)

## Installation
```bash
git clone https://github.com/yourusername/nmap-parallel-scanner.git
cd nmap-parallel-scanner
python -m venv venv
source venv/bin/activate  # On Windows use venv\Scripts\activate
pip install -r requirements.txt
```

## Running the Command Line Interface
The Typer-based CLI coordinates ingesting targets, planning runs and executing batches.

```bash
python -m src.cli.main ingest data/sample_inputs/example_ips.txt
python -m src.cli.main plan
python -m src.cli.main split 1 --chunk-size 5
python -m src.cli.main run 1
python -m src.cli.main status
```

## Running the Web UI
Generate JSON output with the CLI and then start the Flask application:
```bash
python web_ui/app.py
```
The interface lists available reports under `http://localhost:5000`.
