# Module Overview

This project is organised into several modules that coordinate network scans and result processing. The following list highlights recently added components.

## Configuration (`src/config.py`)
Defines constants used across the project, such as the default path for the SQLite state database.

## Database Repository (`src/db_repository.py`)
Provides a lightweight layer for storing and retrieving host information in a SQLite database. It includes simple CRUD helpers and queries by status.

## Asynchronous Runner (`src/runner.py`)
Runs shell commands concurrently with configurable timeouts and concurrency limits. Jobs are described using the `RunnerJob` dataclass and executed via `run_jobs`.

## Reporting Utilities (`src/reporting.py`)
Summarises scan data stored in the database and exports reports. Helpers return slowest or failed jobs and can write summaries to JSON or CSV.

## Database Package (`src/db/`)
Contains SQLAlchemy models and helpers for a richer persistence layer. It defines objects for scan runs, targets, batches, jobs and results along with session management utilities.

