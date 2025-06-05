
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

## Architecture Overview

The Nmap Parallel Scanner consists of several core components:

- **IP Handler (`src/ip_handler.py`):** Responsible for reading IP targets from a file and dividing them into chunks.
- **Nmap Scanner (`src/nmap_scanner.py`):** Interfaces with the `nmap` command-line tool (via the `python-nmap` library) to perform scans on individual chunks.
- **Parallel Scanner (`src/parallel_scanner.py`):** Manages the parallel execution of Nmap scans using `multiprocessing.Pool`.
- **Results Handler (`src/results_handler.py`):** Consolidates results from all scanned chunks and handles their conversion into various output formats.
- **CLI (`nmap_parallel_scanner.py`):** The main entry point for users, built with `argparse`. It orchestrates the scanning process based on user inputs.
- **Web UI (`web_ui/app.py`):** A Flask application for viewing previously generated JSON scan results. It does not initiate scans but provides a way to browse reports.

## Setup Instructions

### Local Setup

**Prerequisites:**
- Python 3.7+
- Nmap (must be installed and accessible in your system's PATH)

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

3.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```


## Usage

1.  Start the Flask web server:
    ```bash
    python web_ui/app.py
    ```
2.  Open your web browser and navigate to `http://127.0.0.1:5000`.
3.  Enter the IP addresses or hostnames to scan and click "Scan".

## Contributing

Contributions are welcome! Please follow these steps:

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/your-feature-name`).
3.  Make your changes.
4.  Commit your changes (`git commit -am 'Add some feature'`).
5.  Push to the branch (`git push origin feature/your-feature-name`).
6.  Create a new Pull Request.
=======
### Docker Setup

**Prerequisites:**
- Docker installed and running.

**Steps:**
1.  **Build the Docker image:**
    From the project root directory (where the `Dockerfile` is located):
    ```bash
    docker build -t nmap_parallel_scanner .
    ```

2.  **Run the Docker container:**
    You'll typically want to mount volumes for your input IP list and for the output results.

    Example:
    ```bash
    # Create directories on your host for input and output
    mkdir -p ./my_scan_inputs
    mkdir -p ./my_scan_outputs

    # Place your IP list file (e.g., my_ips.txt) in ./my_scan_inputs/
    # For example, copy the sample: cp data/sample_inputs/example_ips.txt ./my_scan_inputs/my_ips.txt
    # (Ensure my_ips.txt is used in the docker run command below)

    docker run --rm -v "$(pwd)/my_scan_inputs:/inputs" -v "$(pwd)/my_scan_outputs:/outputs" \
        nmap_parallel_scanner \
        -i /inputs/my_ips.txt \
        -o /outputs/scan_report \
        --formats json,csv,md \
        --nmap-options "-sV -T4"
    ```
    - `--rm`: Automatically removes the container when it exits.
    - `-v "$(pwd)/my_scan_inputs:/inputs"`: Mounts `./my_scan_inputs` on your host to `/inputs` in the container.
    - `-v "$(pwd)/my_scan_outputs:/outputs"`: Mounts `./my_scan_outputs` on your host to `/outputs` in the container.
    - The `-i` and `-o` paths are relative to the container's filesystem.

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

    If running the main application (CLI scanner) via Docker, the web UI is not automatically started as part of that `docker run` command. You would need to run the web UI separately, potentially in another Docker container with access to the JSON output volume, or on your host machine if it can access the JSON files.

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
```

