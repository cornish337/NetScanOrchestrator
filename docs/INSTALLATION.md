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

## Running with Docker (Recommended for Web UI)

The easiest way to run the NetScan Orchestrator, including the web interface, is with Docker.

### Prerequisites

- **Docker**: You must have Docker installed and running on your system.
- **Docker Compose**: This project uses `docker-compose` to orchestrate the services.

### Building and Running

From the root of the project directory, run the following command:

```bash
docker compose up --build
```

This command will:
1.  Build the Docker image for the application. This includes building the frontend UI and installing all Python dependencies.
2.  Start the application container.

The web interface will be available at `http://localhost:5000`.

## Running the Web API

This project includes a FastAPI-based web API that provides an alternative way to manage and monitor scans.

### Prerequisites

The web API dependencies (`fastapi`, `uvicorn`, etc.) are included in the `requirements.txt` file and will be installed automatically when you follow the installation steps above.

### Starting the Server

To run the web API, use the `uvicorn` command from the root of the project directory:

```bash
# Ensure your virtual environment is active
source venv/bin/activate

# Run the server with auto-reload for development
uvicorn web_api.app:app --reload
```

The server will be available at `http://127.0.0.1:8000`. You can now interact with the API endpoints as described in the [Usage Guide](USAGE.md).
