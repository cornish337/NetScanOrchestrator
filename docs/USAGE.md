# Usage Guide

## SQLite State File

NetScanOrchestrator persists scan metadata and job progress in a local SQLite database.
The database file is created automatically on the first run if it does not already exist.

* **Default location:** `~/.netscan_orchestrator/state.sqlite`
  * The directory is created on demand when the scanner first runs.
* **Override path:**
  * Set the `NSO_STATE_FILE` environment variable to point to a custom file, **or**
  * Pass `--state-db /path/to/custom_state.sqlite` to the CLI tool.

Example overriding the location:

```bash
export NSO_STATE_FILE=/tmp/nso_custom.sqlite
python nmap_parallel_scanner.py -i data/sample_inputs/example_ips.txt -o data/cli_outputs/custom_run --state-db "$NSO_STATE_FILE"
```

## Repository Helpers

Helper utilities are provided to inspect the state database and diagnose scan behaviour.

### Identify Slow Jobs

```bash
python scripts/repo_helpers.py slow-jobs --limit 10
```
Displays the ten jobs with the largest recorded durations.

### Inspect Problematic Targets

```bash
python scripts/repo_helpers.py target-details --failed
python scripts/repo_helpers.py target-details --host 192.0.2.42
```
The first command lists all targets that failed during scanning.
The second drills into a specific host for its error history.

These helpers read from the same SQLite state file described above, so the `NSO_STATE_FILE`
environment variable or `--state-db` option also affects them.
