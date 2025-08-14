# Usage Guide

NetScan Orchestrator uses a command-line interface (CLI) called `netscan` to manage and execute scans. The workflow is divided into several stages: ingesting targets, planning a scan run, splitting the run into batches, executing the scan, and viewing the status.

## Database State

All metadata about targets, scan runs, and job results is stored in a local SQLite database.

- **Default Location:** The database is created at `.netscan_orchestrator/state.db` in the directory where you run the `netscan` command.
- **Custom Location:** You can specify a different path for the database using the global `--db-path` option. For example: `netscan --db-path /tmp/my_scan.db status`.

## CLI Workflow and Commands

Here is a typical workflow using the `netscan` command. All commands support `--help` for more details (e.g., `netscan ingest --help`).

### 1. Ingest Targets

First, you need to create a list of IP addresses or network ranges you want to scan. Create a simple text file with one target per line. An example can be found in `data/sample_inputs/example_ips.txt`.

Use the `ingest` command to load these targets into the database.

**Command:**
```bash
netscan ingest [OPTIONS] INPUT_FILE
```

**Example:**
```bash
netscan ingest data/sample_inputs/example_ips.txt
```
This command will read the specified file and create a `Target` record for each address in the database.

### 2. Plan a Scan Run

Next, create a `ScanRun`. This represents a single, cohesive scanning effort. You can add notes or specify the Nmap options you intend to use for this run.

**Command:**
```bash
netscan plan [OPTIONS]
```

**Example:**
```bash
# Plan a run with specific nmap options
netscan plan --options "-sV -T4 --open" --notes "Service version scan for open ports."

# The command will output the ID of the new scan run, e.g.:
# Created scan run 1
```
Make a note of the `ScanRun` ID, as you will need it for the next steps.

### 3. Split the Run into Batches

Now, divide the targets into smaller `Batches` for parallel processing. The `split` command takes the `ScanRun` ID and a `--chunk-size` to determine how many targets go into each batch.

**Command:**
```bash
netscan split [OPTIONS] SCAN_RUN_ID
```

**Example:**
```bash
# Split scan run 1 into batches of 5 targets each
netscan split 1 --chunk-size 5
```

### 4. Execute the Scan

With the batches created, you can now execute the scan using the `run` command. This will process all the batches associated with the specified `ScanRun` ID in parallel.

**Command:**
```bash
netscan run [OPTIONS] SCAN_RUN_ID
```

**Example:**
```bash
# Execute scan run 1
netscan run 1

# You can also control the job concurrency and timeout
netscan run 1 --concurrency 8 --timeout-sec 60
```
This command will execute the Nmap scans and store the results in the database.

### 5. Check the Status

Finally, you can view the status of all your scan runs, see the slowest jobs, and identify any jobs that failed.

**Command:**
```bash
netscan status [OPTIONS]
```

**Example:**
```bash
# Display a summary report in the console
netscan status

# You can also export the summary to JSON or CSV
netscan status --json-out scan_summary.json --csv-out scan_summary.csv
```

### Other Commands

- **`resplit`**: This command allows you to take an existing batch and split it into smaller child batches. This can be useful for retrying a subset of targets from a failed batch.
- **`--db-path` (Global Option)**: Use this option before any command to specify a different database file for that operation.
  ```bash
  netscan --db-path /path/to/another.db ingest new_ips.txt
  ```
