
# Nmap Parallel Scanner

Nmap Parallel Scanner is a Python-based framework designed to run Nmap scans against a large number of IP addresses or ranges in parallel. It breaks down the target list into smaller chunks, executes Nmap scans concurrently, and then consolidates the results. This approach helps in efficiently scanning large networks and quickly identifying responsive hosts and open ports, especially when some targets might significantly slow down a monolithic scan.

## Features

- **Parallel Scanning:** Leverages Python's `multiprocessing` module to run multiple Nmap instances simultaneously.
- **Flexible Target Input:** Reads IP addresses, CIDR notations, and hyphenated ranges from a text file.
- **Chunking:** Divides the target list into manageable chunks based on user-defined size.
- **Consolidated Results:** Merges scan outputs from all chunks into a unified dataset.
- **Multiple Output Formats:** Saves scan results in JSON, CSV, TXT, Markdown, and custom XML formats.
- **Command-Line Interface (CLI):** Provides a robust CLI for configuring and running scans.
- **Basic Web UI:** Includes a simple Flask-based web interface to view generated JSON scan reports.
- **Scan Management:** Offers insights into scan coverage, detailing which IPs were successfully scanned, which failed, and which remain unscanned.
- **Docker Support:** Can be built and run as a Docker container, bundling Nmap and all dependencies.

## State Database

The CLI persists targets and scan metadata in a SQLite database. By default the database file is created at `.netscan_orchestrator/state.db` in the current working directory. Use the `--db-path` option to point to a different location if needed. The database and its parent directory are created automatically on first use.

## Architecture Overview

The Nmap Parallel Scanner consists of several core components:

- **IP Handler (`src/ip_handler.py`):** Responsible for reading IP targets from a file and dividing them into chunks.
- **Nmap Scanner (`src/nmap_scanner.py`):** Interfaces with the `nmap` command-line tool (via the `python-nmap` library) to perform scans on individual chunks.
- **Parallel Scanner (`src/parallel_scanner.py`):** Manages the parallel execution of Nmap scans using `multiprocessing.Pool`.
- **Results Handler (`src/results_handler.py`):** Consolidates results from all scanned chunks and handles their conversion into various output formats.
- **CLI (`nmap_parallel_scanner.py`):** The main entry point for users, built with `argparse`. It orchestrates the scanning process based on user inputs.
- **Web UI (`web_ui/app.py`):** A Flask application for viewing previously generated JSON scan results. It does not initiate scans but provides a way to browse reports.
- **Configuration (`src/config.py`):** Central location for default settings such as the path to the state database.
- **Database Layer (`src/db/` and `src/db_repository.py`):** SQLAlchemy models and repository helpers for managing targets, runs and jobs.
- **Asynchronous Runner (`src/runner.py`):** Executes scan jobs with concurrency limits and timeout handling.
- **Reporting Utilities (`src/reporting.py`):** Generates summaries of runs and jobs and can export them to JSON or CSV.

Further details on these modules can be found in [`docs/MODULES.md`](docs/MODULES.md).

## Setup Instructions

For a concise walkthrough of installation and executing scans, refer to [`docs/INSTALLATION.md`](docs/INSTALLATION.md).

### Local Setup

**Prerequisites:**
- Python 3.7+
- Nmap: This is the primary system-level dependency. Ensure Nmap is installed and accessible in your system's PATH for the scanner to function correctly.

**Steps:**
1.  **Clone the repository:**
    ```bash
    git clone https://github.com/yourusername/nmap-parallel-scanner.git # Replace with your repo URL if applicable
    cd nmap-parallel-scanner
    ```
    *(If you cloned from a generic source, replace `<repository_url>` above with the actual URL or remove the line if working from a local copy.)*

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies using the Makefile or pip:**
    ```bash
    make install
    # OR
    # pip install -r requirements.txt
    ```

=======
### Docker Setup

**Prerequisites:**
- **Docker installed and running.**

**1. Building the Docker Image:**

The recommended way to build the image is using the Makefile:
```bash
make build-docker
```
This uses `docker build` internally and tags the image as `nmap_parallel_scanner`.
Alternatively, you can run the Docker command directly:
```bash
docker build -t nmap_parallel_scanner .
```

**2. Running the CLI Scanner in Docker:**

The easiest way to run a scan using Docker is with the Makefile target:
```bash
make run-docker-scan
```
This command uses pre-defined variables in the `Makefile` for the input file (`data/sample_inputs/example_ips.txt`) and output prefix (`data/cli_outputs/make_scan_results`). It handles mounting the necessary volumes for inputs and outputs. You can customize these variables in the Makefile or override them on the command line (see Makefile section below).

For more custom scenarios, or to understand what the `make` target does, you can use `docker run` directly. The `make run-docker-scan` target effectively runs a command similar to this:
```bash
# Ensure your input directory (e.g., ./data/sample_inputs) and output directory (e.g., ./data/cli_outputs) exist.
# The Makefile target creates the output directory automatically.
docker run --rm \
    -v "$(pwd)/data/sample_inputs:/inputs" \
    -v "$(pwd)/data/cli_outputs:/outputs" \
    nmap_parallel_scanner \
    -i /inputs/example_ips.txt \
    -o /outputs/make_scan_results \
    --formats json,csv,md \
    --nmap-options "-T4 -F"
    # Note: paths like /inputs/example_ips.txt and /outputs/make_scan_results are paths *inside* the container.
```
Key points:
- `--rm`: Automatically removes the container when it exits.
- `-v "$(pwd)/data/sample_inputs:/inputs"`: Mounts your local `./data/sample_inputs` directory to `/inputs` inside the container.
- `-v "$(pwd)/data/cli_outputs:/outputs"`: Mounts your local `./data/cli_outputs` directory to `/outputs` inside the container.

**3. Running the Web UI in Docker:**

The Web UI can be run using the same `nmap_parallel_scanner` Docker image by overriding the default entrypoint. It's designed for *viewing* scan results that have been previously generated by the CLI scanner (either local or Dockerized).

The recommended way is using the Makefile:
```bash
make start-docker-webui
```
This command:
- Starts the Flask application server within a Docker container named `nmap_webui`.
- Maps port 5000 from the container to port 5000 on your host.
- Mounts your local `data/cli_outputs` directory to `/app/data/cli_outputs` in the container, so the Web UI can find the JSON scan results.
- Mounts your local `data/sample_inputs` directory (for consistency, though not strictly used by the current UI).
- The Web UI will be accessible at `http://localhost:5000`.

To stop the Web UI container:
```bash
make stop-docker-webui
```

Alternatively, the `make start-docker-webui` target runs a command similar to this:
```bash
# Ensure data/cli_outputs exists on your host
mkdir -p data/cli_outputs

docker run -d --rm --name nmap_webui -p 5000:5000 \
    -v "$(pwd)/data/cli_outputs:/app/data/cli_outputs" \
    -v "$(pwd)/data/sample_inputs:/app/data/sample_inputs" \
    --entrypoint python nmap_parallel_scanner web_ui/app.py
```
- `-d`: Runs the container in detached mode (in the background).
- `--name nmap_webui`: Assigns a name to the container for easy reference (e.g., for stopping or viewing logs).
- `--entrypoint python`: Overrides the default entrypoint to execute `python`.
- `web_ui/app.py`: Is the command passed to the new entrypoint (`python`).

### Using the Makefile

A `Makefile` is provided in the root of the project to simplify common operations.

Here are some common targets:
-   `make help`: Displays a help message listing all available targets.
-   `make install`: Installs Python dependencies from `requirements.txt` (ideally into an active virtual environment).
-   `make build-docker`: Builds the Docker image for the scanner, tagging it as `nmap_parallel_scanner`.
-   `make run-cli-scan`: Runs an Nmap scan using the local Python script. Input/output locations are defined by variables in the Makefile.
-   `make run-docker-scan`: Runs an Nmap scan using the Docker container. Input/output locations are defined by variables in the Makefile and mounted into the container.
-   `make start-webui`: Starts the Flask web UI locally (using your system's Python) for viewing scan results from `data/cli_outputs/`.
-   `make start-docker-webui`: Starts the Flask web UI in a Docker container, serving results from `data/cli_outputs/` (mounted volume).
-   `make stop-docker-webui`: Stops the Web UI Docker container.
-   `make clean`: Removes Python cache files (`.pyc`, `__pycache__`), Pytest cache, coverage data, etc.

You can customize scan parameters for `run-cli-scan` and `run-docker-scan` directly within the `Makefile` by editing variables like `INPUT_FILE`, `OUTPUT_PREFIX`, `NMAP_OPTIONS`, and `FORMATS`. Alternatively, you can override these variables from the command line when invoking `make`. For example:
```bash
make run-cli-scan INPUT_FILE=path/to/your_custom_ips.txt OUTPUT_PREFIX=results/custom_scan_results
```
This allows for flexible scan execution without modifying the Makefile itself for each run.

## Usage

### Command-Line Interface (CLI)

The main script is `nmap_parallel_scanner.py`.

```bash
python nmap_parallel_scanner.py [OPTIONS]
```

**CLI Arguments:**

-   `-i INPUT_FILE`, `--input-file INPUT_FILE` (required)
    -   Path to the file containing IP addresses/ranges (one per line).
    -   An example is provided: `data/sample_inputs/example_ips.txt`

-   `-o OUTPUT_PREFIX`, `--output-prefix OUTPUT_PREFIX` (required)
    -   Prefix for output file names (e.g., `scan_results`).
    -   If a path is included (e.g., `data/cli_outputs/scan_report`), the directory will be created if it doesn't exist.

-   `-f FORMATS`, `--formats FORMATS` (optional)
    -   Comma-separated list of output formats (json, csv, txt, md, xml).
    -   Default: `json,csv,txt,md,xml` (all formats).

-   `--chunk-size CHUNK_SIZE` (optional)
    -   Number of IPs per chunk for parallel scanning.
    -   Default: `10`.

-   `--select-chunks` (optional)
    -   After displaying the list of chunks, prompt to choose specific chunk numbers to scan.
    -   Press Enter to scan all chunks.

-   `--num-processes NUM_PROCESSES` (optional)
    -   Number of parallel Nmap processes.
    -   Default: Number of CPU cores on your system.

-   `--nmap-options NMAP_OPTIONS` (optional)
    -   Nmap command-line options string. Enclose in quotes if it contains spaces.
    -   Default: `"-T4 -F"` (Fast scan, default top 100 ports).
    -   Example: `"-sV -p 1-1000 --open"` (Service version detection, scan ports 1-1000, only show open ports).

**Example CLI Commands:**

1.  **Basic scan using the example IP list, outputting all formats to `data/cli_outputs`:**
    ```bash
    python nmap_parallel_scanner.py -i data/sample_inputs/example_ips.txt -o data/cli_outputs/example_scan_results
    ```

2.  **Scan with specific Nmap options, custom chunk size, and only JSON/CSV output:**
    ```bash
    python nmap_parallel_scanner.py \
        -i data/sample_inputs/example_ips.txt \
        -o data/cli_outputs/my_custom_scan \
        -f json,csv \
        --chunk-size 5 \
        --nmap-options "-sS -A -T3"
    ```

### Web Interface (for viewing results)

The web UI is a simple Flask application to view *previously generated JSON results*. It does not initiate scans.

1.  **Ensure you have JSON output files** from the CLI in a known directory. The default directory configured in `web_ui/app.py` is `data/cli_outputs/`. You can generate a JSON file using the CLI, for example:
    ```bash
    python nmap_parallel_scanner.py -i data/sample_inputs/example_ips.txt -o data/cli_outputs/web_ui_test -f json
    ```
2.  **Run the Flask app from the project root directory:**
    ```bash
    python web_ui/app.py
    ```
3.  **Access in your browser:**
    Open `http://127.0.0.1:5000/` (or the address shown in the terminal, usually `http://<your_ip>:5000/` if listening on `0.0.0.0`).
    You will see a list of available JSON files from the `data/cli_outputs/` directory. Click to view a formatted version of the scan report.
    For the Dockerized Web UI, use `make start-docker-webui` and `make stop-docker-webui`.

## Testing

The project includes both unit tests (for individual modules) and integration tests (for the CLI tool).

**Running Tests:**

1.  Ensure you have followed the **Local Setup** instructions and activated your virtual environment.
2.  From the project root directory, run the following command to discover and execute all tests in the `tests/` directory:

    ```bash
    python -m unittest discover tests
    ```

    Or, to run a specific test file:
    ```bash
    python -m unittest tests.test_ip_handler
    python -m unittest tests.test_cli_integration
    ```

**Notes on Integration Tests:**
- The CLI integration test (`tests/test_cli_integration.py`) performs a live Nmap scan against an external host (`scanme.nmap.org`). This test may take a few minutes to complete.
- This live test is automatically skipped when running in GitHub Actions environments to prevent potential flakiness or network policy issues.

## Output Formats

The scanner can generate reports in the following formats:

-   **JSON (`.json`):** Detailed, structured data, suitable for machine parsing or as input for other tools. Contains all information including host details, ports, services, and scan statistics.
-   **CSV (`.csv`):** Comma-Separated Values, primarily listing open/detailed ports per host. Good for quick analysis in spreadsheet software. Columns include Host_IP, Hostname, Protocol, Port_ID, State, Service_Name, Product, Version, etc.
-   **Text (`.txt`):** Human-readable summary of the scan, including overall stats, details for each host (status, open ports), and any errors.
-   **Markdown (`.md`):** Similar to Text but formatted with Markdown for better readability, using tables for port details and errors.
-   **XML (`.xml`):** A custom XML format representing the consolidated scan data, including stats, host details (hostnames, status, ports with service info), and errors.

## Scan Management & Coverage

After each scan, the CLI provides a "Scan Coverage & Status" summary:

-   **Total unique IPs/targets provided:** The total number of unique targets parsed from your input file.
-   **IPs with scan data (hosts found):** IPs for which Nmap returned detailed scan information (e.g., open/closed ports, OS info). These are hosts considered "up" or responsive enough for Nmap to gather data.
-   **IPs without scan data (down/filtered/error):** These are targets that were processed by Nmap, but no detailed host information (like open ports) was gathered. This can occur if:
    -   The host was down or unresponsive to the specific Nmap probes used.
    -   The host was up but filtered all scanned ports according to Nmap's perspective.
    -   Nmap options used (e.g., `--open`) meant only certain conditions were reported, and those conditions weren't met.
    -   The target was part of a chunk where Nmap execution failed for other reasons (see next point).
-   **IPs from chunks with execution errors:** For these IPs, the Nmap command itself failed to run correctly for their chunk (e.g., due to a syntax error in Nmap options that Nmap rejected, Nmap crashing, or Nmap not being found by a subprocess).

If you see IPs in the "IPs without scan data" or "IPs from chunks with execution errors" lists, you might consider:
-   Checking your Nmap options for correctness and suitability for the targets.
-   Verifying the targets are actually reachable and not firewalled in a way that prevents any response.
-   Creating a new input file with these specific IPs for a targeted re-scan, perhaps with different Nmap options (e.g., a simple ping scan `-sn` first, or more aggressive timing if timeouts are suspected, or fewer probes if overwhelming a target).
-   Reviewing any error messages in the console output or in the `errors` section of the JSON/XML reports for clues.

This project aims to provide a flexible and efficient way to conduct large-scale network reconnaissance.

