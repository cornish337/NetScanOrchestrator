# Module Overview

The NetScan Orchestrator is organized into several Python packages and modules within the `src` directory. This document provides an overview of their roles.

## `cli` (`src/cli/`)
This package contains the main entry point for the command-line interface.
- **`main.py`**: A [Typer](https://typer.tiangolo.com/) application that defines all the `netscan` commands (`ingest`, `plan`, `run`, etc.) and orchestrates the application workflow.

## `db` (`src/db/`)
This package manages all database interactions using [SQLAlchemy](https://www.sqlalchemy.org/).
- **`models.py`**: Defines the SQLAlchemy ORM models (`Target`, `ScanRun`, `Batch`, `Job`, `Result`) that represent the database schema.
- **`repository.py`**: Provides convenience functions for all Create, Read, Update, and Delete (CRUD) operations on the database models.
- **`session.py`**: Manages the database connection and session lifecycle.

## Core Logic Modules (`src/`)

- **`ip_handler.py`**: Contains utilities for parsing and expanding target IP addresses and ranges from input files.
- **`nmap_scanner.py`**: A wrapper around the `python-nmap` library that executes Nmap scans for a given set of targets.
- **`runner.py`**: An asynchronous runner that executes scan jobs with concurrency limits and timeout handling. It uses `asyncio` to manage parallel processes.
- **`reporting.py`**: Provides functions to query the database and generate summary data, such as the slowest jobs or failed jobs. This module powers the `netscan status` command.
- **`results_handler.py`**: This module is currently **unused** in the main CLI workflow but contains functions for consolidating and formatting scan results into various file types (JSON, CSV, etc.). Its functionality has been largely superseded by the database-driven approach.

## `web_ui` (`web_ui/`)
This directory contains a simple Flask-based web application.
- **`app.py`**: The main Flask application file.
- **`templates/`**: Contains the HTML templates for the web interface.
**Note:** The web UI is not fully integrated with the new database-driven workflow and may not be fully functional. See the project `README.md` for more details on its status.
