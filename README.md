# NetScan Orchestrator

NetScan Orchestrator is a Python-based framework for managing and executing Nmap scans against a large number of targets. It provides a command-line interface (CLI) to ingest targets, plan scan runs, and execute them in parallel, with all metadata and results stored in a local SQLite database.

## Features

- **Database-Driven Workflow:** Manages targets, scan runs, batches, and results in a SQLite database for persistent state.
- **Parallel Scanning:** Executes Nmap scans concurrently to efficiently scan large numbers of targets.
- **Command-Line Interface:** A powerful CLI (built with Typer) provides a structured workflow for managing scans.
- **Flexible Target Input:** Reads IP addresses, CIDR notations, and hyphenated ranges from a text file.
- **Status Reporting:** The CLI can provide summaries of scan runs, including failed jobs and the slowest-running jobs.

## Architecture Overview

The application is structured as a Python package with the following key components:

- **CLI (`src/cli/main.py`):** The main entry point for the `netscan` command, orchestrating the entire workflow.
- **Database Layer (`src/db/`):** SQLAlchemy models and a repository pattern for all database interactions.
- **Core Logic (`src/`):** Modules for handling IP addresses, running Nmap scans, and generating reports.
- **Web API (`web_api/`):** A FastAPI-based web API for managing and monitoring network scans.

For more details on the modules, see the [Module Overview](docs/MODULES.md).

### Scan Request Flow

1. **Request:** A client submits a scan via `POST /api/scans`, handled by
   [`web_api/app.py`](web_api/app.py). The endpoint validates and expands the
   target list using [`src/ip_handler.py`](src/ip_handler.py) before creating a
   database record for the scan run and individual jobs.
2. **Job Creation:** Each target becomes a job in the database. The API spins
   up a background task (`scan_task_wrapper`) to process these jobs.
3. **Concurrent Execution:** The background task invokes
   [`run_jobs_concurrently`](src/runner.py) which uses `asyncio` to execute Nmap
   jobs in parallel, storing results and streaming updates.
4. **Result Retrieval:** Clients poll `GET /api/scans/{scan_id}` (also in
   `web_api/app.py`) or open the matching WebSocket to retrieve progress and the
   latest results.

## Getting Started

### Prerequisites

- Python 3.7+
- Nmap

### Installation

For detailed instructions on how to set up your environment and install the package, please see the [Installation Guide](docs/INSTALLATION.md).

In summary, you will need to:
1.  Set up a Python virtual environment.
2.  Install the package using `pip install .`.

### Usage

Once installed, the `netscan` command will be available. The general workflow is:
1.  `netscan ingest <your_ip_file.txt>`
2.  `netscan plan`
3.  `netscan split <scan_run_id>`
4.  `netscan run <scan_run_id>`
5.  `netscan status`

For a detailed walkthrough with examples, please see the [Usage Guide](docs/USAGE.md).

### Running with Docker

A `docker-compose.yml` file is provided to run the application inside a container. To build the image and start the service, run:

```bash
docker compose up --build
```

The web API will be accessible at http://localhost:8000.

### Production Deployment

For production use, run the FastAPI application with Gunicorn and Uvicorn workers:

```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker web_api.app:app -b 0.0.0.0:8000
```


