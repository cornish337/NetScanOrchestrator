# Installation Guide

Follow these steps to set up the NetScan Orchestrator.

## Prerequisites

- **Python 3.7+**: Ensure you have a compatible version of Python installed.
- **Nmap**: The core scanning functionality relies on the Nmap command-line tool. You must install it on your system and ensure it is available in your system's PATH.

## Installation

The recommended way to install NetScan Orchestrator is using `pip` within a Python virtual environment.

1.  **Clone the repository:**
    If you haven't already, clone the project repository to your local machine.

2.  **Create and activate a virtual environment:**
    From the project's root directory, run the following commands. Using a virtual environment is a best practice to avoid conflicts with other Python projects.

    ```bash
    # Create the virtual environment
    python3 -m venv venv

    # Activate the virtual environment
    # On macOS and Linux:
    source venv/bin/activate
    # On Windows:
    # venv\Scripts\activate
    ```
    You will know the environment is active when you see `(venv)` at the beginning of your command prompt.

3.  **Install the package:**
    With the virtual environment active, install the package using `pip`. This command will also install all the necessary dependencies from `requirements.txt`.

    For regular use:
    ```bash
    pip install .
    ```

    For development (this allows you to edit the code and have the changes immediately reflected without reinstalling):
    ```bash
    pip install -e .
    ```

## Verifying the Installation

Once the installation is complete, a new command-line tool called `netscan` will be available in your environment. You can verify that it's installed correctly by running:

```bash
netscan --help
```

This should display the main help menu with a list of available commands, confirming that the installation was successful. You are now ready to use the NetScan Orchestrator. See the [Usage Guide](USAGE.md) for details on how to run scans.
